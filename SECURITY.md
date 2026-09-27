# Security Policy

## Supported versions

The latest release on the default branch receives security fixes.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could put users at risk. Use GitHub's private vulnerability reporting feature for this repository when available. Include reproduction steps, affected versions, impact, and any suggested mitigation.

Local Planner sends prompts to the configured Ollama endpoint. Keep Ollama on a trusted network, do not expose it publicly without authentication and network controls, and treat generated plans as untrusted model output that must be reviewed before execution.
