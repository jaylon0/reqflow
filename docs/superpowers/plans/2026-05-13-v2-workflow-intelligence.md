# V2 Workflow Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade V1 workflow intelligence from keyword matching + hardcoded profile to 8-scenario rule engine, dynamic profiles, layer-based decomposition, dynamic checklists, compliance assessment, and evolution suggestions.

**Architecture:** Runner handles deterministic work (rules, templates, I/O). Skill tells Claude how to do intelligent analysis (refine scenario, validate decomposition, assess compliance). Same Runner+Skill pattern as V2 Agent Execution.

**Tech Stack:** Python 3 (runner), Markdown (skill), JSON (artifacts)

---

## File Structure

```text
requirement-flow-plugin/
├── scripts/
│   ├── workflow_intelligence_runner.py      # MAJOR REWRITE — 8 scenarios, profiles, decomposition, checklists, compliance, evolution
│   └── workflow_intelligence_regression.py  # CREATE — regression tests
├── skills/
│   ├── workflow-intelligence/
│   │   └── SKILL.md                        # MODIFY — V2 behavior guidance
│   └── main-flow/
│       └── SKILL.md                        # MODIFY — Step 3 update
└── docs/
    └── main-flow.md                        # MODIFY — Step 3 description
```

---

### Task 1: Expand Scenario Detection and Profile Selection

**Files:**
- Modify: `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`
- Create: `requirement-flow-plugin/scripts/workflow_intelligence_regression.py`

- [ ] **Step 1: Add SCENARIO_RULES constant**

Replace the existing `detect_scenario` function and add the rules table before it:

```python
SCENARIO_RULES = [
    {
        "id": "java-api-change",
        "name": "Java API or controller change",
        "keywords": ["controller", "api", "接口", "列表", "查询", "filter", "筛选", "endpoint", "rest", "request", "response"],
        "layers": ["controller"],
        "confidence_base": 0.85,
    },
    {
        "id": "java-service-change",
        "name": "Java service logic change",
        "keywords": ["service", "业务", "逻辑", "处理", "流程", "计算", "校验", "validation", "business"],
        "layers": ["service"],
        "confidence_base": 0.80,
    },
    {
        "id": "java-dao-change",
        "name": "Java DAO or database change",
        "keywords": ["dao", "mapper", "数据库", "sql", "查询", "表", "字段", "column", "table", "query", "repository"],
        "layers": ["dao", "mapper"],
        "confidence_base": 0.85,
    },
    {
        "id": "java-message-change",
        "name": "Java message or event change",
        "keywords": ["消息", "mq", "kafka", "rabbit", "event", "message", "队列", "topic", "consumer", "producer"],
        "layers": ["message"],
        "confidence_base": 0.80,
    },
    {
        "id": "java-task-change",
        "name": "Java scheduled task or job change",
        "keywords": ["定时", "任务", "job", "task", "schedule", "cron", "batch", "批处理"],
        "layers": ["task"],
        "confidence_base": 0.80,
    },
    {
        "id": "java-cache-change",
        "name": "Java cache change",
        "keywords": ["缓存", "cache", "redis", "memcached", "过期", "失效"],
        "layers": ["cache"],
        "confidence_base": 0.75,
    },
    {
        "id": "java-rpc-change",
        "name": "Java RPC or service invocation change",
        "keywords": ["rpc", "调用", "远程", "feign", "dubbo", "grpc", "远程服务", "client"],
        "layers": ["rpc", "client"],
        "confidence_base": 0.75,
    },
    {
        "id": "java-test-change",
        "name": "Java test change",
        "keywords": ["测试", "test", "单测", "集成测试", "mock", "断言", "assert"],
        "layers": ["test"],
        "confidence_base": 0.80,
    },
]
```

- [ ] **Step 2: Rewrite detect_scenario()**

```python
def detect_scenario(requirement: str) -> dict:
    lowered = requirement.lower()
    scores = []
    for rule in SCENARIO_RULES:
        hits = sum(1 for kw in rule["keywords"] if kw in lowered)
        if hits > 0:
            score = rule["confidence_base"] * min(hits / 3, 1.0)
            scores.append((score, rule))
    scores.sort(reverse=True)
    if not scores:
        return {
            "id": "java-backend-change",
            "name": "Java backend change",
            "confidence": 0.62,
            "alternatives": ["java-service-change"],
            "layers": ["service"],
            "reason": "Requirement is backend-oriented but lacks a precise layer signal.",
        }
    top_score, top_rule = scores[0]
    alternatives = [r["id"] for _, r in scores[1:3]]
    return {
        "id": top_rule["id"],
        "name": top_rule["name"],
        "confidence": round(top_score, 2),
        "alternatives": alternatives,
        "layers": top_rule["layers"],
        "reason": f"Matched {len([kw for kw in top_rule['keywords'] if kw in lowered])} keywords for {top_rule['name']}.",
    }
```

- [ ] **Step 3: Add PROFILE_TEMPLATES and SEVERITY_ADJUSTMENTS**

```python
PROFILE_TEMPLATES = {
    "java-api-change": {
        "ruleset": [
            "Controller methods must have explicit request/response types.",
            "API endpoints need input validation and error responses.",
            "REST conventions: proper HTTP methods, status codes, URL patterns.",
            "Keep controller thin — delegate to service layer.",
            "Every API change needs integration test or HTTP verification.",
        ],
    },
    "java-service-change": {
        "ruleset": [
            "Service methods must have clear single responsibility.",
            "Business validation happens in service layer, not controller.",
            "Transaction boundaries must be explicit.",
            "Service dependencies should be constructor-injected.",
            "Every service change needs unit test coverage.",
        ],
    },
    "java-dao-change": {
        "ruleset": [
            "SQL queries must be reviewed for performance.",
            "Schema changes need migration scripts.",
            "DAO methods must handle empty results gracefully.",
            "N+1 query prevention for list operations.",
            "Database changes need rollback strategy.",
        ],
    },
    "java-message-change": {
        "ruleset": [
            "Message consumers must be idempotent.",
            "Dead letter queue handling required.",
            "Message schema changes need backward compatibility.",
            "Consumer failures must not block other messages.",
            "Message flow needs end-to-end verification.",
        ],
    },
    "java-task-change": {
        "ruleset": [
            "Scheduled tasks must handle overlapping executions.",
            "Task failures must be logged and alerted.",
            "Task parameters should be configurable.",
            "Long-running tasks need progress tracking.",
            "Task state must survive restarts.",
        ],
    },
    "java-cache-change": {
        "ruleset": [
            "Cache invalidation strategy must be explicit.",
            "Cache key naming conventions must be followed.",
            "Cache miss handling must not cause thundering herd.",
            "TTL values must be documented.",
            "Cache changes need performance verification.",
        ],
    },
    "java-rpc-change": {
        "ruleset": [
            "RPC calls must have timeout and retry configuration.",
            "Remote service degradation must be handled.",
            "RPC contracts must be versioned.",
            "Circuit breaker pattern for critical dependencies.",
            "RPC changes need integration test with mock server.",
        ],
    },
    "java-test-change": {
        "ruleset": [
            "Tests must be deterministic and isolated.",
            "Test data setup must be explicit.",
            "Mock boundaries must match production call boundaries.",
            "Test coverage for happy path and error paths.",
            "Tests must not depend on execution order.",
        ],
    },
}

SEVERITY_ADJUSTMENTS = {
    "strict": "All rules are mandatory. Fail on any violation.",
    "balanced": "Core rules are mandatory. Important rules warn. Nice-to-have rules suggest.",
    "relaxed": "Core rules are mandatory. Others are informational.",
}
```

- [ ] **Step 4: Rewrite profile_for_scenario()**

```python
def profile_for_scenario(scenario_id: str, severity: str = "balanced") -> dict:
    template = PROFILE_TEMPLATES.get(scenario_id, PROFILE_TEMPLATES["java-service-change"])
    return {
        "name": f"{scenario_id}-delivery",
        "source": "Requirement Flow V2",
        "severity": severity,
        "scenario": scenario_id,
        "ruleset": template["ruleset"],
        "severity_guidance": SEVERITY_ADJUSTMENTS.get(severity, SEVERITY_ADJUSTMENTS["balanced"]),
    }
```

- [ ] **Step 5: Create regression test file with scenario and profile tests**

Create `requirement-flow-plugin/scripts/workflow_intelligence_regression.py`:

```python
#!/usr/bin/env python3
"""Regression test for V2 workflow_intelligence_runner functions."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workflow_intelligence_runner import (
    detect_scenario,
    profile_for_scenario,
    SCENARIO_RULES,
    PROFILE_TEMPLATES,
)


def test_detect_api_scenario():
    result = detect_scenario("添加用户列表查询接口")
    assert result["id"] == "java-api-change", f"Expected java-api-change, got {result['id']}"
    assert result["confidence"] > 0.7
    assert "controller" in result["layers"]


def test_detect_dao_scenario():
    result = detect_scenario("修改数据库表字段映射")
    assert result["id"] == "java-dao-change"
    assert "dao" in result["layers"] or "mapper" in result["layers"]


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
    # More keywords = higher confidence
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
    # Falls back to java-service-change template
    assert len(profile["ruleset"]) == 5


def test_scenario_rules_count():
    assert len(SCENARIO_RULES) == 8


def test_profile_templates_count():
    assert len(PROFILE_TEMPLATES) == 8


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
    test_profile_for_api_scenario,
    test_profile_for_dao_scenario,
    test_profile_severity_strict,
    test_profile_unknown_scenario,
    test_scenario_rules_count,
    test_profile_templates_count,
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
```

- [ ] **Step 6: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/workflow_intelligence_regression.py`
Expected: All 16 tests PASS

- [ ] **Step 7: Commit**

---

### Task 2: Add Work Item Decomposition

**Files:**
- Modify: `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`

- [ ] **Step 1: Add _criteria_for_layer() function**

```python
def _criteria_for_layer(layer: str, scenario: dict) -> list[str]:
    base = [
        "Implementation stays within authorized scope.",
        "Code follows project coding standards.",
    ]
    layer_specific = {
        "controller": [
            "API endpoints have proper request/response types.",
            "Input validation is present for all parameters.",
            "Error responses follow project conventions.",
        ],
        "service": [
            "Business logic is correctly implemented.",
            "Service methods have clear single responsibility.",
            "Transaction boundaries are explicit if applicable.",
        ],
        "dao": [
            "SQL queries are correct and performant.",
            "Empty results are handled gracefully.",
            "No N+1 query issues in list operations.",
        ],
        "mapper": [
            "MyBatis/JPA mappings are correct.",
            "Result maps handle null/empty cases.",
        ],
        "message": [
            "Message consumers are idempotent.",
            "Dead letter handling is present.",
        ],
        "task": [
            "Task handles overlapping executions.",
            "Failures are logged properly.",
        ],
        "cache": [
            "Cache invalidation is correct.",
            "TTL values are appropriate.",
        ],
        "rpc": [
            "Timeout and retry are configured.",
            "Degradation handling is present.",
        ],
        "test": [
            "Tests are deterministic and isolated.",
            "Happy and error paths covered.",
        ],
        "verification": [
            "All changes compile together.",
            "Integration verified.",
        ],
    }
    return base + layer_specific.get(layer, ["Changes are correct and complete."])
```

- [ ] **Step 2: Add decompose_items() function**

```python
def decompose_items(requirement: str, scenario: dict) -> list[dict]:
    layers = scenario.get("layers", ["service"])
    items = []
    priority = 1
    for layer in layers:
        item_id = f"wi-{len(items)+1:03d}"
        items.append({
            "id": item_id,
            "title": f"Implement {layer} layer changes",
            "scenario": scenario["id"],
            "layer": layer,
            "story_size": "one supervised agent iteration",
            "description": f"Changes to the {layer} layer for: {requirement[:200]}",
            "acceptance_criteria": _criteria_for_layer(layer, scenario),
            "priority": priority,
            "passes": False,
            "notes": "",
        })
        priority += 1
    return items
```

- [ ] **Step 3: Update seed_work_items() to use decompose_items()**

Replace the existing `seed_work_items` function:

```python
def seed_work_items(requirement: str, scenario: dict) -> dict:
    items = decompose_items(requirement, scenario)
    return {
        "version": "work-items-seed-v2",
        "source": "workflow_intelligence_runner.py",
        "items": items,
    }
```

- [ ] **Step 4: Add decomposition tests to regression file**

Add to `workflow_intelligence_regression.py`:

```python
from workflow_intelligence_runner import decompose_items, _criteria_for_layer, seed_work_items


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
```

Add these tests to the `ALL_TESTS` list.

- [ ] **Step 5: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/workflow_intelligence_regression.py`
Expected: All tests PASS (22+ tests)

- [ ] **Step 6: Commit**

---

### Task 3: Add Checklist Generation

**Files:**
- Modify: `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`

- [ ] **Step 1: Add _layer_checklist_items() function**

```python
def _layer_checklist_items(layer: str) -> list[dict]:
    items = {
        "controller": [
            {"id": "layer-input-validation", "required": True,
             "text": "All API inputs are validated.", "source": "layer"},
            {"id": "layer-error-response", "required": True,
             "text": "Error responses follow project conventions.", "source": "layer"},
            {"id": "layer-http-method", "required": False,
             "text": "HTTP methods match REST conventions.", "source": "layer"},
        ],
        "service": [
            {"id": "layer-single-responsibility", "required": True,
             "text": "Service methods have single responsibility.", "source": "layer"},
            {"id": "layer-transaction", "required": False,
             "text": "Transaction boundaries are explicit.", "source": "layer"},
        ],
        "dao": [
            {"id": "layer-sql-performance", "required": True,
             "text": "SQL queries reviewed for performance.", "source": "layer"},
            {"id": "layer-empty-result", "required": True,
             "text": "Empty results handled gracefully.", "source": "layer"},
            {"id": "layer-n-plus-one", "required": False,
             "text": "No N+1 query issues.", "source": "layer"},
        ],
        "mapper": [
            {"id": "layer-mapping-correct", "required": True,
             "text": "MyBatis/JPA mappings are correct.", "source": "layer"},
            {"id": "layer-null-handling", "required": True,
             "text": "Result maps handle null/empty cases.", "source": "layer"},
        ],
        "message": [
            {"id": "layer-idempotent", "required": True,
             "text": "Consumer is idempotent.", "source": "layer"},
            {"id": "layer-dlq", "required": True,
             "text": "Dead letter handling present.", "source": "layer"},
        ],
        "task": [
            {"id": "layer-overlap", "required": True,
             "text": "Handles overlapping executions.", "source": "layer"},
            {"id": "layer-logging", "required": True,
             "text": "Failures are logged.", "source": "layer"},
        ],
        "cache": [
            {"id": "layer-invalidation", "required": True,
             "text": "Invalidation strategy is correct.", "source": "layer"},
            {"id": "layer-ttl", "required": False,
             "text": "TTL values documented.", "source": "layer"},
        ],
        "rpc": [
            {"id": "layer-timeout", "required": True,
             "text": "Timeout and retry configured.", "source": "layer"},
            {"id": "layer-degradation", "required": True,
             "text": "Degradation handling present.", "source": "layer"},
        ],
        "test": [
            {"id": "layer-deterministic", "required": True,
             "text": "Tests are deterministic and isolated.", "source": "layer"},
            {"id": "layer-coverage", "required": True,
             "text": "Happy and error paths covered.", "source": "layer"},
        ],
        "verification": [
            {"id": "layer-compile", "required": True,
             "text": "All changes compile together.", "source": "layer"},
            {"id": "layer-integration", "required": True,
             "text": "Integration verified.", "source": "layer"},
        ],
    }
    return items.get(layer, [])
```

- [ ] **Step 2: Add _deduplicate_checks() function**

```python
def _deduplicate_checks(checks: list[dict]) -> list[dict]:
    seen = {}
    for check in checks:
        text_key = check["text"].lower().strip()
        if text_key in seen:
            existing = seen[text_key]
            if check["required"] and not existing["required"]:
                seen[text_key] = check
        else:
            seen[text_key] = check
    return list(seen.values())
```

- [ ] **Step 3: Add generate_checklist() function**

```python
def generate_checklist(item: dict, profile: dict) -> dict:
    checks = []
    checks.extend([
        {"id": "ctx", "required": True, "text": "Context pack is present before execution.", "source": "base"},
        {"id": "scope", "required": True, "text": "Authorized scope is recorded before edits.", "source": "base"},
        {"id": "acceptance", "required": True, "text": "Acceptance criteria are verifiable.", "source": "base"},
    ])
    for i, rule in enumerate(profile.get("ruleset", [])):
        checks.append({
            "id": f"rule-{i}",
            "required": profile.get("severity") == "strict",
            "text": rule,
            "source": "profile",
        })
    layer = item.get("layer", "service")
    checks.extend(_layer_checklist_items(layer))
    for i, ac in enumerate(item.get("acceptance_criteria", [])):
        checks.append({
            "id": f"ac-{i}",
            "required": True,
            "text": f"AC: {ac}",
            "source": "acceptance_criteria",
        })
    checks = _deduplicate_checks(checks)
    return {
        "id": item["id"],
        "scenario": item.get("scenario", ""),
        "layer": layer,
        "severity": profile.get("severity", "balanced"),
        "source": "workflow_intelligence_runner.py V2",
        "checks": checks,
        "summary": {
            "total": len(checks),
            "required": sum(1 for c in checks if c["required"]),
            "optional": sum(1 for c in checks if not c["required"]),
        },
    }
```

- [ ] **Step 4: Update main() to use generate_checklist()**

Replace the checklist generation loop in `main()`:

```python
for item in work_items["items"]:
    write_json(run_dir / f"agent/checklists/{item['id']}.json", generate_checklist(item, profile))
```

- [ ] **Step 5: Add checklist tests to regression file**

```python
from workflow_intelligence_runner import generate_checklist, _layer_checklist_items, _deduplicate_checks


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
```

Add these tests to the `ALL_TESTS` list.

- [ ] **Step 6: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/workflow_intelligence_regression.py`
Expected: All tests PASS (28+ tests)

- [ ] **Step 7: Commit**

---

### Task 4: Add Compliance Assessment and Evolution Suggestions

**Files:**
- Modify: `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`

- [ ] **Step 1: Add assess_compliance() function**

```python
def assess_compliance(work_items: list[dict], checklists: dict, profile: dict) -> dict:
    total = len(work_items)
    passed = sum(1 for item in work_items if item.get("passes"))
    failed = total - passed
    mandatory_total = 0
    mandatory_complete = 0
    for item in work_items:
        checklist = checklists.get(item["id"], {})
        for check in checklist.get("checks", []):
            if check.get("required"):
                mandatory_total += 1
                if check.get("completed", False):
                    mandatory_complete += 1
    if failed == 0 and mandatory_complete == mandatory_total:
        grade, status = "A", "PASS"
    elif failed == 0:
        grade, status = "B", "CONDITIONAL PASS"
    elif failed <= total * 0.3:
        grade, status = "C", "CONDITIONAL PASS"
    else:
        grade, status = "D", "FAIL"
    risk = "low"
    if profile.get("severity") == "strict" and failed > 0:
        risk = "high"
    elif failed > 0:
        risk = "medium"
    return {
        "status": status,
        "quality_grade": grade,
        "risk_level": risk,
        "work_items": {"total": total, "passed": passed, "failed": failed},
        "mandatory_checks": {"total": mandatory_total, "complete": mandatory_complete},
        "guideline_adherence": f"{passed}/{total} items passed.",
        "missing_evidence": [],
    }
```

- [ ] **Step 2: Add suggest_evolution() function**

```python
def suggest_evolution(work_items: list[dict], scenario: dict, profile: dict,
                      compliance: dict) -> dict:
    proposals = []
    if scenario.get("confidence", 0) < 0.8:
        proposals.append({
            "category": "scenario_detection",
            "type": "needs-human",
            "reason": f"Low confidence ({scenario['confidence']}) for {scenario['id']}.",
            "source_artifact": "agent/scenario.json",
        })
    for item in work_items:
        if item.get("passes") and item.get("attempts", 0) > 1:
            proposals.append({
                "category": "checklist_update",
                "type": "auto",
                "reason": f"{item['id']} needed {item['attempts']} attempts.",
                "source_artifact": f"agent/reports/{item['id']}/",
            })
    if compliance.get("quality_grade") in ["C", "D", "F"]:
        proposals.append({
            "category": "profile_update",
            "type": "needs-human",
            "reason": f"Quality grade {compliance['quality_grade']} suggests profile rules may need strengthening.",
            "source_artifact": "agent/compliance-report.md",
        })
    for item in work_items:
        if item.get("status") == "fail":
            proposals.append({
                "category": "context_pack_update",
                "type": "auto",
                "reason": f"{item['id']} failed. Consider enriching context pack.",
                "source_artifact": f"agent/context-packs/{item['id']}.md",
            })
    lessons = []
    for item in work_items:
        if item.get("passes") and item.get("attempts", 0) > 0:
            lessons.append(f"{item['id']}: required {item['attempts']} repair rounds.")
    return {
        "proposals": proposals,
        "lessons_learned": lessons,
        "summary": {
            "total_proposals": len(proposals),
            "auto_applicable": sum(1 for p in proposals if p["type"] == "auto"),
            "needs_human": sum(1 for p in proposals if p["type"] == "needs-human"),
        },
    }
```

- [ ] **Step 3: Update main() to generate compliance and evolution artifacts**

After the checklist loop in `main()`, add:

```python
    # Generate compliance
    checklists_data = {}
    for item in work_items["items"]:
        cl_path = run_dir / f"agent/checklists/{item['id']}.json"
        checklists_data[item["id"]] = load_json(cl_path, {})
    compliance = assess_compliance(work_items["items"], checklists_data, profile)
    write_json(run_dir / "agent/compliance-report.json", compliance)

    # Generate evolution
    evolution = suggest_evolution(work_items["items"], scenario, profile, compliance)
    write_json(run_dir / "agent/evolution-report.json", evolution)
```

Also add `load_json` to the imports from `runtime_support`.

Update the `update_section` call to include the new artifacts:

```python
    update_section(
        state,
        "workflow_intelligence",
        "complete",
        [
            ARTIFACT_PATHS["workflow_intelligence"],
            ARTIFACT_PATHS["agent_scenario"],
            ARTIFACT_PATHS["agent_profile"],
            ARTIFACT_PATHS["agent_work_items_seed"],
            "agent/compliance-report.json",
            "agent/evolution-report.json",
        ],
        [ARTIFACT_PATHS["spec_delta"], ARTIFACT_PATHS["workflow_intelligence"]],
        [],
        {"scenario_id": scenario["id"], "profile": profile["name"]},
    )
```

- [ ] **Step 4: Add compliance and evolution tests to regression file**

```python
from workflow_intelligence_runner import assess_compliance, suggest_evolution


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
```

Add these tests to the `ALL_TESTS` list.

- [ ] **Step 5: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/workflow_intelligence_regression.py`
Expected: All tests PASS (35+ tests)

- [ ] **Step 6: Commit**

---

### Task 5: Update main() to Use All V2 Functions

**Files:**
- Modify: `requirement-flow-plugin/scripts/workflow_intelligence_runner.py`

- [ ] **Step 1: Update the 03_workflow_intelligence.md template**

Replace the `write_text` call in `main()` to include V2 content:

```python
    write_text(
        run_dir / ARTIFACT_PATHS["workflow_intelligence"],
        f"""# 03 Workflow Intelligence

## Scenario

- ID: {scenario['id']}
- Name: {scenario['name']}
- Confidence: {scenario['confidence']}
- Reason: {scenario['reason']}
- Layers: {', '.join(scenario.get('layers', []))}

## Guideline Profile

- Name: {profile['name']}
- Severity: {profile['severity']}
- Severity Guidance: {profile['severity_guidance']}

## Capability Trace

{capability_trace()}
## Work Item Seed

- Path: {ARTIFACT_PATHS['agent_work_items_seed']}
- Count: {len(work_items['items'])}
- Layers: {', '.join(item['layer'] for item in work_items['items'])}

## Compliance

- Grade: {compliance['quality_grade']}
- Risk: {compliance['risk_level']}
- Status: {compliance['status']}

## Evolution Proposals

- Total: {evolution['summary']['total_proposals']}
- Auto-applicable: {evolution['summary']['auto_applicable']}
- Needs human: {evolution['summary']['needs_human']}

## BLOCKER

- None
""",
    )
```

- [ ] **Step 2: Run unified runtime regression**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/unified_runtime_regression.py`
Expected: PASS

- [ ] **Step 3: Run workflow intelligence regression**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/workflow_intelligence_regression.py`
Expected: All tests PASS

- [ ] **Step 4: Commit**

---

### Task 6: Update workflow-intelligence Skill

**Files:**
- Modify: `requirement-flow-plugin/skills/workflow-intelligence/SKILL.md`

- [ ] **Step 1: Update the SKILL.md**

Replace the existing content with V2:

```markdown
---
name: workflow-intelligence
description: >
  Builds the V2 Java backend workflow intelligence: 8-scenario detection,
  dynamic profile selection, layer-based work item decomposition, dynamic
  checklist generation, compliance assessment, and evolution suggestions.
  Use when main-flow reaches Step 3 or the user asks for workflow intelligence.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# workflow-intelligence

Workflow Intelligence converts a natural-language Java backend requirement into
structured evidence that later planning and agent execution can consume.

## Mandatory Rules

- Keep `main-flow` as the orchestrator; this skill only supplies intelligence artifacts.
- Record every source capability as `v1`, `v2`, `v3`, or `deferred`.
- Use scenario confidence. Ask only when confidence is too low or top scenarios conflict.
- Select and record the guideline profile before creating work items.
- Generate checklists before any module is marked ready for implementation.
- Treat memory and evolution as contracts; do not silently patch skills, templates, or memory.
- Do not store secrets in intelligence artifacts.

## Flow

1. Read `01_prd_summary.md`, `02_spec_delta.md` when present, and `state.json`.
2. Run `workflow_intelligence_runner.py --run-dir <dir>` for base scenario, profile, items, checklists, compliance, and evolution.
3. Review scenario detection confidence. If < 0.7, ask user to confirm or adjust.
4. Review work item decomposition. Confirm layer assignments are correct.
5. Review checklists for completeness. Add project-specific items if needed.
6. Review compliance assessment and evolution proposals.
7. Update `state.json.workflow_intelligence`.

## Scenario Scope

V2 covers 8 Java backend scenarios:

- API/controller changes (java-api-change)
- Service logic changes (java-service-change)
- DAO/database changes (java-dao-change)
- Message/event changes (java-message-change)
- Scheduled task changes (java-task-change)
- Cache changes (java-cache-change)
- RPC changes (java-rpc-change)
- Test changes (java-test-change)

Performance, security, migration, documentation, and DDD scenarios are recognized as risk signals.

## Outputs

```text
WORKFLOW_INTELLIGENCE_STATUS: ready|blocked|failed
SCENARIO:
- <id, name, confidence, layers>
PROFILE:
- <profile, severity, ruleset>
WORK_ITEMS:
- <count, layers>
COMPLIANCE:
- <grade, risk, status>
ARTIFACTS:
- agent/scenario.json
- agent/profile.json
- agent/work_items.seed.json
- agent/checklists/<work-item-id>.json
- agent/compliance-report.json
- agent/evolution-report.json
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <action>
```
```

- [ ] **Step 2: Commit**

---

### Task 7: Update main-flow Integration

**Files:**
- Modify: `requirement-flow-plugin/skills/main-flow/SKILL.md`
- Modify: `requirement-flow-plugin/docs/main-flow.md`

- [ ] **Step 1: Update Step 3 in main-flow SKILL.md Flow section**

Find the Flow section item 3 and update:

```
3. Workflow intelligence -> 03_workflow_intelligence.md and agent/* intelligence artifacts
   - Run workflow_intelligence_runner.py for base artifacts
   - Review scenario confidence, work item decomposition, checklists
   - Generate compliance and evolution artifacts
```

- [ ] **Step 2: Add Step 3 detail section**

Add after the existing Step detail sections:

```markdown
## Step 3: Workflow Intelligence

1. Run `workflow_intelligence_runner.py --run-dir <dir>` for base scenario, profile, items, checklists, compliance, and evolution.
2. Load workflow-intelligence skill.
3. Review scenario detection:
   - If confidence < 0.7, ask user to confirm or adjust.
   - Confirm layers are correct for the requirement.
4. Review work item decomposition:
   - Confirm each item's layer assignment.
   - Add or merge items if needed.
5. Review checklists:
   - Verify mandatory items cover the requirement.
   - Add project-specific checks.
6. Review compliance and evolution artifacts.
7. Update state.json.workflow_intelligence.status.
```

- [ ] **Step 3: Update Knowledge Hooks for Step 3**

```markdown
- Step 3: `workflow-intelligence`, `dynamic-checklist`, `compliance-report`, `evolution-proposal`
```

- [ ] **Step 4: Update docs/main-flow.md Step 3**

```markdown
3. Workflow intelligence: 8-scenario detection, dynamic profiles, layer-based
   work item decomposition, dynamic checklists, compliance assessment, and
   evolution suggestions.
```

- [ ] **Step 5: Commit**

---

### Task 8: Install and Verify

**Files:**
- All install roots

- [ ] **Step 1: Run plugin self-check**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/plugin_self_check.py`
Expected: status success

- [ ] **Step 2: Run all regression tests**

Run: `python3 scripts/workflow_intelligence_regression.py && python3 scripts/unified_runtime_regression.py && python3 scripts/agent_execution_regression.py`
Expected: All PASS

- [ ] **Step 3: Verify skill count unchanged**

Check that skill count is still 85 (no new skills, only modifications).

- [ ] **Step 4: Commit**
