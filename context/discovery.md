---
name: java-context-engine
description: >
  Coordinates Java backend context discovery through code graph, semantic index,
  and impact analysis contracts. Use when main-flow reaches Java/JVM context
  discovery, when a Java backend requirement needs entrypoint discovery, call-chain
  analysis, affected-node discovery, or graph/RAG evidence before planning.
---

# java-context-engine

Java backend context discovery router.

This is an internal workflow skill, not a support-* capability wrapper. When a
Java project root and run directory are available, use the local V1 provider
before falling back to manual mode:

```bash
python3 {pluginRoot}/scripts/java_context_engine.py analyze \
  --project-root <project-root> \
  --run-dir <run-dir> \
  --requirement "<requirement text>"
```

## Mandatory Rules

- Use this only for Java backend or JVM service work.
- Prefer existing run artifacts before rebuilding indexes.
- Do not claim graph or RAG evidence exists unless a provider or artifact returned it.
- Use the local V1 provider when source files are available; if it cannot run, record `blocked` or `manual` status and continue only when code evidence is sufficient.
- Local V1 evidence is source-heuristic evidence only; do not present it as ASM bytecode, graph database, embedding, or vector RAG evidence.
- Keep large raw graph and retrieval outputs in `graph/` and `rag/` artifacts; summarize them in `03_context_discovery.md`.

## Flow

1. Read project context and current run state.
2. Decide whether graph build, graph query, semantic indexing, semantic retrieval, or combined impact analysis is needed.
3. If local V1 is applicable, run `scripts/java_context_engine.py analyze`.
4. Otherwise, use `java-code-graph` for call graph and dependency evidence.
5. Use `java-semantic-index` for class and method semantic retrieval.
6. Use `java-impact-analysis` to combine evidence into candidate scope and risk signals.
7. Write summary results to `03_context_discovery.md`.

## Output

```text
JAVA_CONTEXT_ENGINE_STATUS: ready|blocked|manual|failed
GRAPH_STATUS: missing|ready|blocked|failed
RAG_STATUS: missing|ready|blocked|failed
ARTIFACTS:
- <path>
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <action>
```
