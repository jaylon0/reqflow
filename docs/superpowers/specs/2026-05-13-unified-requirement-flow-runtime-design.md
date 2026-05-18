# Unified Requirement Flow Runtime

Date: 2026-05-13

## Goal

Upgrade `requirement-flow-plugin` from a set of partially connected workflow
contracts into one unified Requirement Flow runtime for Java backend delivery.

The runtime must keep `main-flow` as the only user-facing entry point while
integrating the strongest ideas from Ralph, PCE, gstack/gbrain, Superpowers,
KStack, and the existing Requirement Flow plugin.

The integration must not expose competing flows to the user. Source names remain
visible in trace and evidence artifacts so capability coverage can be audited,
but the operating model is Requirement Flow.

## Confirmed Direction

- Use `main-flow` as the single user-facing workflow.
- Use a 10-stage artifact chain instead of the current 01-09 chain.
- Keep user-facing names unified under Requirement Flow.
- Preserve source capability names in trace and evidence layers.
- Use one agent execution model, not separate Ralph, main/sub-agent, and
  Superpowers subagent loops.
- Implement V1 as local runners plus supervised agent contracts.
- Reserve autonomous execution, external learning backends, true graph
  databases, and vector indexes for later versions.

## Architecture

`main-flow` owns flow order, state recovery, checkpoints, user confirmation,
runner dispatch, and final completion decisions.

Specialized runners own artifact generation and state updates:

```text
main-flow
  -> spec_governance_runner.py
  -> workflow_intelligence_runner.py
  -> java_context_engine.py
  -> agent_execution_runner.py
  -> delivery_verification_runner.py
  -> evolution_runner.py
```

`main-flow` must not absorb each runner's implementation logic. It should call
the runner, inspect the status, write or update `state.json`, and decide whether
to continue, checkpoint, or stop.

## Runtime Artifact Chain

The runtime writes fixed run artifacts under:

```text
.dev-workflow/runs/<run-id>/
```

The V1 stage artifacts are:

```text
01_prd_summary.md
02_spec_delta.md
03_workflow_intelligence.md
04_context_discovery.md
05_tech_plan.md
06_impl_plan.md
07_agent_execution.md
08_code_review.md
09_verification.md
10_archive.md
```

The renamed and inserted stages are intentional:

- `03_workflow_intelligence.md` makes Ralph, PCE, gstack/gbrain, Superpowers,
  and KStack capability trace visible before implementation planning.
- `04_context_discovery.md` keeps Java code graph, semantic search, impact
  analysis, and context pack generation in one context stage.
- `07_agent_execution.md` makes supervised work item execution, handoff, report
  paths, and repair state explicit.
- `10_archive.md` separates final archive and evolution proposals from
  verification.

## Source Capability Mapping

User-facing workflow names are Requirement Flow names:

- scenario
- profile
- work items
- context pack
- checklist
- verification
- archive
- evolution proposal

Trace and evidence artifacts preserve source families:

| Source | Core Capability Absorbed | Requirement Flow Location |
|---|---|---|
| Ralph | PRD clarification, one-iteration work item sizing, acceptance criteria, pass/fail/notes | `06_impl_plan.md`, `07_agent_execution.md`, `agent/work_items.json` |
| PCE | Scenario detection, guideline profile, dynamic checklist, memory contract, evolution hook | `03_workflow_intelligence.md`, `agent/scenario.json`, `agent/profile.json`, `agent/checklists/` |
| gstack/gbrain | Tool verification signals, browser/API/UI evidence, learning signals, skill evolution proposal | `09_verification.md`, `10_archive.md`, `agent/lessons-learned.md`, `agent/evolution-report.md` |
| Superpowers | Design before implementation, TDD discipline, subagent boundaries, review, verification before completion | All stages, especially `05_tech_plan.md`, `07_agent_execution.md`, `08_code_review.md`, `09_verification.md` |
| KStack | Java code graph, semantic context, impact analysis, delivery verification and repair | `04_context_discovery.md`, `09_verification.md` |
| Requirement Flow | Orchestration, checkpoints, state recovery, provider-neutral delivery | `main-flow`, `state.json`, all run artifacts |

## Agent Execution Model

Ralph loop, main/sub-agent collaboration, and Superpowers
subagent-driven-development are mutually overlapping execution ideas. The
runtime must not expose them as separate competing loops.

Requirement Flow uses one execution model:

```text
main agent
  -> coordinator
      -> dev agent
      -> verify agent
      -> review agent
      -> repair decision
```

V1 mode is `supervised_agents`.

Responsibilities:

- `main agent`: user interaction, confirmations, final decisions, cross-turn
  context, and checkpoint handling.
- `coordinator`: work item state, handoff paths, report paths, and status
  updates. It does not edit production code.
- `dev agent`: implements one authorized work item at a time.
- `verify agent`: read-only verification for one work item or completed run.
- `review agent`: read-only review for spec match and code quality.

The agent execution artifacts are:

```text
07_agent_execution.md
agent/work_items.json
agent/main-log.md
agent/reports/<work-item-id>/dev-report.md
agent/reports/<work-item-id>/verify-report.md
agent/reports/<work-item-id>/review-report.md
```

V1 state records:

```json
{
  "agent_execution": {
    "execution_mode": "supervised_agents",
    "write_parallelism": "serial",
    "read_parallelism": "allowed",
    "autonomous_loop": "reserved",
    "current_work_item": "",
    "repair_round": 0,
    "max_repair_rounds": 2
  }
}
```

Only one `execution_mode` may be active in a run:

```text
manual_contract | supervised_agents | autonomous_loop
```

V1 implements `supervised_agents` and may support `manual_contract` as a
fallback. `autonomous_loop` is reserved for future versions and must not be
enabled by default.

## Workflow Intelligence Boundary

PCE-derived capability belongs before execution. It informs planning and
checklists, but it does not schedule agents or modify code.

`workflow_intelligence_runner.py` writes:

```text
03_workflow_intelligence.md
agent/scenario.json
agent/profile.json
agent/checklists/<work-item-id>.json
agent/work_items.seed.json or agent/work_items.json
state.json.workflow_intelligence
```

It must:

- Generate a capability trace matrix.
- Detect the scenario with confidence and alternatives.
- Select the guideline profile for the scenario.
- Generate dynamic checklists for work items.
- Record the memory contract and evolution hook.
- Checkpoint through `main-flow` when scenario confidence is too low or
  alternatives conflict in a way that changes implementation.

It must not:

- Dispatch agents.
- Edit production code.
- Patch skills, templates, or persistent memory.
- Pretend a source capability is executable when only a contract exists.

## Context Discovery Boundary

`java_context_engine.py` remains the Java context provider for V1.

It writes:

```text
04_context_discovery.md
graph/java-code-graph.response.json
rag/java-semantic-index.response.json
graph/java-impact-analysis.response.json
agent/context-packs/java-context.md
state.json.context_engine
```

The current provider is a local heuristic source scanner. It must identify its
provider honestly as local source scanning and lexical semantic matching. It
must not claim ASM bytecode evidence, a graph database, or vector RAG evidence.

## Runner Contracts

### `spec_governance_runner.py`

Inputs:

```text
01_prd_summary.md
.dev-workflow/constitution.md
.dev-workflow/specs/
```

Outputs:

```text
02_spec_delta.md
state.json.spec_governance
```

Responsibilities:

- Generate or update the delta spec.
- Run constitution checks.
- Mark clarification blockers.
- Decide whether the run may enter context discovery.

### `workflow_intelligence_runner.py`

Inputs:

```text
01_prd_summary.md
02_spec_delta.md
state.json
```

Outputs:

```text
03_workflow_intelligence.md
agent/scenario.json
agent/profile.json
agent/checklists/<work-item-id>.json
agent/work_items.seed.json or agent/work_items.json
state.json.workflow_intelligence
```

Responsibilities:

- Create the capability trace.
- Detect scenario and confidence.
- Select guideline profile.
- Generate dynamic checklist artifacts.
- Seed initial work items.

### `agent_execution_runner.py`

Inputs:

```text
06_impl_plan.md
04_context_discovery.md
agent/work_items.json
agent/checklists/
agent/context-packs/
```

Outputs:

```text
07_agent_execution.md
agent/main-log.md
agent/reports/<work-item-id>/
state.json.agent_execution
```

Responsibilities:

- Validate Ralph-style work item sizing.
- Prepare dev, verify, and review handoffs.
- Record supervised agent dispatch state.
- Summarize reports.
- Manage bounded repair rounds.

### `delivery_verification_runner.py`

Inputs:

```text
07_agent_execution.md
agent/reports/
providers.yaml
```

Outputs:

```text
09_verification.md
state.json.delivery_verification
```

Responsibilities:

- Summarize build, test, API, RPC, message, UI, DB, cache, search, and log
  verification.
- Distinguish automated evidence, manual evidence, and missing providers.
- Produce the final verification status for `main-flow`.

### `evolution_runner.py`

Inputs:

```text
03_workflow_intelligence.md
07_agent_execution.md
08_code_review.md
09_verification.md
state.json
```

Outputs:

```text
10_archive.md
agent/lessons-learned.md
agent/evolution-report.md
state.json.archive
```

Responsibilities:

- Archive the accepted spec delta.
- Record run lessons.
- Generate evolution proposals for checklists, skills, templates, providers, or
  memory.
- Avoid applying proposals without explicit user confirmation.

## State Model

`state.json` remains the source of truth for recovery. V1 should add or update
these top-level sections:

```json
{
  "spec_governance": {},
  "workflow_intelligence": {},
  "context_engine": {},
  "agent_execution": {},
  "delivery_verification": {},
  "archive": {}
}
```

Each section must include:

- `status`: `not_started | ready | blocked | failed | complete`
- `artifact_paths`
- `blockers`
- `last_updated_at`
- `evidence_refs`

`main-flow` uses these sections to resume from the last stable stage instead of
guessing from markdown content.

## V1 Scope

V1 focuses on making the full chain runnable, traceable, and resumable.

V1 includes:

- 10-stage artifact chain.
- Updated `state.json` schema.
- Local `workflow_intelligence_runner.py`.
- Local `spec_governance_runner.py`.
- Existing `java_context_engine.py` wired into stage 04.
- Local `agent_execution_runner.py` for supervised agent contracts and state.
- Local `delivery_verification_runner.py` for automated, manual, and
  missing-provider summaries.
- Local `evolution_runner.py` for archive, lessons, and proposals.
- Regression coverage for the complete artifact chain.
- `main-flow` skill and documentation updates for the unified entry point.

V1 does not include:

- A true autonomous Ralph loop.
- Child agents running without main-agent supervision.
- Automatic writes to global memory.
- Automatic skill patches.
- Real gstack/gbrain backend integration.
- Neo4j, ASM bytecode parsing, or vector database backends.
- A provider platform rewrite.
- Parallel production code writes.

## Later Versions

V2 may add:

- More automatic supervised agent dispatch.
- Parallel read-only verify and review agents.
- Richer provider adapters.
- Stricter spec validation.
- Deeper scenario, profile, and checklist rules.

V3 may add:

- `autonomous_loop`.
- Ralph-style autonomous iterations.
- gbrain and skill evolution backends.
- Graph database and vector index backends.
- Cross-project learning and global capability evolution.

## Success Criteria

Given a requirement and a project path, `main-flow` can:

1. Generate the full 01-10 artifact chain.
2. Preserve source capability trace for Ralph, PCE, gstack/gbrain,
   Superpowers, KStack, and Requirement Flow.
3. Write status and evidence back to `state.json`.
4. Produce Java context evidence through the existing local context engine.
5. Generate supervised agent handoff and report contracts.
6. Summarize verification with automated, manual, and missing-provider evidence.
7. Generate archive output, lessons learned, and evolution proposals without
   silently modifying memory, skills, templates, or global configuration.

## Implementation Decisions

- `workflow_intelligence_runner.py` owns initial work item seeding and writes
  `agent/work_items.seed.json`.
- `agent_execution_runner.py` owns final work item validation and writes
  `agent/work_items.json`.
- `agent_execution_runner.py` must reject work items that are too large for one
  supervised agent iteration, lack acceptance criteria, or lack report paths.
- Existing installed plugin copies must be synchronized only after source
  verification succeeds.
- The current workspace is not a git repository, so commit steps cannot run
  unless the project is moved into or initialized as a repository.
