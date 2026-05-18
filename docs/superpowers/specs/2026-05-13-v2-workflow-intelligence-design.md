# V2 Workflow Intelligence Design

## Overview

V2 Workflow Intelligence upgrades the V1 contract-only layer with deeper scenario detection, dynamic profile selection, layer-based work item decomposition, dynamic checklist generation, compliance assessment, and evolution suggestions. It follows the same Runner+Skill pattern as V2 Agent Execution.

## Architecture

```text
main-flow Step 3
      │
      ▼
workflow-intelligence skill (V2, Claude behavior guide)
      │
      ▼
workflow_intelligence_runner.py (V1→V2, rules/templates/I/O)
```

**Responsibilities:**
- `workflow-intelligence` skill: tells Claude how to analyze requirements, decompose items, assess compliance, suggest evolution
- `workflow_intelligence_runner.py`: scenario rules, profile templates, checklist templates, artifact I/O
- `main-flow` Step 3: calls runner for base structure, then skill guides Claude for intelligent analysis

## Scenario Detection

### V1 → V2

V1: 2 scenarios, simple keyword matching.
V2: 8 scenarios, structured rule engine with weighted keyword scoring.

### Scenario Rules

| ID | Name | Keywords | Layers | Base Confidence |
|----|------|----------|--------|-----------------|
| java-api-change | API/controller change | controller, api, 接口, endpoint, rest, request, response | controller | 0.85 |
| java-service-change | Service logic change | service, 业务, 逻辑, 处理, business | service | 0.80 |
| java-dao-change | DAO/database change | dao, mapper, 数据库, sql, table, repository | dao, mapper | 0.85 |
| java-message-change | Message/event change | 消息, mq, kafka, event, topic, consumer | message | 0.80 |
| java-task-change | Scheduled task change | 定时, 任务, job, task, schedule, cron, batch | task | 0.80 |
| java-cache-change | Cache change | 缓存, cache, redis, 过期, 失效 | cache | 0.75 |
| java-rpc-change | RPC change | rpc, 调用, feign, dubbo, grpc, client | rpc, client | 0.75 |
| java-test-change | Test change | 测试, test, 单测, mock, assert | test | 0.80 |

### Detection Algorithm

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
        return default_backend_scenario()
    top_score, top_rule = scores[0]
    alternatives = [r["id"] for _, r in scores[1:3]]
    return {
        "id": top_rule["id"],
        "name": top_rule["name"],
        "confidence": round(top_score, 2),
        "alternatives": alternatives,
        "layers": top_rule["layers"],
        "reason": f"Matched keywords for {top_rule['name']}.",
    }
```

### Output

`agent/scenario.json`: id, name, confidence, alternatives, layers, reason

## Profile Selection

### V1 → V2

V1: Hardcoded `java-backend-delivery` with 4 rules.
V2: Dynamic profile per scenario with severity adjustments.

### Profile Templates

Each scenario has a dedicated ruleset:

- **java-api-change**: Controller thin delegation, input validation, REST conventions, error responses, integration test
- **java-service-change**: Single responsibility, business validation, transaction boundaries, DI, unit test
- **java-dao-change**: SQL performance, migration scripts, empty results, N+1 prevention, rollback strategy
- **java-message-change**: Idempotent consumers, DLQ, schema compatibility, non-blocking failures, E2E verification
- **java-task-change**: Overlap handling, failure logging, configurable params, progress tracking, restart survival
- **java-cache-change**: Invalidation strategy, key conventions, thundering herd prevention, TTL docs, perf verification
- **java-rpc-change**: Timeout/retry, degradation handling, contract versioning, circuit breaker, integration test
- **java-test-change**: Deterministic isolation, explicit setup, mock boundaries, coverage, order independence

### Severity Adjustments

- **strict**: All rules mandatory. Fail on any violation.
- **balanced**: Core rules mandatory. Important rules warn. Nice-to-have suggest.
- **relaxed**: Core rules mandatory. Others informational.

### Output

`agent/profile.json`: name, severity, scenario, ruleset, severity_guidance

## Work Item Decomposition

### V1 → V2

V1: 1 item = entire requirement.
V2: Decomposed by layer, each item corresponds to one layer's changes.

### Decomposition Strategy

```python
def decompose_items(requirement: str, scenario: dict, spec_delta: dict = None) -> list[dict]:
    layers = scenario.get("layers", ["service"])
    items = []
    for layer in layers:
        items.append({
            "id": f"wi-{len(items)+1:03d}",
            "title": f"Implement {layer} layer changes",
            "layer": layer,
            "scenario": scenario["id"],
            "acceptance_criteria": _criteria_for_layer(layer, scenario),
            ...
        })
    # Optional: verification item if spec_delta has changes
    if spec_delta and spec_delta.get("changes"):
        items.append({
            "id": f"wi-{len(items)+1:03d}",
            "title": "Verification and integration",
            "layer": "verification",
            ...
        })
    return items
```

### Layer-Specific Acceptance Criteria

Each layer has default acceptance criteria:

- **controller**: API types, input validation, error responses
- **service**: Business logic, single responsibility, transactions
- **dao**: SQL correctness, empty results, N+1 prevention
- **mapper**: Mapping correctness, null handling
- **message**: Idempotency, DLQ handling
- **task**: Overlap handling, failure logging
- **cache**: Invalidation correctness, TTL appropriateness
- **rpc**: Timeout/retry, degradation handling
- **test**: Deterministic, coverage
- **verification**: Compilation, integration, no regressions

### Output

`agent/work_items.seed.json`: items array with layer field per item

## Checklist Generation

### V1 → V2

V1: 4 fixed checks (ctx, scope, acceptance, verification).
V2: Dynamic generation from scenario + profile + layer + acceptance criteria.

### Generation Logic

```python
def generate_checklist(item: dict, profile: dict) -> dict:
    checks = []
    # 1. Base checks (always present)
    checks.extend([ctx, scope, acceptance])
    # 2. Profile rule checks
    for rule in profile["ruleset"]:
        checks.append({"source": "profile", ...})
    # 3. Layer-specific checks
    checks.extend(_layer_checklist_items(item["layer"]))
    # 4. Acceptance criteria checks
    for ac in item["acceptance_criteria"]:
        checks.append({"source": "acceptance_criteria", ...})
    # 5. Deduplicate
    checks = _deduplicate_checks(checks)
    return {"checks": checks, "summary": {total, required, optional}}
```

### Deduplication

Semantic dedup: same text → keep one, required takes precedence.

### Output

`agent/checklists/<item-id>.json`: checks array, summary (total, required, optional)

## Compliance Assessment

### V1 → V2

V2: Runner generates compliance-report.md initial assessment.

### Assessment Logic

```python
def assess_compliance(work_items, checklists, profile) -> dict:
    # Count passed/failed items
    # Count mandatory checklist completion
    # Grade: A (all pass + all mandatory), B (all pass), C (≤30% fail), D (>30% fail)
    # Risk: low (all pass), medium (some fail), high (strict + fail)
    return {status, quality_grade, risk_level, work_items, mandatory_checks, ...}
```

### Grade Mapping

| Grade | Condition | Status |
|-------|-----------|--------|
| A | All items pass + all mandatory checks complete | PASS |
| B | All items pass | CONDITIONAL PASS |
| C | ≤30% items fail | CONDITIONAL PASS |
| D | >30% items fail | FAIL |

### Output

`agent/compliance-report.md`

## Evolution Suggestions

### V2 Logic

```python
def suggest_evolution(work_items, scenario, profile, compliance) -> dict:
    proposals = []
    # 1. Low confidence scenario → suggest keyword refinement
    # 2. Items with repair rounds → suggest checklist improvement
    # 3. Low quality grade → suggest profile strengthening
    # 4. Failed items → suggest context pack enrichment
    # 5. Lessons learned from repair rounds
    return {proposals, lessons_learned, summary}
```

### Proposal Categories

- `scenario_detection`: keyword refinement
- `checklist_update`: add failure pattern checks
- `profile_update`: strengthen rules
- `context_pack_update`: enrich domain info

### Safety (unchanged from V1)

- Proposals only, never auto-apply
- All memory/skill/template changes need user confirmation

### Output

`agent/evolution-report.md`

## Runner Changes

### workflow_intelligence_runner.py V1 → V2

**Changed:**
- `detect_scenario()` — expanded from 2 to 8 scenarios with weighted scoring
- `profile_for_scenario()` — dynamic rulesets per scenario
- `seed_work_items()` — calls `decompose_items()` instead of returning single item

**New functions:**
- `decompose_items()` — layer-based decomposition
- `_criteria_for_layer()` — default acceptance criteria per layer
- `generate_checklist()` — dynamic checklist from scenario+profile+layer+AC
- `_layer_checklist_items()` — layer-specific check items
- `_deduplicate_checks()` — semantic deduplication
- `assess_compliance()` — compliance grading
- `suggest_evolution()` — evolution proposals
- `SCENARIO_RULES` — 8 scenario rule definitions
- `PROFILE_TEMPLATES` — per-scenario profile templates
- `SEVERITY_ADJUSTMENTS` — severity level guidance

### Artifact Changes

| Artifact | V1 | V2 |
|----------|----|----|
| agent/scenario.json | 2 fields | +layers, +confidence scoring |
| agent/profile.json | hardcoded | +severity_guidance, +per-scenario ruleset |
| agent/work_items.seed.json | 1 item | N items by layer |
| agent/checklists/*.json | 4 fixed | dynamic by scenario+profile+layer+AC |
| agent/compliance-report.md | not generated | generated with grade+risk |
| agent/evolution-report.md | not generated | generated with proposals |

## main-flow Integration

### Step 3 Update

```text
1. Run workflow_intelligence_runner.py for base scenario/profile/items
2. Load workflow-intelligence skill
3. Review and refine:
   a. Validate scenario detection confidence
   b. Confirm or adjust profile selection
   c. Review work item decomposition
   d. Validate checklists completeness
4. Generate compliance and evolution artifacts
5. Update state.json.workflow_intelligence
```

### Knowledge Hooks

```text
Step 3: workflow-intelligence, dynamic-checklist, compliance-report, evolution-proposal
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scenario detection | Extended rule engine | Deterministic, testable, fast; covers 8 scenarios |
| Profile selection | Per-scenario templates | Each scenario has distinct quality concerns |
| Decomposition | By layer | Maps to Java backend architecture; each item is independently testable |
| Checklist generation | Dynamic from 4 sources | More thorough than fixed; deduplicates automatically |
| Compliance | Runner-generated initial | Deterministic base; skill refines with judgment |
| Evolution | Runner-generated proposals | Safe (proposals only); skill adds context |
