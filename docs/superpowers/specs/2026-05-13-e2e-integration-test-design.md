# End-to-End Integration Test Design

## Overview

Extend `unified_runtime_regression.py` to cover all 12 integration testing gaps identified in the V2 requirement-flow-plugin. Uses a hybrid architecture: one full-chain test as the base, plus independent scenario tests for specific gaps.

## Architecture

```text
unified_runtime_regression.py
├── test_full_chain()                    # Base: complete 10-stage chain
│   ├── Stage 01-10 runner execution
│   ├── Artifact existence + content assertions
│   ├── state.json section assertions
│   └── Evidence chain validation
├── test_provider_dispatch_integration() # Gap #3, #10
├── test_repair_round_loop()             # Gap #4
├── test_multi_work_item()               # Gap #5
├── test_recovery_resume()               # Gap #9
├── test_adapter_factory()               # Gap #11
└── test_agent_execution_main()          # Gap #12
```

## Gap Coverage Matrix

| Gap | Description | Covered By |
|-----|-------------|------------|
| #1 | Stages 05, 06 in chain | `test_full_chain` |
| #2 | Stage 08 (code review) | `test_full_chain` |
| #3 | Provider dispatch with runner | `test_provider_dispatch_integration` |
| #4 | Repair round loop | `test_repair_round_loop` |
| #5 | Multi-work-item scenarios | `test_multi_work_item` |
| #6 | Context-pack integration | `test_full_chain` |
| #7 | Compliance/evolution with real items | `test_full_chain` |
| #8 | state.json evidence chain | `test_full_chain` |
| #9 | Recovery/resume | `test_recovery_resume` |
| #10 | providers.yaml end-to-end | `test_provider_dispatch_integration` |
| #11 | adapter_factory flow | `test_adapter_factory` |
| #12 | agent_execution main() | `test_agent_execution_main` |

## Test Functions

### test_full_chain

**Purpose:** Verify the complete 10-stage artifact chain runs end-to-end.

**Setup:**
- Create tempfile run directory
- Write `01_prd_summary.md` fixture (Java API requirement)
- Write `05_tech_plan.md` fixture (technical decisions)
- Write `06_impl_plan.md` fixture (implementation plan)
- Write `08_code_review.md` fixture (code review summary)

**Execution:**
- Run stages 02, 03, 04, 07, 09, 10 via their runners
- Stages 01, 05, 06, 08 are fixture-provided (manual/skill stages)

**Assertions:**
- All 10 markdown artifacts exist and contain a heading
- `agent/scenario.json` has valid scenario id
- `agent/profile.json` has valid profile name
- `agent/work_items.seed.json` has at least 1 work item
- `agent/work_items.json` work items have `execution_record`
- `agent/checklists/` has at least 1 checklist file
- `agent/compliance-report.json` exists with grade
- `agent/evolution-report.json` exists
- `agent/context-packs/java-context.md` exists
- `state.json` sections: all have correct status, `evidence_refs` reference existing files

### test_provider_dispatch_integration

**Purpose:** Verify a runner uses configured provider instead of manual mode fallback.

**Setup:**
- Create tempfile run directory with full chain fixtures
- Create `providers.yaml` with `test_adapter_echo.py` as adapter for `deploy` capability
- Run chain through stage 09 (delivery verification)

**Assertions:**
- `load_providers()` returns non-empty registry
- Stage 09 produces verification artifact without `missing-provider` marker for configured capability
- `agent/provider-results/` directory has dispatch result files

### test_repair_round_loop

**Purpose:** Verify work item repair round creation and progression.

**Setup:**
- Create tempfile run directory
- Write seed work items with one item marked as `failed`
- Run `agent_execution_runner.main()`

**Assertions:**
- Failed item gets `execution_record.repair_rounds > 0`
- New repair round entry appears in work item
- `state.json` agent_execution section tracks repair state

### test_multi_work_item

**Purpose:** Verify multi-layer scenario produces and manages multiple work items.

**Setup:**
- Create tempfile run directory
- Write PRD fixture that triggers multi-layer scenario (controller + service + dao)
- Run workflow intelligence runner

**Assertions:**
- `agent/work_items.seed.json` has 3+ work items
- Each item has distinct `id` and `layer`
- Checklists exist for each work item
- Items reference correct context packs

### test_recovery_resume

**Purpose:** Verify the chain can resume from partial state.json.

**Setup:**
- Create tempfile run directory
- Run stages 02-03, then simulate failure
- Load state.json, verify partial completion
- Resume from stage 04

**Assertions:**
- Stage 04 runs successfully with existing stage 02-03 artifacts
- Final state.json shows all stages complete
- No duplicate artifacts created

### test_adapter_factory

**Purpose:** Verify adapter_factory.py generates working adapters.

**Setup:**
- Create tempfile run directory
- Run adapter_factory with `deploy` capability

**Assertions:**
- Generated adapter file exists
- Adapter is executable (subprocess run with test input returns valid JSON)
- Manifest file exists with correct metadata

### test_agent_execution_main

**Purpose:** Verify agent_execution_runner.main() with real seed file.

**Setup:**
- Create tempfile run directory
- Write seed work items from workflow intelligence output
- Run `agent_execution_runner.main()` with `--run-dir`

**Assertions:**
- `agent/work_items.json` created with validated items
- `agent/main-log.md` exists with execution log
- `07_agent_execution.md` exists with heading
- `state.json` agent_execution section has correct status

## File Structure

```text
requirement-flow-plugin/
└── scripts/
    ├── unified_runtime_regression.py    # MODIFY — add 6 new test functions
    ├── test_adapter_echo.py             # EXISTS — reuse for provider tests
    └── runtime_support.py               # EXISTS — reuse helpers
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Test location | Extend unified_runtime_regression.py | Single entry point, consistent with existing pattern |
| Test data | tempfile fixtures | Isolation, no cleanup needed, each test independent |
| Architecture | Hybrid (chain + scenarios) | Chain validates connectivity, scenarios validate edge cases |
| Stage 01/05/06/08 | Fixture-provided | These are manual/skill stages without runners |
| Provider test adapter | test_adapter_echo.py | Already exists, deterministic, no real provider calls |
| Multi-item scenario | controller+service+dao | Realistic Java backend decomposition |

## Out of Scope

- Performance/load testing
- Real provider API calls (GitHub, K8s, etc.)
- UI/visual testing
- Cross-platform testing
- Concurrent execution testing
