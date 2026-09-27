# Architecture

Local Planner is a local-first planning service. It deliberately separates probabilistic model generation from deterministic validation.

```text
User query
   │
   ▼
Domain classification
   │
   ├──────────────┬──────────────┐
   ▼              ▼              ▼
Role           Expertise       Gaps
   └──────────────┴──────────────┘
                  │
                  ▼
              3 Epics
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
     3 Stories / Epic  →  canonical IDs
        │
        ▼
     3 Tasks / Story   →  canonical IDs
        │
        ▼
   3 Sub-tasks / Task
        │
        ▼
Deterministic dependency/truncation validation
        │
        ▼
FinalPlan JSON
```

## Reliability model

Each model call asks for JSON. `generate_with_consensus` rejects malformed candidates, missing required keys, and invalid list cardinality. Valid candidates participate in exact canonical-JSON voting. The orchestration layer then assigns deterministic IDs so generated acronyms cannot collide. Finally `validate_final_plan` checks self-dependencies, dangling dependencies, duplicate IDs, cycles, and suspicious truncation.

This does **not** prove semantic correctness. Plans remain model-generated suggestions and should be reviewed before execution.

## Why local-first

The default backend is Ollama at `127.0.0.1:11434`. The API does not need a hosted LLM key. This makes the project useful for private/offline planning, experiments with local models, and teams that want to benchmark planner behavior without sending prompts to a third-party inference API.
