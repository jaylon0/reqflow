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


def write_stage_fixtures(run_dir: Path) -> None:
    """Write fixture artifacts for manual/skill stages (05, 06, 08)."""
    (run_dir / "05_tech_plan.md").write_text(
        """# 05 Tech Plan

## Technical Decisions

- Use Spring Boot REST controller pattern
- MyBatis mapper for database access
- Unit tests for service layer
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "06_impl_plan.md").write_text(
        """# 06 Implementation Plan

## Work Items

- wi-001: Controller layer changes
- wi-002: Service layer changes
- wi-003: DAO layer changes
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "08_code_review.md").write_text(
        """# 08 Code Review

## Review Summary

- All work items reviewed
- No blocking issues found
- Approved for delivery
""".strip()
        + "\n",
        encoding="utf-8",
    )


def setup_run_dir(tmp_root: Path, requirement: str | None = None) -> tuple[Path, Path]:
    """Create project root and run dir with standard fixtures."""
    project_root = tmp_root / "project"
    run_dir = tmp_root / "run"
    project_root.mkdir()
    write_sample_java_project(project_root)
    write_prd(run_dir)
    if requirement:
        (run_dir / "01_prd_summary.md").write_text(
            f"# 01 PRD Summary\n\n## Requirement\n\n{requirement}\n",
            encoding="utf-8",
        )
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        state["requirement"] = requirement
        (run_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return project_root, run_dir


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


def assert_dir_has_files(path: Path, min_count: int = 1) -> list[Path]:
    """Assert directory exists and has at least min_count files."""
    if not path.exists():
        raise AssertionError(f"missing directory: {path}")
    files = [f for f in path.iterdir() if f.is_file()]
    if len(files) < min_count:
        raise AssertionError(f"expected >= {min_count} files in {path}, got {len(files)}")
    return files


def assert_all_sections_complete(state: dict, sections: list[str]) -> None:
    """Assert all state.json sections have status 'complete'."""
    for section in sections:
        if section not in state:
            raise AssertionError(f"missing state section: {section}")
        if state[section]["status"] != "complete":
            raise AssertionError(f"{section} status is {state[section]['status']}, expected complete")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        project_root, run_dir = setup_run_dir(tmp_root)

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
        assert profile["name"] == "java-api-change-delivery"
        assert seeded["items"][0]["id"] == "wi-001"
        assert work_items["items"][0]["status"] == "pending"
        assert state["workflow_intelligence"]["status"] == "complete"
        assert state["agent_execution"]["mode"] == "supervised_agents"
        assert state["delivery_verification"]["status"] == "complete"
        assert state["archive"]["status"] == "complete"

        # V2: verify providers section exists with initial status
        assert "providers" in state, "state.json should have providers section"
        assert state["providers"]["status"] == "not_started"

        # V2: verify work_items.json has execution_record
        work_items = assert_json(run_dir / "agent/work_items.json")
        for item in work_items.get("items", []):
            assert "execution_record" in item, f"{item['id']} missing execution_record"
            assert item["execution_record"]["repair_rounds"] == 0

        # V2: verify max_repair_rounds is 3
        state = assert_json(run_dir / "state.json")
        assert state["agent_execution"].get("max_repair_rounds") == 3, "max_repair_rounds should be 3"

    print("unified runtime regression passed")
    return 0


def test_full_chain() -> None:
    """Full 10-stage chain: validates connectivity, artifacts, state, evidence chain."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        project_root, run_dir = setup_run_dir(tmp_root)
        write_stage_fixtures(run_dir)

        # Run automated stages
        run_cmd([sys.executable, "scripts/spec_governance_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/workflow_intelligence_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd(
            [
                sys.executable, "scripts/java_context_engine.py", "analyze",
                "--project-root", str(project_root), "--run-dir", str(run_dir),
                "--requirement", "新增订单列表筛选并同步 list count 查询", "--top-k", "5",
            ],
            PLUGIN_ROOT,
        )
        run_cmd([sys.executable, "scripts/agent_execution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/delivery_verification_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/evolution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Assert all 10 markdown artifacts exist with headings
        all_markdown = [
            "01_prd_summary.md", "02_spec_delta.md", "03_workflow_intelligence.md",
            "04_context_discovery.md", "05_tech_plan.md", "06_impl_plan.md",
            "07_agent_execution.md", "08_code_review.md", "09_verification.md", "10_archive.md",
        ]
        for rel in all_markdown:
            assert_text(run_dir / rel, ["#"])

        # Gap #6: context-pack integration
        assert (run_dir / "agent/context-packs/java-context.md").exists()

        # Gap #7: compliance/evolution artifacts
        compliance = assert_json(run_dir / "agent/compliance-report.json")
        assert "quality_grade" in compliance
        evolution = assert_json(run_dir / "agent/evolution-report.json")
        assert "proposals" in evolution

        # Agent artifacts
        scenario = assert_json(run_dir / "agent/scenario.json")
        assert "id" in scenario
        profile = assert_json(run_dir / "agent/profile.json")
        assert "name" in profile
        seeded = assert_json(run_dir / "agent/work_items.seed.json")
        assert len(seeded["items"]) >= 1

        # Checklists exist for each work item
        for item in seeded["items"]:
            checklist_path = run_dir / f"agent/checklists/{item['id']}.json"
            assert checklist_path.exists(), f"missing checklist for {item['id']}"

        # Work items with execution_record
        work_items = assert_json(run_dir / "agent/work_items.json")
        for item in work_items["items"]:
            assert "execution_record" in item
            assert item["execution_record"]["repair_rounds"] == 0

        # Gap #8: state.json evidence chain
        state = assert_json(run_dir / "state.json")
        for section in ["spec_governance", "workflow_intelligence", "context_engine",
                        "agent_execution", "delivery_verification", "archive"]:
            assert section in state, f"missing state section: {section}"
            if state[section].get("artifact_paths"):
                for art_path in state[section]["artifact_paths"]:
                    assert (run_dir / art_path).exists(), f"evidence ref not found: {art_path}"

    print("test_full_chain passed")


def test_provider_dispatch_integration() -> None:
    """Provider dispatch: configured adapter used instead of manual mode fallback."""
    from runtime_support import load_providers, dispatch_provider, write_dispatch_result

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        run_dir = tmp_root / "run"
        run_dir.mkdir()

        # Write providers.yaml with echo adapter
        echo_adapter = str(Path(__file__).resolve().parent / "test_adapter_echo.py")
        providers_yaml = run_dir / "providers.yaml"
        providers_yaml.write_text(
            f"""providers:
  deploy:
    adapter: "{echo_adapter}"
    params:
      target: "staging"
    enabled: true
""",
            encoding="utf-8",
        )

        # Load and verify registry
        registry = load_providers(providers_yaml)
        assert "deploy" in registry, "deploy not in registry"
        assert registry["deploy"]["adapter"] == echo_adapter

        # Dispatch a provider action
        result = dispatch_provider(run_dir, "deploy", "deploy", {"target": "staging"}, registry)
        assert result["status"] == "success", f"expected success, got {result['status']}"
        assert len(result["artifacts"]) >= 1

        # Write dispatch result for audit
        (run_dir / "agent").mkdir()
        write_dispatch_result(run_dir, "deploy", "deploy", result)
        results_dir = run_dir / "agent" / "provider-results"
        assert results_dir.exists(), "provider-results dir not created"
        files = list(results_dir.glob("deploy-deploy-*.json"))
        assert len(files) == 1, f"expected 1 result file, got {len(files)}"

        # Verify result file content
        result_data = assert_json(files[0])
        assert result_data["capability"] == "deploy"
        assert result_data["action"] == "deploy"
        assert result_data["result"]["status"] == "success"

    print("test_provider_dispatch_integration passed")


def test_repair_round_loop() -> None:
    """Repair round: simulate failed item -> repair round -> verify state."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        project_root, run_dir = setup_run_dir(tmp_root)

        # Run chain through agent execution
        run_cmd([sys.executable, "scripts/spec_governance_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/workflow_intelligence_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/agent_execution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Load work items and verify initial state
        work_items = assert_json(run_dir / "agent/work_items.json")
        assert len(work_items["items"]) >= 1
        item = work_items["items"][0]
        assert item["status"] == "pending"
        assert item["execution_record"]["repair_rounds"] == 0

        # Import repair functions
        sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
        from agent_execution_runner import create_repair_round, update_item_status

        # Mark item as failed
        update_item_status(run_dir, item["id"], "failed")
        work_items = assert_json(run_dir / "agent/work_items.json")
        failed_item = next(i for i in work_items["items"] if i["id"] == item["id"])
        assert failed_item["status"] == "failed"

        # Create repair round
        create_repair_round(
            run_dir, item["id"],
            findings=["Build failed: missing dependency"],
            round_num=1,
        )

        # Verify repair round was recorded
        work_items = assert_json(run_dir / "agent/work_items.json")
        updated_item = next(i for i in work_items["items"] if i["id"] == item["id"])
        assert updated_item["execution_record"]["repair_rounds"] == 1

        # Verify repair report exists (create_repair_round writes repair-{round_num}.json)
        report_path = run_dir / f"agent/reports/{item['id']}/repair-1.json"
        assert report_path.exists(), f"repair report not found: {report_path}"
        report = assert_json(report_path)
        assert report["round"] == 1
        assert "Build failed" in report["findings"][0]

    print("test_repair_round_loop passed")


def test_multi_work_item() -> None:
    """Multi-layer scenario: DAO keywords trigger dao+mapper layers."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        _, run_dir = setup_run_dir(
            tmp_root,
            requirement="新增订单 DAO 层 mapper 查询，优化 SQL table 索引",
        )

        run_cmd([sys.executable, "scripts/workflow_intelligence_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Verify multi-layer scenario detected
        scenario = assert_json(run_dir / "agent/scenario.json")
        assert scenario["id"] == "java-dao-change", f"expected java-dao-change, got {scenario['id']}"
        assert len(scenario["layers"]) >= 2, f"expected >= 2 layers, got {len(scenario['layers'])}"

        # Verify multiple work items
        seeded = assert_json(run_dir / "agent/work_items.seed.json")
        assert len(seeded["items"]) >= 2, f"expected >= 2 items, got {len(seeded['items'])}"

        # Each item has distinct id and layer
        ids = [i["id"] for i in seeded["items"]]
        layers = [i["layer"] for i in seeded["items"]]
        assert len(ids) == len(set(ids)), "work item ids should be unique"
        assert len(layers) == len(set(layers)), "layers should be unique"

        # Checklists exist for each work item
        for item in seeded["items"]:
            checklist_path = run_dir / f"agent/checklists/{item['id']}.json"
            assert checklist_path.exists(), f"missing checklist for {item['id']}"
            checklist = assert_json(checklist_path)
            assert len(checklist["checks"]) >= 1

    print("test_multi_work_item passed")


def test_recovery_resume() -> None:
    """Incremental resume: run stages 02-03, then resume from stage 04."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        project_root, run_dir = setup_run_dir(tmp_root)
        write_stage_fixtures(run_dir)

        # Run stages 02-03 only
        run_cmd([sys.executable, "scripts/spec_governance_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/workflow_intelligence_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Verify partial completion
        state = assert_json(run_dir / "state.json")
        assert state["spec_governance"]["status"] == "complete"
        assert state["workflow_intelligence"]["status"] == "complete"

        # Resume: run stages 04-10
        run_cmd(
            [
                sys.executable, "scripts/java_context_engine.py", "analyze",
                "--project-root", str(project_root), "--run-dir", str(run_dir),
                "--requirement", "新增订单列表筛选并同步 list count 查询", "--top-k", "5",
            ],
            PLUGIN_ROOT,
        )
        run_cmd([sys.executable, "scripts/agent_execution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/delivery_verification_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/evolution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Verify runner-managed stages complete (context_engine only writes artifacts)
        state = assert_json(run_dir / "state.json")
        assert_all_sections_complete(state, [
            "spec_governance", "workflow_intelligence",
            "agent_execution", "delivery_verification", "archive",
        ])
        # context_engine: java_context_engine.py only writes artifacts (e.g. 04_context_discovery.md)
        # but does not update state.json status — this is intentional, so we only check key existence
        assert "context_engine" in state

        # Verify no duplicate artifacts (each exists exactly once)
        for rel in ["02_spec_delta.md", "03_workflow_intelligence.md", "04_context_discovery.md",
                     "07_agent_execution.md", "09_verification.md", "10_archive.md"]:
            assert (run_dir / rel).exists()

        # Verify work items are valid
        work_items = assert_json(run_dir / "agent/work_items.json")
        assert len(work_items["items"]) >= 1

    print("test_recovery_resume passed")


def test_adapter_factory() -> None:
    """Adapter factory: generate adapter and verify it works."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "project"
        project_dir.mkdir()

        # Run adapter_factory in dry-run mode (plan only)
        result = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "scripts/adapter_factory.py"),
             "--project-dir", str(project_dir), "--capability", "deploy"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"dry-run failed: {result.stderr}"
        plan = json.loads(result.stdout)
        assert plan["status"] == "planned"
        assert plan["capability"] == "deploy"

        # Run with --write to actually generate
        result = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "scripts/adapter_factory.py"),
             "--project-dir", str(project_dir), "--capability", "deploy", "--write"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"write failed: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["status"] == "generated", f"unexpected status: {output['status']}"

        # Verify generated adapter exists at expected path
        adapter_path = Path(output["adapter_file"])
        assert adapter_path.exists(), f"adapter file not found at {adapter_path}"

        # Verify manifest exists
        manifest_path = Path(output["manifest_file"])
        assert manifest_path.exists(), "adapter-manifest.yaml not found"

        # Verify generated adapter is executable (returns valid JSON with allowed status)
        test_input = json.dumps({
            "action": "check",
            "project_dir": str(project_dir),
            "environment": "dry-run",
            "change": {"branch": "", "commit": "", "files": []},
            "context": {"dry_run": True, "capability": "deploy"},
        })
        result = subprocess.run(
            [sys.executable, str(adapter_path)],
            input=test_input, capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        adapter_output = json.loads(result.stdout)
        assert adapter_output["status"] in ("success", "failed", "blocked", "skipped")

    print("test_adapter_factory passed")


def test_agent_execution_main() -> None:
    """Agent execution main(): validation-to-contract flow with seed file."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        project_root, run_dir = setup_run_dir(tmp_root)

        # Run prerequisite stages to get valid seed
        run_cmd([sys.executable, "scripts/spec_governance_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)
        run_cmd([sys.executable, "scripts/workflow_intelligence_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Verify seed exists
        seeded = assert_json(run_dir / "agent/work_items.seed.json")
        assert len(seeded["items"]) >= 1

        # Run agent execution main()
        run_cmd([sys.executable, "scripts/agent_execution_runner.py", "--run-dir", str(run_dir)], PLUGIN_ROOT)

        # Verify outputs
        work_items = assert_json(run_dir / "agent/work_items.json")
        assert len(work_items["items"]) >= 1
        for item in work_items["items"]:
            assert item["status"] == "pending"
            assert "execution_record" in item
            assert "authorized_scope" in item
            assert "context_pack" in item
            assert "checklist" in item

        # Verify execution markdown
        assert_text(run_dir / "07_agent_execution.md", ["#"])

        # Verify main log exists
        assert (run_dir / "agent/main-log.md").exists()

        # Verify report directories created
        for item in work_items["items"]:
            report_dir = run_dir / f"agent/reports/{item['id']}"
            assert report_dir.exists(), f"missing report dir for {item['id']}"

        # Verify state
        state = assert_json(run_dir / "state.json")
        assert state["agent_execution"]["status"] == "complete"
        assert state["agent_execution"]["mode"] == "supervised_agents"
        assert state["agent_execution"]["max_repair_rounds"] == 3

    print("test_agent_execution_main passed")


ALL_TESTS = [
    test_full_chain,
    test_provider_dispatch_integration,
    test_repair_round_loop,
    test_multi_work_item,
    test_recovery_resume,
    test_adapter_factory,
    test_agent_execution_main,
]


def run_all_tests() -> int:
    passed = 0
    failed = 0
    for test in ALL_TESTS:
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-only", action="store_true", help="Run only new E2E tests")
    args = parser.parse_args()
    if args.test_only:
        raise SystemExit(run_all_tests())
    else:
        raise SystemExit(main())
