# Java Context Engine

The Java context engine provides graph and semantic evidence for Java backend
requirements before technical planning and coding.

## Capabilities

- `java-code-graph` defines the bytecode and graph query contract.
- `java-semantic-index` defines method-level semantic retrieval.
- `java-impact-analysis` combines graph and RAG evidence into candidate scope.
- `java-context-engine` routes the stage and writes a concise summary to
  `03_context_discovery.md`.
- `context-pack-builder` turns discovery results, version constraints, entry
  coverage, reuse examples, and workflow overlay into work-item context packs.

## Backend Model

The target full engine is ASM bytecode parsing plus graph storage and semantic
indexing. The workflow contract stays backend-neutral so projects can use Neo4j,
local files, or another graph/vector backend.

## Safety

The context engine does not edit source code. It provides evidence, scope, and
risk signals for `main-flow`.

Context packs must not claim graph or RAG evidence unless the provider or
artifact exists. Missing providers should be recorded as manual or blocked
evidence rather than hidden.
