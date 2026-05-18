# V2 Agent Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace V1 contract-only agent execution with real subagent dispatch — coordinator skill + runner state management + prompt templates.

**Architecture:** New `agent-coordinator` skill tells Claude how to dispatch dev/verify/review subagents via Agent tool. `agent_execution_runner.py` gains dispatch logging, status update, and report writing functions. Prompt templates define structured result formats for each agent type.

**Tech Stack:** Python 3 (runner), Markdown (skill + prompts), JSON (state + work items)

---

## File Structure

```text
requirement-flow-plugin/
├── scripts/
│   ├── agent_execution_runner.py        # MODIFY — add dispatch logging, status update, report write
│   └── agent_execution_regression.py    # CREATE — regression test for V2 runner functions
├── skills/
│   ├── agent-coordinator/               # CREATE — new skill
│   │   ├── SKILL.md
│   │   └── prompts/
│   │       ├── dev-agent.md
│   │       ├── verify-agent.md
│   │       └── review-agent.md
│   └── main-flow/
│       └── SKILL.md                     # MODIFY — Step 7 update
├── templates/
│   └── run-state.example.json           # MODIFY — agent_execution V2 fields
└── docs/
    └── main-flow.md                     # MODIFY — Step 7 description
```

---

### Task 1: Extend agent_execution_runner.py with V2 Functions

**Files:**
- Modify: `requirement-flow-plugin/scripts/agent_execution_runner.py`
- Create: `requirement-flow-plugin/scripts/agent_execution_regression.py`

- [ ] **Step 1: Add `write_dispatch_log` function**

```python
def write_dispatch_log(run_dir: Path, action: str, agent_id: str, summary: str) -> None:
    """Append a timestamped line to agent/main-log.md."""
    log_path = run_dir / ARTIFACT_PATHS["agent_main_log"]
    timestamp = utc_now()
    line = f"| {timestamp} | {action} | {agent_id} | {summary} |"
    existing = read_text(log_path, "# Agent Main Log\n")
    write_text(log_path, existing.rstrip() + "\n" + line)
```

- [ ] **Step 2: Add `update_item_status` function**

```python
def update_item_status(run_dir: Path, item_id: str, status: str, report: dict | None = None) -> None:
    """Update a single work item's status and optional execution record in work_items.json."""
    work_items_path = run_dir / ARTIFACT_PATHS["agent_work_items"]
    data = load_json(work_items_path, {"version": "work-items-v1", "items": []})
    for item in data["items"]:
        if item["id"] == item_id:
            item["status"] = status
            if report:
                item.setdefault("execution_record", {}).update(report)
            break
    write_json(work_items_path, data)
```

- [ ] **Step 3: Add `write_report` function**

```python
def write_report(run_dir: Path, item_id: str, stage: str, result: dict) -> None:
    """Write a JSON report to agent/reports/<item_id>/<stage>.json."""
    report_path = run_dir / f"agent/reports/{item_id}/{stage}.json"
    write_json(report_path, result)
```

- [ ] **Step 4: Add `create_repair_round` function**

```python
def create_repair_round(run_dir: Path, item_id: str, findings: list, round_num: int) -> None:
    """Record a repair round: update attempts, write repair report."""
    work_items_path = run_dir / ARTIFACT_PATHS["agent_work_items"]
    data = load_json(work_items_path, {"version": "work-items-v1", "items": []})
    for item in data["items"]:
        if item["id"] == item_id:
            item["attempts"] = round_num
            item.setdefault("execution_record", {})["repair_rounds"] = round_num
            break
    write_json(work_items_path, data)
    write_report(run_dir, item_id, f"repair-{round_num}", {"findings": findings, "round": round_num})
```

- [ ] **Step 5: Add `init_work_item_execution` function**

```python
def init_work_item_execution(run_dir: Path, item_id: str) -> None:
    """Mark a work item as in_progress and create its report directory."""
    update_item_status(run_dir, item_id, "in_progress")
    report_dir = run_dir / f"agent/reports/{item_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 6: Update `final_item` to include `execution_record` field**

In `final_item()`, add to the returned dict:

```python
"execution_record": {
    "dev_agent_id": "",
    "verify_agent_id": "",
    "review_agent_id": "",
    "repair_rounds": 0,
    "reports": {
        "dev": f"agent/reports/{item_id}/dev.json",
        "verify": f"agent/reports/{item_id}/verify.json",
        "review": f"agent/reports/{item_id}/review.json",
    },
},
```

- [ ] **Step 7: Update `max_repair_rounds` default from 2 to 3**

In `main()`, change the `update_section` call's extra dict:

```python
"max_repair_rounds": 3,
```

- [ ] **Step 8: Create regression test**

Create `requirement-flow-plugin/scripts/agent_execution_regression.py`:

```python
#!/usr/bin/env python3
"""Regression test for V2 agent_execution_runner functions."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Allow import from scripts dir
sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, write_json, write_text
from agent_execution_runner import (
    validate_item,
    final_item,
    write_dispatch_log,
    update_item_status,
    write_report,
    create_repair_round,
    init_work_item_execution,
)


def test_validate_item_valid():
    item = {"id": "WI-001", "story_size": "one supervised agent iteration", "acceptance_criteria": ["c1"]}
    errors = validate_item(item)
    assert errors == [], f"Expected no errors, got {errors}"


def test_validate_item_missing_id():
    item = {"story_size": "one supervised agent iteration", "acceptance_criteria": ["c1"]}
    errors = validate_item(item)
    assert any("missing id" in e for e in errors)


def test_final_item_has_execution_record():
    item = {
        "id": "WI-001",
        "title": "Test",
        "scenario": "java-api-change",
        "story_size": "one supervised agent iteration",
        "acceptance_criteria": ["c1"],
    }
    result = final_item(item)
    assert "execution_record" in result
    assert result["execution_record"]["repair_rounds"] == 0
    assert result["execution_record"]["dev_agent_id"] == ""


def test_write_dispatch_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        write_text(run_dir / ARTIFACT_PATHS["agent_main_log"], "# Agent Main Log\n")
        write_dispatch_log(run_dir, "dev-dispatch", "agent-001", "Implementing WI-001")
        content = (run_dir / ARTIFACT_PATHS["agent_main_log"]).read_text()
        assert "dev-dispatch" in content
        assert "agent-001" in content
        assert "Implementing WI-001" in content


def test_update_item_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        items = {
            "version": "work-items-v1",
            "items": [{"id": "WI-001", "status": "pending"}],
        }
        write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], items)
        update_item_status(run_dir, "WI-001", "in_progress")
        data = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {})
        assert data["items"][0]["status"] == "in_progress"


def test_update_item_status_with_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        items = {
            "version": "work-items-v1",
            "items": [{"id": "WI-001", "status": "pending"}],
        }
        write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], items)
        update_item_status(run_dir, "WI-001", "completed", {"dev_agent_id": "agent-001"})
        data = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {})
        assert data["items"][0]["status"] == "completed"
        assert data["items"][0]["execution_record"]["dev_agent_id"] == "agent-001"


def test_write_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        write_report(run_dir, "WI-001", "dev", {"status": "success", "files_changed": ["A.java"]})
        report_path = run_dir / "agent/reports/WI-001/dev.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert data["status"] == "success"


def test_create_repair_round():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        items = {
            "version": "work-items-v1",
            "items": [{"id": "WI-001", "status": "in_progress", "attempts": 0}],
        }
        write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], items)
        create_repair_round(run_dir, "WI-001", ["test failed"], 1)
        data = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {})
        assert data["items"][0]["attempts"] == 1
        assert data["items"][0]["execution_record"]["repair_rounds"] == 1
        repair_report = run_dir / "agent/reports/WI-001/repair-1.json"
        assert repair_report.exists()


def test_init_work_item_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        items = {
            "version": "work-items-v1",
            "items": [{"id": "WI-001", "status": "pending"}],
        }
        write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], items)
        init_work_item_execution(run_dir, "WI-001")
        data = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {})
        assert data["items"][0]["status"] == "in_progress"
        assert (run_dir / "agent/reports/WI-001").is_dir()


def main() -> int:
    tests = [
        test_validate_item_valid,
        test_validate_item_missing_id,
        test_final_item_has_execution_record,
        test_write_dispatch_log,
        test_update_item_status,
        test_update_item_status_with_report,
        test_write_report,
        test_create_repair_round,
        test_init_work_item_execution,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 9: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/agent_execution_regression.py`
Expected: All 9 tests PASS

- [ ] **Step 10: Commit**

```bash
git add scripts/agent_execution_runner.py scripts/agent_execution_regression.py
git commit -m "feat: add V2 agent execution runner functions and regression tests"
```

---

### Task 2: Create agent-coordinator Skill

**Files:**
- Create: `requirement-flow-plugin/skills/agent-coordinator/SKILL.md`

- [ ] **Step 1: Create agent-coordinator SKILL.md**

```markdown
---
name: agent-coordinator
description: >
  Coordinates supervised agent execution for Java backend work items.
  Dispatches dev, verify, and review subagents using the Agent tool.
  Manages repair loops with agent resume. Use when main-flow Step 7
  begins and agent/work_items.json exists.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# agent-coordinator

Supervised agent execution coordinator. Dispatches dev, verify, and review
subagents for each work item. Manages bounded repair loops.

## Mandatory Rules

- Do not edit production source code from the coordinator role.
- Dispatch subagents using the Agent tool (subagent_type=claude).
- Do NOT read subagent internal conversation content — only use structured results.
- Verify and review agents dispatch in parallel after dev completes.
- Repair resumes the same dev agent via SendMessage.
- Update state.json and agent/main-log.md after every dispatch/complete/repair.
- Max repair rounds: read from state.json.agent_execution.max_repair_rounds (default 3).
- Mark work item as failed when max repair rounds exceeded.
- Write structured reports to agent/reports/<item-id>/.

## Work Item States

```text
pending | in_progress | completed | failed | blocked
```

## Per-Work-Item Loop

For each item in agent/work_items.json with status "pending":

### 1. Initialize

- Call `agent_execution_runner.py init_work_item_execution` to set status to in_progress
- Read work item fields: id, description, acceptance_criteria, authorized_scope, context_pack, checklist
- Read context pack from agent/context-packs/<id>.md if it exists
- Write dispatch log: action=init, agent_id=N/A

### 2. Dispatch Dev Agent

- Load prompt template from `{baseDir}/prompts/dev-agent.md`
- Replace template variables: {work_item_json}, {context_pack_content}, {coding_standards}
- Dispatch via Agent tool:
  ```
  Agent(
    description="Dev: {item_id} — {title}",
    prompt=<filled dev-agent.md>,
    subagent_type="claude",
    model="opus" if complex else "sonnet"
  )
  ```
- Record agent_id from result
- Write dispatch log: action=dev-dispatch, agent_id=<id>
- Update work item execution_record.dev_agent_id

### 3. Dispatch Verify + Review (Parallel)

After dev agent returns with status=success:

**Verify agent:**
- Load prompt template from `{baseDir}/prompts/verify-agent.md`
- Replace: {work_item_json}, {files_changed}
- Dispatch via Agent tool
- Record agent_id

**Review agent:**
- Load prompt template from `{baseDir}/prompts/review-agent.md`
- Replace: {work_item_json}, {files_changed}
- Dispatch via Agent tool
- Record agent_id

Both dispatch in a single message with two Agent tool calls.

### 4. Evaluate Results

Collect structured JSON results from both agents.

**Pass conditions:**
- verify agent: status=pass AND build_result=pass AND test_result=pass
- review agent: status=pass AND spec_compliance.status=pass AND code_quality.status=pass

**If all pass:**
- Update work item status to completed
- Write reports: dev.json, verify.json, review.json
- Write dispatch log: action=complete

**If any fail:**
- Go to Repair Loop (section 5)

### 5. Repair Loop

Check current repair round against max_repair_rounds.

**If round < max:**
- Increment repair round
- Construct repair prompt containing:
  - Original work item
  - Specific verify failures (build errors, test failures, unmet criteria)
  - Specific review findings (spec violations, code quality issues)
  - Instruction: "Fix these specific issues. Do not repeat the same approach."
- Resume dev agent via SendMessage (do NOT create new agent):
  ```
  SendMessage(
    to=<dev_agent_id>,
    message=<repair prompt>
  )
  ```
- Write dispatch log: action=repair-dispatch, round=N
- Go back to step 3 (parallel verify+review)

**If round >= max:**
- Update work item status to failed
- Write all reports
- Write dispatch log: action=max-repair-exceeded
- Add blocker to state.json.pending_confirmations

## Output Format

After processing all work items:

```text
AGENT_COORDINATOR_STATUS: complete|blocked
WORK_ITEMS_PROCESSED: <count>
WORK_ITEMS_PASSED: <count>
WORK_ITEMS_FAILED: <count>
ARTIFACTS:
- agent/work_items.json
- agent/main-log.md
- agent/reports/<id>/*.json
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <action>
```

## Knowledge Hooks

When present, load before dispatching:
- `coding-standards` — include in dev agent prompt
- `infra-components` — include in dev agent prompt
- `context-pack-builder` — generate per-item context packs
- `dynamic-checklist` — generate per-item checklists
```

- [ ] **Step 2: Commit**

```bash
git add skills/agent-coordinator/SKILL.md
git commit -m "feat: add agent-coordinator skill for supervised agent dispatch"
```

---

### Task 3: Create Subagent Prompt Templates

**Files:**
- Create: `requirement-flow-plugin/skills/agent-coordinator/prompts/dev-agent.md`
- Create: `requirement-flow-plugin/skills/agent-coordinator/prompts/verify-agent.md`
- Create: `requirement-flow-plugin/skills/agent-coordinator/prompts/review-agent.md`

- [ ] **Step 1: Create dev-agent.md**

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
5. Return your result as a JSON code block:

```json
{{
  "status": "success|failed",
  "files_changed": ["path/to/file.java"],
  "summary": "what was done",
  "compilation_result": "pass|fail",
  "notes": "anything noteworthy"
}}
```

Do NOT return anything after the JSON block.
```

- [ ] **Step 2: Create verify-agent.md**

```markdown
# Verify Agent

You are verifying a work item implementation. You are read-only — do NOT edit any files.

## Work Item

{work_item_json}

## Files Changed

{files_changed}

## Instructions

1. Run build command (mvn compile or project-configured equivalent)
2. Run test command (mvn test or project-configured equivalent)
3. Check that each acceptance criterion is met by the implementation
4. Return your result as a JSON code block:

```json
{{
  "status": "pass|fail",
  "build_result": "pass|fail",
  "test_result": "pass|fail",
  "criteria_met": ["criterion description"],
  "criteria_failed": ["criterion description"],
  "errors": ["error details if any"]
}}
```

Do NOT return anything after the JSON block.
```

- [ ] **Step 3: Create review-agent.md**

```markdown
# Review Agent

You are reviewing a work item implementation for spec compliance and code quality.
You are read-only — do NOT edit any files.

## Work Item

{work_item_json}

## Files Changed

{files_changed}

## Spec Compliance Review

Check each acceptance criterion:
- Does the implementation satisfy it?
- Is authorized_scope respected (no files outside scope)?
- Are domain rules followed?

## Code Quality Review

- Coding standards compliance
- Error handling adequacy
- Naming, structure, readability
- No security issues (injection, XSS, etc.)

## Return your result as a JSON code block:

```json
{{
  "status": "pass|fail",
  "spec_compliance": {{
    "status": "pass|fail",
    "findings": [
      {{"criterion": "...", "verdict": "met|unmet", "detail": "..."}}
    ]
  }},
  "code_quality": {{
    "status": "pass|fail",
    "findings": [
      {{"category": "...", "severity": "critical|major|minor", "detail": "..."}}
    ]
  }}
}}
```

Do NOT return anything after the JSON block.
```

- [ ] **Step 4: Commit**

```bash
git add skills/agent-coordinator/prompts/
git commit -m "feat: add subagent prompt templates for dev, verify, review"
```

---

### Task 4: Update main-flow Skill for V2 Agent Execution

**Files:**
- Modify: `requirement-flow-plugin/skills/main-flow/SKILL.md`
- Modify: `requirement-flow-plugin/docs/main-flow.md`

- [ ] **Step 1: Update Step 7 in main-flow SKILL.md**

Replace the current Step 7 content in the Flow section with:

```markdown
7. Agent execution -> 07_agent_execution.md and agent/work_items.json
   - Load agent-coordinator skill
   - For each work item: dispatch dev -> parallel verify+review -> repair if needed
   - Coordinator writes structured reports to agent/reports/<id>/
```

- [ ] **Step 2: Add Step 7 detail section after Module Progression**

Add a new section:

```markdown
## Step 7: Agent Execution

1. Run agent_execution_runner.py to validate work_items.seed.json → work_items.json
2. Load agent-coordinator skill
3. For each work item with status pending:
   a. Dispatch dev agent (Agent tool, subagent_type=claude)
   b. On dev success → dispatch verify + review agents in parallel
   c. Evaluate results: all pass → mark completed; any fail → repair loop
   d. Repair: resume same dev agent, max 3 rounds
4. After all items processed:
   - Run agent_execution_runner.py to validate final states
   - Write 07_agent_execution.md summary
   - Update state.json.agent_execution.status
5. If any items blocked/failed:
   - Write BLOCKER to pending_confirmations
```

- [ ] **Step 3: Update Step 8 description in Flow section**

```markdown
8. Code review -> 08_code_review.md (aggregate review agent results)
```

- [ ] **Step 4: Update Knowledge Hooks for Step 7**

```markdown
- Step 7: `java-agent-coordinator`, `agent-coordinator`, `context-pack-builder`, `dynamic-checklist`
```

- [ ] **Step 5: Update docs/main-flow.md Step 7**

Replace the current Step 7 description with:

```markdown
7. Agent execution: coordinator dispatches dev, verify, and review subagents
   for each work item. Repair loop with agent resume on failure. Reports
   written to agent/reports/<item-id>/.
```

- [ ] **Step 6: Commit**

```bash
git add skills/main-flow/SKILL.md docs/main-flow.md
git commit -m "feat: update main-flow for V2 agent execution with real subagent dispatch"
```

---

### Task 5: Update run-state Template

**Files:**
- Modify: `requirement-flow-plugin/templates/run-state.example.json`

- [ ] **Step 1: Update agent_execution section**

Replace the current `agent_execution` block:

```json
"agent_execution": {
  "mode": "supervised_agents",
  "status": "not_started",
  "current_work_item": "",
  "current_agent_id": "",
  "work_items_path": "agent/work_items.json",
  "repair_round": 0,
  "max_repair_rounds": 3,
  "dispatch_history": []
}
```

- [ ] **Step 2: Commit**

```bash
git add templates/run-state.example.json
git commit -m "feat: update run-state template with V2 agent execution fields"
```

---

### Task 6: Update Unified Runtime Regression

**Files:**
- Modify: `requirement-flow-plugin/scripts/unified_runtime_regression.py`

- [ ] **Step 1: Add V2 assertions to regression test**

After the existing agent_execution_runner assertions, add checks for the new functions:

```python
# V2: verify work_items.json has execution_record
work_items = load_json(run_dir / "agent/work_items.json", {})
for item in work_items.get("items", []):
    assert "execution_record" in item, f"{item['id']} missing execution_record"
    assert item["execution_record"]["repair_rounds"] == 0

# V2: verify max_repair_rounds is 3
state = load_json(run_dir / "state.json", {})
assert state["agent_execution"].get("max_repair_rounds") == 3, "max_repair_rounds should be 3"
```

- [ ] **Step 2: Run full regression**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/unified_runtime_regression.py`
Expected: PASS

- [ ] **Step 3: Run V2 agent execution regression**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/agent_execution_regression.py`
Expected: All 9 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/unified_runtime_regression.py
git commit -m "feat: add V2 assertions to unified runtime regression"
```

---

### Task 7: Install and Verify

**Files:**
- All 6 install roots

- [ ] **Step 1: Run plugin self-check**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/plugin_self_check.py`
Expected: status success

- [ ] **Step 2: Sync to all install roots**

Run the install sync script or manually copy to all 6 roots. Verify new files present:
- `skills/agent-coordinator/SKILL.md`
- `skills/agent-coordinator/prompts/dev-agent.md`
- `skills/agent-coordinator/prompts/verify-agent.md`
- `skills/agent-coordinator/prompts/review-agent.md`

- [ ] **Step 3: Verify skill count**

Check that skill count increased by 1 (new agent-coordinator skill).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: sync V2 agent execution to all install roots"
```
