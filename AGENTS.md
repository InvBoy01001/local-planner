# AGENTS.md

Guidance for coding agents and contributors working in this repository.

## Goals
- Preserve the local-first property: planning content must go only to the configured Ollama endpoint unless a feature explicitly documents otherwise.
- Keep model output untrusted. Validate structure deterministically before returning it.
- Prefer small, testable changes over prompt-only patches.

## Commands
- Install dev dependencies: `python -m pip install -e '.[dev]'`
- Tests: `pytest`
- Lint: `ruff check .`
- Run API: `uvicorn main:app --reload`

## Architecture boundaries
- `main.py`: HTTP surface only.
- `state_manager.py`: orchestration and plan assembly.
- `ollama_client.py`: model transport and consensus/red-flagging.
- `prompts.py`: prompt contracts.
- `plan_validation.py`: deterministic validation; do not put LLM calls here.
- `schemas.py`: public request/response contract.

Any change to output schema, consensus behavior, or prompt list cardinality should include regression tests and README updates when user-visible.
