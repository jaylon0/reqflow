"""ReqFlow Quality Gate — 质量门禁执行器。

质量门禁是硬约束，不通过就不能进入下一阶段。
支持 V7 可配置模式：auto / human / hybrid。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class GateMode(Enum):
    """门禁模式。"""
    AUTO = "auto"      # 自动通过/重试，不等待用户
    HUMAN = "human"    # 必须人工确认
    HYBRID = "hybrid"  # 自动重试 N 次后升级到用户


@dataclass
class CheckResult:
    """单项检查结果。"""
    name: str
    passed: bool
    message: str = ""
    severity: str = "error"  # error | warning | info
    evidence: str = ""


@dataclass
class GateResult:
    """门禁检查结果。"""
    gate: str
    passed: bool
    mode: GateMode = GateMode.HYBRID
    retry_count: int = 0
    max_retries: int = 3
    details: list[CheckResult] = field(default_factory=list)
    blocking_items: list[CheckResult] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    summary: str = ""
    action: str = "proceed"  # proceed | retry | escalate | pause


# 门禁定义
DESIGN_GATE_CHECKS = [
    {
        "name": "meta_spec_exists",
        "description": "Meta Spec 是否定义了系统级约束？",
        "check": lambda ctx: bool(ctx.get("meta_spec")),
    },
    {
        "name": "feature_spec_delta",
        "description": "Feature Spec 是否描述了 Delta 变化？",
        "check": lambda ctx: bool(ctx.get("feature_spec")),
    },
    {
        "name": "tech_plan_stages",
        "description": "技术方案是否包含多阶段规划？",
        "check": lambda ctx: ctx.get("tech_plan_stages", 0) >= 2,
    },
    {
        "name": "completeness_check",
        "description": "是否进行了完备性检查？",
        "check": lambda ctx: ctx.get("completeness_checked", False),
    },
    {
        "name": "high_risk_approved",
        "description": "所有高风险设计决策是否已获批准？",
        "check": lambda ctx: ctx.get("high_risk_approved", True),
    },
]

TDD_GATE_CHECKS = [
    {
        "name": "failing_tests_defined",
        "description": "可测试工作项是否有失败测试？",
        "check": lambda ctx: ctx.get("failing_tests_count", 0) > 0,
    },
    {
        "name": "test_plan_exists",
        "description": "测试计划是否存在？",
        "check": lambda ctx: bool(ctx.get("test_plan")),
    },
]

COMPLETION_GATE_CHECKS = [
    {
        "name": "all_work_items_done",
        "description": "所有工作项是否完成？",
        "check": lambda ctx: ctx.get("completed_items", 0) >= ctx.get("total_items", 1),
    },
    {
        "name": "tests_passing",
        "description": "测试是否全部通过？",
        "check": lambda ctx: ctx.get("tests_passing", False),
    },
    {
        "name": "spec_compliance",
        "description": "是否通过 Spec 合规审查？",
        "check": lambda ctx: ctx.get("spec_compliant", False),
    },
    {
        "name": "build_success",
        "description": "构建是否成功？",
        "check": lambda ctx: ctx.get("build_success", False),
    },
]

COMPLIANCE_REPORT_CHECKS = [
    {
        "name": "verification_evidence",
        "description": "是否有验证证据？",
        "check": lambda ctx: bool(ctx.get("verification_evidence")),
    },
    {
        "name": "review_evidence",
        "description": "是否有审查证据？",
        "check": lambda ctx: bool(ctx.get("review_evidence")),
    },
    {
        "name": "test_evidence",
        "description": "是否有测试证据？",
        "check": lambda ctx: bool(ctx.get("test_evidence")),
    },
]

# 门禁注册表
GATES: dict[str, list[dict]] = {
    "design-gate": DESIGN_GATE_CHECKS,
    "tdd-gate": TDD_GATE_CHECKS,
    "completion-gate": COMPLETION_GATE_CHECKS,
    "compliance-report": COMPLIANCE_REPORT_CHECKS,
}


class QualityGate:
    """质量门禁执行器 V7。

    支持三种模式：
    - auto: 自动通过/重试，不等待用户
    - human: 必须人工确认
    - hybrid: 自动重试 N 次后升级到用户
    """

    # V7 默认门禁模式配置
    DEFAULT_STAGE_MODES: dict[str, GateMode] = {
        "PRD理解": GateMode.HUMAN,
        "技术方案": GateMode.HUMAN,
        "交付验证": GateMode.HUMAN,
    }
    DEFAULT_MODE = GateMode.HYBRID
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        stage_modes: dict[str, str] | None = None,
        max_retries: int = 3,
    ):
        self._custom_gates: dict[str, list[dict]] = {}
        self._max_retries = max_retries

        # 合并用户配置和默认配置
        self._stage_modes: dict[str, GateMode] = dict(self.DEFAULT_STAGE_MODES)
        if stage_modes:
            for stage, mode_str in stage_modes.items():
                try:
                    self._stage_modes[stage] = GateMode(mode_str)
                except ValueError:
                    logger.warning("未知门禁模式 %s for stage %s, 使用默认", mode_str, stage)

    def get_mode(self, stage_name: str) -> GateMode:
        """获取阶段的门禁模式。"""
        return self._stage_modes.get(stage_name, self.DEFAULT_MODE)

    def register_gate(self, name: str, checks: list[dict]) -> None:
        """注册自定义门禁。"""
        self._custom_gates[name] = checks
        logger.info("注册自定义门禁: %s (%d 项检查)", name, len(checks))

    def check(
        self,
        gate_name: str,
        context: dict[str, Any],
        stage_name: str = "",
        retry_count: int = 0,
    ) -> GateResult:
        """执行门禁检查。

        Args:
            gate_name: 门禁名称
            context: 检查上下文
            stage_name: 阶段名称（用于确定模式）
            retry_count: 当前重试次数

        Returns:
            GateResult 包含检查结果和建议动作
        """
        checks = self._custom_gates.get(gate_name) or GATES.get(gate_name)
        if not checks:
            return GateResult(
                gate=gate_name,
                passed=False,
                summary=f"未知门禁: {gate_name}",
                action="escalate",
            )

        mode = self.get_mode(stage_name) if stage_name else self.DEFAULT_MODE

        results: list[CheckResult] = []
        for check_def in checks:
            name = check_def["name"]
            desc = check_def["description"]
            check_fn = check_def["check"]

            try:
                passed = check_fn(context)
                results.append(CheckResult(
                    name=name,
                    passed=passed,
                    message=desc if not passed else "",
                    severity="error" if not passed else "info",
                ))
            except Exception as e:
                results.append(CheckResult(
                    name=name,
                    passed=False,
                    message=f"检查异常: {e}",
                    severity="error",
                ))

        blocking = [r for r in results if not r.passed]
        all_passed = len(blocking) == 0

        # 生成建议
        suggestions = []
        for item in blocking:
            suggestions.append(f"修复 {item.name}: {item.message}")

        # 确定动作
        action = self._determine_action(all_passed, mode, retry_count)

        # 生成摘要
        summary_parts = []
        if all_passed:
            summary_parts.append(f"门禁 {gate_name} 通过 ({mode.value} 模式)")
        else:
            summary_parts.append(f"门禁 {gate_name} 未通过，{len(blocking)} 项阻塞 ({mode.value} 模式，重试 {retry_count}/{self._max_retries}):")
            for item in blocking:
                summary_parts.append(f"  - {item.name}: {item.message}")
            summary_parts.append(f"  建议动作: {action}")

        return GateResult(
            gate=gate_name,
            passed=all_passed,
            mode=mode,
            retry_count=retry_count,
            max_retries=self._max_retries,
            details=results,
            blocking_items=blocking,
            suggestions=suggestions,
            summary="\n".join(summary_parts),
            action=action,
        )

    def _determine_action(self, passed: bool, mode: GateMode, retry_count: int) -> str:
        """根据模式和结果确定动作。"""
        if passed:
            return "proceed"

        if mode == GateMode.AUTO:
            if retry_count < self._max_retries:
                return "retry"
            return "escalate"

        if mode == GateMode.HUMAN:
            return "pause"

        # hybrid 模式
        if retry_count < self._max_retries:
            return "retry"
        return "escalate"

    def list_gates(self) -> list[str]:
        """列出所有可用门禁。"""
        return list(GATES.keys()) + list(self._custom_gates.keys())

    def get_mode_label(self, mode: GateMode) -> str:
        """获取模式的中文标签。"""
        labels = {
            GateMode.AUTO: "自动",
            GateMode.HUMAN: "人工确认",
            GateMode.HYBRID: "混合",
        }
        return labels.get(mode, mode.value)
