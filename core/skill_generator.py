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
        "总结",
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
        "总结",
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
    auto_pilot: bool = False,
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
    sections.append(_generate_header(run_id, requirement, routing, auto_pilot=auto_pilot))
    sections.append(_generate_global_constraints(routing, auto_pilot=auto_pilot))
    sections.append(_generate_mcp_guide())

    for i, stage in enumerate(stages, 1):
        sections.append(_generate_stage(i, stage, routing, project_structure, context_info, work_items, auto_pilot=auto_pilot))

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
    auto_pilot: bool = False,
) -> str:
    """生成 Execution Skill 头部。"""
    mode_line = "**模式:** 自动模式（auto_pilot）— 跳过中间确认，仅验收时停止" if auto_pilot else "**模式:** 标准模式 — 每阶段停止等待确认"
    return f"""---
name: exec-{run_id}
description: 执行技能 — {requirement[:50]}
routing_level: {routing.level.value}
entry_point: prd
auto_pilot: {str(auto_pilot).lower()}
---

# Execution Skill: {requirement[:80]}

**运行 ID:** {run_id}
**路由级别:** {routing.level.value} — {routing.reason}
**置信度:** {routing.confidence:.0%}
**信号:** {', '.join(routing.signals) if routing.signals else '无'}
{mode_line}"""


def _generate_global_constraints(routing: RoutingDecision, auto_pilot: bool = False) -> str:
    """生成全局约束。"""
    if auto_pilot:
        confirmation_rule = "4. **仅验收时停止** — 自动模式下中间阶段自动继续，所有阶段完成后停止等待用户验收"
    else:
        confirmation_rule = "4. **每阶段停止确认** — 每个阶段完成后必须停止，等待用户确认后才进入下一阶段"
    constraints = [
        "## 全局约束",
        "",
        "### ⛔ 强制执行协议（不可违反）",
        "",
        "1. **必须执行所有阶段** — 按顺序执行本文件定义的每一个阶段，不得跳过、不得提前结束",
        "2. **每阶段必须报告** — 每个阶段完成后必须调用 `reqflow_report` 报告状态",
        "3. **门禁必须验证** — 指定的门禁检查点必须调用 `reqflow_verify`，未通过则修复后重新验证",
        confirmation_rule,
        "5. **不得自行验收** — 只有用户才能决定是否通过，Agent 不得自行调用 `reqflow_accept`",
        "",
        "### ⛔ V7 多 Agent 协作协议（强制）",
        "",
        "**核心原则：多 Agent 视角切换，不是多进程，而是同一 LLM 从不同角色视角输出。**",
        "",
        "1. **强制参与** — 每阶段指定的 Agent 必须全部输出，不得跳过、不得合并、不得省略",
        "2. **leader-agent 全程参与** — 在有 leader_role 的阶段，leader 必须首先输出统筹分析",
        "3. **research-agent 全程参与** — 在所有非轻量阶段，research-agent 必须提供证据支撑",
        "4. **共识表必须输出** — 每阶段结束必须输出共识表，展示各 Agent 对各维度的评估",
        "5. **置信度必须自评** — 每个 Agent 必须输出 0-100% 的置信度和理由",
        "6. **白盒透明** — 用户必须看到每个 Agent 的完整推理过程，不能只展示结论",
        "",
        "**⛔ 违反以上任何一条即为流程失败。**",
        "",
        f"{_LEADER_DECISION_PRINCIPLES}",
        "",
        f"{_DEGRADATION_MATRIX}",
        "",
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

    constraints.extend([
        "",
        "### 开发准则",
        "",
        "Agent 在生码阶段必须遵守以下准则：",
        "",
        "**内置准则：**",
        "- Karpathy Guidelines（Think Before Coding, Simplicity First, Surgical Changes）",
        "- SOLID 原则（SRP, OCP, LSP, ISP, DIP）",
        "- DRY 原则（消除重复逻辑）",
        "",
        "**技术栈自适应准则（根据项目自动启用）：**",
        "- Spring 项目：Spring Best Practices",
        "- MyBatis 项目：MyBatis Best Practices",
        "- Java 项目：Java 编码规范",
        "",
        "**项目自定义准则（从 config/rules.yaml 读取）：**",
        "- 遵循项目特定的编码规范和架构约束",
        "",
        "**准则检查：**",
        "- 每个模块完成后，检查是否遵守了适用的准则",
        "- 违规必须在 Review 阶段报告",
        "",
        "### 行为记录",
        "",
        "Agent 的关键行为必须记录到 conversation.md：",
        "",
        "**记录级别（从 config/project.yaml 读取）：**",
        "- critical：关键决策、错误、BLOCKER → 始终记录",
        "- normal：模块完成、测试结果、Review 发现 → 默认记录",
        "- verbose：文件读写、命令执行、中间状态 → 可选记录",
        "",
        "**记录格式：**",
        "```",
        "## [时间] Agent: <agent-name> | 阶段: <stage> | 级别: <level>",
        "### 输入",
        "### 输出",
        "### 决策（选择 X 而非 Y，因为 Z）",
        "### 耗时",
        "```",
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


# V7 Agent 映射表 — leader 全程参与 + research-agent 参与所有必要阶段
_STAGE_AGENTS = {
    "启动": {"leader": None, "specialists": ["doc-agent"]},
    "PRD理解": {"leader": "需求审查官", "specialists": ["research-agent", "architecture-agent", "compliance-agent"]},
    "Spec治理": {"leader": "规格审计员", "specialists": ["research-agent", "security-agent", "architecture-agent", "data-agent", "compliance-agent"]},
    "工作流智能": {"leader": "流程架构师", "specialists": ["research-agent", "architecture-agent", "api-agent"]},
    "上下文发现": {"leader": "上下文裁判", "specialists": ["research-agent", "architecture-agent", "security-agent"]},
    "技术方案": {"leader": "技术决策者", "specialists": ["research-agent", "architecture-agent", "security-agent", "performance-agent", "data-agent", "api-agent"]},
    "实施计划": {"leader": "任务分解官", "specialists": ["research-agent", "architecture-agent", "test-gen-agent", "debug-agent"]},
    "Agent执行": {"leader": "质量门禁官", "specialists": ["research-agent", "debug-agent", "test-gen-agent", "security-agent"]},
    "代码审查": {"leader": "审查综合者", "specialists": ["research-agent", "security-agent", "performance-agent", "architecture-agent", "test-gen-agent"]},
    "交付验证": {"leader": "最终裁决者", "specialists": ["research-agent", "test-gen-agent", "security-agent", "compliance-agent"]},
    "总结": {"leader": "复盘主持人", "specialists": ["research-agent", "doc-agent"]},
    "归档": {"leader": None, "specialists": ["doc-agent"]},
    # 旧名称兼容
    "上下文理解": {"leader": "上下文裁判", "specialists": ["research-agent", "architecture-agent", "security-agent"]},
    "代码梳理": {"leader": "上下文裁判", "specialists": ["research-agent", "architecture-agent", "security-agent"]},
    "生成代码": {"leader": "质量门禁官", "specialists": ["research-agent", "debug-agent", "test-gen-agent", "security-agent"]},
    "跨模块终检": {"leader": "审查综合者", "specialists": ["research-agent", "security-agent", "performance-agent", "architecture-agent", "test-gen-agent"]},
    # L0/L1 特有
    "分析报告": {"leader": "需求审查官", "specialists": ["research-agent", "architecture-agent"]},
    "轻量实现": {"leader": "质量门禁官", "specialists": ["research-agent", "debug-agent", "test-gen-agent"]},
    "局部验证": {"leader": "最终裁决者", "specialists": ["research-agent", "test-gen-agent", "security-agent"]},
}

# 向后兼容：_AUXILIARY_AGENTS 只返回 specialist 列表
_AUXILIARY_AGENTS = {k: v["specialists"] for k, v in _STAGE_AGENTS.items()}

# V7 Agent 角色定义 — 11 个 agent，模型不限（由宿主 agent 决定）
_AGENT_ROLES = {
    "leader-agent": {
        "role": "统筹协调",
        "responsibility": "路由、派遣、聚合、裁决，全程参与决策",
    },
    "research-agent": {
        "role": "调研分析",
        "responsibility": "技术调研、竞品分析、证据支撑、行业对标",
    },
    "architecture-agent": {
        "role": "架构设计",
        "responsibility": "架构设计、模块划分、重构规划、接口定义",
    },
    "security-agent": {
        "role": "安全审查",
        "responsibility": "安全审查、鉴权方案、注入防护、XSS/CSRF 防御、漏洞检查",
    },
    "performance-agent": {
        "role": "性能优化",
        "responsibility": "性能分析、缓存策略、查询优化、并发处理、内存优化",
    },
    "test-gen-agent": {
        "role": "测试生成",
        "responsibility": "测试用例设计、覆盖率分析、边界条件测试、回归测试",
    },
    "debug-agent": {
        "role": "调试修复",
        "responsibility": "错误诊断、异常排查、堆栈分析、问题定位与修复",
    },
    "doc-agent": {
        "role": "文档生成",
        "responsibility": "文档编写、注释规范、README 生成、API 文档维护",
    },
    "data-agent": {
        "role": "数据建模",
        "responsibility": "数据库 schema 设计、ER 图、数据流设计、表结构优化",
    },
    "api-agent": {
        "role": "API 设计",
        "responsibility": "接口设计、契约定义、API 规范、RESTful/GraphQL 设计",
    },
    "compliance-agent": {
        "role": "合规审查",
        "responsibility": "法规合规、数据隐私、许可证检查、GDPR/合规标准",
    },
}

# Leader 决策规则（借鉴 gstack 6 原则）
_LEADER_DECISION_PRINCIPLES = """**Leader 决策规则（6 原则）：**
1. **Choose completeness** — 选覆盖更多边缘情况的方案
2. **Pragmatic** — 两个方案解决同一问题时，选更干净的
3. **DRY** — 重复现有功能？拒绝
4. **Explicit over clever** — 10 行显而易见 > 200 行抽象
5. **Bias toward action** — 执行 > 审查循环 > 陈旧审议
6. **User sovereignty** — AI 推荐，用户决策

**决策分类：**
- **Mechanical** — 明确正确答案，静默自动决定
- **Taste** — 自动决定但呈现给用户
- **User Challenge** — 挑战用户方向时，永不自动决定，提交用户"""

# 降级矩阵
_DEGRADATION_MATRIX = """**降级矩阵：**
- leader-agent 可用 → 正常多 Agent 协作 + 共识表
- leader-agent 失败 → specialist agents 自组织 + 简化共识
- 所有 specialist 失败 → 单 Agent 模式 + 标记 [degraded]"""

# 置信度提取 prompt（基于 Anthropic P(True) 研究）
_CONFIDENCE_PROMPT = """**置信度自评（每个 agent 必须执行）：**
Rate your confidence in this analysis from 0-100%.
Consider:
- Is the information well-established in the codebase?
- Did you have sufficient context to make this judgment?
- Are there edge cases you couldn't verify?
Format: confidence=<0-100>, reasoning=<your reasoning>"""


def _generate_standard_actions(stage_name: str, routing: RoutingDecision, auto_pilot: bool = False) -> str:
    """V7 阶段标准动作 — 共识表、质量门、置信度、反思点。"""
    is_deep = routing.level in (RoutingLevel.L2, RoutingLevel.L3)
    stage_info = _STAGE_AGENTS.get(stage_name, {})
    leader_role = stage_info.get("leader")
    specialists = stage_info.get("specialists", [])
    all_agents = (["leader-agent"] if leader_role else []) + specialists

    lines = [
        "",
        "### 阶段标准动作（⛔ 强制执行，不得跳过）",
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

    # Agent 视角输出（强制，不可跳过）
    if specialists:
        lines.extend([
            "",
            "#### 3. ⛔ 强制 Agent 视角输出（不可跳过、不可合并、不可省略）",
            "",
            "**必须依次输出以下 Agent 视角，每个视角独立输出：**",
            "",
        ])
        if leader_role:
            lines.append(f"##### 3.0 leader-agent（{leader_role}）")
            lines.append(f'"作为 leader-agent（{leader_role}），本阶段的统筹分析是："')
            lines.append(f"- 必须输出完整分析，至少 100 字")
            lines.append(f"- 分析本阶段任务、确定关键决策点")
            lines.append("")

        for i, agent in enumerate(specialists, 1):
            info = _AGENT_ROLES.get(agent, {})
            role = info.get("role", "通用")
            resp = info.get("responsibility", "")
            lines.extend([
                f"##### 3.{i} {agent}（{role}）",
                f'"作为 {agent}（{role}），针对本阶段任务，我的分析是："',
                f"- 职责范围: {resp}",
                f"- 必须输出完整分析，至少 200 字",
                f"- 必须包含证据支撑（代码引用、调研数据、标准对标）",
                f"- {_CONFIDENCE_PROMPT}",
                "",
            ])

    # 共识表
    lines.extend([
        "",
        "#### 4. ⛔ 共识表（必须输出）",
        "",
        "**必须在对话中输出以下格式的共识表：**",
        "",
        "```",
        "┌─────────────────────────────────────────────────────────┐",
        f"│ 📋 {stage_name} — 阶段共识表                               │",
        "├─────────────────────────────────────────────────────────┤",
        f"│ 🧑‍💼 leader-agent: {leader_role or 'N/A'}                         │",
        "│                                                          │",
        "│ 维度         │ agent1  │ agent2  │ agent3  │ 共识       │",
        "│──────────────┼─────────┼─────────┼─────────┼────────────│",
        "│ 维度1        │ 0.85 ✅ │ 0.80 ✅ │ 0.75 ✅ │ CONFIRMED  │",
        "│ 维度2        │ 0.70 ⚠️ │ 0.80 ✅ │ —       │ FLAGGED    │",
        "│──────────────┼─────────┼─────────┼─────────┼────────────│",
        "│ 共识统计: CONFIRMED=X DISAGREE=X FLAGGED=X N/A=X        │",
        "│                                                          │",
        "│ 🧑‍💼 leader 裁决: [具体决策和理由]                          │",
        "│ 决策类型: Mechanical/Taste/User Challenge                │",
        "│ 综合置信度: 0.XX (LEVEL) → action                       │",
        "└─────────────────────────────────────────────────────────┘",
        "```",
        "",
        "**共识判定规则：**",
        "- ≥2 agent 一致 ✅ → CONFIRMED",
        "- ≥1 agent 标记 ❌ → DISAGREE，提交用户",
        "- ≥1 agent 标记 ⚠️ → FLAGGED，leader 裁决",
        "- 仅 1 agent 评估 → N/A，下阶段补充",
        "- 平票 → 置信度加权打破",
    ])

    # 质量门
    lines.extend([
        "",
        "#### 5. ⛔ 质量门（必须执行）",
        "",
        "**必须在对话中输出质量门报告：**",
        "",
        "```",
        "┌─────────────────────────────────────┐",
        f"│ 🔒 质量门 — {stage_name}                  │",
        "├─────────────────────────────────────┤",
        "│ 检查项           │ 结果    │ 详情    │",
        "│─────────────────┼────────┼────────│",
        "│ 产出物完整性      │ ✅ PASS │ 6/6    │",
        "│ 测试用例覆盖      │ ⚠️ WARN │ 75%    │",
        "│ 安全扫描          │ ✅ PASS │ 0 高危  │",
        "│─────────────────┼────────┼────────│",
        "│ 综合: PASS (hybrid 模式，重试 0/3)  │",
        "└─────────────────────────────────────┘",
        "```",
    ])

    # 置信度
    lines.extend([
        "",
        "#### 6. ⛔ 置信度评估（必须执行）",
        "",
        "**必须在对话中输出置信度报告（5 维度）：**",
        "",
        "```",
        "┌─────────────────────────────────────┐",
        "│ 📊 阶段置信度报告                     │",
        "├─────────────────────────────────────┤",
        "│ 完整性:   [████████░░] 80%  🟢       │",
        "│ 一致性:   [██████████] 100% 🟢       │",
        "│ 准确性:   [████████░░] 80%  🟢       │",
        "│ 可测试性: [██████░░░░] 60%  🟡       │",
        "│ 风险覆盖: [████████░░] 80%  🟢       │",
        "│─────────────────────────────────────│",
        "│ 综合分: 0.80  级别: HIGH             │",
        "│ 建议:   proceed → 进入下一阶段        │",
        "│                                     │",
        "│ Agent 共识详情:                       │",
        "│  research-agent: 0.85 (证据充分)      │",
        "│  architecture-agent: 0.80 (方案清晰)  │",
        "│  共识度: 0.92 (高度一致)              │",
        "└─────────────────────────────────────┘",
        "```",
        "",
        "- 调用 `reqflow_confidence(completeness=..., consistency=..., accuracy=..., testability=..., risk_coverage=...)`",
        "- **very_high (≥0.9)** → 自动进入下一阶段",
        "- **high (≥0.75)** → 进入下一阶段",
        "- **medium (≥0.5)** → 暂停，列出不确定点，等待用户判断",
        "- **low (≥0.3)** → 自动重试（最多 2 次），仍 low 则升级到用户",
        "- **very_low (<0.3)** → 升级到用户",
    ])

    # 反思点
    lines.extend([
        "",
        "#### 7. ⛔ 反思点（必须执行）",
        "",
        "**必须在对话中输出反思总结：**",
        "",
        "1. **本阶段成功模式** — 哪些做法有效，值得后续阶段借鉴",
        "2. **本阶段不足** — 哪些地方做得不够，需要后续阶段补充",
        "3. **改进建议** — 对后续阶段的具体建议",
        "",
        "**写入 memory：** 调用 `reqflow_memory_save(category=\"reflection\", key=\"{stage_name}\", value=...)`",
        "",
    ])

    lines.extend([
        "",
        "#### 7a. ⛔ 阶段报告（必须在对话中输出完整报告）",
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
        "{置信度报告（6 维度 Unicode 可视化）}",
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

    # 阶段确认
    if auto_pilot:
        lines.extend([
            "#### 8. 阶段确认（自动模式）",
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
            "#### 8. 阶段确认（⛔ 硬停止点）",
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

    return "\n".join(lines)


def _generate_brainstorming_section(stage_name: str, routing: RoutingDecision) -> str:
    """V7 头脑风暴 — leader 全程参与 + 强制 agent 视角输出。"""
    stage_info = _STAGE_AGENTS.get(stage_name, {})
    leader_role = stage_info.get("leader")
    specialists = stage_info.get("specialists", [])

    if not specialists:
        return ""

    # 确定头脑风暴模式
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
        mode = "round-robin"
        max_rounds = 1
        value_level = "标准"

    all_agents = (["leader-agent"] if leader_role else []) + specialists
    agent_list = ", ".join(f"`{a}`" for a in all_agents)

    # 生成 agent 角色描述表
    role_lines = []
    if leader_role:
        role_lines.append(f"| `leader-agent` | 统筹协调 | any | {leader_role}：路由、派遣、聚合、裁决 |")
    for agent_name in specialists:
        info = _AGENT_ROLES.get(agent_name, {})
        role = info.get("role", "通用")
        resp = info.get("responsibility", "通用任务")
        role_lines.append(f"| `{agent_name}` | {role} | any | {resp} |")
    role_table = "\n".join(role_lines)

    return f"""
### 多 Agent 协作（⛔ 必须执行）

**模式:** {mode} | **轮次:** {max_rounds} | **价值级别:** {value_level}

**参与 Agent 角色表（必须在对话中输出）：**

| Agent | 角色 | 模型 | 职责 |
|-------|------|------|------|
{role_table}

**执行流程（⛔ 必须在对话中完整输出，不可跳过）：**
1. **首先输出上方 Agent 角色表**，让用户知道哪些 agent 参及其职责
2. {"**leader-agent 作为 " + leader_role + " 统筹本阶段**" if leader_role else ""}
3. 调用 `reqflow_brainstorm(mode="{mode}", agents=[{repr(specialists)}], topic="{stage_name}", context="本阶段上下文")`
4. **每个 specialist agent 的发言必须在对话中逐条展示**，格式：
   ```
   🔵 [agent-name]（角色）: <具体观点和分析>
   置信度: XX% (理由)
   ```
5. 记录讨论过程到 `brainstorming/{stage_name}.md`
6. **输出共识结果**，作为本阶段决策参考
7. 如果有分歧，展示正反观点和 leader 最终裁决

{_LEADER_DECISION_PRINCIPLES}

{_DEGRADATION_MATRIX}

**白盒要求：** 用户必须能看到每个 agent 的角色、完整推理过程、置信度和决策依据，不能只展示结论。
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
    auto_pilot: bool = False,
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
        "总结": _stage_summary,
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
        stage_content += _generate_standard_actions(stage_name, routing, auto_pilot=auto_pilot)

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

### 10.4 产物清理

归档阶段执行:
1. 保留: `.reqflow/changes/{name}/` (交付记录)
2. 清理: `target/` 编译产物 (自动删除)
3. 清理: `.reqflow/changes/{name}/runs/{{run_id}}/tmp/` (临时文件)

验收拒绝时:
- 保留所有中间产物用于调试
- 询问用户: "是否保留编译产物(target/)用于调试？[Y/n]"

验收通过时:
- 自动清理编译产物
- 保留 .reqflow 归档

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
- 产出: 11_archive.md"""


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
        "### TDD 强制检查（⛔ 生码阶段专用）",
        "",
        "**每个模块必须遵循 Red-Green-Refactor 循环：**",
        "1. **Red** — 先写失败测试（failing tests count > 0）",
        "2. **Green** — 实现最小代码使测试通过",
        "3. **Refactor** — 优化代码，测试仍然全部通过",
        "",
        "**门禁检查：**",
        "- 开始实现前：`reqflow_verify(gate=\"tdd-gate\")` — failing tests > 0",
        "- 实现完成后：所有测试必须通过（failing tests = 0）",
        "- 重构后：测试仍然全部通过",
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

### 分级 Review

**关键模块即时 Review（Agent 执行阶段内）：**
- DB schema 变更 → 安全审查 + 架构审查
- 安全相关代码 → 安全审查 + Spec 合规
- 跨模块接口 → 架构审查 + Spec 合规

**总 Review（所有模块完成后）：**
- Spec 合规审查 — 是否所有需求都已实现
- 代码质量审查 — 规范、可读性、职责边界
- 安全审查 — SQL 注入、XSS、鉴权
- 性能审查 — N+1 查询、内存泄漏
- 架构审查 — 职责边界、依赖方向

**Review 后用户决策：**
- ⛔ 展示 Review 结果后停止，等待用户决定
- 选项 1：接受，进入交付验证
- 选项 2：进入修复循环
- 选项 3：部分接受（标记剩余问题为 P1/P2）

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

### 9.6 测试执行策略

不得假设测试命令格式。必须按以下顺序探测：

1. **首选:** `mvn -pl {{module}} -am -Dtest={{TestClass}} test`
   - 成功 → 记录此命令
   - 失败 "No tests were executed" → 进入步骤 2
   - 失败 "Could not resolve dependencies" → 补 `-am` 重试

2. **降级:** `mvn -pl {{module}} -am -Dtest={{TestClass}} -DfailIfNoTests=false test`
   - 检查 Tests run > 0 → 成功
   - Tests run: 0 → 进入步骤 3

3. **兜底:** `java -cp {{classpath}} org.junit.runner.JUnitCore {{TestClass}}`
   - 手动构建 classpath: test-classes + classes + 依赖 jar
   - 成功 → 记录完整 classpath 命令

⚠️ 不得报告"测试通过"除非实际执行了测试且 Tests run > 0
⚠️ 必须在 evidence 中记录最终使用的测试命令

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

### Spec 驱动开发（SDD）

**技术方案阶段必须输出：**
1. `spec.md` — 设计规格（Source of Truth）
2. 从 spec 导出 test plan（验收标准 → 测试用例）
3. 后续阶段以此 spec 为基准

### 3.6 报告
- 调用 `reqflow_report` 报告完成
- 产出: 05_tech_plan.md"""


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


def _stage_summary(
    index: int,
    name: str,
    routing: RoutingDecision,
    structure: ProjectStructure | None,
    context_info: dict[str, Any] | None,
    work_items: list[WorkItem] | None,
) -> str:
    """总结阶段 — 在归档之前，输出完整总结。"""
    return f"""## {name}

### 量化指标
- 使用 ASCII 表格展示：总耗时、模块数、测试通过率、Review 发现数、BLOCKER 数、置信度平均

### 决策回顾
- 使用 ASCII 表格展示所有关键决策、理由、替代方案

### 经验教训
- 做得好的（保持）
- 可以改进的（下次优化）
- 需要注意的（风险提示）

### 知识沉淀
- 调用 `reqflow_memory_save` 保存关键决策到 knowledge/
- 识别可复用的模式写入 knowledge/patterns/

### 可视化
- 阶段耗时分布（Mermaid 甘特图）
- 置信度变化趋势（ASCII 趋势图）
- 模块完成状态（进度条）

### 输出
- 对话中展示完整总结（含可视化图表）
- 落文件到 `summary/summary.md` 和 `summary/metrics.md`
- 调用 `reqflow_report` 报告完成"""


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

### 步骤 3: 展示验收决策面板

**必须向用户输出以下完整的验收决策面板：**

```
### 🏁 验收决策面板

**当前状态:** 全部阶段完成，等待你的验收决定。

#### 已交付产物清单
| # | 文件 | 操作 | 验证 |
|---|------|------|------|
| {{列出所有产物}} |

#### 质量摘要
- 综合置信度: {{overall}}%
- 门禁: {{gate_results}}
- BLOCKER: P0={{p0_count}}, 全部={{total_count}}
- Spec Drift: {{drift_count}} 项

#### 请做出决定

| 选项 | 操作 | 后续流程 |
|------|------|----------|
| ✅ **通过验收** | 调用 `reqflow_accept(run_id="{run_id}")` | 1. 生成交付报告 2. 归档所有产物 3. 清理临时文件 4. 流程结束 |
| ❌ **拒绝验收** | 调用 `reqflow_reject(run_id="{run_id}", reason="原因")` | 1. 进入修复循环（最多 3 轮） 2. 重新执行失败阶段 3. 重新提交验收 |
| 🔧 **部分验收** | 调用 `reqflow_accept(run_id="{run_id}", scope="范围")` | 1. 标记已验收部分 2. 未验收部分进入修复 3. 生成部分交付报告 |
| ⏸ **暂挂** | 不调用工具 | 1. 保持当前状态 2. 可随时回来继续 3. 不会自动超时 |
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
