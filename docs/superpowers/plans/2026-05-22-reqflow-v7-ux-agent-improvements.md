# ReqFlow V7 UX & Agent Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 17 improvements to ReqFlow's confidence visualization, stage reporting, multi-agent dispatch, MCP instant output, and acceptance panels.

**Architecture:** Three-layer changes — Core Python modules (new files: confidence_tracker, artifact_verifier, agent_dispatcher), MCP tool layer (mcp_server.py gate schema + error messages + dashboard fix), and SKILL.md behavior layer (prescriptive templates for agent behavior).

**Tech Stack:** Python 3.10+, MCP protocol, Unicode box-drawing visualization, Claude Code Agent tool for subagent dispatch.

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `core/confidence_tracker.py` | 6+5 dimension model, trend tracking, history persistence, Unicode visualization |
| `core/artifact_verifier.py` | File existence + content verification for claimed changes |
| `core/agent_dispatcher.py` | Agent role matrix, dispatch prompt templates, timeout handling |
| `tests/test_confidence_tracker.py` | Tests for confidence tracker |
| `tests/test_artifact_verifier.py` | Tests for artifact verifier |
| `tests/test_agent_dispatcher.py` | Tests for agent dispatcher |

### Modified Files
| File | Changes |
|------|---------|
| `core/confidence.py` | Add 6th dimension (spec_compliance), adjust weights |
| `core/state_manager.py` | Add current_stage_index, steps_executed to RunState |
| `runner/mcp_server.py` | Gate schema in verify description, enhanced error messages, dashboard state sync |
| `core/skill_generator.py` | Agent dispatch templates, report templates, confirmation panels, MCP trace sections |
| `skills/main-flow/SKILL.md` | MCP instant output rules, per-stage report, agent dispatch, confirmation panels |
| `skills/full-auto/SKILL.md` | Same as main-flow with auto_pilot variants |
| `skills/auto-flow/SKILL.md` | MCP trace rules, simplified confirmation |
| `skills/quality-gates/SKILL.md` | Diagnostic output format |
| `skills/harness-orchestrator/SKILL.md` | Agent dispatch rules, context bundle, artifact verification |

---

### Task 1: Confidence Tracker — 6+5 Dimension Model with Trend Tracking

**Files:**
- Create: `core/confidence_tracker.py`
- Create: `tests/test_confidence_tracker.py`

- [ ] **Step 1: Write the failing test for ConfidenceTracker**

```python
# tests/test_confidence_tracker.py
"""Tests for ConfidenceTracker — 6+5 dimension model with trend tracking."""

import json
import pytest
from pathlib import Path
from reqflow.core.confidence_tracker import ConfidenceTracker, DimensionResult


def test_six_core_dimensions():
    """ConfidenceTracker should have 6 core dimensions with correct weights."""
    tracker = ConfidenceTracker()
    result = tracker.assess(
        completeness=0.85,
        consistency=0.92,
        accuracy=0.78,
        testability=0.90,
        risk_coverage=0.88,
        spec_compliance=0.95,
    )
    assert len(result.core_dimensions) == 6
    assert result.core_dimensions[0].name == "completeness"
    assert result.core_dimensions[5].name == "spec_compliance"
    assert result.overall > 0


def test_weighted_average():
    """Overall score should be weighted average of core dimensions."""
    tracker = ConfidenceTracker()
    result = tracker.assess(
        completeness=1.0,
        consistency=1.0,
        accuracy=1.0,
        testability=1.0,
        risk_coverage=1.0,
        spec_compliance=1.0,
    )
    assert result.overall == pytest.approx(1.0, abs=0.01)


def test_minimum_gate_warning():
    """Any core dimension < 0.6 should trigger a warning."""
    tracker = ConfidenceTracker()
    result = tracker.assess(
        completeness=0.9,
        consistency=0.9,
        accuracy=0.3,  # below 0.6
        testability=0.9,
        risk_coverage=0.9,
        spec_compliance=0.9,
    )
    assert any(w.dimension == "accuracy" for w in result.warnings)


def test_progress_bar_rendering():
    """Progress bar should render Unicode block characters."""
    tracker = ConfidenceTracker()
    bar = tracker.render_progress_bar(0.85, width=10)
    assert "█" in bar
    assert "░" in bar
    assert len(bar) == 10


def test_heat_map_emoji():
    """Heat map should use colored emoji based on score."""
    tracker = ConfidenceTracker()
    assert tracker.heat_emoji(0.90) == "🟩"
    assert tracker.heat_emoji(0.75) == "🟨"
    assert tracker.heat_emoji(0.65) == "🟧"
    assert tracker.heat_emoji(0.50) == "🟥"


def test_trend_arrow():
    """Trend arrow should show direction based on delta."""
    tracker = ConfidenceTracker()
    assert "↑" in tracker.trend_arrow(0.90, 0.85)
    assert "↓" in tracker.trend_arrow(0.70, 0.85)
    assert "→" in tracker.trend_arrow(0.82, 0.83)


def test_sparkline_rendering():
    """Sparkline should render Unicode characters from a list of scores."""
    tracker = ConfidenceTracker()
    sparkline = tracker.render_sparkline([0.1, 0.3, 0.5, 0.7, 0.9])
    assert len(sparkline) == 5
    assert sparkline[0] == "▁"
    assert sparkline[4] == "█"


def test_history_persistence(tmp_path):
    """Confidence history should persist to JSON file."""
    history_file = tmp_path / "confidence_history.json"
    tracker = ConfidenceTracker(history_file=str(history_file))

    tracker.assess(
        completeness=0.8, consistency=0.8, accuracy=0.8,
        testability=0.8, risk_coverage=0.8, spec_compliance=0.8,
        run_id="run-001", stage="test",
    )

    assert history_file.exists()
    data = json.loads(history_file.read_text())
    assert len(data) == 1
    assert data[0]["run_id"] == "run-001"


def test_trend_from_history(tmp_path):
    """Trend should be calculated from previous entries in history."""
    history_file = tmp_path / "confidence_history.json"
    tracker = ConfidenceTracker(history_file=str(history_file))

    # First assessment
    tracker.assess(
        completeness=0.7, consistency=0.7, accuracy=0.7,
        testability=0.7, risk_coverage=0.7, spec_compliance=0.7,
        run_id="run-001", stage="test",
    )

    # Second assessment with higher scores
    result = tracker.assess(
        completeness=0.9, consistency=0.9, accuracy=0.9,
        testability=0.9, risk_coverage=0.9, spec_compliance=0.9,
        run_id="run-002", stage="test",
    )

    assert result.trend_delta > 0


def test_format_per_stage_report():
    """Per-stage report should include all required sections."""
    tracker = ConfidenceTracker()
    result = tracker.assess(
        completeness=0.85, consistency=0.92, accuracy=0.78,
        testability=0.90, risk_coverage=0.88, spec_compliance=0.95,
    )
    report = tracker.format_per_stage_report(result, stage_name="技术方案")
    assert "📊 置信度报告" in report
    assert "完整性" in report
    assert "一致性" in report
    assert "准确性" in report
    assert "可测试性" in report
    assert "风险覆盖" in report
    assert "Spec合规" in report
    assert "综合" in report
    assert "█" in report


def test_format_full_dashboard():
    """Full dashboard should include sparklines and radar overview."""
    tracker = ConfidenceTracker()
    results = []
    for i in range(5):
        r = tracker.assess(
            completeness=0.7 + i * 0.05, consistency=0.8 + i * 0.04,
            accuracy=0.75 + i * 0.04, testability=0.85 + i * 0.03,
            risk_coverage=0.8 + i * 0.03, spec_compliance=0.9 + i * 0.02,
        )
        results.append(r)
    dashboard = tracker.format_full_dashboard(results, stage_names=["启动", "PRD理解", "技术方案", "实施计划", "Agent执行"])
    assert "📈 置信度仪表盘" in dashboard
    assert "sparkline" in dashboard.lower() or "▁" in dashboard
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_confidence_tracker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'reqflow.core.confidence_tracker'"

- [ ] **Step 3: Implement ConfidenceTracker**

```python
# core/confidence_tracker.py
"""Confidence Tracker — 6+5 dimension model with trend tracking and Unicode visualization."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DimensionResult:
    """Single dimension score."""
    name: str
    display_name: str
    score: float  # 0-1
    weight: float
    heat: str  # emoji


@dataclass
class Warning:
    """Warning for a dimension below threshold."""
    dimension: str
    score: float
    threshold: float
    message: str


@dataclass
class ConfidenceReport:
    """Full confidence assessment result."""
    core_dimensions: list[DimensionResult]
    extended_dimensions: list[DimensionResult]
    overall: float
    warnings: list[Warning]
    trend_delta: float = 0.0
    previous_overall: float | None = None


# Core dimension definitions with weights
CORE_DIMENSIONS = [
    ("completeness", "完整性", 0.20),
    ("consistency", "一致性", 0.15),
    ("accuracy", "准确性", 0.20),
    ("testability", "可测试性", 0.15),
    ("risk_coverage", "风险覆盖", 0.15),
    ("spec_compliance", "Spec合规", 0.15),
]

EXTENDED_DIMENSIONS = [
    ("security", "安全性"),
    ("performance", "性能"),
    ("maintainability", "可维护性"),
    ("dependency_health", "依赖健康度"),
    ("documentation", "文档完整性"),
]

MIN_GATE_THRESHOLD = 0.6

# Sparkline characters (8 levels)
SPARK_CHARS = "▁▂▃▄▅▆▇█"


class ConfidenceTracker:
    """6+5 dimension confidence model with trend tracking and Unicode visualization."""

    def __init__(self, history_file: str | None = None):
        self._history_file = Path(history_file) if history_file else None
        self._history: list[dict] = []
        if self._history_file and self._history_file.exists():
            try:
                self._history = json.loads(self._history_file.read_text(encoding="utf-8"))
            except Exception:
                self._history = []

    def assess(
        self,
        completeness: float = 0.0,
        consistency: float = 0.0,
        accuracy: float = 0.0,
        testability: float = 0.0,
        risk_coverage: float = 0.0,
        spec_compliance: float = 0.0,
        extended: dict[str, float] | None = None,
        run_id: str = "",
        stage: str = "",
    ) -> ConfidenceReport:
        """Assess confidence across 6 core + 5 extended dimensions."""
        scores = {
            "completeness": completeness,
            "consistency": consistency,
            "accuracy": accuracy,
            "testability": testability,
            "risk_coverage": risk_coverage,
            "spec_compliance": spec_compliance,
        }

        core_dims = []
        weighted_sum = 0.0
        for key, display, weight in CORE_DIMENSIONS:
            score = scores[key]
            weighted_sum += score * weight
            core_dims.append(DimensionResult(
                name=key,
                display_name=display,
                score=score,
                weight=weight,
                heat=self.heat_emoji(score),
            ))

        overall = weighted_sum

        # Extended dimensions (optional, not in weighted average)
        ext = extended or {}
        ext_dims = []
        for key, display in EXTENDED_DIMENSIONS:
            score = ext.get(key, 0.0)
            ext_dims.append(DimensionResult(
                name=key,
                display_name=display,
                score=score,
                weight=0.0,
                heat=self.heat_emoji(score),
            ))

        # Warnings for dimensions below gate
        warnings = []
        for dim in core_dims:
            if dim.score < MIN_GATE_THRESHOLD:
                warnings.append(Warning(
                    dimension=dim.name,
                    score=dim.score,
                    threshold=MIN_GATE_THRESHOLD,
                    message=f"{dim.display_name} 得分 {dim.score:.0%}，低于 {MIN_GATE_THRESHOLD:.0%} 门槛",
                ))

        # Trend calculation
        previous_overall = None
        trend_delta = 0.0
        if self._history:
            last = self._history[-1]
            previous_overall = last.get("overall", 0.0)
            trend_delta = overall - previous_overall

        report = ConfidenceReport(
            core_dimensions=core_dims,
            extended_dimensions=ext_dims,
            overall=overall,
            warnings=warnings,
            trend_delta=trend_delta,
            previous_overall=previous_overall,
        )

        # Persist to history
        if run_id or stage:
            entry = {
                "run_id": run_id,
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
                "overall": round(overall, 4),
                "dimensions": {k: round(v, 4) for k, v in scores.items()},
            }
            self._history.append(entry)
            if self._history_file:
                self._history_file.parent.mkdir(parents=True, exist_ok=True)
                self._history_file.write_text(
                    json.dumps(self._history, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

        return report

    def render_progress_bar(self, score: float, width: int = 10) -> str:
        """Render a Unicode progress bar: ████████░░"""
        filled = int(round(score * width))
        filled = max(0, min(width, filled))
        return "█" * filled + "░" * (width - filled)

    def heat_emoji(self, score: float) -> str:
        """Return colored emoji based on score thresholds."""
        if score >= 0.85:
            return "🟩"
        elif score >= 0.70:
            return "🟨"
        elif score >= 0.60:
            return "🟧"
        else:
            return "🟥"

    def trend_arrow(self, current: float, previous: float) -> str:
        """Return trend arrow with delta."""
        delta = current - previous
        if abs(delta) < 0.02:
            return "→"
        elif delta > 0:
            return f"↑{int(round(delta * 100))}"
        else:
            return f"↓{int(round(abs(delta) * 100))}"

    def render_sparkline(self, scores: list[float]) -> str:
        """Render sparkline from a list of scores (0-1)."""
        if not scores:
            ""
        result = []
        for s in scores:
            idx = int(round(s * (len(SPARK_CHARS) - 1)))
            idx = max(0, min(len(SPARK_CHARS) - 1, idx))
            result.append(SPARK_CHARS[idx])
        return "".join(result)

    def format_per_stage_report(self, report: ConfidenceReport, stage_name: str = "") -> str:
        """Format per-stage confidence report with Unicode visualization."""
        lines = [f"### 📊 置信度报告", ""]

        # Table header
        lines.append("| 维度 | 得分 | 状态 | 趋势 |")
        lines.append("|------|------|------|------|")

        # Core dimensions
        prev_dims = {}
        if self._history and len(self._history) >= 2:
            prev_dims = self._history[-2].get("dimensions", {})

        for dim in report.core_dimensions:
            bar = self.render_progress_bar(dim.score)
            prev_score = prev_dims.get(dim.name)
            if prev_score is not None:
                trend = self.trend_arrow(dim.score, prev_score)
            else:
                trend = "→" if report.previous_overall is None else ""
            lines.append(f"| {dim.display_name} | {dim.score:.0%} | {bar} | {trend} |")

        # Overall
        if report.previous_overall is not None:
            overall_trend = self.trend_arrow(report.overall, report.previous_overall)
        else:
            overall_trend = "→"
        overall_bar = self.render_progress_bar(report.overall)
        lines.append(f"| **综合** | **{report.overall:.0%}** | {overall_bar} | {overall_trend} |")

        # Heat map legend
        lines.append("")
        lines.append("热力图: 🟩高(≥85) 🟨中(70-84) 🟧低(60-69) 🟥危(<60)")

        # Warnings
        if report.warnings:
            lines.append("")
            for w in report.warnings:
                lines.append(f"⚠️ {w.message}")

        return "\n".join(lines)

    def format_full_dashboard(self, reports: list[ConfidenceReport], stage_names: list[str] | None = None) -> str:
        """Format full dashboard with sparklines and overview (archive stage only)."""
        lines = ["### 📈 置信度仪表盘（全流程汇总）", ""]

        # Sparklines per dimension across stages
        dim_names = [d[0] for d in CORE_DIMENSIONS]
        dim_displays = [d[1] for d in CORE_DIMENSIONS]

        lines.append("趋势 sparkline（按阶段）:")
        for i, (key, display, _) in enumerate(CORE_DIMENSIONS):
            scores = []
            for r in reports:
                if i < len(r.core_dimensions):
                    scores.append(r.core_dimensions[i].score)
            if scores:
                sparkline = self.render_sparkline(scores)
                last_score = scores[-1]
                lines.append(f"{display}  {sparkline} {last_score:.0%}")

        # Heat map distribution
        lines.append("")
        heat_counts = {"🟩": 0, "🟨": 0, "🟧": 0, "🟥": 0}
        if reports:
            last = reports[-1]
            for dim in last.core_dimensions:
                heat_counts[dim.heat] = heat_counts.get(dim.heat, 0) + 1
        dist_parts = [f"{k}×{v}" for k, v in heat_counts.items()]
        lines.append(f"分布: {' '.join(dist_parts)}")

        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_confidence_tracker.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add core/confidence_tracker.py tests/test_confidence_tracker.py
git commit -m "feat: add ConfidenceTracker with 6+5 dimensions, trend tracking, Unicode visualization"
```

---

### Task 2: Artifact Verifier — File Integrity Verification

**Files:**
- Create: `core/artifact_verifier.py`
- Create: `tests/test_artifact_verifier.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_artifact_verifact_verifier.py
"""Tests for ArtifactVerifier — file existence + content verification."""

import pytest
from pathlib import Path
from reqflow.core.artifact_verifier import ArtifactVerifier, ArtifactClaim, VerificationResult


def test_verify_existing_file(tmp_path):
    """Should pass for existing file with matching action."""
    test_file = tmp_path / "test.py"
    test_file.write_text("hello")
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="test.py", action="create")]
    result = verifier.verify(claims)
    assert result.all_pass
    assert len(result.details) == 1
    assert result.details[0].passed


def test_verify_missing_file(tmp_path):
    """Should fail for missing file."""
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="missing.py", action="create")]
    result = verifier.verify(claims)
    assert not result.all_pass
    assert not result.details[0].passed


def test_verify_modify_existing(tmp_path):
    """Should pass for modify action when file exists."""
    test_file = tmp_path / "existing.py"
    test_file.write_text("content")
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="existing.py", action="modify")]
    result = verifier.verify(claims)
    assert result.all_pass


def test_verify_modify_missing(tmp_path):
    """Should fail for modify action when file does not exist."""
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="missing.py", action="modify")]
    result = verifier.verify(claims)
    assert not result.all_pass


def test_format_verification_table(tmp_path):
    """Should format results as a markdown table."""
    test_file = tmp_path / "test.py"
    test_file.write_text("hello")
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="test.py", action="create")]
    result = verifier.verify(claims)
    table = verifier.format_table(result)
    assert "产物验证" in table
    assert "test.py" in table
    assert "✅" in table
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_artifact_verifier.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement ArtifactVerifier**

```python
# core/artifact_verifier.py
"""Artifact Verifier — file existence and integrity verification."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ArtifactClaim:
    """A claimed file change."""
    path: str
    action: str  # "create" | "modify"


@dataclass
class ArtifactDetail:
    """Verification result for a single artifact."""
    path: str
    action: str
    exists: bool
    passed: bool
    message: str = ""


@dataclass
class VerificationResult:
    """Overall verification result."""
    all_pass: bool
    details: list[ArtifactDetail]
    passed_count: int = 0
    total_count: int = 0


class ArtifactVerifier:
    """Verifies that claimed file changes actually exist on disk."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)

    def verify(self, claims: list[ArtifactClaim]) -> VerificationResult:
        """Verify a list of artifact claims."""
        details = []
        for claim in claims:
            file_path = self.base_dir / claim.path
            exists = file_path.exists()

            if claim.action in ("create", "modify"):
                passed = exists
                message = "文件存在" if exists else f"文件不存在: {claim.path}"
            else:
                passed = True
                message = "未知操作，跳过验证"

            details.append(ArtifactDetail(
                path=claim.path,
                action=claim.action,
                exists=exists,
                passed=passed,
                message=message,
            ))

        passed_count = sum(1 for d in details if d.passed)
        return VerificationResult(
            all_pass=all(d.passed for d in details),
            details=details,
            passed_count=passed_count,
            total_count=len(details),
        )

    def format_table(self, result: VerificationResult) -> str:
        """Format verification results as a markdown table."""
        lines = ["#### 产物验证", ""]
        lines.append("| 文件 | 操作 | 存在 | 状态 |")
        lines.append("|------|------|------|------|")
        for d in result.details:
            exists_icon = "✅" if d.exists else "❌"
            status_icon = "通过" if d.passed else "失败"
            lines.append(f"| {d.path} | {d.action} | {exists_icon} | {status_icon} |")
        lines.append(f"\n产物完整性: {result.passed_count}/{result.total_count} 通过")
        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_artifact_verifier.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add core/artifact_verifier.py tests/test_artifact_verifier.py
git commit -m "feat: add ArtifactVerifier for file integrity verification"
```

---

### Task 3: Agent Dispatcher — Role Matrix and Prompt Templates

**Files:**
- Create: `core/agent_dispatcher.py`
- Create: `tests/test_agent_dispatcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent_dispatcher.py
"""Tests for AgentDispatcher — role matrix and prompt templates."""

import pytest
from reqflow.core.agent_dispatcher import AgentDispatcher, AgentRole


def test_get_agents_for_stage():
    """Should return agent list for a given stage."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("PRD理解")
    assert len(agents) >= 2
    roles = [a.role for a in agents]
    assert "research-agent" in roles
    assert "architecture-agent" in roles


def test_required_vs_optional():
    """Agents should have required flag."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("PRD理解")
    required = [a for a in agents if a.required]
    assert len(required) >= 1


def test_build_prompt():
    """Should build a complete prompt for an agent."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("PRD理解")
    prompt = dispatcher.build_prompt(
        agents[0],
        context="测试需求：写一个测试接口",
        stage_name="PRD理解",
    )
    assert agents[0].role in prompt
    assert "测试需求" in prompt
    assert "输出格式" in prompt


def test_timeout_strategy():
    """Should return timeout handling instructions."""
    dispatcher = AgentDispatcher()
    strategy = dispatcher.get_timeout_strategy()
    assert "60s" in strategy
    assert "SKIPPED" in strategy
    assert "BLOCKER" in strategy


def test_format_dispatch_plan():
    """Should format a dispatch plan for a stage."""
    dispatcher = AgentDispatcher()
    plan = dispatcher.format_dispatch_plan("PRD理解", context="测试上下文")
    assert "Agent 派遣" in plan
    assert "research-agent" in plan
    assert "Agent tool" in plan


def test_stages_without_agents():
    """Some stages should have no agents (e.g., startup)."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("启动")
    assert len(agents) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agent_dispatcher.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement AgentDispatcher**

```python
# core/agent_dispatcher.py
"""Agent Dispatcher — role matrix, prompt templates, and timeout handling."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentRole:
    """Definition of an agent's role for a specific stage."""
    role: str
    task: str
    required: bool = True
    description: str = ""


# Stage → Agent role matrix
STAGE_AGENT_MATRIX: dict[str, list[dict]] = {
    "启动": [],
    "PRD理解": [
        {"role": "research-agent", "task": "扫描仓库结构、现有接口模式、模块依赖", "required": True},
        {"role": "architecture-agent", "task": "评估架构约束、技术栈限制、分层约定", "required": True},
        {"role": "compliance-agent", "task": "检查安全约束、鉴权机制、敏感数据边界", "required": False},
    ],
    "Spec治理": [
        {"role": "research-agent", "task": "验证 spec 中引用的代码路径是否真实存在", "required": True},
        {"role": "security-agent", "task": "审查 spec 中的安全约束", "required": False},
    ],
    "工作流智能": [
        {"role": "research-agent", "task": "分析场景类型和工作项分解", "required": True},
        {"role": "architecture-agent", "task": "评估工作流设计合理性", "required": False},
    ],
    "上下文发现": [
        {"role": "research-agent", "task": "扫描仓库结构、依赖关系、接口模式", "required": True},
        {"role": "architecture-agent", "task": "评估架构约束、模块边界", "required": True},
        {"role": "security-agent", "task": "检查安全约束、鉴权机制", "required": False},
    ],
    "技术方案": [
        {"role": "architecture-agent", "task": "设计 2-3 个候选方案，对比优劣，给出推荐", "required": True},
        {"role": "test-architect-agent", "task": "设计测试策略、测试金字塔、覆盖率目标", "required": True},
        {"role": "security-agent", "task": "安全审查：注入、鉴权、数据泄露风险", "required": False},
    ],
    "实施计划": [
        {"role": "architecture-agent", "task": "评估工作项分解和依赖关系合理性", "required": True},
        {"role": "test-gen-agent", "task": "为每个工作项生成测试计划", "required": True},
    ],
    "Agent执行": [
        {"role": "implementer-agent", "task": "按 spec 实现代码", "required": True},
    ],
    "代码审查": [
        {"role": "quality-agent", "task": "代码质量审查：命名、复杂度、重复、SOLID", "required": True},
        {"role": "security-agent", "task": "安全审查：OWASP Top 10", "required": True},
    ],
    "交付验证": [
        {"role": "test-agent", "task": "执行测试、验证构建", "required": True},
    ],
    "总结": [],
    "归档": [],
}

# Prompt templates for each agent role
AGENT_PROMPT_TEMPLATES = {
    "research-agent": """你是仓库分析专家（research-agent）。你的唯一职责是扫描当前仓库并提供证据支撑。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "research-agent", "findings": ["发现1", "发现2", ...], "confidence": 0-100, "risks": ["风险1", ...]}}

禁止：
- 编造未在上下文中看到的信息
- 超出你的职责范围
- 置信度凭感觉给分（必须基于实际证据）""",

    "architecture-agent": """你是架构评审专家（architecture-agent）。你的唯一职责是评估架构和设计方案。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "architecture-agent", "findings": ["发现1", ...], "recommendations": ["建议1", ...], "confidence": 0-100, "risks": ["风险1", ...]}}

禁止：
- 只给一个方案（必须 2-3 个候选方案对比）
- 不给推荐理由
- 置信度凭感觉给分""",

    "compliance-agent": """你是合规审查专家（compliance-agent）。你的唯一职责是检查安全和合规约束。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "compliance-agent", "findings": ["发现1", ...], "violations": ["违规1", ...], "confidence": 0-100}}

禁止：
- 读取用户、税务、发票或数据库信息
- 编造合规要求""",

    "security-agent": """你是安全审查专家（security-agent）。你的唯一职责是安全审查。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "security-agent", "findings": ["发现1", ...], "severity": "high/medium/low", "confidence": 0-100}}""",

    "test-architect-agent": """你是测试架构师（test-architect-agent）。你的唯一职责是设计测试策略。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "test-architect-agent", "test_strategy": "描述", "coverage_targets": {{"unit": "80%", "integration": "60%"}}, "confidence": 0-100}}""",

    "test-agent": """你是测试执行专家（test-agent）。你的唯一职责是执行测试并验证构建。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "test-agent", "test_results": "描述", "tests_run": 0, "tests_passed": 0, "build_success": true/false, "confidence": 0-100}}""",

    "quality-agent": """你是代码质量审查专家（quality-agent）。你的唯一职责是代码质量审查。

输入上下文：
{context}

阶段任务：{task}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "quality-agent", "findings": ["发现1", ...], "metrics": {{"complexity": "low/medium/high", "duplication": "none/minimal/significant"}}, "confidence": 0-100}}""",
}

# Default template for roles without specific templates
_DEFAULT_PROMPT = """你是 {role}。你的唯一职责是 {task}。

输入上下文：
{context}

输出要求（必须严格遵守 JSON 格式）：
{{"role": "{role}", "findings": ["发现1", ...], "confidence": 0-100}}

禁止：
- 超出你的职责范围
- 编造信息
- 置信度凭感觉给分"""


class AgentDispatcher:
    """Manages agent roles, prompts, and dispatch strategies per stage."""

    def get_agents(self, stage_name: str) -> list[AgentRole]:
        """Get the list of agents for a given stage."""
        agents_data = STAGE_AGENT_MATRIX.get(stage_name, [])
        return [
            AgentRole(
                role=a["role"],
                task=a["task"],
                required=a.get("required", True),
            )
            for a in agents_data
        ]

    def build_prompt(self, agent: AgentRole, context: str, stage_name: str = "") -> str:
        """Build a complete prompt for dispatching an agent."""
        template = AGENT_PROMPT_TEMPLATES.get(agent.role, _DEFAULT_PROMPT)
        return template.format(
            role=agent.role,
            task=agent.task,
            context=context,
        )

    def get_timeout_strategy(self) -> str:
        """Return timeout handling instructions."""
        return """Agent 超时与降级策略：
- subagent 60s 无响应 → 标记 TIMEOUT，重试 1 次
- 重试仍 TIMEOUT → 标记 SKIPPED
- required agent SKIPPED → 报告 BLOCKER，等待用户决策
- optional agent SKIPPED → 继续，在报告中标注降级"""

    def format_dispatch_plan(self, stage_name: str, context: str = "") -> str:
        """Format a complete dispatch plan for a stage."""
        agents = self.get_agents(stage_name)
        if not agents:
            return f"### Agent 派遣\n\n本阶段无需派遣 agent。"

        lines = [
            "### Agent 派遣（强制执行）",
            "",
            f"本阶段必须派遣以下 agent，不得自己扮演任何角色：",
            "",
        ]

        for i, agent in enumerate(agents, 1):
            required_str = "required" if agent.required else "optional"
            lines.append(f"{i}. **{agent.role}** ({required_str})")
            lines.append(f"   - 工具: Agent tool (run_in_background=true)")
            lines.append(f"   - 任务: {agent.task}")
            lines.append(f"   - 输出格式: JSON with role, findings, confidence")
            lines.append("")

        lines.extend([
            "⛔ 不得省略任何 required agent",
            "⛔ 不得自己回答 agent 应该回答的问题",
            "⛔ 不得串行派遣——必须并行（同一条消息中多个 Agent tool call）",
            "",
            self.get_timeout_strategy(),
        ])

        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agent_dispatcher.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add core/agent_dispatcher.py tests/test_agent_dispatcher.py
git commit -m "feat: add AgentDispatcher with role matrix, prompt templates, timeout strategy"
```

---

### Task 4: Confidence.py — Add 6th Dimension

**Files:**
- Modify: `core/confidence.py`
- Modify: `tests/test_confidence.py`

- [ ] **Step 1: Add spec_compliance dimension to DEFAULT_WEIGHTS**

```python
# In core/confidence.py, change DEFAULT_WEIGHTS:
DEFAULT_WEIGHTS = {
    "completeness": 0.17,
    "consistency": 0.15,
    "accuracy": 0.18,
    "testability": 0.15,
    "risk_coverage": 0.15,
    "spec_compliance": 0.20,
}
```

- [ ] **Step 2: Add spec_compliance parameter to assess()**

```python
# In core/confidence.py, update assess() signature and body:
def assess(
    self,
    completeness: float = 0.0,
    consistency: float = 0.0,
    accuracy: float = 0.0,
    testability: float = 0.0,
    risk_coverage: float = 0.0,
    spec_compliance: float = 0.0,  # NEW
    retry_count: int = 0,
    max_retries: int = 2,
    agent_confidences: list[AgentConfidence] | None = None,
) -> ConfidenceResult:
    dimensions = [
        DimensionScore("完整性", completeness, self.DEFAULT_WEIGHTS["completeness"]),
        DimensionScore("一致性", consistency, self.DEFAULT_WEIGHTS["consistency"]),
        DimensionScore("准确性", accuracy, self.DEFAULT_WEIGHTS["accuracy"]),
        DimensionScore("可测试性", testability, self.DEFAULT_WEIGHTS["testability"]),
        DimensionScore("风险覆盖", risk_coverage, self.DEFAULT_WEIGHTS["risk_coverage"]),
        DimensionScore("Spec合规", spec_compliance, self.DEFAULT_WEIGHTS["spec_compliance"]),  # NEW
    ]
    # ... rest stays the same
```

- [ ] **Step 3: Update existing test to include spec_compliance**

```python
# In tests/test_confidence.py, update test calls to include spec_compliance
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_confidence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/confidence.py tests/test_confidence.py
git commit -m "feat: add spec_compliance as 6th confidence dimension"
```

---

### Task 5: State Manager — Add Stage Tracking Fields

**Files:**
- Modify: `core/state_manager.py`

- [ ] **Step 1: Add fields to RunState dataclass**

```python
# In core/state_manager.py, add to RunState:
@dataclass
class RunState:
    # ... existing fields ...
    current_stage_index: int = 0  # NEW: index in stages list
    steps_executed: int = 0  # NEW: total MCP tool calls executed
```

- [ ] **Step 2: Add update_stage_index method**

```python
# Add to StateManager class:
def update_stage_progress(self, stage: str, stage_index: int | None = None):
    """Update current stage and index, increment steps."""
    self.state.current_stage = stage
    if stage_index is not None:
        self.state.current_stage_index = stage_index
    self.state.steps_executed += 1
    self.save_state()
```

- [ ] **Step 3: Run existing tests**

Run: `python -m pytest tests/test_state_manager.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add core/state_manager.py
git commit -m "feat: add current_stage_index and steps_executed to RunState"
```

---

### Task 6: MCP Server — Gate Schema, Error Messages, Dashboard Fix

**Files:**
- Modify: `runner/mcp_server.py`

- [ ] **Step 1: Update reqflow_verify description with gate schemas**

```python
# In TOOLS list, update the reqflow_verify entry:
{
    "name": "reqflow_verify",
    "description": """验证质量门禁。

gate 可选值及 evidence schema:

design-gate:
  meta_spec: str (truthy) - Meta Spec 路径
  feature_spec: str (truthy) - Feature Spec 路径
  tech_plan_stages: int >= 2 - 技术方案阶段数
  completeness_checked: bool - 是否完成完备性检查

tdd-gate:
  failing_tests_count: int > 0 - 失败测试数量（必须 > 0）
  test_plan: bool (truthy) - 测试计划是否存在

completion-gate:
  build_success: bool - 构建是否成功
  tests_passing: bool - 测试是否全部通过
  spec_compliant: bool - 是否通过 Spec 合规审查
  completed_items: int - 已完成工作项数
  total_items: int - 总工作项数

compliance-report:
  verification_evidence: str (truthy) - 验证证据
  review_evidence: str (truthy) - 审查证据
  test_evidence: str (truthy) - 测试证据

若字段名或类型不匹配，返回精确错误信息。""",
    "inputSchema": { ... }  # keep existing
},
```

- [ ] **Step 2: Add _validate_evidence function**

```python
# Add before _handle_verify:
_GATE_EVIDENCE_SCHEMAS = {
    "design-gate": {
        "meta_spec": {"type": "str", "description": "Meta Spec 路径", "check": lambda v: bool(v)},
        "feature_spec": {"type": "str", "description": "Feature Spec 路径", "check": lambda v: bool(v)},
        "tech_plan_stages": {"type": "int >= 2", "description": "技术方案阶段数", "check": lambda v: isinstance(v, int) and v >= 2},
        "completeness_checked": {"type": "bool", "description": "是否完成完备性检查", "check": lambda v: isinstance(v, bool)},
    },
    "tdd-gate": {
        "failing_tests_count": {"type": "int > 0", "description": "失败测试数量", "check": lambda v: isinstance(v, (int, float)) and v > 0},
        "test_plan": {"type": "bool (truthy)", "description": "测试计划是否存在", "check": lambda v: bool(v)},
    },
    "completion-gate": {
        "build_success": {"type": "bool", "description": "构建是否成功", "check": lambda v: isinstance(v, bool)},
        "tests_passing": {"type": "bool", "description": "测试是否全部通过", "check": lambda v: isinstance(v, bool)},
        "spec_compliant": {"type": "bool", "description": "是否通过 Spec 合规审查", "check": lambda v: isinstance(v, bool)},
        "completed_items": {"type": "int", "description": "已完成工作项数", "check": lambda v: isinstance(v, int)},
        "total_items": {"type": "int", "description": "总工作项数", "check": lambda v: isinstance(v, int)},
    },
    "compliance-report": {
        "verification_evidence": {"type": "str (truthy)", "description": "验证证据", "check": lambda v: bool(v)},
        "review_evidence": {"type": "str (truthy)", "description": "审查证据", "check": lambda v: bool(v)},
        "test_evidence": {"type": "str (truthy)", "description": "测试证据", "check": lambda v: bool(v)},
    },
}


def _validate_evidence(gate: str, evidence: dict) -> str | None:
    """Validate evidence against gate schema. Returns error message or None."""
    schema = _GATE_EVIDENCE_SCHEMAS.get(gate)
    if not schema:
        return None

    missing = []
    wrong_type = []
    for field, spec in schema.items():
        if field not in evidence:
            missing.append(f"  - {field}: {spec['description']} (要求 {spec['type']})")
        elif not spec['check'](evidence[field]):
            wrong_type.append(f"  - {field}: 值 {evidence[field]} 不满足 {spec['type']}")

    if missing or wrong_type:
        parts = ["门禁未通过:"]
        if missing:
            parts.append("缺失字段:")
            parts.extend(missing)
        if wrong_type:
            parts.append("类型错误:")
            parts.extend(wrong_type)
        parts.append(f"请修正后重新调用 reqflow_verify(gate=\"{gate}\", evidence={{...}})")
        return "\n".join(parts)
    return None
```

- [ ] **Step 3: Update _handle_verify to use validation**

```python
# In _handle_verify, add validation before calling QualityGate:
async def _handle_verify(arguments: dict) -> list:
    run_id = arguments.get("run_id", "")
    gate = arguments.get("gate", "")
    evidence = arguments.get("evidence", {})

    if not run_id or not gate:
        return [TextContent(type="text", text="[错误] run_id 和 gate 不能为空。")]

    # NEW: Validate evidence against schema
    validation_error = _validate_evidence(gate, evidence)
    if validation_error:
        return [TextContent(type="text", text=validation_error)]

    # ... rest of existing logic
```

- [ ] **Step 4: Fix dashboard state sync in _handle_report**

```python
# In _handle_report, after updating state, add:
# Update stage index and steps count
stages = state.get("stages", [])
if stage in stages:
    idx = stages.index(stage)
    state["current_stage_index"] = idx
state["steps_executed"] = state.get("steps_executed", 0) + 1
```

- [ ] **Step 5: Run existing tests**

Run: `python -m pytest tests/ -v -k "mcp"`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add runner/mcp_server.py
git commit -m "feat: embed gate schemas in verify description, add evidence validation, fix dashboard state sync"
```

---

### Task 7: skill_generator.py — Agent Dispatch, Report Templates, Confirmation Panels

**Files:**
- Modify: `core/skill_generator.py`

- [ ] **Step 1: Add MCP instant output rules to _generate_global_constraints**

```python
# In _generate_global_constraints, add after the existing constraints:
constraints.extend([
    "",
    "### ⛔ MCP 即时输出规则（强制）",
    "",
    "每次调用 MCP 工具后，必须立即在对话中输出：",
    "",
    "1. **工具名 + 输入参数摘要**（一行，emoji 前缀 📡）",
    "2. **返回结果摘要**（一行，用 ✅/❌ 标记成功/失败）",
    "3. **失败时必须输出失败原因和修复计划**",
    "",
    "格式示例：",
    "  📡 reqflow_report(stage=\"PRD理解\") → ✅ 已记录",
    "  📡 reqflow_verify(gate=\"tdd-gate\") → ❌ 未通过: failing_tests_count 缺失",
    "  🔧 修复计划: 编写失败测试后重新提交",
    "",
    "⛔ 禁止：",
    "- 静默调用 MCP 工具不输出",
    "- 批量调用后统一输出",
    "- 只输出成功，隐藏失败",
])
```

- [ ] **Step 2: Add per-stage report template to _generate_standard_actions**

```python
# In _generate_standard_actions, add before step 8 (阶段确认):
lines.extend([
    "",
    "#### 8a. ⛔ 阶段报告（必须在对话中输出完整报告）",
    "",
    "**每个阶段必须输出以下完整报告结构：**",
    "",
    "```",
    "### 📋 阶段报告：{stage_name}",
    "",
    "**状态:** ✅ 完成 | ⚠️ 有警告 | ❌ 失败",
    "**耗时:** {duration}s",
    "",
    "#### 产出清单",
    "| # | 产出 | 类型 | 路径 |",
    "|---|------|------|------|",
    "| 1 | ... | 修改/新增 | ... |",
    "",
    "#### 置信度",
    "{置信度报告（Task 1 格式）}",
    "",
    "#### Agent 共识",
    "{多 agent 结果矩阵}",
    "",
    "#### MCP 执行追踪",
    "| # | 时间 | 工具 | 输入摘要 | 结果 | 耗时 |",
    "|---|------|------|----------|------|------|",
    "| 1 | ... | reqflow_report | ... | ✅ | 0.1s |",
    "",
    "#### 问题与风险",
    "| # | 级别 | 描述 | 状态 |",
    "|---|------|------|------|",
    "| 1 | ⚠️ P1 | ... | 已降级处理 |",
    "",
    "#### 趋势",
    "- 置信度: 87% ↑2 (上阶段 85%)",
    "- BLOCKER: 0 (不变)",
    "",
    "#### 下一步",
    "- 进入 {next_stage}",
    "```",
])
```

- [ ] **Step 3: Add confirmation panel templates**

```python
# Replace the existing stage confirmation section with enhanced panels:
if auto_pilot:
    lines.extend([
        "#### 9. 阶段确认（自动模式）",
        "",
        "**必须在对话中展示以下确认面板（自动选择第一选项，但仍展示）：**",
        "",
        "```",
        "### 📋 阶段确认：{stage_name}",
        "",
        "**本阶段产出:** {summary}",
        "",
        "| 选项 | 操作 | 说明 |",
        "|------|------|------|",
        "| ✅ **确认通过** | 自动进入下一阶段 | 产出已验证，继续 |",
        "| 🔄 **重新执行** | 重新运行本阶段 | 发现问题需要修正 |",
        "| ✏️ **修改需求** | 调整需求后重新分析 | 需求本身有变化 |",
        "| ⏭ **跳过** | 直接进入下一阶段 | 不推荐，可能遗漏 |",
        "",
        "⚡ 自动模式：已选择「确认通过」",
        "```",
        "",
        "- **例外：有 P0 阻塞时必须停止，等待用户决策**",
    ])
else:
    lines.extend([
        "#### 9. 阶段确认（⛔ 硬停止点）",
        "",
        "**必须在对话中展示以下确认面板，等待用户选择：**",
        "",
        "```",
        "### 📋 阶段确认：{stage_name}",
        "",
        "**本阶段产出:** {summary}",
        "",
        "| 选项 | 操作 | 说明 |",
        "|------|------|------|",
        "| ✅ **确认通过** | 进入下一阶段 | 产出已验证，继续 |",
        "| 🔄 **重新执行** | 重新运行本阶段 | 发现问题需要修正 |",
        "| ✏️ **修改需求** | 调整需求后重新分析 | 需求本身有变化 |",
        "| ⏭ **跳过** | 直接进入下一阶段 | 不推荐，可能遗漏 |",
        "```",
        "",
        "⛔ 停止，等待用户选择后才进入下一阶段。",
        "- 不得自行跳过确认点",
    ])
```

- [ ] **Step 4: Enhance completion protocol with acceptance decision panel**

```python
# In _generate_completion_protocol, replace step 3 with enhanced panel:
# Step 3: 告知用户等待验收 → 改为完整的验收决策面板
```

The enhanced panel includes:
- Artifact list table
- Quality summary
- 4 options (accept, reject, partial, pause) with consequences

- [ ] **Step 5: Add test execution strategy to delivery verification stage**

```python
# In _stage_delivery_verification, add test probe logic:
### 测试执行策略
不得假设测试命令格式。必须按以下顺序探测：
1. 首选: mvn -pl {module} -am -Dtest={TestClass} test
   - 成功 → 记录此命令
   - 失败 "No tests were executed" → 进入步骤 2
2. 降级: mvn -pl {module} -am -Dtest={TestClass} -DfailIfNoTests=false test
   - 检查 Tests run > 0 → 成功
3. 兜底: java -cp {classpath} org.junit.runner.JUnitCore {TestClass}
⚠️ 不得报告"测试通过"除非实际执行了测试且 Tests run > 0
⚠️ 必须在 evidence 中记录最终使用的测试命令
```

- [ ] **Step 6: Add cleanup strategy to archive stage**

```python
# In _stage_archive, add cleanup section:
### 产物清理
归档阶段执行:
1. 保留: .reqflow/changes/{name}/ (交付记录)
2. 清理: target/ 编译产物 (自动删除)
3. 清理: .reqflow/changes/{name}/runs/{run_id}/tmp/ (临时文件)
验收拒绝时: 保留所有中间产物用于调试
验收通过时: 自动清理编译产物，保留 .reqflow 归档
```

- [ ] **Step 7: Run existing tests**

Run: `python -m pytest tests/ -v -k "skill"`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add core/skill_generator.py
git commit -m "feat: add MCP instant output rules, per-stage report templates, confirmation panels, test strategy, cleanup"
```

---

### Task 8: SKILL.md Files — Behavior Layer Updates

**Files:**
- Modify: `skills/main-flow/SKILL.md`
- Modify: `skills/full-auto/SKILL.md`
- Modify: `skills/auto-flow/SKILL.md`
- Modify: `skills/quality-gates/SKILL.md`
- Modify: `skills/harness-orchestrator/SKILL.md`

- [ ] **Step 1: Update main-flow SKILL.md**

Add to the "执行流程" section, after "步骤 3: 逐阶段执行":

```markdown
### ⛔ MCP 即时输出规则

每次调用 MCP 工具后，必须立即在对话中输出：

1. **工具名 + 输入参数摘要**（一行，📡 前缀）
2. **返回结果摘要**（一行，用 ✅/❌ 标记）
3. **失败时输出失败原因和修复计划**

格式：
```
📡 reqflow_report(stage="PRD理解") → ✅ 已记录
📡 reqflow_verify(gate="tdd-gate") → ❌ 未通过: failing_tests_count 缺失
🔧 修复计划: 编写失败测试后重新提交
```

⛔ 禁止静默调用 MCP 工具不输出。

### ⛔ Agent 真实派遣规则

多 Agent 协作必须通过 Claude Code 的 Agent tool 真实派遣 subagent，不得自己扮演多个角色。

每个阶段的 agent 角色矩阵由 Execution Skill 定义。派遣时：
- 同一阶段的 agents 必须并行派遣（同一条消息中多个 Agent tool call）
- 每个 agent 的 prompt 必须包含：角色定义、任务描述、上下文、输出格式
- 主 agent 不得"代替"任何子 agent 回答
- 子 agent 超时或失败时，按降级策略处理

### ⛔ 阶段报告结构

每个阶段完成后必须在对话中输出完整报告：

```
### 📋 阶段报告：{stage_name}
**状态:** ✅ 完成 | ⚠️ 有警告 | ❌ 失败
#### 产出清单
#### 置信度（6 维度 + Unicode 可视化）
#### Agent 共识
#### MCP 执行追踪
#### 问题与风险
#### 趋势
#### 下一步
#### 阶段确认面板
```

### ⛔ 阶段确认面板

每个阶段结束时必须展示确认选项（auto_pilot 自动选择第一选项但仍展示）：

```
### 📋 阶段确认：{stage_name}
| 选项 | 操作 | 说明 |
|------|------|------|
| ✅ 确认通过 | 进入下一阶段 | 产出已验证 |
| 🔄 重新执行 | 重新运行本阶段 | 发现问题 |
| ✏️ 修改需求 | 调整需求后重新分析 | 需求变化 |
| ⏭ 跳过 | 直接进入下一阶段 | 不推荐 |
```

### ⛔ 验收决策面板

所有阶段完成后必须展示完整验收决策面板：

```
### 🏁 验收决策面板
**当前状态:** 全部阶段完成，等待你的验收决定。
#### 已交付产物清单
#### 质量摘要
#### 请做出决定
| 选项 | 操作 | 后续流程 |
|------|------|----------|
| ✅ 通过验收 | reqflow_accept | 归档、清理、流程结束 |
| ❌ 拒绝验收 | reqflow_reject | 修复循环（最多 3 轮） |
| 🔧 部分验收 | reqflow_accept + scope | 部分归档 |
| ⏸ 暂挂 | 不调用工具 | 保持状态 |
```
```

- [ ] **Step 2: Update full-auto SKILL.md**

Same content as main-flow but with auto_pilot-specific behavior notes.

- [ ] **Step 3: Update auto-flow SKILL.md**

Add simplified MCP trace rules and confirmation panels.

- [ ] **Step 4: Update quality-gates SKILL.md**

Add diagnostic output format for gate failures:

```markdown
### 门禁失败诊断

门禁失败时，MCP 工具返回精确的诊断信息：
- 缺失字段列表及期望类型
- 类型错误字段及实际值
- 修复建议和示例调用
```

- [ ] **Step 5: Update harness-orchestrator SKILL.md**

Add agent dispatch rules and artifact verification sections.

- [ ] **Step 6: Commit**

```bash
git add skills/
git commit -m "feat: update SKILL.md files with MCP output rules, agent dispatch, report templates, confirmation panels"
```

---

### Task 9: Sync to npm project and local codex

**Files:**
- Sync all changes to `/Users/yuanjulong/Documents/ai_flow/reqflow-npm/`
- Sync to local codex cache

- [ ] **Step 1: Copy modified files to npm project**

```bash
# Copy core Python files
cp core/confidence_tracker.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/core/
cp core/artifact_verifier.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/core/
cp core/agent_dispatcher.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/core/
cp core/confidence.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/core/
cp core/state_manager.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/core/
cp core/skill_generator.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/core/
cp runner/mcp_server.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/runner/

# Copy test files
cp tests/test_confidence_tracker.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/tests/
cp tests/test_artifact_verifier.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/tests/
cp tests/test_agent_dispatcher.py /Users/yuanjulong/Documents/ai_flow/reqflow-npm/tests/
```

- [ ] **Step 2: Sync to local codex cache**

```bash
# Sync skills to codex
cp -r skills/ ~/.codex/plugins/cache/local/reqflow/latest/skills/
```

- [ ] **Step 3: Verify npm project tests pass**

```bash
cd /Users/yuanjulong/Documents/ai_flow/reqflow-npm
python -m pytest tests/test_confidence_tracker.py tests/test_artifact_verifier.py tests/test_agent_dispatcher.py -v
```

- [ ] **Step 4: Commit npm project**

```bash
cd /Users/yuanjulong/Documents/ai_flow/reqflow-npm
git add -A
git commit -m "feat: sync V7 UX & Agent improvements from reqflow"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- ✅ Item 1 (Confidence visualization) → Task 1 (ConfidenceTracker)
- ✅ Item 2 (Stage reports) → Task 7 (skill_generator templates)
- ✅ Item 3 (Multi-agent dispatch) → Task 3 (AgentDispatcher)
- ✅ Item 4 (MCP instant output) → Task 7 (global constraints)
- ✅ Item 5 (Acceptance panels) → Task 7 (completion protocol)
- ✅ Item 6 (Agent behavior enforcement) → Task 8 (SKILL.md)
- ✅ Item 7 (Dashboard sync) → Task 6 (mcp_server fix)
- ✅ Item 8 (Agent timeout) → Task 3 (AgentDispatcher)
- ✅ Item 9 (Context bundle) → Task 7 (skill_generator)
- ✅ Item 10 (Confidence trends) → Task 1 (ConfidenceTracker)
- ✅ Item 11 (Gate diagnostics) → Task 6 (mcp_server validation)
- ✅ Item 12 (Test strategy) → Task 7 (delivery verification)
- ✅ Item 13 (Artifact verification) → Task 2 (ArtifactVerifier)
- ✅ Item 14 (Spec drift) → Task 8 (SKILL.md code review section)
- ✅ Item 15 (Gate schema in MCP) → Task 6 (verify description)
- ✅ Item 16 (Cleanup strategy) → Task 7 (archive stage)
- ✅ Item 17 (Error messages) → Task 6 (_validate_evidence)

**2. Placeholder scan:** No TBD/TODO found. All steps have concrete code.

**3. Type consistency:**
- `ConfidenceTracker` methods use consistent `float` (0-1) for scores
- `ArtifactClaim` uses `str` for path and action
- `AgentRole` uses `str` for role and task, `bool` for required
- RunState fields use `int` for indices and counts
