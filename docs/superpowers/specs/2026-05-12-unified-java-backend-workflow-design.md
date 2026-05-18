# Unified Java Backend Workflow Design

Date: 2026-05-12

## Goal

Upgrade `requirement-flow-plugin` from a generic requirement-to-delivery skeleton into a Java backend first AI Coding workflow that integrates:

- Requirement Flow orchestration.
- Superpowers-style quality discipline.
- OpenSpec-style delta specifications.
- Spec-Kit-style constitution and clarification gates.
- Java code graph and semantic RAG context engines.
- Delivery verification through provider adapters.

The design keeps the plugin modular. `main-flow` remains the orchestrator, while graph/RAG, spec governance, quality gates, and delivery verification each own a clear boundary.

## Confirmed Direction

The selected direction is:

- Full unified workflow.
- Java backend first.
- Full context engine target: ASM bytecode parsing, graph database, semantic index, Graph Agent, and RAG Agent.
- Modular built-in architecture with replaceable backends.
- Layered fusion architecture rather than a single oversized `main-flow` prompt or multiple separately installed plugins.

## Architecture

```text
requirement-flow-plugin
├── main-flow
│   └── PRD -> spec -> context -> plan -> code -> review -> verify -> archive
├── java-context-engine
│   ├── code-graph
│   ├── semantic-index
│   └── context-agents
├── spec-governance
│   ├── delta spec
│   ├── constitution
│   └── clarification
├── quality-gates
│   ├── design gate
│   ├── TDD gate
│   ├── review gate
│   └── completion gate
└── delivery-engine
    ├── build / deploy
    ├── API / MQ / RPC / Task / UI verification
    └── DB / cache / search / log read-only validation
```

`main-flow` owns stage ordering, state, user interaction, checkpoints, and final status. It must not embed Java graph implementation details directly.

`java-context-engine` owns Java backend context discovery. The first full engine target is ASM plus a graph backend and semantic index, but the workflow uses contracts so graph and vector backends remain replaceable.

`spec-governance` owns durable requirement truth: proposal, delta spec, constitution checks, clarification markers, and archive behavior.

`quality-gates` owns Superpowers-style discipline: design approval, TDD where practical, code review, and completion verification.

`delivery-engine` continues the existing provider-neutral model. Internal platforms can be added later through adapters rather than copied into the core plugin.

## Runtime Flow

```text
1. PRD Intake
2. Spec Governance
3. Java Context Build / Query
4. Technical Plan
5. Implementation Plan
6. Coding With Gates
7. Review And Repair
8. Delivery Verification
9. Archive And Learn
```

Stage 1 extracts functional points, boundaries, acceptance criteria, and blockers.

Stage 2 creates or updates delta specs and checks constitution constraints.

Stage 3 builds or queries code graph and semantic index, then records entrypoints, call chains, affected nodes, and risk signals.

Stage 4 produces the technical plan using PRD, spec delta, graph/RAG evidence, and gap checks for traffic, idempotency, rollout, stability, and ownership.

Stage 5 decomposes work into modules with authorized scope, dependency order, and verification plans.

Stage 6 implements module by module. TDD is required when behavior can be expressed as a local failing check. If TDD is not practical, the reason must be recorded.

Stage 7 reviews for spec match and standards match. Findings enter the bounded repair loop.

Stage 8 verifies build, deploy, API, MQ, RPC, task, UI, DB, cache, search, and log signals through configured providers or manual checklists.

Stage 9 archives accepted delta specs and records reusable learning.

## Runtime Artifacts

The existing `.dev-workflow/runs/<run-id>/` model is retained and expanded:

```text
.dev-workflow/
├── context.yaml
├── providers.yaml
├── constitution.md
├── specs/
│   └── <capability>/spec.md
├── changes/
│   └── <change-id>/
│       ├── proposal.md
│       ├── specs/<capability>/spec.md
│       ├── design.md
│       └── tasks.md
└── runs/<run-id>/
    ├── state.json
    ├── memory.md
    ├── 01_prd_summary.md
    ├── 02_spec_delta.md
    ├── 03_context_discovery.md
    ├── 04_tech_plan.md
    ├── 05_impl_plan.md
    ├── 06_coding.md
    ├── 07_code_review.md
    ├── 08_verification.md
    ├── 09_archive.md
    ├── graph/
    │   ├── build-request.json
    │   ├── graph-summary.json
    │   └── impact-query-results.json
    ├── rag/
    │   ├── index-summary.json
    │   └── retrieval-results.json
    └── loops/<loop-id>.md
```

## Contracts

### Java Code Graph Request

```json
{
  "project_root": "/path/to/java/project",
  "build_tool": "maven",
  "source_roots": ["src/main/java"],
  "class_roots": ["target/classes"],
  "dependency_classpath": [],
  "entrypoints": [
    {
      "type": "http",
      "pattern": "/rest/example/list",
      "hint": "Controller method if known"
    }
  ],
  "query": {
    "intent": "impact_analysis",
    "targets": ["Controller.list"],
    "depth": 4,
    "include": ["calls", "field_refs", "inheritance", "annotations", "sql"]
  }
}
```

### Java Code Graph Response

```json
{
  "status": "success",
  "graph_version": "java-graph-v1",
  "entrypoints": [],
  "call_chains": [],
  "affected_nodes": [],
  "risk_signals": [
    "list query and count query may need synchronized filtering",
    "VO mapping crosses helper layer"
  ],
  "evidence": []
}
```

### Semantic Index Request

```json
{
  "project_root": "/path/to/java/project",
  "chunk_level": "method",
  "include": ["class_summary", "method_body", "annotations", "javadocs"],
  "query": {
    "text": "新增物料优先级筛选并展示归因方案字段",
    "top_k": 20,
    "filters": {
      "modules": [],
      "layers": ["controller", "service", "dao", "vo"]
    }
  }
}
```

### Semantic Index Response

```json
{
  "status": "success",
  "index_version": "semantic-index-v1",
  "matches": [
    {
      "file": "ExampleController.java",
      "symbol": "list",
      "score": 0.87,
      "reason": "route and request parameter match",
      "snippet_ref": "artifact://..."
    }
  ],
  "missing_context": []
}
```

### Delta Spec Format

```markdown
## ADDED Requirements
### Requirement: <name>
#### Scenario: <scenario>

## MODIFIED Requirements
### Requirement: <name>

## REMOVED Requirements
### Requirement: <name>
Reason: <reason>
```

### Constitution Format

```markdown
# Constitution

## Non-negotiable Rules
- Do not introduce write operations in verification adapters.
- Java backend changes must preserve controller/service/dao boundaries.
- External calls must define timeout, fallback, and observability.
```

## State Extensions

`state.json` should gain:

```json
{
  "change_id": "",
  "spec_status": "draft|approved|archived",
  "constitution_checks": [],
  "context_engine": {
    "graph_status": "missing|building|ready|failed",
    "rag_status": "missing|building|ready|failed",
    "last_graph_version": "",
    "last_index_version": ""
  },
  "quality_gates": {
    "design_approved": false,
    "tdd_required": false,
    "review_passed": false,
    "verification_passed": false
  },
  "archive_status": "not_started|ready|archived|blocked"
}
```

## Gates

### Human Confirmation Gates

- PRD Summary Gate: unresolved requirement boundaries, acceptance criteria, or business rules block the flow.
- Spec Delta Gate: delta spec must be confirmed before technical planning.
- Technical Plan Gate: architecture, interface, DB, cache, MQ/RPC, permission, configuration, rollout, and fallback decisions require confirmation.
- Data/Contract Gate: DB table, cache key, PB/DTO/VO, API contract, MQ payload, and RPC contract changes require explicit confirmation.
- Module Coding Gate: each module stops after coding, local verification, and review unless configured for low-risk auto-continue.
- Archive Gate: delta spec archive behavior must be confirmed.

### Automatic Quality Gates

- Constitution Check.
- Context Sufficiency Check.
- TDD Gate.
- Spec Match Review.
- Standards Review.
- Verification Before Completion.
- Read-only Safety Gate.

## Failure Recovery

All failures route through `loop-engine` with typed handling:

```text
build failure
  -> localize compile/test error
  -> patch authorized scope only
  -> rerun smallest proving check

spec mismatch
  -> compare implementation vs 02_spec_delta/04_tech_plan
  -> patch or mark BLOCKER if plan is wrong

context insufficiency
  -> rerun graph/rag query
  -> ask user only if code evidence cannot answer

verification failure
  -> preserve request/response/log/data evidence
  -> classify API/MQ/RPC/DB/cache/log/UI
  -> repair source or provider config
  -> stop after repeated fingerprint

constitution violation
  -> stop unless an obvious local fix exists

archive conflict
  -> stop and show conflicting requirement headers or scenarios
```

Failure fingerprints include:

```text
stage + module + failing command/provider + normalized error + affected artifact
```

The loop may attempt automatic repair twice. A third occurrence of the same fingerprint becomes a `BLOCKER`.

## Recovery Order

Resume in this order:

```text
1. Read state.json
2. Read memory.md
3. Read constitution.md
4. Read current change proposal/spec/design/tasks
5. Read last_stable_artifact
6. Read graph/index summaries without loading large raw results
7. Continue from current_step/current_module
```

## Subagent Strategy

The main agent keeps decision context and user interaction. Heavy IO and noisy work should be delegated:

- PRD image or long document extraction.
- Repository scan and graph build.
- RAG retrieval.
- Large code discovery.
- Large module coding or review above threshold.
- Build, deploy, and verification.

Only the main agent may ask the user for confirmations.

## First Implementation Slice

The first slice should solidify workflow, contracts, artifacts, and skill entry points. It should not implement the full ASM/Neo4j/vector engine.

Add these skill groups:

- `java-context-engine`, `java-code-graph`, `java-semantic-index`, `java-impact-analysis`.
- `spec-governance`, `spec-delta`, `constitution-check`, `spec-archive`.
- `quality-gates`, `design-gate`, `tdd-gate`, `completion-gate`.

Add run artifact templates:

- `02_spec_delta.template.md`
- `03_context_discovery.template.md`
- `08_verification.template.md`
- `09_archive.template.md`

Add contract templates:

- `java-code-graph.request.example.json`
- `java-code-graph.response.example.json`
- `java-semantic-index.request.example.json`
- `java-semantic-index.response.example.json`
- `java-impact-analysis.response.example.json`

Add docs:

- `java-context-engine.md`
- `spec-governance.md`
- `quality-gates.md`
- `unified-java-backend-workflow.md`

Modify:

- `skills/main-flow/SKILL.md`
- `templates/run-state.example.json`
- `templates/context.template.yaml`
- `README.md`
- `docs/main-flow.md`
- `docs/migration-from-specialized-plugins.md`
- `skills/support-router/SKILL.md`

## First Slice Non-goals

- Do not start Neo4j.
- Do not implement ASM bytecode parsing.
- Do not add a real vector database.
- Do not copy internal platform scripts.
- Do not modify the three original plugins.
- Do not change global CodeFlicker installation unless explicitly requested.
