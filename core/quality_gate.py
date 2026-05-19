"""ReqFlow Quality Gate — 质量门禁执行器。

质量门禁是硬约束，不通过就不能进入下一阶段。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


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
    details: list[CheckResult] = field(default_factory=list)
    blocking_items: list[CheckResult] = field(default_factory=list)
    summary: str = ""


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
    """质量门禁执行器。

    硬约束，不通过就不能进入下一阶段，无例外。
    """

    def __init__(self):
        self._custom_gates: dict[str, list[dict]] = {}

    def register_gate(self, name: str, checks: list[dict]) -> None:
        """注册自定义门禁。"""
        self._custom_gates[name] = checks
        logger.info("注册自定义门禁: %s (%d 项检查)", name, len(checks))

    def check(self, gate_name: str, context: dict[str, Any]) -> GateResult:
        """执行门禁检查。

        Args:
            gate_name: 门禁名称
            context: 检查上下文

        Returns:
            GateResult 包含检查结果
        """
        checks = self._custom_gates.get(gate_name) or GATES.get(gate_name)
        if not checks:
            return GateResult(
                gate=gate_name,
                passed=False,
                summary=f"未知门禁: {gate_name}",
            )

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

        summary_parts = []
        if all_passed:
            summary_parts.append(f"门禁 {gate_name} 通过")
        else:
            summary_parts.append(f"门禁 {gate_name} 未通过，{len(blocking)} 项阻塞:")
            for item in blocking:
                summary_parts.append(f"  - {item.name}: {item.message}")

        return GateResult(
            gate=gate_name,
            passed=all_passed,
            details=results,
            blocking_items=blocking,
            summary="\n".join(summary_parts),
        )

    def list_gates(self) -> list[str]:
        """列出所有可用门禁。"""
        return list(GATES.keys()) + list(self._custom_gates.keys())
