# Evaluation strategy

The project currently has deterministic unit tests for query normalization, schema isolation, consensus red-flagging, and dependency-graph validation. The next quality milestone is a small public golden evaluation suite.

Suggested evaluation dimensions:

- requirement recall: explicit user constraints present in the plan;
- structural validity: expected cardinality, unique IDs, valid dependency DAG;
- grounding: avoids invented APIs or vendor capabilities;
- non-duplication: siblings add distinct work;
- usefulness: tasks are concrete enough to execute;
- latency and model calls: measured per phase and end-to-end.

Golden cases should include software, research, operations, creative/non-software planning, ambiguous requests, and contradictory constraints. Store prompts and machine-checkable expectations rather than a single subjective score.
