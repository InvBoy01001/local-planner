# Research background

Local Planner experiments with **decomposition**, **red-flagging**, and **first-to-ahead-by-k voting** for LLM planning.

The main inspiration is:

> Elliot Meyerson et al., *Solving a Million-Step LLM Task with Zero Errors*, arXiv:2511.09030 (2025).  
> https://arxiv.org/abs/2511.09030

The paper describes MAKER, a massively decomposed agentic process that combines focused micro-agents with voting/error correction for very long tasks.

## What Local Planner borrows

- split a large objective into smaller model decisions;
- reject malformed outputs before they can participate in voting;
- use a first-to-ahead-by-k style stopping rule over repeated candidates.

## What Local Planner does **not** claim

This repository is **not** a reproduction of the paper's million-step experiment and does not claim zero-error planning. Its decomposition depth, prompts, model backend, validation rules, and voting implementation are application-specific. Exact-output agreement also does not imply factual correctness.

The practical goal is narrower: make local-model planning more inspectable and structurally reliable, then measure where the approach helps and where it fails.
