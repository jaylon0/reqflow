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
