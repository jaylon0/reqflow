#!/usr/bin/env python3
"""Regression tests for agent_execution_runner V2 functions."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Ensure the scripts directory is on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, write_json, write_text
from agent_execution_runner import (
    create_repair_round,
    final_item,
    init_work_item_execution,
    update_item_status,
    validate_item,
    write_dispatch_log,
    write_report,
)


def _make_run_dir(tmp: str) -> Path:
    """Create a minimal run_dir with work_items.json seeded."""
    run_dir = ensure_run_dir(Path(tmp))
    work_items = {
        "version": "work-items-v1",
        "items": [
            {
                "id": "wi-001",
                "title": "Test item",
                "scenario": "test",
                "status": "pending",
                "priority": 1,
                "story_size": "one supervised agent iteration",
                "acceptance_criteria": ["must pass"],
                "attempts": 0,
            }
        ],
    }
    write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], work_items)
    write_text(run_dir / ARTIFACT_PATHS["agent_main_log"], "# Agent Main Log\n")
    return run_dir


def _sample_item() -> dict:
    return {
        "id": "wi-001",
        "title": "Test item",
        "scenario": "test-scenario",
        "story_size": "one supervised agent iteration",
        "acceptance_criteria": ["must compile", "must pass tests"],
        "priority": 1,
        "notes": "sample note",
    }


def test_validate_item_valid() -> None:
    errors = validate_item(_sample_item())
    assert errors == [], f"expected no errors, got {errors}"


def test_validate_item_missing_id() -> None:
    item = _sample_item()
    item["id"] = ""
    errors = validate_item(item)
    assert any("missing id" in e for e in errors), f"expected 'missing id' error, got {errors}"


def test_final_item_has_execution_record() -> None:
    result = final_item(_sample_item())
    assert "execution_record" in result, "execution_record key missing"
    er = result["execution_record"]
    assert er["dev_agent_id"] == ""
    assert er["verify_agent_id"] == ""
    assert er["review_agent_id"] == ""
    assert er["repair_rounds"] == 0
    assert "dev" in er["reports"]
    assert "verify" in er["reports"]
    assert "review" in er["reports"]
    assert er["reports"]["dev"] == "agent/reports/wi-001/dev.json"


def test_write_dispatch_log() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        write_dispatch_log(run_dir, "dispatch", "agent-dev-1", "started coding")
        log_text = (run_dir / ARTIFACT_PATHS["agent_main_log"]).read_text()
        assert "dispatch" in log_text
        assert "agent-dev-1" in log_text
        assert "started coding" in log_text
        # Second call should append, not overwrite.
        write_dispatch_log(run_dir, "complete", "agent-dev-1", "done")
        log_text2 = (run_dir / ARTIFACT_PATHS["agent_main_log"]).read_text()
        assert log_text2.count("dispatch") == 1
        assert log_text2.count("complete") == 1


def test_update_item_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        update_item_status(run_dir, "wi-001", "in_progress")
        data = json.loads((run_dir / ARTIFACT_PATHS["agent_work_items"]).read_text())
        assert data["items"][0]["status"] == "in_progress"


def test_update_item_status_with_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        report = {"dev_agent_id": "agent-dev-1"}
        update_item_status(run_dir, "wi-001", "in_progress", report)
        data = json.loads((run_dir / ARTIFACT_PATHS["agent_work_items"]).read_text())
        item = data["items"][0]
        assert item["status"] == "in_progress"
        assert item["execution_record"]["dev_agent_id"] == "agent-dev-1"


def test_write_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        result = {"status": "pass", "details": "all green"}
        write_report(run_dir, "wi-001", "dev", result)
        report_path = run_dir / "agent/reports/wi-001/dev.json"
        assert report_path.exists(), f"report not found at {report_path}"
        data = json.loads(report_path.read_text())
        assert data["status"] == "pass"
        assert data["details"] == "all green"


def test_create_repair_round() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        findings = ["compile error in Foo.java"]
        create_repair_round(run_dir, "wi-001", findings, 1)
        # Check work_items.json was updated.
        data = json.loads((run_dir / ARTIFACT_PATHS["agent_work_items"]).read_text())
        item = data["items"][0]
        assert item["attempts"] == 1
        assert item["execution_record"]["repair_rounds"] == 1
        # Check repair report was written.
        report_path = run_dir / "agent/reports/wi-001/repair-1.json"
        assert report_path.exists(), f"repair report not found at {report_path}"
        report_data = json.loads(report_path.read_text())
        assert report_data["findings"] == findings
        assert report_data["round"] == 1


def test_create_repair_round_missing_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        findings = ["compile error"]
        create_repair_round(run_dir, "wi-999", findings, 1)
        # Should not crash; work_items.json should be unchanged for existing items
        data = json.loads((run_dir / ARTIFACT_PATHS["agent_work_items"]).read_text())
        item = data["items"][0]
        assert item["attempts"] == 0, "Existing item should be unchanged"
        # execution_record may not exist in minimal items, so use get
        er = item.get("execution_record", {})
        assert er.get("repair_rounds", 0) == 0, "Existing item should be unchanged"


def test_init_work_item_execution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = _make_run_dir(tmp)
        init_work_item_execution(run_dir, "wi-001")
        # Status should be in_progress.
        data = json.loads((run_dir / ARTIFACT_PATHS["agent_work_items"]).read_text())
        assert data["items"][0]["status"] == "in_progress"
        # Report directory should exist.
        report_dir = run_dir / "agent/reports/wi-001"
        assert report_dir.is_dir(), f"report dir not created at {report_dir}"


def test_update_item_status_missing_id() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        items = {
            "version": "work-items-v1",
            "items": [{"id": "WI-001", "status": "pending"}],
        }
        write_json(run_dir / ARTIFACT_PATHS["agent_work_items"], items)
        result = update_item_status(run_dir, "WI-999", "completed")
        assert result is False, "Should return False for missing item_id"
        data = load_json(run_dir / ARTIFACT_PATHS["agent_work_items"], {})
        assert data["items"][0]["status"] == "pending", "Original item should be unchanged"


def test_update_item_status_no_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = ensure_run_dir(Path(tmpdir))
        # Don't create work_items.json -- let load_json use default
        result = update_item_status(run_dir, "WI-001", "in_progress")
        assert result is False


ALL_TESTS = [
    test_validate_item_valid,
    test_validate_item_missing_id,
    test_final_item_has_execution_record,
    test_write_dispatch_log,
    test_update_item_status,
    test_update_item_status_with_report,
    test_write_report,
    test_create_repair_round,
    test_create_repair_round_missing_id,
    test_init_work_item_execution,
    test_update_item_status_missing_id,
    test_update_item_status_no_file,
]


def main() -> int:
    passed = 0
    failed = 0
    for test_fn in ALL_TESTS:
        try:
            test_fn()
            passed += 1
            print(f"  PASS  {test_fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  FAIL  {test_fn.__name__}: {exc}")

    total = passed + failed
    print(f"\n{passed}/{total} tests passed")
    if failed:
        print("REGRESSION FAILED")
        return 1
    print("REGRESSION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
