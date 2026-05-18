#!/usr/bin/env python3
"""Generate V2 workflow intelligence artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_support import ARTIFACT_PATHS, ensure_run_dir, load_json, load_state, requirement_text, save_state, update_section, write_json, write_text


TASK_TYPES = ["EXTEND", "MODIFY", "REFACTOR", "DIAGNOSE", "UPGRADE", "DELETE", "DEBUG", "MIGRATE"]

TASK_TYPE_KEYWORDS = {
    "EXTEND": ["add", "create", "new", "implement", "introduce", "新增", "添加", "实现"],
    "MODIFY": ["modify", "change", "update", "adjust", "alter", "修改", "调整", "变更"],
    "REFACTOR": ["refactor", "restructure", "optimize", "clean", "重构", "优化", "整理"],
    "DIAGNOSE": ["investigate", "diagnose", "analyze", "排查", "诊断", "分析"],
    "UPGRADE": ["upgrade", "migrate version", "bump", "升级", "版本升级"],
    "DELETE": ["remove", "delete", "deprecate", "废弃", "删除"],
    "DEBUG": ["fix", "bug", "repair", "resolve", "patch", "修复", "bug修复"],
    "MIGRATE": ["migrate", "migration", "迁移", "数据迁移"],
}


def classify_task_type(requirement: str) -> str:
    lowered = requirement.lower()
    scores = []
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lowered)
        if hits > 0:
            scores.append((hits, task_type))
    if not scores:
        return "EXTEND"
    scores.sort(reverse=True)
    return scores[0][1]


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
        "keywords": ["dao", "mapper", "数据库", "sql", "表", "字段", "column", "table", "query", "repository"],
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
    alternatives = [r["id"] for s, r in scores[1:3] if s >= 0.5]
    return {
        "id": top_rule["id"],
        "name": top_rule["name"],
        "confidence": round(top_score, 2),
        "alternatives": alternatives,
        "layers": top_rule["layers"],
        "reason": f"Matched {len([kw for kw in top_rule['keywords'] if kw in lowered])} keywords for {top_rule['name']}.",
    }


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

MAX_DESCRIPTION_LENGTH = 200


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


def decompose_items(requirement: str, scenario: dict) -> list[dict]:
    layers = scenario.get("layers", ["service"])
    task_type = classify_task_type(requirement)
    items = []
    priority = 1
    for layer in layers:
        item_id = f"wi-{len(items)+1:03d}"
        items.append({
            "id": item_id,
            "title": f"Implement {layer} layer changes",
            "scenario": scenario.get("id", "unknown"),
            "task_type": task_type,
            "layer": layer,
            "story_size": "one supervised agent iteration",
            "description": f"Changes to the {layer} layer for: {requirement[:MAX_DESCRIPTION_LENGTH]}",
            "acceptance_criteria": _criteria_for_layer(layer, scenario),
            "priority": priority,
            "passes": False,
            "notes": "",
        })
        priority += 1
    return items


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
    if compliance.get("quality_grade") in ["C", "D"]:
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
        if item.get("passes") and item.get("attempts", 0) > 1:
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


def seed_work_items(requirement: str, scenario: dict) -> dict:
    items = decompose_items(requirement, scenario)
    return {
        "version": "work-items-seed-v2",
        "source": "workflow_intelligence_runner.py",
        "items": items,
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
        write_json(run_dir / f"agent/checklists/{item['id']}.json", generate_checklist(item, profile))

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
    save_state(run_dir, state)
    print("WORKFLOW_INTELLIGENCE_STATUS: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
