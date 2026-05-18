# V2 Agent Execution Design

## Overview

V2 Agent Execution replaces the V1 contract-only mode with real subagent dispatch. The coordinator (Claude) uses the Agent tool to dispatch dev, verify, and review subagents for each work item, with a bounded repair loop on failure.

## Architecture

```text
main-flow Step 7
      │
      ▼
agent-coordinator skill (Claude behavior guide)
      │
      ├── dev agent (Agent tool)
      ├── verify agent (Agent tool, parallel with review)
      └── review agent (Agent tool, parallel with verify)
            │
            ▼
      repair loop (dispatch new dev agent with prior findings, max 3 rounds)

agent_execution_runner.py (state/validation/artifact backend)
```

**Responsibilities:**
- `agent-coordinator` skill: tells Claude how to dispatch subagents, manage repair loops, handle failures
- `agent_execution_runner.py`: state management, artifact I/O, validation (unchanged interface, new functions)
- Agent tool subagents: actual execution (dev writes code, verify runs checks, review does spec + quality review)

**Key constraints:**
- Coordinator does NOT read subagent internal conversation (context protection)
- Repair resumes the same dev agent (preserves implementation context)
- Verify and review dispatch in parallel
- Max repair rounds = 3 (configurable)

## agent-coordinator Skill

### File Structure

```text
skills/agent-coordinator/
├── SKILL.md
├── prompts/
│   ├── dev-agent.md
│   ├── verify-agent.md
│   └── review-agent.md
```

### SKILL.md Behavior

**Trigger:** main-flow Step 7 begins, reads `agent/work_items.json`.

**Per work item loop:**

1. Read work item: id, description, acceptance_criteria, authorized_scope, context_pack
2. Dispatch dev agent (Agent tool, subagent_type=claude)
   - Prompt includes: work item + coding-standards + infra-components
   - Model: opus (complex) or sonnet (standard)
   - Record agent_id
3. On dev completion → dispatch in parallel:
   - verify agent: run build/test checks
   - review agent: spec compliance + code quality (two stages merged into one)
4. Collect verify + review results
5. Decision:
   - All pass → mark work item complete, write report
   - Any fail → repair loop:
     a. Construct repair prompt (with review findings + verify errors)
     b. Resume dev agent (SendMessage, not new agent)
     c. Re-dispatch verify + review
     d. Max 3 rounds → mark failed, write BLOCKER

**Repair loop rules:**
- Resume same agent (preserves implementation context)
- Repair prompt must contain: specific failures + expected fix direction
- No "retry same fix" — each round must have a new strategy
- On max exceeded: mark blocked, write to pending_confirmations

**Context protection:**
- Do not read subagent internal conversation content
- Only use structured results returned by subagents
- Subagent result format: `{ status, findings[], files_changed[], verification_result }`

**Logging:**
- Each dispatch/complete/repair writes to `agent/main-log.md`
- Format: `| timestamp | action | agent_id | summary |`

## Subagent Prompt Templates

### dev-agent.md

```markdown
# Dev Agent

You are implementing a work item for a Java backend project.

## Work Item
{work_item_json}

## Context Pack
{context_pack_content}

## Coding Standards
{coding_standards}

## Instructions
1. Implement ONLY the changes described in the work item
2. Stay within authorized_scope — do not modify files outside it
3. Follow coding standards
4. Run local compilation after changes
5. Return structured result:

\`\`\`json
{
  "status": "success|failed",
  "files_changed": ["path/to/file.java"],
  "summary": "what was done",
  "compilation_result": "pass|fail",
  "notes": "anything noteworthy"
}
\`\`\`
```

### verify-agent.md

```markdown
# Verify Agent

You are verifying a work item implementation.

## Work Item
{work_item_json}

## Files Changed
{files_changed}

## Instructions
1. Run build: `mvn compile` or configured build command
   - If the build fails, set status to fail and skip test execution.
2. Run tests: `mvn test` or configured test command
3. Check that acceptance_criteria are met by the implementation
4. Return structured result:

\`\`\`json
{
  "status": "pass|fail",
  "build_result": "pass|fail",
  "test_result": "pass|fail",
  "criteria_met": ["criterion1"],
  "criteria_failed": ["criterion2"],
  "errors": ["error details"]
}
\`\`\`
```

### review-agent.md

```markdown
# Review Agent

You are reviewing a work item implementation for spec compliance and code quality.

## Work Item
{work_item_json}

## Files Changed
{files_changed}

## Spec Compliance Review
1. Does the implementation match acceptance_criteria?
2. Is authorized_scope respected?
3. Are domain rules followed?

## Code Quality Review
1. Coding standards compliance
2. Error handling
3. Naming, structure, readability
4. No security issues

## Return structured result:
\`\`\`json
{
  "status": "pass|fail",
  "spec_compliance": {
    "status": "pass|fail",
    "findings": [{"criterion": "...", "verdict": "met|unmet", "detail": "..."}]
  },
  "code_quality": {
    "status": "pass|fail",
    "findings": [{"category": "...", "severity": "critical|major|minor", "detail": "..."}]
  }
}
\`\`\`
```

Template variables are injected by the coordinator before dispatch via Python string format.

## Runner Changes

### agent_execution_runner.py V1 → V2

**Unchanged:**
- `validate_item()` — validates work item structure
- `final_item()` — generates complete work item with paths and agent_ids
- Artifact path constants

**New functions:**

```python
def write_dispatch_log(run_dir: Path, action: str, agent_id: str, summary: str):
    """Append one line to main-log.md"""

def update_item_status(run_dir: Path, item_id: str,
                       status: str, report: dict = None):
    """Update single work item status and report"""

def write_report(run_dir: Path, item_id: str, stage: str, result: dict):
    """Write report to reports/<item_id>/<stage>.json"""

def create_repair_round(run_dir: Path, item_id: str,
                        findings: list, round_num: int):
    """Record repair round information"""

def init_work_item_execution(run_dir: Path, item_id: str):
    """Mark a work item as in_progress and create its report directory."""
```

### state.json Changes

```json
{
  "agent_execution": {
    "mode": "supervised_agents",
    "status": "in_progress",
    "current_work_item": "WI-001",
    "current_agent_id": "agent-xxx",
    "repair_round": 0,
    "max_repair_rounds": 3,
    "dispatch_history": [
      {"item_id": "WI-001", "agent_id": "agent-xxx", "action": "dev-dispatch"}
    ]
  }
}
```

### Work Item Status Flow

```text
pending → in_progress → pass
                      → fail (max repair exceeded)
                      → blocked (missing dependency/decision)
```

Each work item gains an `execution_record`:

```json
{
  "id": "WI-001",
  "status": "pass",
  "execution_record": {
    "dev_agent_id": "agent-xxx",
    "verify_agent_id": "agent-yyy",
    "review_agent_id": "agent-zzz",
    "repair_rounds": 1,
    "reports": {
      "dev": "reports/WI-001/dev.json",
      "verify": "reports/WI-001/verify.json",
      "review": "reports/WI-001/review.json",
      "repair-1": "reports/WI-001/repair-1.json"
    }
  }
}
```

## main-flow Integration

### Step 7 Update

```text
1. Read agent/work_items.json
2. Load agent-coordinator skill
3. Process each work item sequentially:
   - Dispatch dev agent → wait
   - Dispatch verify + review in parallel → wait
   - If all pass → next item; if fail → repair loop
4. After all items:
   - Run agent_execution_runner.py to validate all item states
   - Write 07_agent_execution.md summary
   - Update state.json.agent_execution.status = "complete"
5. If blocked/failed items:
   - Write BLOCKER to pending_confirmations
   - Set state to blocked
```

### Step 6 → 7 Handoff

```text
Step 6 produces:
  06_impl_plan.md           — module-level implementation plan
  agent/work_items.seed.json — initial work items (from workflow intelligence)

Transition:
  agent_execution_runner.py validates work_items.seed.json
  → outputs agent/work_items.json (with full paths and authorized_scope)
```

### Step 7 → 8 Relationship

```text
V2 change: review is already done in Step 7's review agent
Step 8 becomes: aggregate all review agent results into 08_code_review.md
No duplicate review — aggregation only
```

### Knowledge Hooks

```text
Step 7 hooks:
  - java-agent-coordinator (existing → triggers agent-coordinator skill)
  - context-pack-builder (generates context pack per work item)
  - dynamic-checklist (generates checklist per work item)
```

### Error Recovery

```text
Scenario: Step 7 interrupted mid-execution
Recovery:
  1. Read state.json.agent_execution
  2. Find current_work_item and current_agent_id
  3. Check dispatch_history last entry
  4. If dev-dispatch incomplete → re-dispatch dev
  5. If verify/review incomplete → re-dispatch
  6. If repair interrupted → resume dev agent
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Coordinator implementation | Skill (not Python) | Claude can use Agent tool natively; Python cannot |
| Repair strategy | Dispatch new dev agent with prior findings | Preserves implementation context; avoids re-discovery |
| Review granularity | Merged spec+quality in one agent | Reduces agent count; both reviews read same files |
| Verify + review ordering | Parallel | Independent checks; halves wait time |
| Max repair rounds | 3 | Balances retry tolerance vs. stuck detection |
| Context protection | Don't read subagent logs | Prevents context bloat; structured results suffice |
| Work item sequencing | Serial per item | Simplifies scope tracking; parallel items risk merge conflicts |

## Out of Scope (V2)

- Autonomous execution mode (V3)
- Cross-repository agent dispatch
- Dynamic model selection per work item complexity (future)
- Real verification provider integration (covered by V2 Provider Adapters sub-project)
