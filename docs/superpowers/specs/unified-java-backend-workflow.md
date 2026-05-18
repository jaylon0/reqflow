# Unified Java Backend Workflow

The unified Java backend workflow combines Requirement Flow orchestration,
spec governance, Java context discovery, quality gates, and delivery
verification.

## Layers

- `main-flow` orchestrates the run.
- `spec-governance` keeps requirement truth in delta specs and constitution checks.
- `java-context-engine` provides graph and semantic evidence.
- `quality-gates` blocks unsafe implementation and premature completion.
- Delivery skills verify build, API, message, RPC, task, UI, data, cache, search, and logs.

## First Slice Boundary

The first slice adds contracts and workflow entry points. It does not implement
ASM parsing, Neo4j storage, vector indexing, or internal platform adapters.
