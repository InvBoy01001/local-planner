# Changelog

All notable changes to this project are documented here.

## [0.2.0] - 2026-09-27

### Added
- Environment-driven Ollama configuration and readiness/liveness endpoints.
- Deterministic canonical story/task IDs and dependency remapping.
- Dependency integrity and cycle validation.
- Unit tests, Ruff linting, GitHub Actions CI, Docker/Compose, contribution and security docs.
- Complete public README and project metadata.

### Changed
- Renamed the orchestration class to `PlannerStateManager` while retaining `AragStateManager` as a compatibility alias.
- Replaced mutable Pydantic list defaults with `default_factory`.
- Replaced console prints with structured Python logging.
- Removed the custom package mirror from `requirements.txt`.

### Security
- API errors no longer expose arbitrary internal exception details.
