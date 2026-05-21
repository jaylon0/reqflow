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


# 阶段模板 — 对齐 main-flow.yaml 的 11 阶段管线
# Stage 0: 启动  Stage 1: PRD理解  Stage 2: Spec治理  Stage 3: 工作流智能
# Stage 4: 上下文发现  Stage 5: 技术方案  Stage 6: 实施计划
# Stage 7: Agent执行  Stage 8: 代码审查  Stage 9: 交付验证  Stage 10: 归档
_STAGE_TEMPLATES = {
    RoutingLevel.L0: [
        "启动",
        "PRD理解",
        "上下文发现",
        "分析报告",
        "归档",
    ],
    RoutingLevel.L1: [
        "启动",
        "PRD理解",
        "上下文发现",
        "轻量实现",
        "局部验证",
        "归档",
    ],
    RoutingLevel.L2: [
        "启动",
        "PRD理解",
        "上下文发现",
        "技术方案",
        "实施计划",
        "Agent执行",
        "代码审查",
        "交付验证",
        "归档",
    ],
    RoutingLevel.L3: [
        "启动",
        "PRD理解",
        "Spec治理",
        "工作流智能",
        "上下文发现",
        "技术方案",
        "实施计划",
        "Agent执行",
        "代码审查",
        "交付验证",
        "归档",
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
        "",
        "### 执行流畅性约束",
        "",
        "- **减少用户中断** — 只在关键决策点（Spec 治理确认、技术方案确认、人工确认点）暂停等待用户",
        "- **MCP 工具自动执行** — reqflow_* 系列工具应自动执行，不弹出权限确认",
        "- **批量操作** — 文件读写、测试运行、构建命令等日常操作不要逐个询问用户",
        "- **自主决策** — 对于低风险操作（格式化代码、运行测试、生成文档），直接执行不等待确认",
        "",
        "### Subagent 协调约束",
        "",
        "- Agent 执行阶段使用多智能体模式：dev-agent → verify-agent + review-agent（并行）",
        "- dev-agent 使用 acceptEdits 权限模式",
        "- verify-agent 和 review-agent 并行执行，互不阻塞",
        "- 模型选择：复杂任务用 opus，标准任务用 sonnet",
        "",
        "### Loop Engine 约束",
        "",
        "- 修复循环状态机: observe → classify → localize → patch → verify → review → decide",
        "- 最多 3 轮修复",
        "- 同一问题指纹出现两次 → 升级到用户",
        "- 修复需要修改授权模块外的文件 → 升级到用户",
        "- 失败分类: code_issue / test_issue / environment_issue / requirement_unclear / external_dependency",
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

**BLOCKER 管理工具：**
- `reqflow_blocker_add` — 添加 BLOCKER（P0/P1/P2）
- `reqflow_blocker_resolve` — 解决 BLOCKER
- `reqflow_blocker_check` — 检查 BLOCKER 状态（P0 未关闭数）

**状态与记忆工具：**
- `reqflow_status` — 查询当前状态和下一步指引
- `reqflow_dashboard` — 展示运行面板（阶段状态、产出物、BLOCKER）
- `reqflow_memory_save` — 保存长期记忆（decision/constraint/naming/pattern）
- `reqflow_memory_load` — 加载长期记忆

**Git 工具：**
- `reqflow_git_check` — 检查 Git 状态（分支、未提交文件、最后提交）

**验收标准工具：**
- `reqflow_acceptance_update` — 更新验收标准状态（verified/failed/pending）

**会话工具：**
- `reqflow_session_save` — 保存会话上下文（跨轮次持久化）
- `reqflow_session_load` — 加载会话上下文

**健康检查：**
- `reqflow_health` — 检查 ReqFlow 系统健康状态"""


# 辅助 Agent 映射表 — 每阶段至少 2-3 个 agent 提升置信度
_AUXILIARY_AGENTS = {
    "启动": [],
    "PRD理解": ["research-agent", "architecture-agent"],
    "Spec治理": ["security-agent", "architecture-agent"],
    "工作流智能": ["architecture-agent", "research-agent"],
    "上下文发现": ["research-agent", "architecture-agent", "security-agent"],
    "技术方案": ["research-agent", "architecture-agent", "security-agent", "performance-agent"],
    "实施计划": ["architecture-agent", "test-gen-agent"],
    "Agent执行": ["debug-agent", "test-gen-agent"],
    "代码审查": ["security-agent", "performance-agent", "architecture-agent"],
    "交付验证": ["test-gen-agent", "security-agent"],
    "总结": ["doc-agent"],
    "归档": ["doc-agent"],
    # 旧名称兼容
    "上下文理解": ["research-agent", "architecture-agent"],
    "代码梳理": ["research-agent", "architecture-agent"],
    "生成代码": ["debug-agent", "test-gen-agent"],
    "跨模块终检": ["security-agent", "performance-agent"],
    # L0/L1 特有
    "分析报告": ["research-agent", "architecture-agent"],
    "轻量实现": ["debug-agent", "test-gen-agent"],
    "局部验证": ["test-gen-agent", "security-agent"],
}


def _generate_standard_actions(stage_name: str, routing: RoutingDecision) -> str:
    """生成阶段标准动作 — 每个阶段都有的自检、问题发现、确认点。"""
    is_deep = routing.level in (RoutingLevel.L2, RoutingLevel.L3)
    agents = _AUXILIARY_AGENTS.get(stage_name, [])

    lines = [
        "",
        "### 阶段标准动作（⛔ 强制执行，不得跳过）",
        "",
        "**完成上述任务后，必须按顺序执行以下标准动作：**",
        "",
        "#### 1. 自检",
        "- 所有必需的产出物已生成",
        "- 产出物格式符合规范",
        "- 无遗漏的关键信息",
        "- 产出内容与需求一致",
        "",
        "#### 2. 问题发现",
        "",
        "检查本阶段产出是否存在以下问题：",
        "",
        "**自修复问题（自行修复，在对话中列出）：**",
        "- 格式不规范、拼写错误、遗漏细节等小问题",
        "",
        "**需确认问题（在对话中报告给用户等待确认）：**",
        "- 与需求不一致、逻辑错误、遗漏重要场景",
        "",
        "**阻塞问题（必须与用户讨论）：**",
        "- 无法继续的技术障碍、需求歧义、外部依赖不可用",
    ]

    if agents:
        agent_names = ", ".join(f"`{a}`" for a in agents)
        lines.extend([
            "",
            "#### 3. 辅助 Agent（按需触发）",
            f"- 本阶段可用的辅助 Agent: {agent_names}",
            "- 触发条件见各 Agent 说明",
            "- 调用后在对话中展示 findings 摘要",
        ])

    lines.extend([
        "",
        "#### 4. 对话中展示摘要（⛔ 必须执行）",
        "",
        "**不能只写到文件里。必须在对话中包含以下内容：**",
        "",
        "1. **本阶段做了什么**（具体操作，不是泛泛而谈）",
        "2. **关键发现**（发现的问题、风险、机会）",
        "3. **决策和理由**（做了什么选择、为什么）",
        "4. **改进建议**（可以优化的地方）",
        "5. **置信度**（high/medium/low + 原因）",
        "6. **文件路径**（供需要详情时查看）",
        "",
        "**可视化要求：**",
        "- 使用 ASCII 表格展示对比/状态信息",
        "- 使用进度条展示完成度/置信度",
        "- 使用 Mermaid 图表展示流程/架构（如果适用）",
        "",
        "#### 5. 阶段确认（⛔ 硬停止点）",
        "- 展示本阶段产出摘要（在对话中，不是文件里）",
        "- 列出自修复问题（已修复）和需确认问题（等待确认）",
        "- 明确告知用户：「本阶段完成，请确认后继续下一步」",
        "- ⛔ **停止执行，等待用户回复**",
        "- 用户确认 → 进入下一阶段",
        "- 用户拒绝 → 询问具体问题 → 修复 → 重新展示 → 再次等待确认",
        "- **修复循环无次数上限 — 直到用户确认**",
        "",
        "#### 6. 置信度评估（⛔ 必须执行）",
        "",
        "- 评估本阶段产出的置信度（high/medium/low）",
        "- 评估维度：完整性（产出物是否齐全）、一致性（产出物是否矛盾）、准确性（是否符合需求）",
        "- 调用 `reqflow_confidence(completeness=..., consistency=..., accuracy=...)` 获取路由建议",
        "- **high** → 自动进入下一阶段，在报告中展示置信度",
        "- **medium** → 暂停，列出不确定点，等待用户判断",
        "- **low** → 自动重试（最多 2 次），仍 low 则升级到用户",
        "- low 必须说明具体原因和重试计划",
    ])

    return "\n".join(lines)


def _generate_brainstorming_section(stage_name: str, routing: RoutingDecision) -> str:
    """生成头脑风暴指令（每个阶段）。"""
    is_deep = routing.level in (RoutingLevel.L2, RoutingLevel.L3)
    if not is_deep:
        return ""

    high_value_stages = {"PRD理解", "上下文发现", "技术方案", "代码审查"}
    medium_value_stages = {"Spec治理", "工作流智能", "实施计划", "交付验证"}

    if stage_name in high_value_stages:
        mode = "panel-of-experts" if stage_name in {"技术方案", "上下文发现"} else "round-robin"
        max_rounds = 3
        value_level = "高价值"
    elif stage_name in medium_value_stages:
        mode = "critique-refine" if stage_name in {"Spec治理", "代码审查"} else "round-robin"
        max_rounds = 1
        value_level = "中价值"
    else:
        return ""

    agents = _AUXILIARY_AGENTS.get(stage_name, [])
    if not agents:
        return ""

    agent_list = ", ".join(f"`{a}`" for a in agents)

    return f"""
### 多 Agent 头脑风暴（⛔ 建议执行）

**模式:** {mode} | **轮次:** {max_rounds} | **价值级别:** {value_level}
**参与 Agent:** {agent_list}

**执行流程：**
1. 调用 `reqflow_brainstorm(mode="{mode}", agents=[...], topic="{stage_name}", context="...")`
2. 每个 agent 从专业角度发表观点
3. 记录讨论过程到 `brainstorming/{stage_name}.md`
4. 输出共识结果，作为本阶段决策参考

**如果 agent 不可用：** 降级为单 agent 模式，继续执行
"""


def _generate_requirement_inquiry(routing: RoutingDecision) -> str:
    """生成需求质询模板（PRD 阶段专用）。"""
    is_deep = routing.level in (RoutingLevel.L2, RoutingLevel.L3)
    num_questions = 5 if is_deep else 3

    return f"""### 需求质询（主动发现问题）

**读取 PRD 后，必须主动提出 {num_questions} 个关键问题：**

1. **矛盾点** — PRD 中相互矛盾的描述
2. **遗漏点** — PRD 中未涉及但应该有的内容
3. **歧义点** — 可以有多种理解的描述
4. **依赖点** — 依赖外部系统或接口的部分
5. **风险点** — 实现难度大或不确定性高的部分

**质询流程：**
1. 提出问题清单
2. 用户逐一回答
3. 根据回答修正理解
4. 生成"确认版 PRD 摘要"
5. 用户确认后才进入下一阶段

**如果 PRD 内容清晰无疑问，仍需输出：**
- "需求质询：未发现问题，PRD 内容清晰完整"
"""


def _generate_solution_comparison(routing: RoutingDecision) -> str:
    """生成方案对比模板（技术方案阶段专用）。"""
    return """### 多方案对比

**必须提出 2-3 个可行方案，每个方案评估：**

| 维度 | 说明 |
|------|------|
| 实现复杂度 | 高/中/低 |
| 风险等级 | 高/中/低 |
| 可扩展性 | 好/一般/差 |
| 兼容性 | 与现有系统的兼容程度 |
| 性能 | 预期性能表现 |
| 维护性 | 后期维护的难度和成本 |

**方案对比矩阵示例：**

| 维度 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| 实现复杂度 | 低 | 中 | 高 |
| 风险等级 | 低 | 中 | 高 |
| 可扩展性 | 差 | 好 | 好 |
| 兼容性 | 好 | 一般 | 差 |

**必须给出：**
- 推荐方案及理由
- 每个方案的风险和缓解措施
- 用户选择方案后，再细化具体设计
"""


def _generate_deep_context_analysis() -> str:
    """生成深度上下文分析模板（L2/L3 上下文发现阶段专用）。"""
    return """### 深度上下文分析（L2/L3 模式）

**除基础结构分析外，还需完成以下深度分析：**

#### 语义分析
- 模块职责：每个模块的核心职责是什么
- 业务流程：关键业务流程的含义和流转
- 领域概念：核心领域概念和术语定义

#### 调用链分析
- 入口→服务→数据→外部依赖的完整链路
- 每个环节的输入输出
- 异常处理和降级路径

#### 复用分析
- 哪些现有代码可以复用
- 推荐复用路径
- 复用的风险和注意事项

#### 缺口标记
- 哪些关键路径未覆盖
- 风险点在哪
- 需要补充的上下文
"""


def _generate_module_confirmation() -> str:
    """生成模块级确认模板（Agent 执行阶段专用）。"""
    return """### 关键模块确认

**关键模块完成后，必须展示给用户确认：**

1. 展示模块完成情况
   - 实现了什么
   - 发现了什么问题
   - 如何解决的
2. 用户可以提出修改意见
3. 修改意见触发模块级修复循环
4. 修复后重新展示，再次确认

**关键模块定义：**
- 数据库 schema 变更
- 核心业务逻辑
- 安全相关代码
- 跨模块接口

**非关键模块：** 完成后记录到报告，不暂停等待确认
"""


def _generate_review_enhancement() -> str:
    """生成审查增强模板（代码审查阶段专用）。"""
    return """### 审查发现处理

**对每个审查发现给出：**

| 字段 | 说明 |
|------|------|
| 问题描述 | 具体描述问题 |
| 影响范围 | 影响哪些模块/功能 |
| 修复建议 | 如何修复 |
| 修复优先级 | 必须修复/建议优化 |

**用户可以逐条确认或拒绝审查发现：**
- 确认 → 记录并继续
- 拒绝 → 讨论：是误报还是确实需要修复
- 讨论后达成一致 → 记录并继续
"""


def _generate_verification_enhancement() -> str:
    """生成验证增强模板（交付验证阶段专用）。"""
    return """### 验证失败处理

**验证失败时：**
1. Agent 分析失败原因
2. 给出修复方案
3. 用户确认修复方案
4. Agent 执行修复
5. 重新验证，展示对比：修复前 vs 修复后

**验证通过后：**
- 生成完整验证报告
- 列出所有验证项和结果
- 标注已知的限制和注意事项
"""


def _generate_archive_enhancement() -> str:
    """生成归档增强模板（归档阶段专用）。"""
    return """### 流程复盘

**生成流程复盘报告：**
- 哪些阶段顺利
- 哪些阶段有阻塞
- 原因分析
- 可复用的经验和模式

**演进建议：**
- 不自动应用，必须用户确认
- 包含：配置变更、skill 变更、模板变更
"""


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
        # YAML 11 阶段对齐
        "启动": _stage_startup,
        "PRD理解": _stage_prd,
        "Spec治理": _stage_spec_governance,
        "工作流智能": _stage_workflow_intelligence,
        "上下文发现": _stage_context_discovery,
        "技术方案": _stage_tech_plan,
        "实施计划": _stage_impl_plan,
        "Agent执行": _stage_agent_execution,
        "代码审查": _stage_code_review,
        "交付验证": _stage_delivery_verification,
        "归档": _stage_archive,
        # 旧名称兼容
        "上下文理解": _stage_context_discovery,
        "代码梳理": _stage_context_discovery,
        "生成代码": _stage_agent_execution,
        "跨模块终检": _stage_code_review,
        "总结": _stage_archive,
        # L0/L1 特有
        "分析报告": _stage_analysis,
        "轻量实现": _stage_light_impl,
        "局部验证": _stage_local_verify,
    }

    generator = stage_generators.get(stage_name, _stage_generic)
    stage_content = generator(index, stage_name, routing, project_structure, context_info, work_items)

    # 启动和归档阶段不加标准动作（它们有自己的特殊流程）
    skip_stages = {"启动", "归档", "总结"}
    if stage_name not in skip_stages:
        stage_content += _generate_brainstorming_section(stage_name, routing)
        stage_content += _generate_standard_actions(stage_name, routing)

    return stage_content


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
        f"## {name}",
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
    return f"""## {name}

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
    """Stage 6: Implementation Plan — 实施计划。"""
    return f"""## {name}

### 6.1 工作项分解
- 将技术方案拆分为模块级实现计划
- 确定模块顺序和依赖关系
- 每个工作项包含: 目标、范围、验收标准、依赖、复杂度
- 生成 planned_modules 列表写入 state.json

### 6.2 上下文包构建
- 为每个模块构建上下文包（context-pack）
- 包含: 相关代码文件、接口定义、测试文件、配置文件
- 确保每个工作项有独立的执行上下文

### 6.3 动态检查清单
- 根据工作项类型生成检查清单
- 包含: 代码规范、测试覆盖、安全检查、性能检查

### 6.4 TDD 门禁
- 为可测试的工作项定义失败测试
- 调用 `reqflow_verify(gate="tdd-gate")`
- 门禁通过 → 进入 Agent 执行阶段

### 6.5 人工确认点
- **⛔ 实现计划确认后才能继续**
- 展示工作项列表和依赖关系图

### 6.6 报告
- 调用 `reqflow_report` 报告完成
- 产出: 06_impl_plan.md, agent/work_items.seed.json"""


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
        f"## {name}",
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
    return f"""## {name}

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
    return f"""## {name}

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
    """Stage 10: Archive and Evolution — 归档与演进（V4）。"""
    return f"""## {name}

### 10.1 确认无未提交代码
- 调用 `reqflow_git_check` 检查 Git 状态

### 10.2 Spec 归档
- 归档 spec 变更到项目持久 spec
- 确认是否还有遗留问题

### 10.3 文档生成（按需）
- 调用 `doc-agent` 生成和更新文档
- 触发条件：代码变更涉及公共 API
- 输出：文档更新内容

{_generate_archive_enhancement()}

### 10.5 演进提案
- 生成演进建议（memory/skill/template/配置变更）
- **⛔ 演进提案不自动应用**，需用户确认

### 10.6 全流程汇总
- 调用 `reqflow_memory_load` 加载 memory.md
- 还原每步方案和关键决策
- 生成配置清单、验收标准汇总、联调 Checklist

### 10.7 归档
- 归档永久文档可回溯
- 更新项目文档和知识库
- 生成运行总结

### 10.8 报告
- 调用 `reqflow_report` 报告完成
- 产出: 10_archive.md"""


def _stage_analysis(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """分析报告阶段（L0）。"""
    return f"""## {name}

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
    return f"""## {name}

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
    return f"""## {name}

### 验证任务
- 运行相关测试
- 验证变更正确性
- 检查是否引入回归

### 报告
- 调用 `reqflow_verify --gate completion-gate`
- 调用 `reqflow_report` 报告验证完成"""


def _stage_startup(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 0: 启动或恢复运行。"""
    return f"""## {name}

### 0.1 初始化运行环境
- 生成 run-id，创建 `.reqflow/runs/<run-id>/` 目录
- 初始化 state.json 和 memory.md
- 如果是恢复运行，读取已有 state.json 确定断点

### 0.2 Git 状态检查
- 调用 `reqflow_git_check` 检查当前分支状态
- 如果在 master/main 上，必须先切功能分支
- 记录未提交文件状态

### 0.3 报告
- 调用 `reqflow_report` 报告启动完成
- 产出: state.json, memory.md"""


def _stage_spec_governance(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 2: Spec Governance — 规格治理。"""
    return f"""## {name}

### 2.1 Spec Delta 分析
- 将需求映射到 spec 变更
- 使用 ADDED/MODIFIED/REMOVED/RENAMED 格式描述变更
- 持久行为变更需要用户审批

### 2.2 Constitution Check（合规检查）
- 检查变更是否符合项目宪法（架构原则、编码规范）
- 安全相关变更必须经过审查
- API/数据库/消息相关变更必须有集成测试计划

### 2.3 人工确认点
- **⛔ spec delta 变更持久行为时必须停止等待用户确认**
- 未确认禁止进入下一阶段

### 2.4 报告
- 调用 `reqflow_report` 报告完成
- 产出: 02_spec_delta.md"""


def _stage_workflow_intelligence(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 3: Workflow Intelligence — 工作流智能。"""
    return f"""## {name}

### 3.1 场景检测
- 分析需求场景类型（新功能/重构/bugfix/性能优化）
- 置信度 < 0.7 时请用户确认
- 生成场景画像（scenario.json）

### 3.2 工作项分解
- 基于场景画像，分解工作项
- 每个工作项包含: 目标、范围、验收标准、依赖、复杂度
- 生成 work_items.seed.json

### 3.3 动态检查清单
- 根据场景类型生成检查清单
- 包含技术差距检查: 流量/容量、幂等性、发布策略、稳定性、前后端边界

### 3.4 合规与演进
- 生成合规报告
- 生成演进提案（不自动应用）

### 3.5 报告
- 调用 `reqflow_report` 报告完成
- 产出: 03_workflow_intelligence.md, agent/scenario.json, agent/work_items.seed.json"""


def _stage_context_discovery(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 4: Context Discovery — 上下文发现（替代旧的上下文理解/代码梳理）。"""
    lines = [
        f"## {name}",
        "",
        "### 4.1 Context 保护扫描",
        "- **必须用 subagent 执行**（保护主会话 context）",
        "- 轻量级扫描接口入口 → 建立提问词 → 深度定向搜索",
        "- **严禁全量扫描**",
        "- 单次搜索结果限制 50 条",
        "",
        "### 4.2 项目结构扫描",
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
        "### 4.3 代码语义分析",
        "- 深度调用链追踪（入口 → 服务 → 数据 → 外部）",
        "- 影响面分析",
        "- 记录高频接口/中间件/同一类对象/统一错误码",
        "- 功能点标注改造点（新增/改造/复用）",
        "",
        "### 4.4 技术差距检查",
        "- 流量/容量评估",
        "- 幂等性分析",
        "- 发布策略（特性开关、灰度）",
        "- 稳定性（降级/限流/超时）",
        "- 前后端边界对齐",
    ])

    # L2/L3 深度模式：增加深度上下文分析
    if routing.level in (RoutingLevel.L2, RoutingLevel.L3):
        lines.extend(["", _generate_deep_context_analysis()])

    lines.extend([
        "",
        "### 4.5 完备性检查",
        "- 上下文是否覆盖需求涉及的所有模块？",
        "- 是否遗漏关键依赖？",
        "- 如果不完备，补充扫描",
        "",
        "### 4.6 报告",
        "- 调用 `reqflow_report` 报告完成",
        "- 产出: 04_context_discovery.md",
    ])

    return "\n".join(lines)


def _stage_agent_execution(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 7: Agent Execution — 多智能体协调执行。"""
    lines = [
        f"## {name}（多智能体协调）",
        "",
        "### 7.1 工作项加载",
        "- 加载 work_items.json（从实施计划阶段产出）",
        "- 验证所有 status=pending 的工作项",
        "",
        "### 7.2 多智能体调度模式",
        "",
        "对每个 pending 工作项，按以下模式执行：",
        "",
        "```",
        "┌─────────────┐",
        "│  dev-agent   │  ← 实现代码",
        "└──────┬───────┘",
        "       │ 成功后并行调度",
        "  ┌────┴────┐",
        "  ▼         ▼",
        "┌────────┐ ┌────────┐",
        "│verify- │ │review- │  ← 并行验证+审查",
        "│agent   │ │agent   │",
        "└────────┘ └────────┘",
        "```",
        "",
        "- **dev-agent**: 负责代码实现（写代码、跑测试）",
        "- **verify-agent**: 负责构建和测试验证（并行）",
        "- **review-agent**: 负责代码质量和 spec 合规审查（并行）",
        "",
        "### 7.3 模型选择策略",
        "- **opus**: 数据库 schema 变更、多服务协调、安全敏感代码、>5 验收标准",
        "- **sonnet**: 标准 API 变更、简单业务逻辑、测试补充、<=5 验收标准",
        "",
        "### 7.4 模块级 8 步循环",
        "",
        "对每个模块执行以下循环：",
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
        "### 7.5 修复循环（Loop Engine）",
        "",
        "如果实现失败，进入修复循环状态机：",
        "",
        "```",
        "observe → classify → localize → patch → verify → review → decide",
        "```",
        "",
        "- **observe**: 收集失败信息（构建错误、测试失败、审查发现）",
        "- **classify**: 分类失败原因（code_issue/test_issue/environment_issue/requirement_unclear）",
        "- **localize**: 定位问题文件和代码位置",
        "- **patch**: 生成修复补丁",
        "- **verify**: 运行测试验证修复",
        "- **review**: 审查修复是否引入新问题",
        "- **decide**: 决定是否继续循环或升级",
        "",
        "- 修复循环无次数上限",
        "- 同一问题指纹出现两次 → 升级到用户",
        "- 修复需要修改授权模块外的文件 → 升级到用户",
        "",
        "### 7.6 强制卡点",
        "- 禁止修改无关逻辑",
        "- 已完成模块禁止重新生成",
        "- 新增逻辑必须用特性开关包裹",
        "- 全路径埋点：写操作/开关分支/频控拦截必须有打点",
        "- 埋点缺失视为 P1 BLOCKER",
    ]

    # L2/L3 深度模式：增加模块级确认
    if routing.level in (RoutingLevel.L2, RoutingLevel.L3):
        lines.extend(["", _generate_module_confirmation()])

    lines.extend([
        "",
        "### 7.7 修复循环 2 轮未解决时",
        "- 调用 `debug-agent` 进行深度调试",
        "- debug-agent 输出根因分析和修复方案",
        "- 用户确认修复方案后执行修复",
        "",
        "### 7.8 Git 规则",
        "- master 上必须先切功能分支",
        "- 单次提交尽量小，能编译过就提交",
        "- BLOCKER 修复后单独 commit（不与编码提交交叉）",
        "",
        "### 7.9 报告",
        "- 每个工作项完成后调用 `reqflow_report`",
        "- 产出: 07_agent_execution.md, agent/work_items.json",
    ])

    if work_items:
        lines.append("")
        lines.append("### 7.9 工作项列表")
        for wi in work_items:
            lines.append(f"- **{wi.id}**: {wi.name} — {wi.goal}")

    return "\n".join(lines)


def _stage_code_review(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 8: Code Review — 代码审查（V4）。"""
    return f"""## {name}

### 8.1 跨模块 Review
- **不看增量只做跨模块 Review**，从最终视角校验
- 接口契约一致性：所有入口两边对齐，公共枚举定义唯一
- 整体依赖开关：存/写/读 + 旁路

### 8.2 质量门禁检查
- 调用 `reqflow_verify(gate="design-gate")` — 设计门禁
- 调用 `reqflow_verify(gate="tdd-gate")` — TDD 门禁
- 调用 `reqflow_verify(gate="completion-gate")` — 完成门禁

### 8.3 编码规范检查
- 代码质量、文件职责、分解合理性
- 仅在 spec 合规通过后执行

### 8.4 影响评估
- 修改方法是否有依赖/调用方？
- 新 DB/缓存 key 是否兼容旧数据？
- 上下游服务是否受影响？

### 8.5 安全审计（按需）
- 调用 `security-agent` 检查安全漏洞
- 触发条件：涉及认证、授权、加密、输入校验
- 输出：安全发现清单、修复建议

### 8.6 性能分析（按需）
- 调用 `performance-agent` 分析性能瓶颈
- 触发条件：涉及数据库查询、缓存、并发处理
- 输出：性能分析报告、优化建议

{_generate_review_enhancement()}

### 8.8 BLOCKER 处理
- BLOCKER 修复后单独 commit（不与编码提交交叉）
- 有 BLOCKER → 修复 + commit + 重给清单
- 无 BLOCKER → 人工确认后继续

### 8.9 报告
- 调用 `reqflow_report` 报告完成
- 产出: 08_code_review.md"""


def _stage_delivery_verification(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """Stage 9: Delivery Verification — 交付验证（V4）。"""
    return f"""## {name}

### 9.1 构建验证
- 运行构建命令，验证成功
- 构建失败 → 进入 Loop Engine 修复循环

### 9.2 测试验证
- 运行测试套件，验证全部通过
- 测试失败 → 进入 Loop Engine 修复循环

### 9.3 测试生成（按需）
- 调用 `test-gen-agent` 生成补充测试用例
- 触发条件：测试覆盖不足
- 输出：补充测试用例

### 9.4 合规报告
- 汇总所有验证证据
- 调用 `reqflow_verify(gate="compliance-report")`
- 状态: PASS / CONDITIONAL PASS / FAIL / BLOCKED

### 9.5 修复循环
- 验证失败时进入 Loop Engine（无次数上限）
- 修复循环状态机: observe → classify → localize → patch → verify → review → decide

{_generate_verification_enhancement()}

### 9.7 报告
- 调用 `reqflow_report` 报告完成
- 产出: 09_verification.md"""


def _stage_generic(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """通用阶段模板。"""
    return f"""## {name}

### 任务
- 执行 {name} 相关任务
- 完成后调用 `reqflow_report` 报告状态"""



def _stage_prd(index, name, routing, structure, context_info, work_items):
    """PRD 理解阶段（V4）。"""
    return f"""## {name}

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

{_generate_requirement_inquiry(routing)}

### 1.6 报告
- 调用 `reqflow_report` 报告完成
- 产出: 01_prd_summary.md"""


def _stage_code_discovery(index, name, routing, structure, context_info, work_items):
    """代码梳理阶段（V3）。"""
    return f"""## {name}

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
    """技术方案阶段（V4）。"""
    return f"""## {name}

### 3.1 方案模板
- 按模板组织内容，不自选章节
- 覆盖 QPS/分桶/缓存/存储/降级选型

{_generate_solution_comparison(routing)}

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
        f"## {name}（模块级 8 步循环）",
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
    return f"""## {name}

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
    return f"""## {name}

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
    """生成强制验收协议 — Agent 必须在此停止等待用户验收，拒绝后必须修复循环。"""
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

**只有用户才能决定是否通过验收。**

### 步骤 5: 验收结果处理（循环直到通过）

#### 如果用户调用 `reqflow_accept`：
- 流程结束，状态标记为 accepted
- 归档产出物

#### 如果用户调用 `reqflow_reject`：
**⛔ Agent 必须进入修复循环，不得结束会话。**

修复循环流程：
1. **记录拒绝原因** — 调用 `reqflow_reject` 记录原因
2. **分析问题** — 如果用户未提供具体原因，主动询问用户哪些方面不满意
3. **回到相关阶段修复** — 根据问题类型回到对应阶段：
   - 代码问题 → 回到 Agent执行 阶段修复
   - 设计问题 → 回到 技术方案 阶段重新设计
   - 测试问题 → 回到 交付验证 阶段重新验证
4. **重新走完剩余阶段** — 修复后重新执行后续所有阶段
5. **再次调用门禁验证** — completion-gate 必须重新通过
6. **再次展示完成状态** — 回到步骤 1，展示修复后的结果
7. **再次等待用户验收** — 回到步骤 3，等待用户决定

**⛔ 修复循环中的禁止事项：**
- 不得在用户拒绝后直接结束会话
- 不得跳过修复直接重新提交验收
- 不得声称"已修复"而不重新走完流程
- 不得在未获得用户新的验收决定前停止

**⛔ 关键行为规则：**
- 用户说"测试一下"→ 执行测试 → 测试通过后**必须主动重新提交验收**
- 用户说"改一下XX"→ 修改 → 修改完成后**必须主动重新提交验收**
- 用户给出任何反馈 → 处理完成后**必须主动询问是否通过验收**
- **处理完用户反馈后，Agent 必须主动回到验收流程，不能等用户再次触发**

**修复循环无次数上限 — 必须持续直到用户调用 `reqflow_accept`。**"""


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
