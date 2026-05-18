#!/usr/bin/env python3
"""Regression test for V2 workflow_intelligence_runner functions."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workflow_intelligence_runner import (
    assess_compliance,
    detect_scenario,
    profile_for_scenario,
    SCENARIO_RULES,
    PROFILE_TEMPLATES,
    decompose_items,
    _criteria_for_layer,
    seed_work_items,
    generate_checklist,
    _layer_checklist_items,
    _deduplicate_checks,
    suggest_evolution,
)


def test_detect_api_scenario():
    result = detect_scenario("添加用户列表查询接口")
    assert result["id"] == "java-api-change", f"Expected java-api-change, got {result['id']}"
    assert result["confidence"] > 0.7
    assert "controller" in result["layers"]


def test_detect_dao_scenario():
    result = detect_scenario("修改数据库表字段映射")
    assert result["id"] == "java-dao-change"
    assert "dao" in result["layers"]
    assert "mapper" in result["layers"]


def test_detect_message_scenario():
    result = detect_scenario("添加 kafka 消息消费处理")
    assert result["id"] == "java-message-change"
    assert "message" in result["layers"]


def test_detect_task_scenario():
    result = detect_scenario("新增定时批处理任务")
    assert result["id"] == "java-task-change"
    assert "task" in result["layers"]


def test_detect_cache_scenario():
    result = detect_scenario("优化 redis 缓存过期策略")
    assert result["id"] == "java-cache-change"
    assert "cache" in result["layers"]


def test_detect_rpc_scenario():
    result = detect_scenario("调用远程 dubbo 服务")
    assert result["id"] == "java-rpc-change"
    assert "rpc" in result["layers"] or "client" in result["layers"]


def test_detect_test_scenario():
    result = detect_scenario("补充单测和 mock 测试")
    assert result["id"] == "java-test-change"
    assert "test" in result["layers"]


def test_detect_service_scenario():
    result = detect_scenario("修改业务处理逻辑")
    assert result["id"] == "java-service-change"
    assert "service" in result["layers"]


def test_detect_default_fallback():
    result = detect_scenario("做一些优化")
    assert result["id"] == "java-backend-change"
    assert result["confidence"] == 0.62


def test_detect_confidence_scoring():
    few = detect_scenario("修改 api 接口")
    many = detect_scenario("添加 controller api 接口 rest endpoint request response 查询")
    assert many["confidence"] >= few["confidence"]


def test_profile_for_api_scenario():
    profile = profile_for_scenario("java-api-change")
    assert profile["scenario"] == "java-api-change"
    assert len(profile["ruleset"]) == 5
    assert "controller" in profile["name"] or "api" in profile["name"]


def test_profile_for_dao_scenario():
    profile = profile_for_scenario("java-dao-change")
    assert profile["scenario"] == "java-dao-change"
    assert any("SQL" in r for r in profile["ruleset"])


def test_profile_severity_strict():
    profile = profile_for_scenario("java-api-change", "strict")
    assert profile["severity"] == "strict"
    assert "mandatory" in profile["severity_guidance"].lower()


def test_profile_unknown_scenario():
    profile = profile_for_scenario("unknown-scenario")
    assert profile["scenario"] == "unknown-scenario"
    assert len(profile["ruleset"]) == 5


def test_detect_empty_input():
    result = detect_scenario("")
    assert result["id"] == "java-backend-change"
    assert result["confidence"] == 0.62


def test_profile_unknown_severity():
    profile = profile_for_scenario("java-api-change", "extreme")
    assert profile["severity"] == "extreme"
    assert "mandatory" in profile["severity_guidance"].lower()  # falls back to balanced


def test_scenario_rules_count():
    assert len(SCENARIO_RULES) == 8


def test_profile_templates_count():
    assert len(PROFILE_TEMPLATES) == 8


def test_decompose_api_scenario():
    scenario = {"id": "java-api-change", "layers": ["controller"]}
    items = decompose_items("添加用户查询接口", scenario)
    assert len(items) == 1
    assert items[0]["layer"] == "controller"
    assert items[0]["id"] == "wi-001"
    assert any("API" in ac or "api" in ac.lower() for ac in items[0]["acceptance_criteria"])


def test_decompose_dao_scenario():
    scenario = {"id": "java-dao-change", "layers": ["dao", "mapper"]}
    items = decompose_items("修改数据库映射", scenario)
    assert len(items) == 2
    assert items[0]["layer"] == "dao"
    assert items[1]["layer"] == "mapper"


def test_decompose_service_scenario():
    scenario = {"id": "java-service-change", "layers": ["service"]}
    items = decompose_items("修改业务逻辑", scenario)
    assert len(items) == 1
    assert items[0]["layer"] == "service"


def test_criteria_for_controller():
    criteria = _criteria_for_layer("controller", {})
    assert any("API" in c for c in criteria)
    assert any("validation" in c.lower() for c in criteria)


def test_criteria_for_dao():
    criteria = _criteria_for_layer("dao", {})
    assert any("SQL" in c for c in criteria)


def test_seed_work_items_version():
    scenario = {"id": "java-api-change", "layers": ["controller"]}
    result = seed_work_items("test", scenario)
    assert result["version"] == "work-items-seed-v2"
    assert len(result["items"]) >= 1


def test_seed_work_items_multi_layer():
    scenario = {"id": "java-dao-change", "layers": ["dao", "mapper"]}
    result = seed_work_items("修改数据库映射", scenario)
    assert result["version"] == "work-items-seed-v2"
    assert len(result["items"]) == 2
    assert result["items"][0]["layer"] == "dao"
    assert result["items"][1]["layer"] == "mapper"


def test_checklist_for_controller():
    item = {"id": "wi-001", "layer": "controller", "scenario": "java-api-change",
            "acceptance_criteria": ["API works"]}
    profile = {"severity": "balanced", "ruleset": ["Rule 1"]}
    result = generate_checklist(item, profile)
    assert result["summary"]["total"] > 3
    assert result["summary"]["required"] >= 3
    assert result["layer"] == "controller"


def test_checklist_for_dao():
    item = {"id": "wi-002", "layer": "dao", "scenario": "java-dao-change",
            "acceptance_criteria": ["SQL correct"]}
    profile = {"severity": "balanced", "ruleset": ["Rule 1"]}
    result = generate_checklist(item, profile)
    assert any(c["id"] == "layer-sql-performance" for c in result["checks"])


def test_checklist_strict_severity():
    item = {"id": "wi-003", "layer": "service", "scenario": "java-service-change",
            "acceptance_criteria": ["Works"]}
    profile = {"severity": "strict", "ruleset": ["Strict rule"]}
    result = generate_checklist(item, profile)
    profile_checks = [c for c in result["checks"] if c["source"] == "profile"]
    assert all(c["required"] for c in profile_checks)


def test_checklist_dedup():
    checks = [
        {"id": "a", "required": False, "text": "Same text", "source": "base"},
        {"id": "b", "required": True, "text": "Same text", "source": "layer"},
    ]
    result = _deduplicate_checks(checks)
    assert len(result) == 1
    assert result[0]["required"] is True


def test_layer_checklist_items_unknown():
    result = _layer_checklist_items("unknown-layer")
    assert result == []


def test_checklist_summary_counts():
    item = {"id": "wi-004", "layer": "service", "scenario": "java-service-change",
            "acceptance_criteria": ["AC1", "AC2"]}
    profile = {"severity": "balanced", "ruleset": ["R1", "R2"]}
    result = generate_checklist(item, profile)
    assert result["summary"]["total"] == result["summary"]["required"] + result["summary"]["optional"]


def test_compliance_all_pass():
    items = [{"id": "wi-001", "passes": True}]
    checklists = {"wi-001": {"checks": [{"required": True, "completed": True}]}}
    profile = {"severity": "balanced"}
    result = assess_compliance(items, checklists, profile)
    assert result["status"] == "PASS"
    assert result["quality_grade"] == "A"
    assert result["risk_level"] == "low"


def test_compliance_some_fail():
    items = [{"id": "wi-001", "passes": True}, {"id": "wi-002", "passes": False}]
    checklists = {}
    profile = {"severity": "balanced"}
    result = assess_compliance(items, checklists, profile)
    assert result["status"] in ["CONDITIONAL PASS", "FAIL"]
    assert result["work_items"]["failed"] == 1


def test_compliance_strict_with_fail():
    items = [{"id": "wi-001", "passes": False}]
    checklists = {}
    profile = {"severity": "strict"}
    result = assess_compliance(items, checklists, profile)
    assert result["risk_level"] == "high"


def test_evolution_low_confidence():
    items = []
    scenario = {"id": "java-api-change", "confidence": 0.6}
    profile = {"severity": "balanced"}
    compliance = {"quality_grade": "A"}
    result = suggest_evolution(items, scenario, profile, compliance)
    assert any(p["category"] == "scenario_detection" for p in result["proposals"])


def test_evolution_with_repair_rounds():
    items = [{"id": "wi-001", "passes": True, "attempts": 2}]
    scenario = {"id": "java-api-change", "confidence": 0.9}
    profile = {"severity": "balanced"}
    compliance = {"quality_grade": "A"}
    result = suggest_evolution(items, scenario, profile, compliance)
    assert any(p["category"] == "checklist_update" for p in result["proposals"])
    assert len(result["lessons_learned"]) == 1


def test_evolution_low_grade():
    items = []
    scenario = {"id": "java-api-change", "confidence": 0.9}
    profile = {"severity": "balanced"}
    compliance = {"quality_grade": "D"}
    result = suggest_evolution(items, scenario, profile, compliance)
    assert any(p["category"] == "profile_update" for p in result["proposals"])


def test_evolution_failed_item():
    items = [{"id": "wi-001", "status": "fail"}]
    scenario = {"id": "java-api-change", "confidence": 0.9}
    profile = {"severity": "balanced"}
    compliance = {"quality_grade": "A"}
    result = suggest_evolution(items, scenario, profile, compliance)
    assert any(p["category"] == "context_pack_update" for p in result["proposals"])


ALL_TESTS = [
    test_detect_api_scenario,
    test_detect_dao_scenario,
    test_detect_message_scenario,
    test_detect_task_scenario,
    test_detect_cache_scenario,
    test_detect_rpc_scenario,
    test_detect_test_scenario,
    test_detect_service_scenario,
    test_detect_default_fallback,
    test_detect_confidence_scoring,
    test_detect_empty_input,
    test_profile_for_api_scenario,
    test_profile_for_dao_scenario,
    test_profile_severity_strict,
    test_profile_unknown_severity,
    test_profile_unknown_scenario,
    test_scenario_rules_count,
    test_profile_templates_count,
    test_decompose_api_scenario,
    test_decompose_dao_scenario,
    test_decompose_service_scenario,
    test_criteria_for_controller,
    test_criteria_for_dao,
    test_seed_work_items_version,
    test_seed_work_items_multi_layer,
    test_checklist_for_controller,
    test_checklist_for_dao,
    test_checklist_strict_severity,
    test_checklist_dedup,
    test_layer_checklist_items_unknown,
    test_checklist_summary_counts,
    test_compliance_all_pass,
    test_compliance_some_fail,
    test_compliance_strict_with_fail,
    test_evolution_low_confidence,
    test_evolution_with_repair_rounds,
    test_evolution_low_grade,
    test_evolution_failed_item,
]


def main() -> int:
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
    raise SystemExit(main())
