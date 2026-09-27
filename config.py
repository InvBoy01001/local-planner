"""Runtime configuration for Local Planner."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value < 1:
        raise ValueError(f"{name} must be >= 1, got {value}")
    return value


def _positive_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration loaded from environment variables at process startup."""

    app_name: str = "Local Planner"
    app_version: str = "0.2.0"
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    ollama_max_concurrency: int = _positive_int("OLLAMA_MAX_CONCURRENCY", 2)
    ollama_timeout_seconds: float = _positive_float("OLLAMA_TIMEOUT_SECONDS", 1000.0)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()
