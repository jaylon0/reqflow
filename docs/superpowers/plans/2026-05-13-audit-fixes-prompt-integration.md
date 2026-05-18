# Audit Fixes + Prompt Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all HIGH/MEDIUM audit issues and integrate prompt project methodology into agent-coordinator.

**Architecture:** Two-part plan — Part A fixes 7 technical debt items across templates, scripts, and hooks. Part B integrates Three Iron Laws, resume-based fix loops, structured output contracts, and lessons-learned into agent-coordinator SKILL.md.

**Tech Stack:** YAML, JSON, Python, Markdown

---

## Part A: Audit Fixes

### Task A-1: Fix context.template.yaml knowledge_hooks alignment

**Files:**
- Modify: `requirement-flow-plugin/templates/context.template.yaml:52-75`

The current `knowledge_hooks` section uses legacy step numbering that doesn't match V2 main-flow SKILL.md. The V2 flow has 10 stages (0-10) with specific hook assignments per stage.

**Current (broken):**
```yaml
knowledge_hooks:
    step_2:
      - spec-governance
      - spec-delta
      - constitution-check
    step_3:
      - java-context-engine
      - java-code-graph
      - java-semantic-index
      - java-impact-analysis
    step_4:
      - infra-components
      - domain-components
    step_6_before_edit:
      - quality-gates
      - tdd-gate
    step_6_after_edit:
      - coding-standards
    step_7:
      - support-review
      - coding-standards
    step_8:
      - completion-gate
```

**Target (matching main-flow SKILL.md Knowledge Hooks section):**

- [ ] **Step 1: Update knowledge_hooks**

Replace the `knowledge_hooks` block in `templates/context.template.yaml` with:

```yaml
  knowledge_hooks:
    step_02:
      - spec-governance
      - spec-delta
      - constitution-check
    step_03:
      - workflow-intelligence
      - dynamic-checklist
      - compliance-report
      - evolution-proposal
    step_04:
      - java-context-engine
      - java-code-graph
      - java-semantic-index
      - java-impact-analysis
      - context-pack-builder
    step_05:
      - infra-components
      - domain-components
      - support-infra-catalog
      - support-domain-rules
    step_06:
      - java-agent-coordinator
      - context-pack-builder
      - dynamic-checklist
    step_07:
      - java-agent-coordinator
      - agent-coordinator
      - context-pack-builder
      - dynamic-checklist
    step_08_before_edit:
      - quality-gates
      - tdd-gate
    step_08_after_edit:
      - coding-standards
    step_09:
      - compliance-report
      - completion-gate
    step_10:
      - spec-archive
      - evolution-proposal
```

- [ ] **Step 2: Verify no syntax errors**

Run: `python3 -c "import yaml; yaml.safe_load(open('requirement-flow-plugin/templates/context.template.yaml'))"`
Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
git add requirement-flow-plugin/templates/context.template.yaml
git commit -m "fix: align knowledge_hooks with V2 main-flow step numbering"
```

---

### Task A-2: Add missing ARTIFACT_PATHS entries

**Files:**
- Modify: `requirement-flow-plugin/scripts/runtime_support.py:15-33`

`ARTIFACT_PATHS` is missing `agent/compliance-report.json`, `agent/evolution-report.json`, and `agent/memory.md`. These are referenced in main-flow SKILL.md Run Files section.

- [ ] **Step 1: Add missing entries**

In `runtime_support.py`, add these three entries to the `ARTIFACT_PATHS` dict:

```python
ARTIFACT_PATHS = {
    # ... existing entries ...
    "agent_compliance_report": "agent/compliance-report.md",
    "agent_evolution_report": "agent/evolution-report.md",
    "agent_memory": "agent/memory.md",
}
```

Note: main-flow SKILL.md lists `compliance-report.md` and `evolution-report.md` (markdown), not `.json`. Use `.md` to match the spec.

- [ ] **Step 2: Run regression tests**

Run: `cd requirement-flow-plugin && python3 scripts/unified_runtime_regression.py`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add requirement-flow-plugin/scripts/runtime_support.py
git commit -m "fix: add missing compliance-report, evolution-report, memory to ARTIFACT_PATHS"
```

---

### Task A-3: Create missing 08_code_review.template.md

**Files:**
- Create: `requirement-flow-plugin/templates/08_code_review.template.md`

This template is referenced in the 10-stage chain but doesn't exist.

- [ ] **Step 1: Create template**

```markdown
# 08 Code Review

## Review Summary

{Aggregate review findings from agent-coordinator review agents}

## Per-Work-Item Reviews

{For each work item that completed agent execution:}

### {item_id}: {title}

- **Spec Compliance:** {pass/fail}
- **Code Quality:** {pass/fail}
- **Key Findings:**
  - {finding 1}
  - {finding 2}

## Cross-Cutting Concerns

- {Concerns that span multiple work items}

## Action Items

- [ ] {Actionable fix 1}
- [ ] {Actionable fix 2}

## Verdict

{PASS / FAIL / CONDITIONAL_PASS}
```

- [ ] **Step 2: Commit**

```bash
git add requirement-flow-plugin/templates/08_code_review.template.md
git commit -m "feat: add 08_code_review template for stage 8"
```

---

### Task A-4: Populate hooks/hooks.json

**Files:**
- Modify: `requirement-flow-plugin/hooks/hooks.json`

Currently empty `{"hooks": {}}`. Should contain stage hook definitions matching the knowledge_hooks in context.template.yaml.

- [ ] **Step 1: Add hook definitions**

```json
{
  "hooks": {
    "spec-governance": {
      "description": "Spec governance checks for durable behavior changes",
      "skill": "spec-governance"
    },
    "spec-delta": {
      "description": "Generate spec delta for requirement changes",
      "skill": "spec-delta"
    },
    "constitution-check": {
      "description": "Verify changes against project constitution",
      "skill": "constitution-check"
    },
    "workflow-intelligence": {
      "description": "Scenario detection and work item decomposition",
      "skill": "workflow-intelligence"
    },
    "dynamic-checklist": {
      "description": "Generate per-item checklists",
      "skill": "dynamic-checklist"
    },
    "compliance-report": {
      "description": "Generate compliance report",
      "skill": "compliance-report"
    },
    "evolution-proposal": {
      "description": "Generate evolution proposals",
      "skill": "evolution-proposal"
    },
    "java-context-engine": {
      "description": "Java code graph and semantic analysis",
      "skill": "java-context-engine"
    },
    "java-code-graph": {
      "description": "Build Java code dependency graph",
      "skill": "java-context-engine"
    },
    "java-semantic-index": {
      "description": "Build Java semantic index",
      "skill": "java-context-engine"
    },
    "java-impact-analysis": {
      "description": "Analyze impact of changes",
      "skill": "java-context-engine"
    },
    "context-pack-builder": {
      "description": "Generate per-item context packs",
      "skill": "context-pack-builder"
    },
    "infra-components": {
      "description": "Infrastructure component catalog",
      "skill": "infra-components"
    },
    "domain-components": {
      "description": "Domain component catalog",
      "skill": "domain-components"
    },
    "support-infra-catalog": {
      "description": "Infrastructure support catalog",
      "skill": "support-infra-catalog"
    },
    "support-domain-rules": {
      "description": "Domain support rules",
      "skill": "support-domain-rules"
    },
    "java-agent-coordinator": {
      "description": "Java-specific agent coordination",
      "skill": "java-agent-coordinator"
    },
    "agent-coordinator": {
      "description": "Supervised agent execution coordinator",
      "skill": "agent-coordinator"
    },
    "quality-gates": {
      "description": "Quality gate checks before module coding",
      "skill": "quality-gates"
    },
    "tdd-gate": {
      "description": "TDD compliance gate",
      "skill": "tdd-gate"
    },
    "coding-standards": {
      "description": "Coding standards compliance",
      "skill": "coding-standards"
    },
    "completion-gate": {
      "description": "Final completion gate",
      "skill": "completion-gate"
    },
    "spec-archive": {
      "description": "Archive specs after verification",
      "skill": "spec-archive"
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add requirement-flow-plugin/hooks/hooks.json
git commit -m "feat: populate hooks.json with stage hook definitions"
```

---

### Task A-5: Fix java_context_engine.py to use ARTIFACT_PATHS

**Files:**
- Modify: `requirement-flow-plugin/scripts/java_context_engine.py`

The `write_markdown()` function hardcodes paths like `agent/context-packs/java-context.md` and `04_context_discovery.md` instead of using `ARTIFACT_PATHS` from `runtime_support.py`.

- [ ] **Step 1: Import and use ARTIFACT_PATHS**

Add import at top of file:
```python
from runtime_support import ARTIFACT_PATHS
```

Update `write_markdown()` to use `ARTIFACT_PATHS`:
```python
def write_markdown(run_dir: Path, graph: dict, semantic: dict, impact: dict) -> None:
    context_pack = run_dir / ARTIFACT_PATHS["agent_context_packs"] / "java-context.md"
    # ... rest of function stays the same, just use ARTIFACT_PATHS for discovery path ...
    discovery = run_dir / ARTIFACT_PATHS["context_discovery"]
```

Wait — `ARTIFACT_PATHS` doesn't have `agent_context_packs` as a key. The context-packs directory is a directory, not a single file. Let me check what keys exist.

Looking at `runtime_support.py`, `ARTIFACT_PATHS` has these agent-related keys:
- `agent_scenario`: `agent/scenario.json`
- `agent_profile`: `agent/profile.json`
- `agent_work_items_seed`: `agent/work_items.seed.json`
- `agent_work_items`: `agent/work_items.json`
- `agent_main_log`: `agent/main-log.md`
- `agent_lessons`: `agent/lessons-learned.md`
- `agent_evolution`: `agent/evolution-report.md`

There's no `agent_context_packs` entry because it's a directory. The fix is to use `ARTIFACT_PATHS` for the discovery path and keep the context-pack path as a derived path.

- [ ] **Step 1 (revised): Use ARTIFACT_PATHS for discovery artifact**

```python
from runtime_support import ARTIFACT_PATHS

def write_markdown(run_dir: Path, graph: dict, semantic: dict, impact: dict) -> None:
    context_pack = run_dir / "agent/context-packs/java-context.md"
    # ... existing context_pack code unchanged ...

    discovery = run_dir / ARTIFACT_PATHS["context_discovery"]
    # ... rest unchanged ...
```

This ensures `04_context_discovery.md` path stays in sync with the central definition.

- [ ] **Step 2: Run regression tests**

Run: `cd requirement-flow-plugin && python3 scripts/unified_runtime_regression.py`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add requirement-flow-plugin/scripts/java_context_engine.py
git commit -m "fix: use ARTIFACT_PATHS for context_discovery path in java_context_engine"
```

---

## Part B: Prompt Project Methodology Integration

### Task B-1: Integrate Three Iron Laws and structured output contracts into agent-coordinator

**Files:**
- Modify: `requirement-flow-plugin/skills/agent-coordinator/SKILL.md`

Integrate the core patterns from the prompt project into agent-coordinator:

1. Three Iron Laws (File-as-Memory, Isolation-as-Norm, Log-as-Insurance)
2. Structured output contracts (strict PASS/FAIL + path-only)
3. Coordinator never does work (dispatch only)
4. lessons-learned.md as cross-task knowledge transfer

- [ ] **Step 1: Add Iron Laws to Mandatory Rules section**

Add after the existing Mandatory Rules in agent-coordinator SKILL.md:

```markdown
## Iron Laws (from multi-agent methodology)

1. **File-as-Memory:** All agent outputs must be persisted to files. Do not rely on conversation context for state. Work items, reports, and lessons must be written to `agent/` artifacts.

2. **Isolation-as-Norm:** Each subagent sees only what the coordinator provides in its prompt. Do not assume subagents have knowledge of other agents' work, prior conversations, or external state. Pass file paths, not file contents, in prompts.

3. **Log-as-Insurance:** Write to `agent/main-log.md` after every dispatch, completion, and repair. Timestamp format: ISO 8601. This log is the single source of truth for debugging agent execution.
```

- [ ] **Step 2: Add structured output contract to agent prompts**

Add a new section after "Output Format":

```markdown
## Agent Output Contracts

All subagents must return structured results. The coordinator extracts results from the agent's final response.

**Dev Agent Output:**
```
DEV_STATUS: success|failed
FILES_CHANGED:
- path/to/file1.java
- path/to/file2.java
SUMMARY: One-line description of what was implemented
BLOCKERS: (empty or list)
```

**Verify Agent Output:**
```
VERIFY_STATUS: pass|fail
BUILD_RESULT: pass|fail
TEST_RESULT: pass|fail
FAILURES: (empty or list of specific failures)
```

**Review Agent Output:**
```
REVIEW_STATUS: pass|fail
SPEC_COMPLIANCE: pass|fail
CODE_QUALITY: pass|fail
FINDINGS: (empty or list of specific findings)
```

**Rules:**
- Status values are strictly `pass` or `fail` — no "partial", "mostly", or "conditional"
- File paths only — never embed file contents in the output
- Findings must be specific: file path + line number + issue description
```

- [ ] **Step 3: Add lessons-learned integration**

Add to the Per-Work-Item Loop, after section 4 (Evaluate Results):

```markdown
### 4b. Update Lessons Learned

After a work item completes (pass or fail):
- Read existing `agent/lessons-learned.md`
- If the work item had repair rounds, extract the root cause pattern
- Append new lesson if the pattern is reusable (not project-specific)
- Format: `- [{item_id}] {lesson description}`
- Skip if no new lessons (don't write empty entries)

Lesson granularity guide:
- Too specific: "UserService.java line 42 needed @Transactional" — only helps this file
- Too broad: "Always check error handling" — no actionable guidance
- Just right: "Spring @Transactional must be on the public method, not the private helper" — reusable pattern
```

- [ ] **Step 4: Add coordinator discipline rules**

Add after Iron Laws:

```markdown
## Coordinator Discipline

The coordinator is an orchestrator, not an implementor:

- **Do NOT** read subagent output file contents — extract status from structured output only
- **Do NOT** edit production source code — dispatch to dev agent
- **Do NOT** run tests yourself — dispatch to verify agent
- **Do NOT** review code yourself — dispatch to review agent
- **DO** maintain state.json, main-log.md, and work_items.json
- **DO** route information between agents (test results → repair prompt)
- **DO** make go/no-go decisions based on structured outputs

Context protection: passing file paths instead of file contents keeps the coordinator's context window clean. If a subagent needs to read a file, give it the path — don't read and paste the content.
```

- [ ] **Step 5: Commit**

```bash
git add requirement-flow-plugin/skills/agent-coordinator/SKILL.md
git commit -m "feat: integrate Three Iron Laws, output contracts, lessons-learned into agent-coordinator"
```

---

### Task B-2: Switch fix loops from new-agent to resume-agent pattern

**Files:**
- Modify: `requirement-flow-plugin/skills/agent-coordinator/SKILL.md` (section 5: Repair Loop)

The current repair loop dispatches a **new** dev agent with prior findings. The prompt project's pattern uses **resume** on the same agent, which preserves the dev agent's context of what it built.

- [ ] **Step 1: Update Repair Loop section**

Replace section 5 in agent-coordinator SKILL.md with:

```markdown
### 5. Repair Loop (Resume Pattern)

Check current repair round against max_repair_rounds.

**If round < max:**
- Increment repair round
- **Resume** the original dev agent (using its agent_id from execution_record.dev_agent_id):
  ```
  Agent(
    resume: "{dev_agent_id}",
    subagent_type="claude",
    prompt: "
      VERIFY FAILURES:
      {specific verify failures}

      REVIEW FINDINGS:
      {specific review findings}

      Fix these specific issues in the files you previously modified.
      Do not repeat the same approach. Output the same structured format.
    "
  )
  ```
- The dev agent retains context of its prior implementation — no need to re-describe the original work item
- Write dispatch log: action=repair-resume, round=N, agent_id={dev_agent_id}
- Go back to step 3 (parallel verify+review)

**If round >= max:**
- Update work item status to fail
- Write all reports
- Write dispatch log: action=max-repair-exceeded
- Add blocker to state.json.pending_confirmations
```

Key change: `Agent(resume: "{dev_agent_id}")` instead of `Agent(description="Repair: ...", prompt=<full context>)`.

- [ ] **Step 2: Update dev agent dispatch to capture agent_id**

In section 2 (Dispatch Dev Agent), add explicit agent_id capture:

After the dispatch, add:
```markdown
- **Capture agent_id** from the Agent tool result
- Store in work item: `execution_record.dev_agent_id = agent_id`
- This ID is required for resume-based repair loops
```

- [ ] **Step 3: Commit**

```bash
git add requirement-flow-plugin/skills/agent-coordinator/SKILL.md
git commit -m "feat: switch repair loops to resume-agent pattern for context preservation"
```

---

### Task B-3: Add context isolation rules to subagent prompts

**Files:**
- Modify: `requirement-flow-plugin/skills/agent-coordinator/SKILL.md`

Add prompt construction rules that enforce the Isolation-as-Norm iron law.

- [ ] **Step 1: Add Prompt Construction Rules section**

Add after Coordinator Discipline:

```markdown
## Prompt Construction Rules

When building prompts for subagents, follow these rules:

1. **Pass paths, not contents:** Include file paths in the prompt. Let the subagent read the file itself. Never paste file contents into the prompt.

2. **Pass only what's needed:** A dev agent needs: work item JSON, context pack path, coding standards path. It does NOT need: other work items' status, state.json internals, or coordinator logs.

3. **Structured instruction:** Each prompt must include:
   - Clear task description (what to do)
   - Input file paths (where to read)
   - Output format (what to return)
   - Constraints (what NOT to do)

4. **Repair prompts are minimal:** When resuming for repair, only include the specific failures/findings. Do not re-describe the original task — the agent remembers.

Example dev agent prompt:
```
Implement work item: {item_id} — {title}

Read these files:
- Work item spec: agent/work_items.json (find item {item_id})
- Context pack: agent/context-packs/{item_id}.md
- Coding standards: path/to/coding-standards.md
- Lessons learned: agent/lessons-learned.md

Constraints:
- Only modify files listed in the work item's authorized scope
- Follow TDD: write failing test first, then implement
- Do not modify files outside your scope

Output format:
DEV_STATUS: success|failed
FILES_CHANGED:
- path/to/file
SUMMARY: what you implemented
```

- [ ] **Step 2: Commit**

```bash
git add requirement-flow-plugin/skills/agent-coordinator/SKILL.md
git commit -m "feat: add prompt construction rules enforcing context isolation"
```

---

### Task B-4: Verify all changes are consistent

- [ ] **Step 1: Run all regression tests**

```bash
cd requirement-flow-plugin
python3 scripts/unified_runtime_regression.py
python3 scripts/provider_adapter_regression.py
python3 scripts/workflow_intelligence_regression.py
python3 scripts/agent_execution_regression.py
```

Expected: All tests pass.

- [ ] **Step 2: Verify plugin loads**

```bash
python3 -c "
import yaml
# Check context template
with open('requirement-flow-plugin/templates/context.template.yaml') as f:
    ctx = yaml.safe_load(f)
    hooks = ctx['workflow']['knowledge_hooks']
    assert 'step_02' in hooks, 'Missing step_02'
    assert 'step_03' in hooks, 'Missing step_03'
    assert 'step_04' in hooks, 'Missing step_04'
    assert 'step_05' in hooks, 'Missing step_05'
    assert 'step_06' in hooks, 'Missing step_06'
    assert 'step_07' in hooks, 'Missing step_07'
    assert 'step_08_before_edit' in hooks, 'Missing step_08_before_edit'
    assert 'step_08_after_edit' in hooks, 'Missing step_08_after_edit'
    assert 'step_09' in hooks, 'Missing step_09'
    assert 'step_10' in hooks, 'Missing step_10'
    print('context.template.yaml: OK')

# Check hooks.json
import json
with open('requirement-flow-plugin/hooks/hooks.json') as f:
    h = json.load(f)
    assert len(h['hooks']) > 0, 'hooks.json still empty'
    print(f'hooks.json: OK ({len(h[\"hooks\"])} hooks)')

# Check ARTIFACT_PATHS
import sys
sys.path.insert(0, 'requirement-flow-plugin/scripts')
from runtime_support import ARTIFACT_PATHS
assert 'agent_compliance_report' in ARTIFACT_PATHS, 'Missing agent_compliance_report'
assert 'agent_evolution_report' in ARTIFACT_PATHS, 'Missing agent_evolution_report'
assert 'agent_memory' in ARTIFACT_PATHS, 'Missing agent_memory'
print('ARTIFACT_PATHS: OK')

print('All checks passed.')
"
```

- [ ] **Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: final consistency checks for audit fixes and prompt integration"
```
