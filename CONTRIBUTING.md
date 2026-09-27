# Contributing

Thanks for improving Local Planner. The project is intentionally small, local-first, and test-driven.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Optional pre-commit hook:

```bash
python -m pip install pre-commit
pre-commit install
```

Ollama is not required for the unit test suite. For end-to-end planning, start Ollama and pull the configured model:

```bash
ollama pull qwen2.5:7b-instruct
uvicorn main:app --reload
```

## Contribution workflow

1. Open or reference an issue for non-trivial changes.
2. Keep changes focused and add tests for behavior changes.
3. Run `pytest` and `ruff check .` before opening a PR.
4. Explain user-visible behavior, trade-offs, and test evidence in the PR description.
5. Do not commit secrets, private prompts, proprietary data, or model weights.

Good first contributions include evaluation cases, deterministic validators, backend adapters, documentation, and performance measurements.
