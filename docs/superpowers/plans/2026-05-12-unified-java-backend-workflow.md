# Unified Java Backend Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first implementation slice for a Java backend first unified workflow in `requirement-flow-plugin`.

**Architecture:** Keep `main-flow` as the orchestrator and add three focused capability groups: Java context engine, spec governance, and quality gates. This slice adds workflow contracts, run artifact templates, skill entry points, and docs without implementing ASM, Neo4j, or a vector database.

**Tech Stack:** Markdown skills and docs, JSON contract examples, YAML context template, existing Python plugin self-check.

---

## File Structure

Create these files:

- `requirement-flow-plugin/skills/java-context-engine/SKILL.md` - Java context engine router and stage rules.
- `requirement-flow-plugin/skills/java-code-graph/SKILL.md` - Java code graph contract and query rules.
- `requirement-flow-plugin/skills/java-semantic-index/SKILL.md` - Java semantic index contract and retrieval rules.
- `requirement-flow-plugin/skills/java-impact-analysis/SKILL.md` - Combined graph and RAG impact analysis rules.
- `requirement-flow-plugin/skills/spec-governance/SKILL.md` - Spec governance router and lifecycle rules.
- `requirement-flow-plugin/skills/spec-delta/SKILL.md` - Delta spec generation and validation rules.
- `requirement-flow-plugin/skills/constitution-check/SKILL.md` - Constitution gate rules.
- `requirement-flow-plugin/skills/spec-archive/SKILL.md` - Archive gate rules.
- `requirement-flow-plugin/skills/quality-gates/SKILL.md` - Quality gate router.
- `requirement-flow-plugin/skills/design-gate/SKILL.md` - Design approval gate rules.
- `requirement-flow-plugin/skills/tdd-gate/SKILL.md` - TDD applicability gate rules.
- `requirement-flow-plugin/skills/completion-gate/SKILL.md` - Completion verification gate rules.
- `requirement-flow-plugin/templates/run-artifacts/02_spec_delta.template.md` - Spec delta run artifact.
- `requirement-flow-plugin/templates/run-artifacts/03_context_discovery.template.md` - Graph/RAG context artifact.
- `requirement-flow-plugin/templates/run-artifacts/08_verification.template.md` - Delivery verification artifact.
- `requirement-flow-plugin/templates/run-artifacts/09_archive.template.md` - Archive artifact.
- `requirement-flow-plugin/templates/contracts/java-code-graph.request.example.json` - Graph request example.
- `requirement-flow-plugin/templates/contracts/java-code-graph.response.example.json` - Graph response example.
- `requirement-flow-plugin/templates/contracts/java-semantic-index.request.example.json` - Semantic request example.
- `requirement-flow-plugin/templates/contracts/java-semantic-index.response.example.json` - Semantic response example.
- `requirement-flow-plugin/templates/contracts/java-impact-analysis.response.example.json` - Impact response example.
- `requirement-flow-plugin/templates/constitution.template.md` - Project constitution starter.
- `requirement-flow-plugin/docs/java-context-engine.md` - Context engine documentation.
- `requirement-flow-plugin/docs/spec-governance.md` - Spec governance documentation.
- `requirement-flow-plugin/docs/quality-gates.md` - Quality gates documentation.
- `requirement-flow-plugin/docs/unified-java-backend-workflow.md` - Unified workflow documentation.

Modify these files:

- `requirement-flow-plugin/skills/main-flow/SKILL.md` - Extend stages, mandatory rules, run files, and knowledge hooks.
- `requirement-flow-plugin/templates/run-state.example.json` - Add change/spec/context/quality/archive state fields and update artifact paths.
- `requirement-flow-plugin/templates/context.template.yaml` - Add Java context engine, spec governance, and quality gate configuration.
- `requirement-flow-plugin/README.md` - Document new architecture and usage.
- `requirement-flow-plugin/docs/main-flow.md` - Document the expanded 01-09 flow.
- `requirement-flow-plugin/docs/migration-from-specialized-plugins.md` - Add Java context and SDD framework migration mapping.
- `requirement-flow-plugin/skills/support-router/SKILL.md` - Add routing entries for the new stable support skills.

## Task 1: Add Run Artifact And Contract Templates

**Files:**
- Create: `requirement-flow-plugin/templates/run-artifacts/02_spec_delta.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/03_context_discovery.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/08_verification.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/09_archive.template.md`
- Create: `requirement-flow-plugin/templates/contracts/java-code-graph.request.example.json`
- Create: `requirement-flow-plugin/templates/contracts/java-code-graph.response.example.json`
- Create: `requirement-flow-plugin/templates/contracts/java-semantic-index.request.example.json`
- Create: `requirement-flow-plugin/templates/contracts/java-semantic-index.response.example.json`
- Create: `requirement-flow-plugin/templates/contracts/java-impact-analysis.response.example.json`
- Create: `requirement-flow-plugin/templates/constitution.template.md`

- [ ] **Step 1: Create the contract directory**

Run:

```bash
mkdir -p requirement-flow-plugin/templates/contracts
```

Expected: command exits with status 0.

- [ ] **Step 2: Add `02_spec_delta.template.md`**

Create `requirement-flow-plugin/templates/run-artifacts/02_spec_delta.template.md`:

```markdown
# 02 Spec Delta

## Change

## Affected Capabilities

## ADDED Requirements

## MODIFIED Requirements

## REMOVED Requirements

## Clarifications

## Constitution Checks

## Approval

- Status: draft
- Approved by:
- Approved at:

## BLOCKER

- None
```

- [ ] **Step 3: Add `03_context_discovery.template.md`**

Create `requirement-flow-plugin/templates/run-artifacts/03_context_discovery.template.md`:

```markdown
# 03 Context Discovery

## Project Context

## Java Code Graph

- Status: missing
- Graph version:
- Request artifact:
- Result artifact:

## Semantic Index

- Status: missing
- Index version:
- Request artifact:
- Result artifact:

## Entrypoints

## Call Chains

## Affected Nodes

## Retrieved Evidence

## Risk Signals

## Candidate Change Scope

## Missing Context

## BLOCKER

- None
```

- [ ] **Step 4: Add `08_verification.template.md`**

Create `requirement-flow-plugin/templates/run-artifacts/08_verification.template.md`:

```markdown
# 08 Verification

## Build Verification

## API Verification

## Message Verification

## RPC Verification

## Task Verification

## UI Verification

## Database Verification

## Cache Verification

## Search Verification

## Log Verification

## Manual Checks

## Result

- Status: pending

## BLOCKER

- None
```

- [ ] **Step 5: Add `09_archive.template.md`**

Create `requirement-flow-plugin/templates/run-artifacts/09_archive.template.md`:

```markdown
# 09 Archive

## Archive Readiness

## Spec Delta Application

## Updated Specs

## Conflicts

## Memory Updates

## Reusable Cases

## Result

- Status: not_started

## BLOCKER

- None
```

- [ ] **Step 6: Add Java code graph request example**

Create `requirement-flow-plugin/templates/contracts/java-code-graph.request.example.json`:

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

- [ ] **Step 7: Add Java code graph response example**

Create `requirement-flow-plugin/templates/contracts/java-code-graph.response.example.json`:

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

- [ ] **Step 8: Add semantic index request example**

Create `requirement-flow-plugin/templates/contracts/java-semantic-index.request.example.json`:

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

- [ ] **Step 9: Add semantic index response example**

Create `requirement-flow-plugin/templates/contracts/java-semantic-index.response.example.json`:

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
      "snippet_ref": "artifact://example"
    }
  ],
  "missing_context": []
}
```

- [ ] **Step 10: Add impact analysis response example**

Create `requirement-flow-plugin/templates/contracts/java-impact-analysis.response.example.json`:

```json
{
  "status": "success",
  "entrypoint_confidence": "high",
  "candidate_change_scope": {
    "modules": [],
    "files": [],
    "symbols": []
  },
  "required_followups": [
    "Confirm whether count queries mirror list query filters",
    "Confirm DTO and VO ownership before adding response fields"
  ],
  "risk_signals": [],
  "evidence_refs": []
}
```

- [ ] **Step 11: Add constitution template**

Create `requirement-flow-plugin/templates/constitution.template.md`:

```markdown
# Constitution

## Non-negotiable Rules

- Do not introduce write operations in verification adapters.
- Java backend changes must preserve controller, service, repository, and data transfer boundaries unless the technical plan explicitly approves a boundary change.
- External calls must define timeout, fallback, and observability behavior.
- API, message, RPC, database, cache, and search contract changes require explicit approval before coding.

## Project Rules

- Prefer existing project patterns and local examples over generic defaults.
- Treat missing product, data, or provider decisions as BLOCKER.
- Keep runtime secrets outside project files.
```

- [ ] **Step 12: Validate JSON examples**

Run:

```bash
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-code-graph.request.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-code-graph.response.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-semantic-index.request.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-semantic-index.response.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-impact-analysis.response.example.json
```

Expected: each command prints formatted JSON and exits with status 0.

- [ ] **Step 13: Commit Task 1**

Run:

```bash
git add requirement-flow-plugin/templates/run-artifacts requirement-flow-plugin/templates/contracts requirement-flow-plugin/templates/constitution.template.md
git commit -m "feat: add unified workflow templates"
```

Expected: commit succeeds when the workspace is a git repository. If the workspace is not a git repository, record that commit was skipped.

## Task 2: Add Java Context Engine Skills

**Files:**
- Create: `requirement-flow-plugin/skills/java-context-engine/SKILL.md`
- Create: `requirement-flow-plugin/skills/java-code-graph/SKILL.md`
- Create: `requirement-flow-plugin/skills/java-semantic-index/SKILL.md`
- Create: `requirement-flow-plugin/skills/java-impact-analysis/SKILL.md`
- Create: `requirement-flow-plugin/docs/java-context-engine.md`

- [ ] **Step 1: Add `java-context-engine` router skill**

Create `requirement-flow-plugin/skills/java-context-engine/SKILL.md`:

```markdown
---
name: java-context-engine
description: >
  Coordinates Java backend context discovery through code graph, semantic index,
  and impact analysis contracts. Use when main-flow reaches context discovery,
  when a Java backend requirement needs entrypoint discovery, call-chain
  analysis, affected-node discovery, or graph/RAG evidence before planning.
---

# java-context-engine

Java backend context discovery router.

## Mandatory Rules

- Use this only for Java backend or JVM service work.
- Prefer existing run artifacts before rebuilding indexes.
- Do not claim graph or RAG evidence exists unless a provider or artifact returned it.
- If graph/RAG providers are unavailable, record `blocked` or `manual` status and continue only when code evidence is sufficient.
- Keep large raw graph and retrieval outputs in `graph/` and `rag/` artifacts; summarize them in `03_context_discovery.md`.

## Flow

1. Read project context and current run state.
2. Decide whether graph build, graph query, semantic indexing, semantic retrieval, or combined impact analysis is needed.
3. Use `java-code-graph` for call graph and dependency evidence.
4. Use `java-semantic-index` for class and method semantic retrieval.
5. Use `java-impact-analysis` to combine evidence into candidate scope and risk signals.
6. Write summary results to `03_context_discovery.md`.

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
```

- [ ] **Step 2: Add `java-code-graph` skill**

Create `requirement-flow-plugin/skills/java-code-graph/SKILL.md`:

```markdown
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

## Mandatory Rules

- Treat this skill as a contract until a project configures a graph provider.
- Do not start Neo4j or any external service from this skill.
- Do not invent call chains. If no graph result exists, return `blocked` or use manual code discovery.
- Store request and response artifacts under `graph/`.
- Keep graph backend replaceable; do not hardcode Neo4j-only output into run artifacts.

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
```

- [ ] **Step 3: Add `java-semantic-index` skill**

Create `requirement-flow-plugin/skills/java-semantic-index/SKILL.md`:

```markdown
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

## Mandatory Rules

- Treat this skill as a contract until a project configures a semantic provider.
- Prefer method-level chunks for implementation planning.
- Do not paste large retrieved code into `03_context_discovery.md`; store raw retrieval output under `rag/`.
- If retrieval confidence is low, record missing context instead of forcing a plan.
- Keep vector backend replaceable.

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
```

- [ ] **Step 4: Add `java-impact-analysis` skill**

Create `requirement-flow-plugin/skills/java-impact-analysis/SKILL.md`:

```markdown
---
name: java-impact-analysis
description: >
  Combines Java code graph and semantic retrieval evidence into affected scope,
  risk signals, missing context, and required follow-up confirmations. Use after
  graph and RAG discovery or when a Java backend change needs impact analysis.
---

# java-impact-analysis

Combined Java impact analysis.

## Mandatory Rules

- Require evidence references for every affected file, module, or symbol.
- Flag synchronized query risks such as list/count drift, DTO/VO mapping drift, cache invalidation, async side effects, and contract ownership.
- Do not authorize code edits; write candidate scope for `main-flow` to confirm.
- Missing graph or RAG data must be visible in output.

## Output

```text
JAVA_IMPACT_ANALYSIS_STATUS: ready|blocked|manual|failed
ENTRYPOINT_CONFIDENCE: high|medium|low|unknown
CANDIDATE_SCOPE:
- <file, module, or symbol>
RISK_SIGNALS:
- <risk>
REQUIRED_FOLLOWUPS:
- <question or decision>
EVIDENCE_REFS:
- <artifact ref>
```
```

- [ ] **Step 5: Add Java context engine docs**

Create `requirement-flow-plugin/docs/java-context-engine.md`:

```markdown
# Java Context Engine

The Java context engine provides graph and semantic evidence for Java backend
requirements before technical planning and coding.

## Capabilities

- `java-code-graph` defines the bytecode and graph query contract.
- `java-semantic-index` defines method-level semantic retrieval.
- `java-impact-analysis` combines graph and RAG evidence into candidate scope.
- `java-context-engine` routes the stage and writes a concise summary to
  `03_context_discovery.md`.

## Backend Model

The target full engine is ASM bytecode parsing plus graph storage and semantic
indexing. The workflow contract stays backend-neutral so projects can use Neo4j,
local files, or another graph/vector backend.

## Safety

The context engine does not edit source code. It provides evidence, scope, and
risk signals for `main-flow`.
```

- [ ] **Step 6: Run plugin self-check**

Run:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected: JSON output with `"status": "success"`.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
git add requirement-flow-plugin/skills/java-context-engine requirement-flow-plugin/skills/java-code-graph requirement-flow-plugin/skills/java-semantic-index requirement-flow-plugin/skills/java-impact-analysis requirement-flow-plugin/docs/java-context-engine.md
git commit -m "feat: add java context engine skills"
```

Expected: commit succeeds when the workspace is a git repository. If the workspace is not a git repository, record that commit was skipped.

## Task 3: Add Spec Governance Skills

**Files:**
- Create: `requirement-flow-plugin/skills/spec-governance/SKILL.md`
- Create: `requirement-flow-plugin/skills/spec-delta/SKILL.md`
- Create: `requirement-flow-plugin/skills/constitution-check/SKILL.md`
- Create: `requirement-flow-plugin/skills/spec-archive/SKILL.md`
- Create: `requirement-flow-plugin/docs/spec-governance.md`

- [ ] **Step 1: Add `spec-governance` router skill**

Create `requirement-flow-plugin/skills/spec-governance/SKILL.md`:

```markdown
---
name: spec-governance
description: >
  Coordinates delta spec creation, constitution checks, clarification markers,
  and spec archive behavior. Use when main-flow reaches spec governance,
  technical plan approval, or final archive.
---

# spec-governance

Spec governance router.

## Mandatory Rules

- Keep requirement truth in specs and changes, not only in chat.
- Stop on unresolved clarification items that affect behavior, data, contracts, or scope.
- Use constitution checks before technical planning and before completion.
- Archive only after verification passes and the user confirms archive behavior.

## Flow

1. Use `spec-delta` to create or validate the change delta.
2. Use `constitution-check` to evaluate project non-negotiable rules.
3. Record unresolved questions as `BLOCKER`.
4. Use `spec-archive` only after completion gates pass.

## Output

```text
SPEC_GOVERNANCE_STATUS: draft|approved|blocked|archived
CHANGE_ID: <change id>
ARTIFACTS:
- <path>
BLOCKERS:
- <blocker or empty>
```
```

- [ ] **Step 2: Add `spec-delta` skill**

Create `requirement-flow-plugin/skills/spec-delta/SKILL.md`:

```markdown
---
name: spec-delta
description: >
  Creates and validates OpenSpec-style delta specifications with ADDED,
  MODIFIED, and REMOVED requirements. Use when a requirement changes durable
  behavior or when main-flow reaches the spec delta stage.
---

# spec-delta

Delta specification support.

## Mandatory Rules

- Use `ADDED Requirements`, `MODIFIED Requirements`, and `REMOVED Requirements`.
- Each requirement must include at least one scenario when behavior is user-observable or externally verifiable.
- Do not copy complete future-state specs for existing capabilities when a delta is sufficient.
- Mark ambiguous behavior as clarification or `BLOCKER`.
- Do not archive from this skill.

## Output

```text
SPEC_DELTA_STATUS: draft|valid|blocked
CHANGED_REQUIREMENTS:
- <requirement>
CLARIFICATIONS:
- <question or empty>
BLOCKERS:
- <blocker or empty>
```
```

- [ ] **Step 3: Add `constitution-check` skill**

Create `requirement-flow-plugin/skills/constitution-check/SKILL.md`:

```markdown
---
name: constitution-check
description: >
  Checks project-level non-negotiable rules before planning, coding, review,
  and completion. Use when main-flow needs Spec-Kit-style constitution gating
  or when a change may violate project principles.
---

# constitution-check

Project constitution gate.

## Mandatory Rules

- Read `.dev-workflow/constitution.md` when it exists.
- If no project constitution exists, use `templates/constitution.template.md` as guidance and record `manual` status.
- Stop on violations that affect data safety, contracts, security, external writes, or architecture boundaries.
- Do not weaken constitution rules without explicit user confirmation.

## Output

```text
CONSTITUTION_STATUS: pass|manual|blocked|failed
CHECKS:
- <rule and result>
VIOLATIONS:
- <violation or empty>
BLOCKERS:
- <blocker or empty>
```
```

- [ ] **Step 4: Add `spec-archive` skill**

Create `requirement-flow-plugin/skills/spec-archive/SKILL.md`:

```markdown
---
name: spec-archive
description: >
  Archives approved delta specs into durable project specs after verification.
  Use when main-flow reaches the archive stage or when the user asks to archive
  a completed change.
---

# spec-archive

Spec archive gate.

## Mandatory Rules

- Archive only after completion verification passes.
- Show the requirements and scenarios that will be added, modified, or removed.
- Stop on conflicting requirement headers or scenario ownership.
- Do not delete run artifacts.
- Require user confirmation before applying archive changes.

## Output

```text
SPEC_ARCHIVE_STATUS: ready|archived|blocked|failed
UPDATED_SPECS:
- <path>
CONFLICTS:
- <conflict or empty>
BLOCKERS:
- <blocker or empty>
```
```

- [ ] **Step 5: Add spec governance docs**

Create `requirement-flow-plugin/docs/spec-governance.md`:

```markdown
# Spec Governance

Spec governance keeps requirement truth outside transient chat context.

## Artifacts

- `.dev-workflow/changes/<change-id>/proposal.md`
- `.dev-workflow/changes/<change-id>/specs/<capability>/spec.md`
- `.dev-workflow/changes/<change-id>/design.md`
- `.dev-workflow/changes/<change-id>/tasks.md`
- `.dev-workflow/specs/<capability>/spec.md`
- `.dev-workflow/constitution.md`

## Flow

1. Create a delta spec.
2. Check constitution rules.
3. Resolve clarification blockers.
4. Use the approved spec during technical planning and review.
5. Archive after verification passes and the user confirms the archive behavior.
```

- [ ] **Step 6: Run plugin self-check**

Run:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected: JSON output with `"status": "success"`.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add requirement-flow-plugin/skills/spec-governance requirement-flow-plugin/skills/spec-delta requirement-flow-plugin/skills/constitution-check requirement-flow-plugin/skills/spec-archive requirement-flow-plugin/docs/spec-governance.md
git commit -m "feat: add spec governance skills"
```

Expected: commit succeeds when the workspace is a git repository. If the workspace is not a git repository, record that commit was skipped.

## Task 4: Add Quality Gate Skills

**Files:**
- Create: `requirement-flow-plugin/skills/quality-gates/SKILL.md`
- Create: `requirement-flow-plugin/skills/design-gate/SKILL.md`
- Create: `requirement-flow-plugin/skills/tdd-gate/SKILL.md`
- Create: `requirement-flow-plugin/skills/completion-gate/SKILL.md`
- Create: `requirement-flow-plugin/docs/quality-gates.md`

- [ ] **Step 1: Add `quality-gates` router skill**

Create `requirement-flow-plugin/skills/quality-gates/SKILL.md`:

```markdown
---
name: quality-gates
description: >
  Coordinates design approval, TDD applicability, review readiness, and
  completion verification gates. Use when main-flow reaches design approval,
  module coding, review, or completion.
---

# quality-gates

Quality gate router.

## Mandatory Rules

- Do not allow coding before required design approval.
- Use `tdd-gate` before behavior-changing implementation.
- Use existing `support-review` and `coding-standards` during review.
- Use `completion-gate` before reporting completion.

## Output

```text
QUALITY_GATES_STATUS: pass|blocked|failed
GATES:
- <gate and result>
BLOCKERS:
- <blocker or empty>
```
```

- [ ] **Step 2: Add `design-gate` skill**

Create `requirement-flow-plugin/skills/design-gate/SKILL.md`:

```markdown
---
name: design-gate
description: >
  Requires explicit approval before implementation for design-sensitive work,
  architecture choices, contracts, data shape, provider behavior, or module
  sequencing.
---

# design-gate

Design approval gate.

## Mandatory Rules

- Require user confirmation for technical plans that change architecture, API, data, messages, RPC, permissions, rollout, or provider behavior.
- Record approved decisions in the run artifact.
- Do not infer approval from silence.

## Output

```text
DESIGN_GATE_STATUS: approved|blocked
APPROVED_DECISIONS:
- <decision>
BLOCKERS:
- <decision needed or empty>
```
```

- [ ] **Step 3: Add `tdd-gate` skill**

Create `requirement-flow-plugin/skills/tdd-gate/SKILL.md`:

```markdown
---
name: tdd-gate
description: >
  Decides whether behavior-changing work should use a red-green-refactor loop.
  Use before module implementation when local tests, API checks, integration
  checks, or focused reproduction are practical.
---

# tdd-gate

TDD applicability gate.

## Mandatory Rules

- Require a failing check first when behavior can be expressed locally.
- If TDD is not practical, record the reason and the alternative verification.
- Keep the proving check focused on the requirement.
- Do not create broad test suites unrelated to the change.

## Output

```text
TDD_GATE_STATUS: required|not_practical|blocked
FAILING_CHECK:
- <command or case>
ALTERNATIVE_VERIFICATION:
- <verification or empty>
REASON:
- <reason when not practical>
```
```

- [ ] **Step 4: Add `completion-gate` skill**

Create `requirement-flow-plugin/skills/completion-gate/SKILL.md`:

```markdown
---
name: completion-gate
description: >
  Verifies that spec match, standards review, build, and required delivery
  checks have passed before main-flow reports completion.
---

# completion-gate

Completion verification gate.

## Mandatory Rules

- Do not report completion until required checks are recorded in `08_verification.md`.
- Require spec match and standards match review results.
- Require manual checklist status when automated providers are unavailable.
- State missing verification as `BLOCKER`.

## Output

```text
COMPLETION_GATE_STATUS: pass|blocked|failed
REQUIRED_EVIDENCE:
- <artifact or command>
MISSING_EVIDENCE:
- <missing item or empty>
BLOCKERS:
- <blocker or empty>
```
```

- [ ] **Step 5: Add quality gates docs**

Create `requirement-flow-plugin/docs/quality-gates.md`:

```markdown
# Quality Gates

Quality gates apply Superpowers-style discipline inside Requirement Flow.

## Gates

- `design-gate` blocks implementation until high-risk design decisions are approved.
- `tdd-gate` requires a focused failing check when behavior can be tested locally.
- `support-review` and `coding-standards` review implementation against spec and standards.
- `completion-gate` prevents premature completion claims without verification evidence.

## Policy

Quality gates are strict about evidence, but they do not force TDD when no local proving check is practical. In those cases the reason and alternative verification must be recorded.
```

- [ ] **Step 6: Run plugin self-check**

Run:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected: JSON output with `"status": "success"`.

- [ ] **Step 7: Commit Task 4**

Run:

```bash
git add requirement-flow-plugin/skills/quality-gates requirement-flow-plugin/skills/design-gate requirement-flow-plugin/skills/tdd-gate requirement-flow-plugin/skills/completion-gate requirement-flow-plugin/docs/quality-gates.md
git commit -m "feat: add quality gate skills"
```

Expected: commit succeeds when the workspace is a git repository. If the workspace is not a git repository, record that commit was skipped.

## Task 5: Extend Main Flow State And Context Templates

**Files:**
- Modify: `requirement-flow-plugin/skills/main-flow/SKILL.md`
- Modify: `requirement-flow-plugin/templates/run-state.example.json`
- Modify: `requirement-flow-plugin/templates/context.template.yaml`
- Modify: `requirement-flow-plugin/docs/main-flow.md`

- [ ] **Step 1: Update `main-flow` run files**

In `requirement-flow-plugin/skills/main-flow/SKILL.md`, replace the run file list with:

```markdown
Each run owns:

```text
state.json
memory.md
01_prd_summary.md
02_spec_delta.md
03_context_discovery.md
04_tech_plan.md
05_impl_plan.md
06_coding.md
07_code_review.md
08_verification.md
09_archive.md
loops/<loop-id>.md
graph/
rag/
```
```

- [ ] **Step 2: Update `main-flow` flow section**

In `requirement-flow-plugin/skills/main-flow/SKILL.md`, replace the flow block with:

```markdown
## Flow

```text
0. Start or resume run
1. PRD understanding -> 01_prd_summary.md -> checkpoint
2. Spec governance -> 02_spec_delta.md -> checkpoint
3. Java context discovery -> 03_context_discovery.md
4. Technical plan -> 04_tech_plan.md -> checkpoint
5. Implementation plan -> 05_impl_plan.md -> checkpoint for high-risk data/API/resource changes
6. Code by module -> 06_coding.md -> per-module checkpoint and loop-engine
7. Review -> 07_code_review.md -> loop-engine for findings
8. Delivery verification -> 08_verification.md -> loop-engine for failures
9. Archive and learn -> 09_archive.md -> checkpoint
```
```

- [ ] **Step 3: Update `main-flow` mandatory rules**

Add these bullets to the mandatory rules in `requirement-flow-plugin/skills/main-flow/SKILL.md`:

```markdown
- Run spec governance before technical planning for durable behavior changes.
- Run Java context discovery before technical planning for Java backend work unless the change is L0 analysis-only or a trivial local edit.
- Do not claim graph, RAG, or impact evidence exists without a provider result or artifact reference.
- Run quality gates before module coding, review completion, and final completion.
- Archive specs only after verification passes and the user confirms archive behavior.
```

- [ ] **Step 4: Update `main-flow` state fields**

Add these fields to the state field list in `requirement-flow-plugin/skills/main-flow/SKILL.md`:

```markdown
- `change_id`: the current spec governance change id.
- `spec_status`: `draft`, `approved`, `archived`, or `blocked`.
- `context_engine`: graph and RAG status plus last graph/index versions.
- `quality_gates`: design, TDD, review, and verification gate status.
- `archive_status`: `not_started`, `ready`, `archived`, or `blocked`.
```

- [ ] **Step 5: Replace `run-state.example.json` content**

Replace `requirement-flow-plugin/templates/run-state.example.json` with:

```json
{
  "run_id": "2026-05-12-example",
  "project": "",
  "requirement": "",
  "change_id": "",
  "repos": [],
  "branch_by_repo": {},
  "current_step": 0,
  "completed_steps": [],
  "step_status": "initialized",
  "blocked_reason": "",
  "spec_status": "draft",
  "constitution_checks": [],
  "context_engine": {
    "graph_status": "missing",
    "rag_status": "missing",
    "last_graph_version": "",
    "last_index_version": ""
  },
  "quality_gates": {
    "design_approved": false,
    "tdd_required": false,
    "review_passed": false,
    "verification_passed": false
  },
  "archive_status": "not_started",
  "current_module": "",
  "planned_modules": [
    {
      "id": "module-example",
      "name": "Example module",
      "status": "pending",
      "authorized_scope": {
        "modules": [],
        "files": []
      }
    }
  ],
  "completed_modules": [],
  "authorized_scope": {
    "modules": [],
    "files": [],
    "reason": ""
  },
  "max_retries": 3,
  "failure_fingerprints": {},
  "current_loop_id": "",
  "pending_confirmations": [],
  "last_stable_step": 0,
  "last_stable_artifact": "",
  "artifact_paths": {
    "memory": "memory.md",
    "prd_summary": "01_prd_summary.md",
    "spec_delta": "02_spec_delta.md",
    "context_discovery": "03_context_discovery.md",
    "tech_plan": "04_tech_plan.md",
    "impl_plan": "05_impl_plan.md",
    "coding": "06_coding.md",
    "code_review": "07_code_review.md",
    "verification": "08_verification.md",
    "archive": "09_archive.md"
  },
  "decisions": [],
  "loops": []
}
```

- [ ] **Step 6: Extend `context.template.yaml`**

Add this block under `workflow:` in `requirement-flow-plugin/templates/context.template.yaml`:

```yaml
  spec_governance:
    enabled: true
    constitution_path: ".dev-workflow/constitution.md"
    specs_root: ".dev-workflow/specs"
    changes_root: ".dev-workflow/changes"
  java_context_engine:
    enabled: true
    graph_provider: "manual"
    semantic_provider: "manual"
    graph_artifact_root: "graph"
    rag_artifact_root: "rag"
  quality_gates:
    design_gate: true
    tdd_gate: true
    completion_gate: true
```

Update `knowledge_hooks` in the same file to include:

```yaml
    step_2:
      - spec-governance
      - spec-delta
      - constitution-check
    step_3:
      - java-context-engine
      - java-code-graph
      - java-semantic-index
      - java-impact-analysis
    step_6_before_edit:
      - quality-gates
      - tdd-gate
```

- [ ] **Step 7: Update `docs/main-flow.md`**

Add this section to `requirement-flow-plugin/docs/main-flow.md`:

```markdown
## Unified Java Backend Flow

For Java backend work, `main-flow` expands the run from the legacy PRD-to-code
sequence into a 01-09 sequence:

1. PRD summary.
2. Spec delta.
3. Context discovery through Java graph and semantic retrieval.
4. Technical plan.
5. Implementation plan.
6. Module coding.
7. Code review.
8. Delivery verification.
9. Archive.

The flow may run in manual mode when graph, semantic, deploy, or verification
providers are not configured. Manual mode must record missing provider evidence
instead of pretending automation succeeded.
```

- [ ] **Step 8: Validate JSON and run self-check**

Run:

```bash
python3 -m json.tool requirement-flow-plugin/templates/run-state.example.json
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected: JSON validation succeeds and self-check returns `"status": "success"`.

- [ ] **Step 9: Commit Task 5**

Run:

```bash
git add requirement-flow-plugin/skills/main-flow/SKILL.md requirement-flow-plugin/templates/run-state.example.json requirement-flow-plugin/templates/context.template.yaml requirement-flow-plugin/docs/main-flow.md
git commit -m "feat: extend main flow for unified java workflow"
```

Expected: commit succeeds when the workspace is a git repository. If the workspace is not a git repository, record that commit was skipped.

## Task 6: Update Public Docs And Support Routing

**Files:**
- Modify: `requirement-flow-plugin/README.md`
- Modify: `requirement-flow-plugin/docs/migration-from-specialized-plugins.md`
- Modify: `requirement-flow-plugin/skills/support-router/SKILL.md`
- Create: `requirement-flow-plugin/docs/unified-java-backend-workflow.md`

- [ ] **Step 1: Add unified workflow docs**

Create `requirement-flow-plugin/docs/unified-java-backend-workflow.md`:

```markdown
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
```

- [ ] **Step 2: Update README architecture list**

In `requirement-flow-plugin/README.md`, add these lines under the architecture section:

```markdown
Java context layer
  java-context-engine   Java backend context discovery router
  java-code-graph       code graph build/query contract
  java-semantic-index   method-level semantic retrieval contract
  java-impact-analysis  combined graph/RAG impact analysis

Spec governance layer
  spec-governance       delta spec, constitution, clarification, and archive router
  spec-delta            ADDED/MODIFIED/REMOVED requirement deltas
  constitution-check    project non-negotiable rule gate
  spec-archive          archive approved deltas into durable specs

Quality gate layer
  quality-gates         design, TDD, review, and completion gate router
  design-gate           explicit design approval gate
  tdd-gate              red/green/refactor applicability gate
  completion-gate       final verification gate
```

- [ ] **Step 3: Add README usage example**

In `requirement-flow-plugin/README.md`, add:

```markdown
For Java backend full workflow:

```text
使用 requirement-flow-plugin:main-flow 运行 Java 服务端完整需求流程:
<PRD or requirement>
```

This flow creates spec delta, context discovery, technical plan, implementation
plan, coding, review, verification, and archive artifacts. Graph and RAG
providers can run in manual mode until configured.
```

- [ ] **Step 4: Update migration docs**

Add this mapping to `requirement-flow-plugin/docs/migration-from-specialized-plugins.md`:

```markdown
| Code graph / system dependency map | `java-code-graph` provider contract |
| Semantic code retrieval / RAG | `java-semantic-index` provider contract |
| PRD-to-spec workflow | `spec-governance` and `spec-delta` |
| Project constitution / hard rules | `constitution-check` |
| Superpowers design/TDD/completion discipline | `quality-gates`, `design-gate`, `tdd-gate`, `completion-gate` |
```

- [ ] **Step 5: Update support router list**

In `requirement-flow-plugin/skills/support-router/SKILL.md`, add these stable entries:

```markdown
- `java-context-engine` (stable): Coordinate Java graph, semantic retrieval, and impact analysis.
- `java-code-graph` (stable): Use Java code graph build/query contracts.
- `java-semantic-index` (stable): Use Java method-level semantic retrieval contracts.
- `java-impact-analysis` (stable): Combine Java graph and RAG evidence into candidate scope and risk signals.
- `spec-governance` (stable): Coordinate delta specs, constitution checks, clarification, and archive.
- `spec-delta` (stable): Create and validate delta specs.
- `constitution-check` (stable): Check project non-negotiable rules.
- `spec-archive` (stable): Archive approved spec deltas.
- `quality-gates` (stable): Coordinate design, TDD, review, and completion gates.
- `design-gate` (stable): Require approval for design-sensitive work.
- `tdd-gate` (stable): Decide and record test-first requirements.
- `completion-gate` (stable): Prevent completion without required verification evidence.
```

- [ ] **Step 6: Run self-check**

Run:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected: JSON output with `"status": "success"`.

- [ ] **Step 7: Commit Task 6**

Run:

```bash
git add requirement-flow-plugin/README.md requirement-flow-plugin/docs/migration-from-specialized-plugins.md requirement-flow-plugin/skills/support-router/SKILL.md requirement-flow-plugin/docs/unified-java-backend-workflow.md
git commit -m "docs: document unified java backend workflow"
```

Expected: commit succeeds when the workspace is a git repository. If the workspace is not a git repository, record that commit was skipped.

## Task 7: Final Verification

**Files:**
- Verify all files changed in Tasks 1-6.

- [ ] **Step 1: Scan for plan failure placeholders in implementation files**

Run:

```bash
rg -n "T[B]D|T[O]DO|F[I]XME|待[定]|未[定]" requirement-flow-plugin/skills requirement-flow-plugin/docs requirement-flow-plugin/templates
```

Expected: no matches introduced by this implementation slice.

- [ ] **Step 2: Validate JSON examples**

Run:

```bash
python3 -m json.tool requirement-flow-plugin/templates/run-state.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-code-graph.request.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-code-graph.response.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-semantic-index.request.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-semantic-index.response.example.json
python3 -m json.tool requirement-flow-plugin/templates/contracts/java-impact-analysis.response.example.json
```

Expected: all files parse as JSON.

- [ ] **Step 3: Run plugin self-check**

Run:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected:

```json
{
  "status": "success"
}
```

The actual output may include additional `results` fields. The top-level status must be `success`.

- [ ] **Step 4: Review changed files**

Run:

```bash
git diff -- requirement-flow-plugin docs/superpowers
```

Expected: diff contains only the planned docs, skills, templates, and context updates.

- [ ] **Step 5: Commit final verification note if previous commits were skipped**

If the workspace is a git repository and previous commits were skipped, commit all first-slice changes:

```bash
git add requirement-flow-plugin docs/superpowers
git commit -m "feat: add unified java backend workflow first slice"
```

Expected: commit succeeds in a git repository. If this workspace is not a git repository, record that no commit was possible.

## Self-Review

Spec coverage:

- Architecture layers are covered by Tasks 2, 3, 4, and 6.
- Runtime artifacts and contracts are covered by Task 1.
- Main-flow state and stage changes are covered by Task 5.
- Gate behavior is covered by Tasks 3, 4, and 5.
- First-slice non-goals are preserved by this plan because no engine implementation, internal platform adapter, or global installation step is included.

Placeholder scan:

- This plan intentionally avoids unresolved implementation placeholders.
- JSON examples use concrete example values.
- Markdown skill outputs use explicit status contracts.

Type consistency:

- State field names match the design spec: `change_id`, `spec_status`, `constitution_checks`, `context_engine`, `quality_gates`, and `archive_status`.
- Artifact names match the design spec: `02_spec_delta.md`, `03_context_discovery.md`, `08_verification.md`, and `09_archive.md`.
