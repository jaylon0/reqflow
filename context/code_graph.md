---
name: java-code-graph
description: >
  Defines Java code graph build and query behavior for ASM-backed bytecode
  parsing, graph storage, and provider-neutral impact queries. Use when Java
  backend work needs entrypoint, call-chain, dependency, field-reference,
  annotation, or affected-node evidence.
---

# java-code-graph

Java code graph contract skill.

This is an internal workflow contract skill, not a support-* capability wrapper.
When a Java project root and run directory are available, the default first
provider is the local V1 source scanner through `scripts/java_context_engine.py`.
It writes `graph/java-code-graph.response.json`.

## Mandatory Rules

- Prefer the local V1 provider before manual graph discovery.
- Do not start Neo4j or any external service from this skill.
- Do not invent call chains. If no graph result exists, return `blocked` or use manual code discovery.
- Store request and response artifacts under `graph/`.
- Keep graph backend replaceable; do not hardcode Neo4j-only output into run artifacts.
- Local V1 output is heuristic source-scan evidence only; it is not ASM bytecode evidence and not graph database evidence.

## Contract

Use `templates/contracts/java-code-graph.request.example.json` and `templates/contracts/java-code-graph.response.example.json`.

## Output

```text
JAVA_CODE_GRAPH_STATUS: ready|blocked|manual|failed
REQUEST_ARTIFACT: <path>
RESULT_ARTIFACT: <path>
ENTRYPOINTS:
- <entrypoint or empty>
RISK_SIGNALS:
- <risk or empty>
BLOCKERS:
- <blocker or empty>
```
