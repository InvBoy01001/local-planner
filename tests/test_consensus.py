import pytest

pytest.importorskip("ollama")
import ollama_client


@pytest.mark.asyncio
async def test_consensus_red_flags_invalid_then_accepts_repeated_candidate(monkeypatch):
    outputs = iter(
        [
            {"error": "JSON_DECODE_FAILED"},
            {"items": [1, 2]},
            {"items": [1, 2, 3]},
            {"items": [1, 2, 3]},
        ]
    )

    async def fake_generate(*args, **kwargs):
        return next(outputs)

    monkeypatch.setattr(ollama_client, "async_generate_json", fake_generate)
    result = await ollama_client.generate_with_consensus(
        "prompt", ["items"], k=2, max_attempts=4
    )
    assert result == {"items": [1, 2, 3]}
