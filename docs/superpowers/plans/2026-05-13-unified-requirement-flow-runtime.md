# Unified Requirement Flow Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable V1 Unified Requirement Flow Runtime that generates the approved 01-10 artifact chain, writes recoverable state, and integrates workflow intelligence, spec governance, Java context, supervised agent execution, delivery verification, and evolution proposals.

**Architecture:** Keep `main-flow` as the only user-facing entry point. Add focused Python runners that write their own artifacts and state sections, plus a shared runtime helper for paths, JSON state, markdown writes, and status updates. Preserve the existing Java context engine but update it to write the new stage-04 artifact while keeping backward-compatible behavior where practical.

**Tech Stack:** Python 3 standard library, Markdown skills/docs/templates, JSON run state, existing plugin self-check.

---

## File Structure

Create these files:

- `requirement-flow-plugin/scripts/runtime_support.py` - shared helpers for state loading, artifact paths, JSON writes, markdown writes, and status updates.
- `requirement-flow-plugin/scripts/unified_runtime_regression.py` - end-to-end regression for the 01-10 local runtime chain.
- `requirement-flow-plugin/scripts/spec_governance_runner.py` - generates `02_spec_delta.md` and `state.json.spec_governance`.
- `requirement-flow-plugin/scripts/workflow_intelligence_runner.py` - generates `03_workflow_intelligence.md`, scenario/profile/checklist artifacts, and `agent/work_items.seed.json`.
- `requirement-flow-plugin/scripts/agent_execution_runner.py` - validates seeded work items and writes `07_agent_execution.md`, final work items, handoff state, and report paths.
- `requirement-flow-plugin/scripts/delivery_verification_runner.py` - writes `09_verification.md` from agent reports and provider evidence.
- `requirement-flow-plugin/scripts/evolution_runner.py` - writes `10_archive.md`, lessons learned, and evolution proposal.
- `requirement-flow-plugin/templates/run-artifacts/03_workflow_intelligence.template.md` - workflow intelligence stage template.
- `requirement-flow-plugin/templates/run-artifacts/04_context_discovery.template.md` - new context discovery stage template.
- `requirement-flow-plugin/templates/run-artifacts/05_tech_plan.template.md` - new tech plan stage template.
- `requirement-flow-plugin/templates/run-artifacts/06_impl_plan.template.md` - new implementation plan stage template.
- `requirement-flow-plugin/templates/run-artifacts/07_agent_execution.template.md` - new agent execution stage template.
- `requirement-flow-plugin/templates/run-artifacts/10_archive.template.md` - new archive stage template.

Modify these files:

- `requirement-flow-plugin/scripts/java_context_engine.py` - add support for writing `04_context_discovery.md`.
- `requirement-flow-plugin/scripts/java_context_engine_regression.py` - assert the new context artifact path.
- `requirement-flow-plugin/templates/run-state.example.json` - update artifact paths and V1 runtime state sections.
- `requirement-flow-plugin/skills/main-flow/SKILL.md` - document 10-stage unified runtime and runner boundaries.
- `requirement-flow-plugin/docs/main-flow.md` - document 10-stage unified runtime.
- `requirement-flow-plugin/docs/workflow-intelligence.md` - align work item seeding and final validation responsibilities.
- `requirement-flow-plugin/README.md` - document the V1 runtime runner chain.

Do not delete old stage templates in this implementation. Keep legacy templates for compatibility unless a separate cleanup task is approved.

## Task 1: Add End-to-End Regression First

**Files:**
- Create: `requirement-flow-plugin/scripts/unified_runtime_regression.py`

- [ ] **Step 1: Create the failing regression script**

Create `requirement-flow-plugin/scripts/unified_runtime_regression.py`:

```python
#!/usr/bin/env python3
"""Regression for the Unified Requirement Flow Runtime V1 chain."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], cwd: Path) -> None:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def write_sample_java_project(project_root: Path) -> None:
    src = project_root / "src/main/java/com/example/order"
    src.mkdir(parents=True)
    (src / "OrderController.java").write_text(
        """
package com.example.order;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
public class OrderController {
  private OrderService orderService;

  @GetMapping("/list")
  public java.util.List<OrderVO> list(OrderDTO dto) {
    return orderService.listOrders(dto);
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (src / "OrderService.java").write_text(
        """
package com.example.order;

public class OrderService {
  private OrderMapper orderMapper;

  public java.util.List<OrderVO> listOrders(OrderDTO dto) {
    int total = orderMapper.countOrders(dto);
    return orderMapper.listOrders(dto, total);
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (src / "OrderMapper.java").write_text(
        """
package com.example.order;

public class OrderMapper {
  public int countOrders(OrderDTO dto) { return 0; }
  public java.util.List<OrderVO> listOrders(OrderDTO dto, int total) { return java.util.Collections.emptyList(); }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (src / "OrderDTO.java").write_text("package com.example.order;\npublic class OrderDTO {}\n", encoding="utf-8")
    (src / "OrderVO.java").write_text("package com.example.order;\npublic class OrderVO {}\n", encoding="utf-8")


def write_prd(run_dir: Path) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "01_prd_summary.md").write_text(
        """
# 01 PRD Summary

## Requirement

新增订单列表筛选并同步 list count 查询。

## Acceptance Criteria

- Controller list endpoint accepts the new filter.
- List and count query behavior remains consistent.
- Verification evidence is recorded.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "run_id": "regression-run",
                "project": "sample-order",
                "requirement": "新增订单列表筛选并同步 list count 查询",
                "current_step": 1,
                "completed_steps": [],
                "artifact_paths": {},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def assert_json(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"missing json artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_text(path: Path, required: list[str]) -> str:
    if not path.exists():
        raise AssertionError(f"missing markdown artifact: {path}")
    text = path.read_text(encoding="utf-8")
    for item in required:
        if item not in text:
            raise AssertionError(f"missing text {item!r} in {path}")
    return text


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        project_root = tmp_root / "project"
        run_dir = tmp_root / "run"
        project_root.mkdir()
        write_sample_java_project(project_root)
        write_prd(run_dir)

        run_cmd([sys.executable, "scripts/spec_governance_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/workflow_intelligence_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd(
            [
                sys.executable,
                "scripts/java_context_engine.py",
                "analyze",
                "--project-root",
                str(project_root),
                "--run-dir",
                str(run_dir),
                "--requirement",
                "新增订单列表筛选并同步 list count 查询",
                "--top-k",
                "5",
            ],
            PLUGIN_ROOT,
        )
        run_cmd([sys.executable, "scripts/agent_execution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/delivery_verification_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/evolution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        expected_markdown = [
            "02_spec_delta.md",
            "03_workflow_intelligence.md",
            "04_context_discovery.md",
            "07_agent_execution.md",
            "09_verification.md",
            "10_archive.md",
        ]
        for rel in expected_markdown:
            assert_text(run_dir / rel, ["#"])

        scenario = assert_json(run_dir / "agent/scenario.json")
        profile = assert_json(run_dir / "agent/profile.json")
        seeded = assert_json(run_dir / "agent/work_items.seed.json")
        work_items = assert_json(run_dir / "agent/work_items.json")
        state = assert_json(run_dir / "state.json")

        assert scenario["id"] == "java-api-change"
        assert profile["name"] == "java-backend-delivery"
        assert seeded["items"][0]["id"] == "wi-001"
        assert work_items["items"][0]["status"] == "pending"
        assert state["workflow_intelligence"]["status"] == "complete"
        assert state["agent_execution"]["execution_mode"] == "supervised_agents"
        assert state["delivery_verification"]["status"] == "complete"
        assert state["archive"]["status"] == "complete"

    print("unified runtime regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the regression to verify RED**

Run from `/Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin`:

```bash
python3 scripts/unified_runtime_regression.py
```

Expected: fails because `scripts/spec_governance_runner.py` does not exist.

## Task 2: Add Shared Runtime Support

**Files:**
- Create: `requirement-flow-plugin/scripts/runtime_support.py`

- [ ] **Step 1: Create runtime helper module**

Create `requirement-flow-plugin/scripts/runtime_support.py`:

```python
#!/usr/bin/env python3
"""Shared helpers for Requirement Flow local runtime runners."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_VALUES = {"not_started", "ready", "blocked", "failed", "complete"}

ARTIFACT_PATHS = {
    "prd_summary": "01_prd_summary.md",
    "spec_delta": "02_spec_delta.md",
    "workflow_intelligence": "03_workflow_intelligence.md",
    "context_discovery": "04_context_discovery.md",
    "tech_plan": "05_tech_plan.md",
    "impl_plan": "06_impl_plan.md",
    "agent_execution": "07_agent_execution.md",
    "code_review": "08_code_review.md",
    "verification": "09_verification.md",
    "archive": "10_archive.md",
    "agent_scenario": "agent/scenario.json",
    "agent_profile": "agent/profile.json",
    "agent_work_items_seed": "agent/work_items.seed.json",
    "agent_work_items": "agent/work_items.json",
    "agent_main_log": "agent/main-log.md",
    "agent_lessons": "agent/lessons-learned.md",
    "agent_evolution": "agent/evolution-report.md",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_run_dir(run_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "agent/checklists").mkdir(parents=True, exist_ok=True)
    (run_dir / "agent/context-packs").mkdir(parents=True, exist_ok=True)
    (run_dir / "agent/reports").mkdir(parents=True, exist_ok=True)
    return run_dir


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_state(run_dir: Path) -> dict[str, Any]:
    state = load_json(run_dir / "state.json", {})
    state.setdefault("artifact_paths", {})
    state["artifact_paths"].update({key: value for key, value in ARTIFACT_PATHS.items()})
    for section in [
        "spec_governance",
        "workflow_intelligence",
        "context_engine",
        "agent_execution",
        "delivery_verification",
        "archive",
    ]:
        state.setdefault(
            section,
            {
                "status": "not_started",
                "artifact_paths": [],
                "blockers": [],
                "last_updated_at": "",
                "evidence_refs": [],
            },
        )
    return state


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    write_json(run_dir / "state.json", state)


def update_section(
    state: dict[str, Any],
    section: str,
    status: str,
    artifact_paths: list[str],
    evidence_refs: list[str],
    blockers: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"invalid status {status!r}")
    payload: dict[str, Any] = {
        "status": status,
        "artifact_paths": artifact_paths,
        "blockers": blockers or [],
        "last_updated_at": utc_now(),
        "evidence_refs": evidence_refs,
    }
    if extra:
        payload.update(extra)
    state[section] = payload


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def requirement_text(run_dir: Path) -> str:
    state = load_json(run_dir / "state.json", {})
    if state.get("requirement"):
        return str(state["requirement"])
    return read_text(run_dir / ARTIFACT_PATHS["prd_summary"], "")
```

- [ ] **Step 2: Run a syntax check**

Run from `/Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin`:

```bash
python3 -m py_compile scripts/runtime_support.py
```

Expected: exits with status 0.

## Task 3: Implement Spec Governance Runner

**Files:**
- Create: `requirement-flow-plugin/scripts/spec_governance_runner.py`

- [ ] **Step 1: Add spec governance runner**

Create `requirement-flow-plugin/scripts/spec_governance_runner.py`:

```python
#!/usr/bin/env python3
"""Generate V1 spec governance artifacts for a Requirement Flow run."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_state, read_text, requirement_text, save_state, update_section, write_text


def build_spec_delta(run_dir: Path) -> str:
    prd = read_text(run_dir / ARTIFACT_PATHS["prd_summary"], "")
    requirement = requirement_text(run_dir).strip() or "Requirement from 01_prd_summary.md"
    blocker = "None" if prd.strip() else "Missing 01_prd_summary.md content"
    status = "ready" if blocker == "None" else "blocked"
    return f"""# 02 Spec Delta

## Change

{requirement}

## Affected Capabilities

- Java backend delivery
- Requirement Flow runtime

## ADDED Requirements

### Requirement: Preserve requested behavior through implementation
#### Scenario: Requirement is implemented and verified
- Given the approved requirement summary
- When the runtime proceeds through planning, execution, and verification
- Then artifacts and state must preserve traceable acceptance evidence

## MODIFIED Requirements

- None

## REMOVED Requirements

- None

## Clarifications

- None

## Constitution Checks

- Status: {status}
- Evidence: local V1 spec governance runner

## Approval

- Status: draft
- Approved by:
- Approved at:

## BLOCKER

- {blocker}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    content = build_spec_delta(run_dir)
    write_text(run_dir / ARTIFACT_PATHS["spec_delta"], content)
    blocked = "Missing 01_prd_summary.md content" in content
    update_section(
        state,
        "spec_governance",
        "blocked" if blocked else "complete",
        [ARTIFACT_PATHS["spec_delta"]],
        [ARTIFACT_PATHS["prd_summary"], ARTIFACT_PATHS["spec_delta"]],
        ["Missing 01_prd_summary.md content"] if blocked else [],
    )
    save_state(run_dir, state)
    print("SPEC_GOVERNANCE_STATUS:", state["spec_governance"]["status"])
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify runner syntax**

Run:

```bash
python3 -m py_compile scripts/spec_governance_runner.py
```

Expected: exits with status 0.

## Task 4: Implement Workflow Intelligence Runner

**Files:**
- Create: `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`

- [ ] **Step 1: Add workflow intelligence runner**

Create `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`:

```python
#!/usr/bin/env python3
"""Generate V1 workflow intelligence artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_state, requirement_text, save_state, update_section, write_json, write_text


def detect_scenario(requirement: str) -> dict:
    lowered = requirement.lower()
    if any(token in lowered for token in ["controller", "api", "接口", "列表", "查询", "filter", "筛选"]):
        return {
            "id": "java-api-change",
            "name": "Java API or controller change",
            "confidence": 0.86,
            "alternatives": ["java-service-change", "java-dao-query-change"],
            "reason": "Requirement mentions API/list/query/filter behavior.",
        }
    return {
        "id": "java-backend-change",
        "name": "Java backend change",
        "confidence": 0.62,
        "alternatives": ["java-service-change"],
        "reason": "Requirement is backend-oriented but lacks a precise layer signal.",
    }


def profile_for_scenario(scenario_id: str) -> dict:
    return {
        "name": "java-backend-delivery",
        "source": "Requirement Flow V1",
        "severity": "balanced",
        "scenario": scenario_id,
        "ruleset": [
            "Preserve controller/service/dao boundaries.",
            "Keep work items small enough for one supervised agent iteration.",
            "Every work item must have acceptance criteria.",
            "Verification evidence must distinguish automated, manual, and missing-provider checks.",
        ],
    }


def seed_work_items(requirement: str, scenario: dict) -> dict:
    return {
        "version": "work-items-seed-v1",
        "source": "workflow_intelligence_runner.py",
        "items": [
            {
                "id": "wi-001",
                "title": "Implement approved Java backend requirement",
                "scenario": scenario["id"],
                "story_size": "one supervised agent iteration",
                "description": requirement,
                "acceptance_criteria": [
                    "Implementation stays within authorized scope from the implementation plan.",
                    "Context evidence from 04_context_discovery.md is reviewed before editing.",
                    "Verification evidence is recorded in 09_verification.md.",
                ],
                "priority": 1,
                "passes": False,
                "notes": "",
            }
        ],
    }


def checklist_for_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "source": "PCE dynamic checklist V1",
        "checks": [
            {"id": "ctx", "required": True, "text": "Context pack is present before execution."},
            {"id": "scope", "required": True, "text": "Authorized scope is recorded before edits."},
            {"id": "acceptance", "required": True, "text": "Acceptance criteria are verifiable."},
            {"id": "verification", "required": True, "text": "Verification result is recorded."},
        ],
    }


def capability_trace() -> str:
    return """| Source | Capability | Runtime Location | Status |
|---|---|---|---|
| Ralph | work item sizing and acceptance criteria | agent/work_items.seed.json | V1 seed |
| PCE | scenario, profile, dynamic checklist | agent/scenario.json, agent/profile.json, agent/checklists/ | V1 local |
| gstack/gbrain | learning and evolution signal | agent/evolution-report.md | V1 proposal |
| Superpowers | design, review, verification discipline | 05-09 artifacts | V1 process |
| KStack | Java context and impact evidence | 04_context_discovery.md | V1 local context |
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    requirement = requirement_text(run_dir).strip()
    scenario = detect_scenario(requirement)
    profile = profile_for_scenario(scenario["id"])
    work_items = seed_work_items(requirement, scenario)

    write_json(run_dir / ARTIFACT_PATHS["agent_scenario"], scenario)
    write_json(run_dir / ARTIFACT_PATHS["agent_profile"], profile)
    write_json(run_dir / ARTIFACT_PATHS["agent_work_items_seed"], work_items)
    for item in work_items["items"]:
        write_json(run_dir / f"agent/checklists/{item['id']}.json", checklist_for_item(item))

    write_text(
        run_dir / ARTIFACT_PATHS["workflow_intelligence"],
        f"""# 03 Workflow Intelligence

## Scenario

- ID: {scenario['id']}
- Name: {scenario['name']}
- Confidence: {scenario['confidence']}
- Reason: {scenario['reason']}

## Guideline Profile

- Name: {profile['name']}
- Severity: {profile['severity']}

## Capability Trace

{capability_trace()}
## Work Item Seed

- Path: {ARTIFACT_PATHS['agent_work_items_seed']}
- Count: {len(work_items['items'])}

## BLOCKER

- None
""",
    )
    update_section(
        state,
        "workflow_intelligence",
        "complete",
        [
            ARTIFACT_PATHS["workflow_intelligence"],
            ARTIFACT_PATHS["agent_scenario"],
            ARTIFACT_PATHS["agent_profile"],
            ARTIFACT_PATHS["agent_work_items_seed"],
        ],
        [ARTIFACT_PATHS["spec_delta"], ARTIFACT_PATHS["workflow_intelligence"]],
        [],
        {"scenario_id": scenario["id"], "profile": profile["name"]},
    )
    save_state(run_dir, state)
    print("WORKFLOW_INTELLIGENCE_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify runner syntax**

Run:

```bash
python3 -m py_compile scripts/workflow_intelligence_runner.py
```

Expected: exits with status 0.

## Task 5: Update Java Context Engine To Stage 04

**Files:**
- Modify: `requirement-flow-plugin/scripts/java_context_engine.py`
- Modify: `requirement-flow-plugin/scripts/java_context_engine_regression.py`

- [ ] **Step 1: Update context artifact name**

In `scripts/java_context_engine.py`, change the markdown artifact write from `03_context_discovery.md` to `04_context_discovery.md`, and update any returned artifact path list to include `04_context_discovery.md`.

The resulting artifact path list must include:

```python
[
    "graph/java-code-graph.response.json",
    "rag/java-semantic-index.response.json",
    "graph/java-impact-analysis.response.json",
    "agent/context-packs/java-context.md",
    "04_context_discovery.md",
]
```

- [ ] **Step 2: Update Java context regression expectation**

In `scripts/java_context_engine_regression.py`, replace the expected context artifact path:

```python
"03_context_discovery.md",
```

with:

```python
"04_context_discovery.md",
```

- [ ] **Step 3: Run Java context regression**

Run:

```bash
python3 scripts/java_context_engine_regression.py
```

Expected: regression passes and confirms `04_context_discovery.md`.

## Task 6: Implement Agent Execution Runner

**Files:**
- Create: `requirement-flow-plugin/scripts/agent_execution_runner.py`

- [ ] **Step 1: Add agent execution runner**

Create `requirement-flow-plugin/scripts/agent_execution_runner.py`:

```python
#!/usr/bin/env python3
"""Validate seeded work items and create supervised agent execution contracts."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, load_state, save_state, update_section, write_json, write_text


def validate_item(item: dict) -> list[str]:
    errors: list[str] = []
    if not item.get("id"):
        errors.append("missing id")
    if item.get("story_size") != "one supervised agent iteration":
        errors.append(f"{item.get('id', '<unknown>')} story_size must be one supervised agent iteration")
    if not item.get("acceptance_criteria"):
        errors.append(f"{item.get('id', '<unknown>')} acceptance_criteria is empty")
    return errors


def final_item(item: dict) -> dict:
    item_id = item["id"]
    return {
        "id": item_id,
        "title": item["title"],
        "scenario": item["scenario"],
        "status": "pending",
        "priority": item.get("priority", 1),
        "story_size": item["story_size"],
        "authorized_scope": {"modules": [], "files": []},
        "context_pack": "agent/context-packs/java-context.md",
        "checklist": f"agent/checklists/{item_id}.json",
        "acceptance_criteria": item["acceptance_criteria"],
        "agent_ids": {"dev": "", "verify": "", "review": ""},
        "reports": {
            "dev": f"agent/reports/{item_id}/dev-report.md",
            "verify": f"agent/reports/{item_id}/verify-report.md",
            "review": f"agent/reports/{item_id}/review-report.md",
        },
        "attempts": 0,
        "blockers": [],
        "evidence": [],
        "passes": False,
        "notes": item.get("notes", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    seed = load_json(run_dir / ARTIFACT_PATHS["agent_work_items_seed"], {"items": []})
    errors: list[str] = []
    for item in seed.get("items", []):
        errors.extend(validate_item(item))
    if not seed.get("items"):
        errors.append("agent/work_items.seed.json contains no items")

    if errors:
        update_section(
            state,
            "agent_execution",
            "blocked",
            [ARTIFACT_PATHS["agent_work_items_seed"]],
            [ARTIFACT_PATHS["agent_work_items_seed"]],
            errors,
            {"execution_mode": "supervised_agents"},
        )
        save_state(run_dir, state)
        print("AGENT_EXECUTION_STATUS: blocked")
        return 1

    final_items = {"version": "work-items-v1", "items": [final_item(item) for item in seed["items"]]}
    write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], final_items)

    for item in final_items["items"]:
        report_dir = run_dir / f"agent/reports/{item['id']}"
        write_text(report_dir / "dev-report.md", f"# Dev Report: {item['id']}\n\n## Status\n\n- pending\n")
        write_text(report_dir / "verify-report.md", f"# Verify Report: {item['id']}\n\n## Status\n\n- pending\n")
        write_text(report_dir / "review-report.md", f"# Review Report: {item['id']}\n\n## Status\n\n- pending\n")

    write_text(
        run_dir / ARTIFACT_PATHS["agent_execution"],
        f"""# 07 Agent Execution

## Mode

- execution_mode: supervised_agents
- write_parallelism: serial
- read_parallelism: allowed
- autonomous_loop: reserved

## Work Items

- Count: {len(final_items['items'])}
- Path: {ARTIFACT_PATHS['agent_work_items']}

## Reports

- Path: agent/reports/<work-item-id>/

## BLOCKER

- None
""",
    )
    write_text(run_dir / ARTIFACT_PATHS["agent_main_log"], "# Agent Main Log\n\n- initialized supervised agent execution\n")
    update_section(
        state,
        "agent_execution",
        "complete",
        [ARTIFACT_PATHS["agent_execution"], ARTIFACT_PATHS["agent_work_items"], ARTIFACT_PATHS["agent_main_log"]],
        [ARTIFACT_PATHS["agent_work_items_seed"], ARTIFACT_PATHS["agent_execution"]],
        [],
        {
            "execution_mode": "supervised_agents",
            "write_parallelism": "serial",
            "read_parallelism": "allowed",
            "autonomous_loop": "reserved",
            "current_work_item": final_items["items"][0]["id"],
            "repair_round": 0,
            "max_repair_rounds": 2,
        },
    )
    save_state(run_dir, state)
    print("AGENT_EXECUTION_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify runner syntax**

Run:

```bash
python3 -m py_compile scripts/agent_execution_runner.py
```

Expected: exits with status 0.

## Task 7: Implement Delivery Verification Runner

**Files:**
- Create: `requirement-flow-plugin/scripts/delivery_verification_runner.py`

- [ ] **Step 1: Add delivery verification runner**

Create `requirement-flow-plugin/scripts/delivery_verification_runner.py`:

```python
#!/usr/bin/env python3
"""Summarize V1 delivery verification evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, load_state, save_state, update_section, write_text


CHECKS = ["build", "test", "api", "rpc", "message", "ui", "database", "cache", "search", "log"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    work_items = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {"items": []})
    lines = ["# 09 Verification", "", "## Work Item Reports", ""]
    for item in work_items.get("items", []):
        lines.append(f"- {item['id']}: dev={item['reports']['dev']} verify={item['reports']['verify']} review={item['reports']['review']}")
    lines.extend(["", "## Verification Matrix", ""])
    for check in CHECKS:
        lines.append(f"- {check}: missing-provider")
    lines.extend(["", "## Result", "", "- Status: complete", "- Evidence type: local summary with missing-provider markers", "", "## BLOCKER", "", "- None"])
    write_text(run_dir / ARTIFACT_PATHS["verification"], "\n".join(lines))
    update_section(
        state,
        "delivery_verification",
        "complete",
        [ARTIFACT_PATHS["verification"]],
        [ARTIFACT_PATHS["agent_execution"], ARTIFACT_PATHS["verification"]],
        [],
        {"automated": [], "manual": [], "missing_provider": CHECKS},
    )
    save_state(run_dir, state)
    print("DELIVERY_VERIFICATION_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify runner syntax**

Run:

```bash
python3 -m py_compile scripts/delivery_verification_runner.py
```

Expected: exits with status 0.

## Task 8: Implement Evolution Runner

**Files:**
- Create: `requirement-flow-plugin/scripts/evolution_runner.py`

- [ ] **Step 1: Add evolution runner**

Create `requirement-flow-plugin/scripts/evolution_runner.py`:

```python
#!/usr/bin/env python3
"""Archive a run and generate safe evolution proposals."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_state, save_state, update_section, write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = ensure_run_dir(Path(args.run_dir))
    state = load_state(run_dir)
    lessons = """# Lessons Learned

## Local Lessons

- Preserve source capability trace in workflow intelligence artifacts.
- Keep evolution proposals separate from automatic memory or skill writes.
"""
    evolution = """# Evolution Report

## Proposals

- Review whether repeated missing-provider verification entries should become configured providers.
- Review whether scenario/profile rules need project-specific additions.

## Safety

- No skill, template, memory, or global configuration changes were applied automatically.
"""
    archive = """# 10 Archive

## Archive Readiness

- Status: complete

## Spec Delta Application

- V1 records archive evidence only.

## Lessons

- Path: agent/lessons-learned.md

## Evolution Proposal

- Path: agent/evolution-report.md

## Result

- Status: complete

## BLOCKER

- None
"""
    write_text(run_dir / ARTIFACT_PATHS["agent_lessons"], lessons)
    write_text(run_dir / ARTIFACT_PATHS["agent_evolution"], evolution)
    write_text(run_dir / ARTIFACT_PATHS["archive"], archive)
    update_section(
        state,
        "archive",
        "complete",
        [ARTIFACT_PATHS["archive"], ARTIFACT_PATHS["agent_lessons"], ARTIFACT_PATHS["agent_evolution"]],
        [ARTIFACT_PATHS["verification"], ARTIFACT_PATHS["archive"]],
        [],
    )
    save_state(run_dir, state)
    print("ARCHIVE_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify runner syntax**

Run:

```bash
python3 -m py_compile scripts/evolution_runner.py
```

Expected: exits with status 0.

## Task 9: Update Templates And State Example

**Files:**
- Create: `requirement-flow-plugin/templates/run-artifacts/03_workflow_intelligence.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/04_context_discovery.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/05_tech_plan.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/06_impl_plan.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/07_agent_execution.template.md`
- Create: `requirement-flow-plugin/templates/run-artifacts/10_archive.template.md`
- Modify: `requirement-flow-plugin/templates/run-state.example.json`

- [ ] **Step 1: Add new stage templates**

Create each file with these exact headings:

```markdown
# 03 Workflow Intelligence

## Scenario

## Guideline Profile

## Capability Trace

## Work Item Seed

## BLOCKER

- None
```

```markdown
# 04 Context Discovery

## Project Context

## Java Code Graph

## Semantic Index

## Impact Analysis

## Context Packs

## BLOCKER

- None
```

```markdown
# 05 Tech Plan

## Architecture

## Affected Modules

## Data Flow

## Risks

## Verification Strategy

## BLOCKER

- None
```

```markdown
# 06 Impl Plan

## Work Item Source

## Authorized Scope

## Module Order

## Acceptance Criteria

## BLOCKER

- None
```

```markdown
# 07 Agent Execution

## Mode

## Work Items

## Handoffs

## Reports

## Repair Loop

## BLOCKER

- None
```

```markdown
# 10 Archive

## Archive Readiness

## Spec Delta Application

## Lessons

## Evolution Proposal

## Result

- Status: not_started

## BLOCKER

- None
```

- [ ] **Step 2: Update state artifact paths**

In `templates/run-state.example.json`, update `artifact_paths` to use the 10-stage chain:

```json
{
  "prd_summary": "01_prd_summary.md",
  "spec_delta": "02_spec_delta.md",
  "workflow_intelligence": "03_workflow_intelligence.md",
  "context_discovery": "04_context_discovery.md",
  "tech_plan": "05_tech_plan.md",
  "impl_plan": "06_impl_plan.md",
  "agent_execution": "07_agent_execution.md",
  "code_review": "08_code_review.md",
  "verification": "09_verification.md",
  "archive": "10_archive.md"
}
```

Keep existing compatibility keys only if the plugin self-check or docs still reference them.

- [ ] **Step 3: Add runtime state sections**

In `templates/run-state.example.json`, add these top-level sections if missing:

```json
{
  "spec_governance": {
    "status": "not_started",
    "artifact_paths": [],
    "blockers": [],
    "last_updated_at": "",
    "evidence_refs": []
  },
  "delivery_verification": {
    "status": "not_started",
    "artifact_paths": [],
    "blockers": [],
    "last_updated_at": "",
    "evidence_refs": []
  },
  "archive": {
    "status": "not_started",
    "artifact_paths": [],
    "blockers": [],
    "last_updated_at": "",
    "evidence_refs": []
  }
}
```

Also update `agent_execution.mode` to `supervised_agents`, and keep `max_retries` at `3` because `plugin_self_check.py` enforces it.

## Task 10: Update Skills And Docs

**Files:**
- Modify: `requirement-flow-plugin/skills/main-flow/SKILL.md`
- Modify: `requirement-flow-plugin/docs/main-flow.md`
- Modify: `requirement-flow-plugin/docs/workflow-intelligence.md`
- Modify: `requirement-flow-plugin/README.md`

- [ ] **Step 1: Update main-flow skill stage list**

In `skills/main-flow/SKILL.md`, update the Java backend stage list to this order:

```text
1. PRD summary -> 01_prd_summary.md
2. Spec governance -> 02_spec_delta.md
3. Workflow intelligence -> 03_workflow_intelligence.md and agent/* intelligence artifacts
4. Context discovery -> 04_context_discovery.md and graph/rag/context-pack artifacts
5. Technical plan -> 05_tech_plan.md
6. Implementation plan -> 06_impl_plan.md and agent/work_items.seed.json
7. Agent execution -> 07_agent_execution.md and agent/work_items.json
8. Code review -> 08_code_review.md
9. Delivery verification -> 09_verification.md
10. Archive and evolution -> 10_archive.md
```

- [ ] **Step 2: Add runner boundary guidance**

In `skills/main-flow/SKILL.md`, add these rules under the mandatory rules:

```markdown
- Keep `main-flow` as the user-facing orchestrator; do not embed runner implementation details in this skill.
- Use `workflow_intelligence_runner.py` for initial work item seeding and `agent_execution_runner.py` for final work item validation.
- Treat `autonomous_loop` as reserved. V1 uses `supervised_agents` or a manual contract fallback.
- Never auto-apply memory, skill, template, or global configuration changes from evolution proposals.
```

- [ ] **Step 3: Update docs**

Update `docs/main-flow.md`, `docs/workflow-intelligence.md`, and `README.md` to mention:

```text
Unified Requirement Flow Runtime V1 uses a 10-stage artifact chain.
PCE-style workflow intelligence writes seed work items.
Agent execution validates final work items and uses supervised_agents mode.
gstack/gbrain-style learning remains proposal-only in V1.
```

## Task 11: Run Full Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run syntax checks**

Run from `/Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin`:

```bash
python3 -m py_compile scripts/runtime_support.py scripts/spec_governance_runner.py scripts/workflow_intelligence_runner.py scripts/agent_execution_runner.py scripts/delivery_verification_runner.py scripts/evolution_runner.py scripts/java_context_engine.py scripts/unified_runtime_regression.py
```

Expected: exits with status 0.

- [ ] **Step 2: Run Java context regression**

Run:

```bash
python3 scripts/java_context_engine_regression.py
```

Expected: exits with status 0 and reports the Java context regression passed.

- [ ] **Step 3: Run unified runtime regression**

Run:

```bash
python3 scripts/unified_runtime_regression.py
```

Expected: exits with status 0 and prints `unified runtime regression passed`.

- [ ] **Step 4: Run plugin self-check**

Run from `/Users/yuanjulong/Documents/ai_flow`:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Expected: top-level `status` is `success`.

- [ ] **Step 5: Run red-flag scan**

Run from `/Users/yuanjulong/Documents/ai_flow`:

```bash
rg -n "T[B]D|T[O]DO|F[I]XME|待[定]|未[定]" requirement-flow-plugin/scripts requirement-flow-plugin/templates requirement-flow-plugin/skills/main-flow requirement-flow-plugin/docs requirement-flow-plugin/README.md
```

Expected: no matches introduced by this implementation.

## Task 12: Sync Installed Copies After Source Verification

**Files:**
- Installed plugin copies under Codex, CodeFlicker, and Claude local plugin roots.

- [ ] **Step 1: Validate install roots**

Run from `/Users/yuanjulong/Documents/ai_flow`:

```bash
test -f /Users/yuanjulong/.codex/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/.codex-plugin/plugin.json
test -f /Users/yuanjulong/.codex/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/.codex-plugin/plugin.json
test -f /Users/yuanjulong/.codeflicker/plugins/installed/requirement-flow-plugin/.codex-plugin/plugin.json
test -f /Users/yuanjulong/.claude/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/.claude-plugin/plugin.json
test -f /Users/yuanjulong/.claude/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/.claude-plugin/plugin.json
```

Expected: every command exits with status 0. If any root is missing, stop and ask before syncing.

- [ ] **Step 2: Sync source to installed copies**

Run from `/Users/yuanjulong/Documents/ai_flow` only after Task 11 passes:

```bash
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.codex/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.codex/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.codeflicker/plugins/installed/requirement-flow-plugin/
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.claude/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.claude/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/
```

Expected: each command exits with status 0.

- [ ] **Step 3: Verify installed copies**

Run from `/Users/yuanjulong/Documents/ai_flow`:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin --install-root /Users/yuanjulong/.codex/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin --install-root /Users/yuanjulong/.codex/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0 --install-root /Users/yuanjulong/.codeflicker/plugins/installed/requirement-flow-plugin --install-root /Users/yuanjulong/.claude/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin --install-root /Users/yuanjulong/.claude/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0
```

Expected: top-level `status` is `success` for source and all install roots.

## Task 13: Completion Notes

**Files:**
- No code changes in this task.

- [ ] **Step 1: Record git limitation**

Run from `/Users/yuanjulong/Documents/ai_flow`:

```bash
git status --short
```

Expected in the current workspace: `fatal: not a git repository (or any of the parent directories): .git`.

- [ ] **Step 2: Report completion**

Report:

```text
Implemented Unified Requirement Flow Runtime V1 plan.
Verified syntax, Java context regression, unified runtime regression, plugin self-check, red-flag scan, and installed-copy self-check.
No git commit was created because /Users/yuanjulong/Documents/ai_flow is not a git repository.
```
