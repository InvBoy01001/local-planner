"""Ollama transport and exact-output consensus helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

import httpx
import ollama
from ollama import ResponseError

from config import settings

logger = logging.getLogger(__name__)

OLLAMA_URL = f"{settings.ollama_host}/api/generate"
DEFAULT_MODEL = settings.ollama_model
_REQUEST_SEMAPHORE = asyncio.Semaphore(settings.ollama_max_concurrency)


class PlannerBackendError(RuntimeError):
    """Raised when the local model backend cannot produce a usable response."""


async def _aclose_ollama_client(client: ollama.AsyncClient) -> None:
    """Close the wrapped HTTP client used by older/newer Ollama SDK variants."""
    http = getattr(client, "_client", None)
    if http is not None and hasattr(http, "aclose"):
        await http.aclose()


def _list_bounds(
    key: str,
    list_lengths: dict[str, tuple[int, int]] | None,
) -> tuple[int, int]:
    if list_lengths and key in list_lengths:
        return list_lengths[key]
    return (3, 3)


def _canonicalize(candidate: dict[str, Any]) -> str:
    return json.dumps(candidate, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


async def async_generate_json(
    prompt: str,
    model: str | None = None,
    *,
    num_ctx: int = 4096,
    num_predict: int = 1024,
    temperature: float = 0.4,
) -> dict[str, Any]:
    """Generate one JSON object from the configured local Ollama model."""
    model = model or DEFAULT_MODEL
    async with _REQUEST_SEMAPHORE:
        client = ollama.AsyncClient(
            host=settings.ollama_host,
            trust_env=False,
            timeout=settings.ollama_timeout_seconds,
        )
        try:
            response = await client.generate(
                model=model,
                prompt=prompt,
                format="json",
                stream=False,
                options={
                    "num_ctx": num_ctx,
                    "num_predict": num_predict,
                    "temperature": temperature,
                },
            )
        except ResponseError as exc:
            raise PlannerBackendError(
                f"Ollama rejected the request at {settings.ollama_host}: {exc}"
            ) from exc
        except (httpx.HTTPError, OSError, ConnectionError) as exc:
            raise PlannerBackendError(
                f"Cannot reach Ollama at {settings.ollama_host}. "
                "Start Ollama or set OLLAMA_HOST to the correct server."
            ) from exc
        finally:
            await _aclose_ollama_client(client)

    result_text = getattr(response, "response", None) or ""
    if not isinstance(result_text, str):
        result_text = str(result_text)

    try:
        parsed = json.loads(result_text)
    except json.JSONDecodeError:
        return {"error": "JSON_DECODE_FAILED", "raw": result_text}

    if not isinstance(parsed, dict):
        return {"error": "JSON_OBJECT_REQUIRED", "raw": parsed}
    return parsed


async def check_ollama() -> dict[str, str | bool]:
    """Return a lightweight readiness result without triggering model generation."""
    client = ollama.AsyncClient(
        host=settings.ollama_host,
        trust_env=False,
        timeout=min(settings.ollama_timeout_seconds, 10.0),
    )
    try:
        await client.list()
        return {"ok": True, "host": settings.ollama_host, "model": DEFAULT_MODEL}
    except Exception as exc:  # readiness must degrade rather than crash the app
        logger.warning("Ollama readiness check failed: %s", exc)
        return {"ok": False, "host": settings.ollama_host, "model": DEFAULT_MODEL}
    finally:
        await _aclose_ollama_client(client)


async def generate_with_consensus(
    prompt: str,
    required_keys: list[str],
    *,
    list_lengths: dict[str, tuple[int, int]] | None = None,
    k: int = 2,
    max_attempts: int = 8,
    model: str | None = None,
    num_ctx: int = 4096,
    num_predict: int = 1024,
    temperature: float = 0.4,
) -> dict[str, Any]:
    """Vote over valid JSON outputs and return the first candidate ahead by ``k``.

    This is deliberately *exact-output* voting: canonical JSON must match exactly.
    Invalid JSON, missing keys, and invalid top-level list lengths are red-flagged
    before they can receive a vote.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    votes: defaultdict[str, int] = defaultdict(int)
    valid_responses: dict[str, dict[str, Any]] = {}

    for attempt in range(1, max_attempts + 1):
        candidate = await async_generate_json(
            prompt,
            model=model,
            num_ctx=num_ctx,
            num_predict=num_predict,
            temperature=temperature,
        )

        if "error" in candidate:
            logger.debug("Red-flagged candidate %s: %s", attempt, candidate["error"])
            continue

        missing_keys = [key for key in required_keys if key not in candidate]
        if missing_keys:
            logger.debug("Red-flagged candidate %s: missing %s", attempt, missing_keys)
            continue

        invalid_length = False
        for key in required_keys:
            value = candidate[key]
            if isinstance(value, list):
                low, high = _list_bounds(key, list_lengths)
                if not low <= len(value) <= high:
                    logger.debug(
                        "Red-flagged candidate %s: %s has %s items, expected %s-%s",
                        attempt,
                        key,
                        len(value),
                        low,
                        high,
                    )
                    invalid_length = True
                    break
        if invalid_length:
            continue

        canonical = _canonicalize(candidate)
        votes[canonical] += 1
        valid_responses[canonical] = candidate

        counts = sorted(votes.values(), reverse=True)
        top_votes = counts[0]
        second_votes = counts[1] if len(counts) > 1 else 0
        if top_votes - second_votes >= k:
            winner = next(key for key, count in votes.items() if count == top_votes)
            logger.info("Consensus reached on attempt %s with lead %s", attempt, top_votes - second_votes)
            return valid_responses[winner]

    if not votes:
        raise PlannerBackendError(
            "All model candidates were red-flagged. Try a stronger model, a simpler request, "
            "or larger OLLAMA context/output limits."
        )

    best = max(votes, key=votes.get)
    logger.info("Consensus threshold not reached; returning plurality candidate after %s attempts", max_attempts)
    return valid_responses[best]
