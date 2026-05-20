"""ReqFlow Skill Generator — Execution Skill 生成器。

Harness 的核心能力：根据需求分析结果，生成完整的 Execution Skill（执行剧本）。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .router import RoutingLevel, RoutingDecision
from .context_scanner import ProjectStructure

logger = logging.getLogger(__name__)


@dataclass
class WorkItem:
    """工作项定义。"""
    id: str
    name: str
    goal: str
    scope: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low | medium | high


@dataclass
class ExecutionSkill:
    """生成的 Execution Skill。"""
    run_id: str
    requirement: str
    routing_level: RoutingLevel
    content: str
    work_items: list[WorkItem] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    output_path: str = ""


# 阶段模板
_STAGE_TEMPLATES = {
    RoutingLevel.L0: [
        "上下文理解",
        "分析报告",
    ],
    RoutingLevel.L1: [
        "上下文理解",
        "轻量实现",
        "局部验证",
    ],
    RoutingLevel.L2: [
        "上下文理解",
        "技术方案",
        "实施计划",
        "生成代码",
        "跨模块终检",
        "总结",
    ],
    RoutingLevel.L3: [
        "PRD理解",
        "代码梳理",
        "技术方案",
        "实施计划",
        "生成代码",
        "跨模块终检",
        "总结",
    ],
}


def generate_execution_skill(
    run_id: str,
    requirement: str,
    routing: RoutingDecision,
    project_structure: ProjectStructure | None = None,
    context_info: dict[str, Any] | None = None,
    work_items: list[WorkItem] | None = None,
) -> ExecutionSkill:
    """生成 Execution Skill。

    Args:
        run_id: 运行 ID
        requirement: 需求文本
        routing: 路由决策
        project_structure: 项目结构扫描结果
        context_info: 上下文信息
        work_items: 工作项列表（L2/L3 使用）

    Returns:
        ExecutionSkill 包含完整的执行剧本
    """
    stages = _STAGE_TEMPLATES.get(routing.level, _STAGE_TEMPLATES[RoutingLevel.L2])

    sections = []
    sections.append(_generate_header(run_id, requirement, routing))
    sections.append(_generate_global_constraints(routing))
    sections.append(_generate_mcp_guide())

    for i, stage in enumerate(stages, 1):
        sections.append(_generate_stage(i, stage, routing, project_structure, context_info, work_items))

    if work_items and routing.level in (RoutingLevel.L2, RoutingLevel.L3):
        sections.append(_generate_work_item_details(work_items))

    sections.append(_generate_pause_conditions())
    sections.append(_generate_completion_protocol(run_id))

    content = "\n\n".join(sections)

    return ExecutionSkill(
        run_id=run_id,
        requirement=requirement,
        routing_level=routing.level,
        content=content,
        work_items=work_items or [],
        stages=stages,
    )


def _generate_header(
    run_id: str,
    requirement: str,
    routing: RoutingDecision,
) -> str:
    """生成 Execution Skill 头部。"""
    return f"""---
name: exec-{run_id}
description: 执行技能 — {requirement[:50]}
routing_level: {routing.level.value}
entry_point: prd
---

# Execution Skill: {requirement[:80]}

**运行 ID:** {run_id}
**路由级别:** {routing.level.value} — {routing.reason}
**置信度:** {routing.confidence:.0%}
**信号:** {', '.join(routing.signals) if routing.signals else '无'}"""


def _generate_global_constraints(routing: RoutingDecision) -> str:
    """生成全局约束。"""
    constraints = [
        "## 全局约束",
        "",
        "### ⛔ 强制执行协议（不可违反）",
        "",
        "1. **必须执行所有阶段** — 按顺序执行本文件定义的每一个阶段，不得跳过、不得提前结束",
        "2. **每阶段必须报告** — 每个阶段完成后必须调用 `reqflow_report` 报告状态",
        "3. **门禁必须验证** — 指定的门禁检查点必须调用 `reqflow_verify`，未通过则修复后重新验证",
        "4. **必须等待用户验收** — 所有阶段完成后必须停止，等待用户调用 `reqflow_accept` 或 `reqflow_reject`",
        "5. **不得自行验收** — 只有用户才能决定是否通过，Agent 不得自行调用 `reqflow_accept`",
        "",
        "### 代码与工程约束",
        "",
        "- 所有代码变更必须通过测试验证",
        "- P0 BLOCKER 全部关闭才能进入下一阶段",
        "- 大量 IO 操作必须用 subagent 隔离（保护主会话 context）",
        "- 主会话不做全量扫描，只做定向搜索，单次搜索结果限制 50 条",
        "- master 上必须先切功能分支",
        "- 单次提交尽量小，能编译过就提交，不攒代码",
        "- 使用中文与用户沟通，技术术语保持原样",
        "- 遇到 BLOCKED 状态时调用 `reqflow_status` 获取下一步指引",
    ]

    if routing.level == RoutingLevel.L3:
        constraints.extend([
            "- API/数据库/消息相关变更必须有集成测试",
            "- 安全相关变更必须经过审查",
            "- 部署相关变更必须有回滚方案",
        ])

    return "\n".join(constraints)


def _generate_mcp_guide() -> str:
    """生成 MCP 工具使用指南。"""
    return """## MCP 工具使用指南

**每个阶段必须调用的工具：**
- `reqflow_report` — 报告阶段完成（每个阶段结束时**必须**调用）
  - 参数: run_id, stage, status (done/blocked/timeout/failed), artifacts, error

**门禁检查工具：**
- `reqflow_verify` — 请求验证（门禁检查时调用）
  - 参数: run_id, gate (design-gate/tdd-gate/completion-gate/compliance-report), evidence

**用户验收工具（所有阶段完成后使用）：**
- `reqflow_accept` — 用户验收通过（**只有用户才能调用**）
- `reqflow_reject` — 用户验收拒绝（触发修复循环）

**辅助工具：**
- `reqflow_status` — 查询当前状态和下一步指引
- `reqflow_dashboard` — 展示运行面板
- `reqflow_blocker_add` — 添加 BLOCKER
- `reqflow_blocker_resolve` — 解决 BLOCKER
- `reqflow_memory_save` — 保存长期记忆
- `reqflow_memory_load` — 加载长期记忆
- `reqflow_git_check` — 检查 Git 状态"""


def _generate_stage(
    index: int,
    stage_name: str,
    routing: RoutingDecision,
    project_structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """生成单个阶段的内容。"""
    stage_generators = {
        "上下文理解": _stage_context,
        "PRD理解": _stage_prd,
        "代码梳理": _stage_code_discovery,
        "技术方案": _stage_tech_plan,
        "实施计划": _stage_impl_plan,
        "生成代码": _stage_coding,
        "跨模块终检": _stage_cross_review,
        "总结": _stage_summary,
        "设计": _stage_design,
        "实现": _stage_implementation,
        "代码审查": _stage_review,
        "交付验证": _stage_verification,
        "归档": _stage_archive,
        "分析报告": _stage_analysis,
        "轻量实现": _stage_light_impl,
        "局部验证": _stage_local_verify,
    }

    generator = stage_generators.get(stage_name, _stage_generic)
    return generator(index, stage_name, routing, project_structure, context_info, work_items)


def _stage_context(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """上下文理解阶段。"""
    lines = [
        f"## 阶段 {index}: {name}",
        "",
        "### 1.1 项目结构扫描",
        "- 执行脚本优先的结构提取",
        "- 识别项目类型、技术栈、目录结构",
    ]

    if structure:
        lines.extend([
            f"- 项目根目录: `{structure.root}`",
            f"- 主要语言: {', '.join(structure.languages.keys()) if structure.languages else '未知'}",
            f"- 入口文件: {', '.join(structure.entry_points[:5]) if structure.entry_points else '未发现'}",
            f"- 测试框架: {structure.test_framework or '未检测到'}",
            f"- 构建系统: {structure.build_system or '未检测到'}",
        ])

    lines.extend([
        "",
        "### 1.2 代码语义分析",
        "- 基于结构提取结果，进行语义丰富",
        "- 深度调用链追踪（入口 → 服务 → 数据 → 外部）",
        "- 影响面分析",
        "",
        "### 1.3 完备性检查",
        "- 上下文是否覆盖需求涉及的所有模块？",
        "- 是否遗漏关键依赖？",
        "- 如果不完备，补充扫描",
        "",
        "### 1.4 报告",
        "- 调用 `reqflow_report` 报告上下文理解完成",
        "- 产出: 上下文发现报告",
    ])

    return "\n".join(lines)


def _stage_design(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """设计阶段。"""
    return f"""## 阶段 {index}: {name}

### 2.1 Meta Spec（元规格）
- 定义系统级约束和架构原则
- 一次定义，多次复用

### 2.2 Feature Spec（功能规格）
- 基于 Meta Spec，定义具体功能规格
- Delta 模式：描述对现有系统的变化
- 使用 ADDED/MODIFIED/REMOVED/RENAMED 格式

### 2.3 技术方案
- 3-5 阶段规划（粗粒度 → 细粒度）
- 定义接口、数据流、异常处理
- 8 步研究协议（如果遇到未知领域）

### 2.4 设计门禁
- 调用 `reqflow_verify --gate design-gate`
- 门禁不通过 → 回到 2.2 重新设计
- 门禁通过 → 进入下一阶段"""


def _stage_impl_plan(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """实现计划阶段。"""
    return f"""## 阶段 {index}: {name}

### 3.1 工作项分解
- 基于层次的工作项分解（API → Service → DAO → Test）
- 每个工作项包含: 目标、范围、验收标准、依赖

### 3.2 TDD 门禁
- 为可测试的工作项定义失败测试
- 调用 `reqflow_verify --gate tdd-gate`
- 门禁通过 → 进入实现阶段"""


def _stage_implementation(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """实现阶段。"""
    lines = [
        f"## 阶段 {index}: {name}",
        "",
        "### 4.1 工作项执行",
        "按工作项顺序执行，每个工作项的流程：",
        "",
        "1. 编写失败测试",
        "2. 实现最小代码使测试通过",
        "3. 运行测试验证",
        "4. 重构（如果需要）",
        "5. 调用 `reqflow_report` 报告完成",
        "",
    ]

    if work_items:
        lines.append("### 4.2 工作项列表")
        lines.append("")
        for wi in work_items:
            lines.append(f"#### 工作项: {wi.id}")
            lines.append(f"- 目标: {wi.goal}")
            if wi.scope:
                lines.append(f"- 范围: {', '.join(wi.scope)}")
            if wi.acceptance_criteria:
                lines.append(f"- 验收标准:")
                for ac in wi.acceptance_criteria:
                    lines.append(f"  - {ac}")
            lines.append("")

    lines.extend([
        "### 4.3 循环修复（如果需要）",
        "- 如果实现失败，进入循环引擎:",
        "  observe → classify → localize → patch → verify → review → decide",
        "- 最多 3 轮修复",
        "- 3 次尝试规则：同一问题失败 3 次 → 升级到用户",
    ])

    return "\n".join(lines)


def _stage_review(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """代码审查阶段。"""
    return f"""## 阶段 {index}: {name}

### 5.1 Spec 合规审查
- 审查实现是否符合规格
- 不信任实现者的报告，独立验证
- 检查：是否有遗漏需求？是否有额外不需要的工作？

### 5.2 代码质量审查
- 代码质量、文件职责、分解合理性
- 仅在 spec 合规通过后执行

### 5.3 完成门禁
- 调用 `reqflow_verify --gate completion-gate`
- 门禁通过 → 进入交付验证"""


def _stage_verification(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """交付验证阶段。"""
    return f"""## 阶段 {index}: {name}

### 6.1 构建验证
- 运行构建命令，验证成功

### 6.2 测试验证
- 运行测试套件，验证全部通过

### 6.3 合规报告
- 汇总所有验证证据
- 调用 `reqflow_verify --gate compliance-report`
- 状态: PASS / CONDITIONAL PASS / FAIL / BLOCKED"""


def _stage_archive(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """归档阶段。"""
    return f"""## 阶段 {index}: {name}

### 7.1 用户验收
- 调用 `reqflow_accept` 或 `reqflow_reject`
- 用户验收通过 → 归档
- 用户拒绝 → 回到阶段 4 修复

### 7.2 归档
- 记录经验教训
- 生成演进提案
- 更新知识库"""


def _stage_analysis(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """分析报告阶段（L0）。"""
    return f"""## 阶段 {index}: {name}

### 分析任务
- 理解需求上下文
- 分析影响面
- 识别风险和约束
- 输出分析报告和建议

### 报告
- 调用 `reqflow_report` 报告分析完成
- 产出: 分析报告"""


def _stage_light_impl(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """轻量实现阶段（L1）。"""
    return f"""## 阶段 {index}: {name}

### 实现任务
- 直接实现代码变更
- 编写或更新相关测试
- 运行测试验证

### 报告
- 调用 `reqflow_report` 报告实现完成"""


def _stage_local_verify(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """局部验证阶段（L1）。"""
    return f"""## 阶段 {index}: {name}

### 验证任务
- 运行相关测试
- 验证变更正确性
- 检查是否引入回归

### 报告
- 调用 `reqflow_verify --gate completion-gate`
- 调用 `reqflow_report` 报告验证完成"""


def _stage_generic(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """通用阶段模板。"""
    return f"""## 阶段 {index}: {name}

### 任务
- 执行 {name} 相关任务
- 完成后调用 `reqflow_report` 报告状态"""



def _stage_prd(index, name, routing, structure, context_info, work_items):
    """PRD 理解阶段（V3）。"""
    return f"""## 阶段 {index}: {name}

### 1.1 PRD 交叉校验
- 更新记录与正文冲突时，以更新记录为准
- 数据字段级理解（用户ID/数据量）

### 1.2 后端逻辑聚焦
- 只关注后端逻辑：触发时机/数据流向/业务规则/边界条件/写操作
- 不做 UI 交互假设，遇到 UI 描述不扩展
- 前后边界对齐：标记【待确认/待前后端分工】

### 1.3 图片处理
- 优先向用户要图片读取
- 大量图片按配额使用 subagent 处理（节省 token）
- 图片中的数据流/架构图必须提取为文字描述

### 1.4 BLOCKER 三级管理
- P0: 必须人工决策，不能继续
- P1: 已解决/不影响继续，记录但不阻塞
- P2: 仅记录，后续处理
- 调用 `reqflow_report` 报告时必须包含 BLOCKER 清单

### 1.5 报告
- 调用 `reqflow_report` 报告完成
- 产出: 01_prd_summary.md"""


def _stage_code_discovery(index, name, routing, structure, context_info, work_items):
    """代码梳理阶段（V3）。"""
    return f"""## 阶段 {index}: {name}

### 2.1 Context 保护扫描
- **必须用 subagent 执行**（保护主会话 context）
- 轻量级扫描接口入口 → 建立提问词 → 深度定向搜索
- **严禁全量扫描**
- 单次搜索结果限制 50 条

### 2.2 代码发现
- 记录高频接口/中间件/同一类对象/统一错误码
- 功能点标注改造点（新增/改造/复用）
- 客观评价不主观臆断

### 2.3 报告
- 调用 `reqflow_report` 报告完成
- 产出: 02_code_discovery.md"""


def _stage_tech_plan(index, name, routing, structure, context_info, work_items):
    """技术方案阶段（V3）。"""
    return f"""## 阶段 {index}: {name}

### 3.1 方案模板
- 按模板组织内容，不自选章节
- 覆盖 QPS/分桶/缓存/存储/降级选型

### 3.2 方案决策点
- 均明确则跳过，否则讨论 2-3 方案并给出推荐
- 数据操作必须明确落地方案（唯一索引/业务key/Redis策略等）

### 3.3 兼容性与稳定性
- 兼容现有系统，不破坏现有能力
- 稳定性模型：关键依赖的降级/限流/超时方案全覆盖

### 3.4 特性开关
- 新功能必须用特性开关控制放量和回滚
- 开关配置必须纳入联调 Checklist

### 3.5 强制卡点
- 技术方案需人工确认（覆盖所有决策点）
- 未确认禁止生成任何代码

### 3.6 报告
- 调用 `reqflow_report` 报告完成
- 产出: 03_tech_plan.md"""


def _stage_coding(index, name, routing, structure, context_info, work_items):
    """生成代码阶段 — 模块级 8 步循环（V3）。"""
    lines = [
        f"## 阶段 {index}: {name}（模块级 8 步循环）",
        "",
        "对每个模块执行以下 8 步循环：",
        "",
        "### 模块: <module-name>",
        "",
        "| 步骤 | 阶段 | 执行要求 |",
        "|------|------|----------|",
        "| 0 | 准备 | 仓库列表对齐 |",
        "| 1 | 建组件 | 调用 common-components |",
        "| 2 | 生成 | 调用 coding-standards |",
        "| 3 | 验收自检 | 调用 pitfall 功能与实现交叉验证 |",
        "| 4 | Review | 提交给用户，+1 确认后才开启下一个模块 |",
        "| 5 | 人确认 | 校验自测结果 |",
        "| 6 | 提交 | commit msg 统一管理 |",
        "| 7 | 更新 state | 更新 completed_modules |",
        "",
        "### 强制卡点",
        "- 每模块需人工确认通过后才能进入下一个模块",
        "- 禁止修改无关逻辑",
        "- 已完成模块禁止重新生成",
        "- 新增逻辑必须用特性开关包裹",
        "- 全路径埋点：写操作/开关分支/频控拦截必须有打点",
        "- 埋点缺失视为 P1 BLOCKER",
        "",
        "### Git 规则",
        "- master 上必须先切功能分支",
        "- 单次提交尽量小，能编译过就提交",
        "- BLOCKER 修复后单独 commit（不与编码提交交叉）",
        "",
        "### 报告",
        "- 每个模块完成后调用 `reqflow_report`",
        "- 产出: 05_coding.md",
    ]
    if work_items:
        lines.append("")
        lines.append("### 工作项列表")
        for wi in work_items:
            lines.append(f"- **{wi.id}**: {wi.name} — {wi.goal}")
    return "\n".join(lines)


def _stage_cross_review(index, name, routing, structure, context_info, work_items):
    """跨模块终检阶段（V3）。"""
    return f"""## 阶段 {index}: {name}

### 6.1 跨模块 Review
- **不看增量只做跨模块 Review**，从最终视角校验
- 接口契约一致性：所有入口两边对齐，公共枚举定义唯一
- 整体依赖开关：存/写/读 + 旁路

### 6.2 影响评估
- 修改方法是否有依赖/调用方？
- 新 DB/缓存 key 是否兼容旧数据？
- 上下游服务是否受影响？

### 6.3 BLOCKER 处理
- BLOCKER 修复后单独 commit（不与编码提交交叉）
- 修复后重给清单
- 有 BLOCKER → 修复 + commit + 重给清单
- 无 BLOCKER → 人工确认后继续

### 6.4 报告
- 调用 `reqflow_verify --gate completion-gate`
- 产出: 06_code_review.md"""


def _stage_summary(index, name, routing, structure, context_info, work_items):
    """总结阶段（V3）。"""
    return f"""## 阶段 {index}: {name}

### 7.1 确认无未提交代码
- 调用 `reqflow_git_check` 检查 Git 状态

### 7.2 全流程汇总
- 调用 `reqflow_memory_load` 加载 memory.md
- 还原每步方案和关键决策

### 7.3 生成清单
- 配置清单（特性开关/KConf 等）
- 验收标准汇总
- 联调 Checklist

### 7.4 归档
- 归档永久文档可回溯
- 确认是否还有遗留问题

### 7.5 报告
- 调用 `reqflow_report` 报告完成
- 产出: 99_summary.md"""


def _generate_work_item_details(work_items: list[WorkItem]) -> str:
    """生成工作项详细信息。"""
    lines = ["## 工作项详细信息", ""]

    for wi in work_items:
        lines.append(f"### {wi.id}: {wi.name}")
        lines.append(f"- **目标:** {wi.goal}")
        lines.append(f"- **复杂度:** {wi.estimated_complexity}")
        if wi.scope:
            lines.append(f"- **范围:**")
            for s in wi.scope:
                lines.append(f"  - `{s}`")
        if wi.acceptance_criteria:
            lines.append(f"- **验收标准:**")
            for ac in wi.acceptance_criteria:
                lines.append(f"  - {ac}")
        if wi.dependencies:
            lines.append(f"- **依赖:** {', '.join(wi.dependencies)}")
        lines.append("")

    return "\n".join(lines)


def _generate_pause_conditions() -> str:
    """生成暂停条件。"""
    return """## 暂停条件

以下情况必须暂停执行并等待用户决策：

1. **P0 BLOCKER 未关闭** — 暂停等待人工决策
2. **Context 接近溢出** — 暂停并清理
3. **3 次尝试失败** — 暂停并升级到用户
4. **人工确认点** — 暂停等待确认
5. **任务不明确** — 暂停并询问用户
6. **实现揭示设计问题** — 暂停并建议更新设计

暂停时输出格式：

```
## 执行暂停
**进度:** X/Y 工作项完成

### 遇到的问题
<问题描述>

**选项:**
1. <选项 1>
2. <选项 2>
3. 其他方案

请选择下一步操作？
```"""


def _generate_completion_protocol(run_id: str) -> str:
    """生成强制验收协议 — Agent 必须在此停止等待用户验收。"""
    return f"""## ⛔ 强制验收协议

> **所有阶段完成后，Agent 必须执行以下协议。违反即为流程失败。**

### 步骤 1: 展示完成状态

调用 `reqflow_dashboard` 展示运行面板：
```
reqflow_dashboard(run_dir=".reqflow/runs/{run_id}")
```

### 步骤 2: 汇总产出物

列出所有已完成阶段和产出物：
- 每个阶段的名称和状态
- 关键产出物文件路径
- 测试结果摘要
- 构建结果摘要

### 步骤 3: 告知用户等待验收

**必须向用户输出以下内容：**

```
所有阶段已完成，请验收。

- 通过验收：调用 reqflow_accept(run_id="{run_id}")
- 拒绝验收：调用 reqflow_reject(run_id="{run_id}", reason="拒绝原因")
```

### 步骤 4: 强制停止

**⛔ 在收到用户的验收决定之前，Agent 不得：**
- 自行调用 `reqflow_accept`
- 结束会话
- 执行任何其他操作
- 声称"已完成"或"已交付"

**只有用户才能决定是否通过验收。**"""


def save_execution_skill(skill: ExecutionSkill, run_dir: str) -> str:
    """保存 Execution Skill 到文件。

    Args:
        skill: ExecutionSkill 对象
        run_dir: 运行目录

    Returns:
        保存的文件路径
    """
    output_path = os.path.join(run_dir, "exec-skill.md")
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(skill.content)

    skill.output_path = output_path
    logger.info("Execution Skill 已保存: %s", output_path)
    return output_path
