---
name: java-semantic-index
description: >
  Defines Java semantic indexing and retrieval behavior for class summaries,
  method-level chunks, annotations, and query-driven RAG evidence. Use when a
  Java backend requirement needs similar implementation discovery, method-level
  context, or semantic evidence for a technical plan.
---

# java-semantic-index

Java semantic RAG contract skill.

This is an internal workflow contract skill, not a support-* capability wrapper.
When a Java project root and run directory are available, the default first
provider is the local V1 lexical semantic scanner through
`scripts/java_context_engine.py`. It writes
`rag/java-semantic-index.response.json`.

## Mandatory Rules

- Prefer the local V1 provider before manual semantic discovery.
- Prefer method-level chunks for implementation planning.
- Do not fabricate RAG evidence. If no retrieval result exists, return `blocked` or use manual code discovery.
- Do not start vector databases or any external service from this skill.
- Do not edit source code from this skill.
- Do not paste large retrieved code into `03_context_discovery.md`; store raw retrieval output under `rag/`.
- If retrieval confidence is low, record missing context instead of forcing a plan.
- Keep vector backend replaceable.
- Local V1 output is lexical source matching only; it is not embedding-based retrieval or true vector RAG evidence.

## Contract

Use `templates/contracts/java-semantic-index.request.example.json` and `templates/contracts/java-semantic-index.response.example.json`.

## Output

```text
JAVA_SEMANTIC_INDEX_STATUS: ready|blocked|manual|failed
REQUEST_ARTIFACT: <path>
RESULT_ARTIFACT: <path>
MATCHES:
- <symbol or empty>
MISSING_CONTEXT:
- <context or empty>
```
