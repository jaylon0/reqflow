"""ReqFlow Router — 路由分析器，根据需求和项目上下文决定执行级别。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RoutingLevel(Enum):
    """路由级别。"""
    L0 = "analyze_only"      # 只读分析
    L1 = "light_change"      # 轻量修改
    L2 = "planned_change"    # 计划性修改
    L3 = "delivery_loop"     # 交付循环


class EntryPoint(Enum):
    """入口点类型。"""
    PRD = "prd"              # 从 PRD 开始完整流程
    TECH_PLAN = "tech_plan"  # 从技术方案开始（跳过 PRD 理解）
    RESUME = "resume"         # 从断点恢复


@dataclass
class RoutingDecision:
    """路由决策结果。"""
    level: RoutingLevel
    reason: str
    confidence: float = 1.0
    signals: list[str] = field(default_factory=list)
    suggested_workflow: str = "main-flow"
    entry_point: EntryPoint = EntryPoint.PRD


@dataclass
class ProjectContext:
    """项目上下文信息。"""
    languages: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_ci: bool = False
    entry_points: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    directory_tree: dict[str, Any] = field(default_factory=dict)


# 关键词模式
_ANALYSIS_KEYWORDS = [
    "分析", "评估", "解释", "说明", "查看", "了解", "inspect", "analyze",
    "assess", "explain", "understand", "review", "audit",
]

_LIGHT_CHANGE_KEYWORDS = [
    "修复", "修改", "调整", "更正", "fix", "patch", "tweak", "update",
    "rename", "refactor", "cleanup", "清理",
]

_API_CONTRACT_KEYWORDS = [
    "api", "接口", "endpoint", "controller", "路由", "route",
    "数据库", "database", "dao", "mapper", "query", "sql",
    "消息", "message", "queue", "mq", "kafka", "rabbitmq",
    "缓存", "cache", "redis",
    "认证", "auth", "login", "token", "jwt", "oauth",
    "部署", "deploy", "release", "publish", "ci", "cd",
    "安全", "security", "permission", "role",
]


def detect_entry_point(
    requirement: str,
    run_id: str | None = None,
) -> EntryPoint:
    """检测入口点类型。

    Args:
        requirement: 需求文本或 PRD 内容
        run_id: 已有 run_id 表示断点恢复

    Returns:
        EntryPoint 入口点类型
    """
    if run_id:
        return EntryPoint.RESUME

    req_lower = requirement.lower()

    # 技术方案关键词
    tech_plan_keywords = [
        "技术方案", "tech plan", "technical design",
        "实施方案", "架构设计", "technical plan",
    ]
    if any(kw in req_lower for kw in tech_plan_keywords):
        return EntryPoint.TECH_PLAN

    return EntryPoint.PRD


def route_requirement(
    requirement: str,
    context: ProjectContext | None = None,
) -> RoutingDecision:
    """根据需求内容和项目上下文决定路由级别。

    Args:
        requirement: 需求文本
        context: 项目上下文（可选）

    Returns:
        RoutingDecision 包含路由级别、原因和信号
    """
    signals: list[str] = []
    req_lower = requirement.lower()

    # L0: 只读分析
    analysis_score = sum(1 for kw in _ANALYSIS_KEYWORDS if kw in req_lower)
    if analysis_score >= 2:
        signals.append(f"分析关键词命中 {analysis_score} 个")
        ep = detect_entry_point(requirement)
        return RoutingDecision(
            level=RoutingLevel.L0,
            reason="需求为分析/评估类请求",
            confidence=0.9,
            signals=signals,
            suggested_workflow="flow",
            entry_point=ep,
        )

    # L3: 交付循环 — API/DB/消息/安全/部署相关
    api_score = sum(1 for kw in _API_CONTRACT_KEYWORDS if kw in req_lower)
    if api_score >= 2:
        signals.append(f"API/基础设施关键词命中 {api_score} 个")
        ep = detect_entry_point(requirement)
        return RoutingDecision(
            level=RoutingLevel.L3,
            reason="需求涉及 API/数据库/消息/安全/部署等外部可见变更",
            confidence=0.85,
            signals=signals,
            suggested_workflow="main-flow",
            entry_point=ep,
        )

    # L1: 轻量修改 — 简单修复
    light_score = sum(1 for kw in _LIGHT_CHANGE_KEYWORDS if kw in req_lower)
    # 检查是否是单文件修改的描述
    single_file_hints = ["单个文件", "一个文件", "single file", "one file"]
    is_single_file = any(hint in req_lower for hint in single_file_hints)

    if light_score >= 1 and is_single_file:
        signals.append(f"轻量修改关键词命中 {light_score} 个，单文件提示")
        ep = detect_entry_point(requirement)
        return RoutingDecision(
            level=RoutingLevel.L1,
            reason="需求为单文件低风险修改",
            confidence=0.8,
            signals=signals,
            suggested_workflow="flow",
            entry_point=ep,
        )

    # L2: 计划性修改 — 多文件功能开发
    multi_file_hints = ["多个文件", "功能", "模块", "feature", "module", "component"]
    is_multi_file = any(hint in req_lower for hint in multi_file_hints)

    if is_multi_file or (light_score >= 1 and not is_single_file):
        signals.append("多文件/功能开发特征")
        ep = detect_entry_point(requirement)
        return RoutingDecision(
            level=RoutingLevel.L2,
            reason="需求为多文件功能开发，需要计划",
            confidence=0.75,
            signals=signals,
            suggested_workflow="main-flow",
            entry_point=ep,
        )

    # 默认 L2 — 安全起见，走计划流程
    signals.append("未匹配明确模式，默认走计划流程")

    # 检测入口点
    ep = detect_entry_point(requirement)

    return RoutingDecision(
        level=RoutingLevel.L2,
        reason="需求未匹配明确模式，默认走计划性修改流程",
        confidence=0.6,
        signals=signals,
        suggested_workflow="main-flow",
        entry_point=ep,
    )
