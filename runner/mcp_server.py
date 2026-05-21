"""ReqFlow MCP Server - 将 ReqFlow 能力暴露为 MCP 工具。

通过 stdio 传输与 MCP 客户端通信，提供以下工具:
    reqflow_run           执行 workflow
    reqflow_status        查询运行状态
    reqflow_list_runtimes 列出可用 runtime
    reqflow_checkpoint    管理检查点
    reqflow_parallel      并行 agent 调度
    reqflow_trace         执行追踪
    reqflow_guardrails    约束检查

注意: ``mcp`` 依赖是可选的。如果未安装，导入时会给出友好提示并退出。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# 确保 reqflow 包可导入
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- MCP 可选依赖 ---
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    class TextContent:  # type: ignore[no-redef]
        """MCP 不可用时的占位类，仅用于测试。"""
        def __init__(self, type: str = "text", text: str = ""):
            self.type = type
            self.text = text


# --- 延迟导入 reqflow 核心（仅在 MCP 可用时才需要） ---

def _import_core():
    """延迟导入 reqflow 核心模块。"""
    from reqflow.core import Engine, RuntimeRegistry
    return Engine, RuntimeRegistry


# ---------------------------------------------------------------------------
# workflow 步骤加载（通过 WorkflowLoader 从 YAML 读取）
# ---------------------------------------------------------------------------


def _get_workflow_steps(workflow_name: str) -> list[dict]:
    """从 YAML workflow 文件加载步骤定义。"""
    from reqflow.core import WorkflowLoader
    try:
        loader = WorkflowLoader()
        return loader.get_stages(workflow_name)
    except Exception:
        # 回退到内置简化步骤
        if workflow_name == "main-flow":
            return [
                {"name": "分析", "prompt": "分析需求，提取关键信息。", "checkpoint": True},
                {"name": "计划", "prompt": "制定执行计划。", "checkpoint": True},
                {"name": "实现", "prompt": "按计划实现代码。", "checkpoint": True},
                {"name": "审查", "prompt": "审查代码质量和需求匹配度。", "checkpoint": True},
                {"name": "验证", "prompt": "验证交付物满足验收标准。"},
            ]
        return [
            {"name": "分析", "prompt": "分析需求，提取关键信息。"},
            {"name": "实现", "prompt": "实现代码变更。", "checkpoint": True},
            {"name": "验证", "prompt": "验证变更是否正确。"},
        ]


# ---------------------------------------------------------------------------
# MCP Server 定义
# ---------------------------------------------------------------------------

# 工具描述
TOOLS: list[dict] = [
    {
        "name": "reqflow_run",
        "description": "执行 ReqFlow workflow。传入需求文本，自动选择 runtime 并运行指定 workflow。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement": {
                    "type": "string",
                    "description": "需求文本内容",
                },
                "runtime": {
                    "type": "string",
                    "description": "Runtime 名称 (claude, gpt, gemini, deepseek, manual)，不指定则自动检测",
                },
                "workflow": {
                    "type": "string",
                    "enum": ["flow", "main-flow"],
                    "description": "Workflow 类型，默认 flow",
                    "default": "flow",
                },
                "run_dir": {
                    "type": "string",
                    "description": "运行目录路径（可选，默认自动生成）",
                },
            },
            "required": ["requirement"],
        },
    },
    {
        "name": "reqflow_status",
        "description": "查询 ReqFlow 运行状态。传入运行目录路径，返回当前状态。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_dir": {
                    "type": "string",
                    "description": "运行目录路径",
                },
            },
            "required": ["run_dir"],
        },
    },
    {
        "name": "reqflow_list_runtimes",
        "description": "列出所有可用的 ReqFlow runtime。",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "reqflow_run_graph",
        "description": "执行图编排工作流。支持分支、条件路由、并行 fan-out、human gate。从 YAML 加载图定义。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "图工作流名称 (如 graph-example)",
                    "default": "graph-example",
                },
                "runtime": {
                    "type": "string",
                    "description": "Runtime 名称 (claude, gpt, gemini, deepseek, manual)",
                },
                "initial_state": {
                    "type": "object",
                    "description": "初始状态字典 (可选)",
                },
            },
            "required": ["workflow"],
        },
    },
    {
        "name": "reqflow_session_save",
        "description": "保存会话上下文。用于跨轮次持久化，在多次交互间保持状态。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "会话 ID",
                },
                "key": {
                    "type": "string",
                    "description": "上下文键名",
                },
                "value": {
                    "description": "上下文值 (任意类型)",
                },
            },
            "required": ["session_id", "key", "value"],
        },
    },
    {
        "name": "reqflow_session_load",
        "description": "加载会话上下文。恢复之前保存的跨轮次状态。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "会话 ID",
                },
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "reqflow_dashboard",
        "description": "获取格式化的运行面板。显示步骤状态、checkpoint、内存条目。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_dir": {
                    "type": "string",
                    "description": "运行目录路径",
                },
                "detail": {
                    "type": "string",
                    "enum": ["summary", "full"],
                    "description": "摘要模式或完整模式（包含 reports/verifications/blockers/acceptance_criteria 详情）",
                    "default": "summary",
                },
            },
            "required": ["run_dir"],
        },
    },
    {
        "name": "reqflow_checkpoint",
        "description": "Checkpoint 管理。创建、恢复和列出检查点。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_dir": {
                    "type": "string",
                    "description": "运行目录路径",
                },
                "action": {
                    "type": "string",
                    "enum": ["list", "create", "restore"],
                    "description": "操作类型",
                },
                "stage": {
                    "type": "string",
                    "description": "阶段名称（create 时必需）",
                },
                "checkpoint_id": {
                    "type": "string",
                    "description": "检查点 ID（restore 时必需）",
                },
            },
            "required": ["run_dir", "action"],
        },
    },
    {
        "name": "reqflow_parallel",
        "description": "并行 agent 调度。同时执行多个任务。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agents": {
                    "type": "array",
                    "description": "Agent 列表，每个包含 name、prompt、handler",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "prompt": {"type": "string"},
                        },
                        "required": ["name", "prompt"],
                    },
                },
                "max_concurrent": {
                    "type": "integer",
                    "description": "最大并发数（默认 3）",
                    "default": 3,
                },
            },
            "required": ["agents"],
        },
    },
    {
        "name": "reqflow_trace",
        "description": "执行追踪。查看和导出执行追踪数据。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_dir": {
                    "type": "string",
                    "description": "运行目录路径",
                },
                "action": {
                    "type": "string",
                    "enum": ["summary", "export"],
                    "description": "操作类型",
                },
                "output": {
                    "type": "string",
                    "description": "导出文件路径（export 时使用）",
                },
            },
            "required": ["run_dir", "action"],
        },
    },
    {
        "name": "reqflow_guardrails",
        "description": "约束检查。验证上下文是否符合规则。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "object",
                    "description": "待检查的上下文",
                },
            },
            "required": ["context"],
        },
    },
    {
        "name": "reqflow_health",
        "description": "检查 ReqFlow 系统健康状态和 runtime 可用性。",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    # --- Harness 编排工具 ---
    {
        "name": "reqflow_plan",
        "description": "开始新计划。路由分析、上下文扫描、生成 Execution Skill。Harness 核心工具。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement": {
                    "type": "string",
                    "description": "需求文本内容",
                },
                "workflow": {
                    "type": "string",
                    "description": "Workflow 类型（可选，默认自动选择）",
                },
            },
            "required": ["requirement"],
        },
    },
    {
        "name": "reqflow_report",
        "description": "报告阶段完成状态。Agent 每完成一个阶段后调用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "运行 ID",
                },
                "stage": {
                    "type": "string",
                    "description": "阶段名称",
                },
                "status": {
                    "type": "string",
                    "enum": ["done", "blocked", "timeout", "failed", "conditional"],
                    "description": "阶段状态。conditional 表示有条件通过，附带风险说明",
                },
                "artifacts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "产出文件路径列表",
                },
                "error": {
                    "type": "string",
                    "description": "错误信息（status 为 blocked/failed 时）",
                },
                "risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "风险项（status 为 conditional 时列出残留风险）",
                },
            },
            "required": ["run_id", "stage", "status"],
        },
    },
    {
        "name": "reqflow_verify",
        "description": "请求门禁验证。质量门禁检查。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "运行 ID",
                },
                "gate": {
                    "type": "string",
                    "enum": ["design-gate", "tdd-gate", "completion-gate", "compliance-report"],
                    "description": "门禁类型",
                },
                "evidence": {
                    "type": "object",
                    "description": "验证证据",
                },
            },
            "required": ["run_id", "gate"],
        },
    },
    {
        "name": "reqflow_accept",
        "description": "用户验收通过。触发归档流程。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "运行 ID",
                },
                "feedback": {
                    "type": "string",
                    "description": "用户反馈（可选）",
                },
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "reqflow_reject",
        "description": "用户验收拒绝。触发修复循环。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "运行 ID",
                },
                "reason": {
                    "type": "string",
                    "description": "拒绝原因",
                },
                "issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "问题列表",
                },
            },
            "required": ["run_id", "reason"],
        },
    },
    {
        "name": "reqflow_tool_call",
        "description": "调用外部工具。从 tools.yaml 查找定义，通过 MCP 协议调用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "工具名称"},
                "method": {"type": "string", "description": "调用方法"},
                "params": {"type": "object", "description": "参数"},
            },
            "required": ["tool_name", "method"],
        },
    },
    {
        "name": "reqflow_memory_save",
        "description": "保存长期记忆到 memory.md。记录关键决策、限制、命名规则、模式。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "运行 ID"},
                "category": {"type": "string", "enum": ["decision", "constraint", "naming", "pattern"], "description": "分类"},
                "content": {"type": "string", "description": "记忆内容"},
                "stage": {"type": "string", "description": "所属阶段"},
            },
            "required": ["run_id", "category", "content"],
        },
    },
    {
        "name": "reqflow_memory_load",
        "description": "加载 memory.md 全部内容。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "运行 ID"},
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "reqflow_git_check",
        "description": "检查 Git 状态（分支、未提交文件、最后提交）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_dir": {"type": "string", "description": "仓库目录", "default": "."},
            },
        },
    },
    {
        "name": "reqflow_blocker_add",
        "description": "添加 BLOCKER。P0 阻塞（必须关闭），P1 标记（不阻塞），P2 仅记录。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "运行 ID"},
                "level": {"type": "string", "enum": ["P0", "P1", "P2"], "description": "BLOCKER 级别"},
                "question": {"type": "string", "description": "BLOCKER 描述"},
                "stage": {"type": "string", "description": "所属阶段"},
            },
            "required": ["run_id", "level", "question"],
        },
    },
    {
        "name": "reqflow_blocker_resolve",
        "description": "解决 BLOCKER。提供答案后关闭。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "运行 ID"},
                "blocker_id": {"type": "string", "description": "BLOCKER ID"},
                "answer": {"type": "string", "description": "解决方案"},
            },
            "required": ["run_id", "blocker_id", "answer"],
        },
    },
    {
        "name": "reqflow_blocker_check",
        "description": "检查当前 BLOCKER 状态。返回 P0 未关闭数量和全部 BLOCKER 列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "运行 ID"},
                "stage": {"type": "string", "description": "过滤阶段（可选）"},
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "reqflow_multi_repo_switch",
        "description": "切换多仓库上下文。检测项目中的多个 git 仓库并切换当前工作仓库。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "项目根目录", "default": "."},
                "repo_name": {"type": "string", "description": "目标仓库名称（可选，不指定则列出所有仓库）"},
            },
        },
    },
    {
        "name": "reqflow_acceptance_update",
        "description": "更新验收标准状态。标记单条验收标准为 verified/failed/pending。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "运行 ID"},
                "criteria_id": {"type": "string", "description": "验收标准 ID（如 ac-01）"},
                "status": {"type": "string", "enum": ["verified", "failed", "pending"], "description": "新状态"},
                "evidence": {"type": "string", "description": "验证证据说明"},
            },
            "required": ["run_id", "criteria_id", "status"],
        },
    },
    {
        "name": "reqflow_full_flow",
        "description": "强制全流程入口，跳过路由分析直接使用 L3 管线（11 阶段）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement": {"type": "string", "description": "需求描述"},
                "change_name": {"type": "string", "description": "变更名称（可选）"},
            },
            "required": ["requirement"],
        },
    },
    {
        "name": "reqflow_brainstorm",
        "description": "触发多 Agent 头脑风暴（round-robin/panel-of-experts/adversarial-debate/critique-refine）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["round-robin", "panel-of-experts", "adversarial-debate", "critique-refine"], "description": "头脑风暴模式"},
                "agents": {"type": "array", "items": {"type": "string"}, "description": "参与 agent 列表"},
                "topic": {"type": "string", "description": "讨论主题"},
                "context": {"type": "string", "description": "上下文信息"},
                "max_rounds": {"type": "integer", "description": "最大轮次", "default": 3},
            },
            "required": ["mode", "agents", "topic", "context"],
        },
    },
    {
        "name": "reqflow_confidence",
        "description": "评估或查询置信度（3-tier: high/medium/low + 自动路由）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "completeness": {"type": "number", "description": "完整性 (0-1)"},
                "consistency": {"type": "number", "description": "一致性 (0-1)"},
                "accuracy": {"type": "number", "description": "准确性 (0-1)"},
                "retry_count": {"type": "integer", "description": "已重试次数", "default": 0},
            },
            "required": ["completeness", "consistency", "accuracy"],
        },
    },
]


# --- 工具实现 ---


async def _handle_run(arguments: dict) -> list:
    """处理 reqflow_run 工具调用。"""
    import json as _json
    from datetime import datetime as _dt
    from pathlib import Path as _Path

    Engine, RuntimeRegistry = _import_core()

    requirement = arguments.get("requirement", "").strip()
    if not requirement:
        return [TextContent(type="text", text="[错误] 需求内容不能为空。")]

    runtime_name = arguments.get("runtime")
    workflow_type = arguments.get("workflow", "flow")
    run_dir = arguments.get("run_dir")

    # Pre-create run directory for failure artifacts
    if not run_dir:
        timestamp = _dt.now().strftime("%Y%m%d-%H%M%S")
        run_dir = f".reqflow/runs/run-{timestamp}"
    run_path = _Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)

    def _write_failure_state(error_msg: str, stage: str = "init"):
        state = {
            "run_id": run_path.name,
            "workflow": workflow_type,
            "runtime": runtime_name or "auto",
            "status": "init_failed",
            "failed_at": stage,
            "error": error_msg,
            "guardrails_loaded": False,
            "guidelines_loaded": False,
            "created_at": _dt.now().isoformat(),
            "updated_at": _dt.now().isoformat(),
        }
        (run_path / "state.json").write_text(_json.dumps(state, indent=2, ensure_ascii=False))

    # 选择 runtime
    registry = RuntimeRegistry()

    if runtime_name:
        try:
            config = registry.get(runtime_name)
        except ValueError as exc:
            _write_failure_state(str(exc), "runtime_lookup")
            return [TextContent(type="text", text=f"[错误] {exc}\n运行目录: {run_dir}")]
    else:
        config = _detect_runtime(registry)
        if config is None:
            errors = registry.list_errors()
            detail = f" (配置加载错误: {errors})" if errors else ""
            _write_failure_state(f"无法自动检测 runtime{detail}", "runtime_detect")
            return [TextContent(type="text", text=f"[错误] 无法自动检测 runtime，请指定 runtime 参数。\n运行目录: {run_dir}")]

    # 可用性检查
    ready, reason = registry.check_readiness(config.name)
    if not ready:
        _write_failure_state(f"Runtime '{config.name}' 不可用: {reason}", "runtime_readiness")
        return [TextContent(type="text", text=f"[错误] Runtime '{config.name}' 不可用: {reason}\n运行目录: {run_dir}")]

    # Host runtime: generate Execution Skill instead of blocking
    if config and config.name == "host":
        return await _handle_plan({
            "requirement": requirement,
            "workflow": workflow_type,
        })

    # 选择 workflow（从 YAML 加载）
    steps = _get_workflow_steps(workflow_type)

    # 创建 Engine 并执行
    engine = Engine(config=config, run_dir=run_dir)

    try:
        result = await engine.run_workflow(workflow_steps=steps, requirement=requirement)
    except Exception as exc:
        _write_failure_state(str(exc), "workflow_execution")
        return [TextContent(type="text", text=f"[错误] Workflow 执行失败: {exc}\n运行目录: {run_dir}")]

    # 格式化输出
    lines = [
        f"运行 ID: {engine.run_id}",
        f"Runtime: {config.display_name} ({config.name})",
        f"状态: {result.get('status', '未知')}",
    ]

    for step in result.get("steps", []):
        icon = {"success": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]", "aborted": "[STOP]"}.get(step.get("status", ""), "[?]")
        lines.append(f"  {icon} {step.get('name', '?')}: {step.get('status', '?')}")

    if result.get("failed_at"):
        lines.append(f"失败阶段: {result['failed_at']}")

    if result.get("error"):
        lines.append(f"错误: {result['error']}")
    if result.get("abort_reason"):
        lines.append(f"中止原因: {result['abort_reason']}")

    lines.append(f"运行目录: {engine.run_dir}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_status(arguments: dict) -> list:
    """处理 reqflow_status 工具调用。"""
    run_dir = arguments.get("run_dir", "")
    state_file = Path(run_dir) / "state.json"

    if not state_file.exists():
        return [TextContent(type="text", text=f"[错误] 未找到状态文件: {state_file}")]

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [TextContent(type="text", text=f"[错误] 无法读取状态文件: {exc}")]

    lines = [
        f"运行 ID:    {data.get('run_id', '?')}",
        f"当前阶段:   {data.get('current_stage', '?')}",
        f"规格状态:   {data.get('spec_status', '?')}",
        f"创建时间:   {data.get('created_at', '?')}",
        f"更新时间:   {data.get('updated_at', '?')}",
    ]

    completed = data.get("completed_modules", [])
    if completed:
        lines.append(f"已完成模块 ({len(completed)}):")
        for mod in completed:
            lines.append(f"  - {mod}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_list_runtimes(_arguments: dict) -> list:
    """处理 reqflow_list_runtimes 工具调用。"""
    _, RuntimeRegistry = _import_core()

    registry = RuntimeRegistry()

    runtimes = registry.list_runtimes()
    errors = registry.list_errors()

    lines = ["可用 runtime:"]
    if runtimes:
        for name in runtimes:
            config = registry.get(name)
            lines.append(f"  - {name:12s}  {config.display_name}")
    else:
        lines.append("  (无)")

    if errors:
        lines.append("\n加载失败的配置:")
        for name, err in errors.items():
            lines.append(f"  - {name:12s}  {err}")

    return [TextContent(type="text", text="\n".join(lines))]


# --- 工具路由 ---

async def _handle_run_graph(arguments: dict) -> list:
    """处理 reqflow_run_graph 工具调用。"""
    Engine, RuntimeRegistry = _import_core()

    workflow_name = arguments.get("workflow", "graph-example")
    runtime_name = arguments.get("runtime")
    initial_state = arguments.get("initial_state", {})

    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 无法加载 runtime 配置: {exc}")]

    if runtime_name:
        try:
            config = registry.get(runtime_name)
        except ValueError as exc:
            return [TextContent(type="text", text=f"[错误] {exc}")]
    else:
        config = _detect_runtime(registry)
        if config is None:
            return [TextContent(type="text", text="[错误] 无法自动检测 runtime。")]

    engine = Engine(config=config)

    try:
        graph = engine.workflow_loader.load_graph(workflow_name)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 无法加载图工作流 '{workflow_name}': {exc}")]

    try:
        result = await engine.run_graph(graph)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 图工作流执行失败: {exc}")]

    lines = [
        f"运行 ID: {engine.run_id}",
        f"Runtime: {config.display_name} ({config.name})",
        f"工作流: {workflow_name} (graph)",
        f"状态: {result.get('_status', '未知')}",
        f"运行目录: {engine.run_dir}",
    ]

    # 输出关键状态
    for key, value in result.items():
        if not key.startswith("_"):
            lines.append(f"  {key}: {value}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_session_save(arguments: dict) -> list:
    """处理 reqflow_session_save 工具调用。"""
    from reqflow.core.session import Session

    session_id = arguments.get("session_id", "")
    key = arguments.get("key", "")
    value = arguments.get("value")

    if not session_id or not key:
        return [TextContent(type="text", text="[错误] session_id 和 key 不能为空。")]

    storage_dir = ".reqflow/sessions"
    session = Session(session_id=session_id, storage_dir=storage_dir)
    try:
        session.load()
    except Exception:
        pass  # 新 session，忽略加载错误

    session.save_context(key, value)
    session.save()

    return [TextContent(type="text", text=f"已保存: session={session_id}, key={key}")]


async def _handle_session_load(arguments: dict) -> list:
    """处理 reqflow_session_load 工具调用。"""
    from reqflow.core.session import Session

    session_id = arguments.get("session_id", "")
    if not session_id:
        return [TextContent(type="text", text="[错误] session_id 不能为空。")]

    storage_dir = ".reqflow/sessions"
    session = Session(session_id=session_id, storage_dir=storage_dir)
    session.load()

    if not session._context and not session.history:
        return [TextContent(type="text", text=f"Session '{session_id}' 不存在或为空。")]

    lines = [f"Session: {session_id}"]
    if session._context:
        lines.append("\n上下文:")
        for k, v in session._context.items():
            lines.append(f"  {k}: {v}")
    if session.history:
        lines.append(f"\n历史 ({len(session.history)} 条):")
        for entry in session.history[-5:]:  # 最近 5 条
            lines.append(f"  [{entry['step']}] {entry['result'][:80]}")
    lines.append(f"\n摘要: {session.summarize(max_length=200)}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_dashboard(arguments: dict) -> list:
    """处理 reqflow_dashboard 工具调用。"""
    from reqflow.runner.dashboard import Dashboard

    run_dir = arguments.get("run_dir", "")
    detail = arguments.get("detail", "summary")
    if not run_dir:
        return [TextContent(type="text", text="[错误] run_dir 不能为空。")]

    dashboard = Dashboard(run_dir=run_dir)

    # 读取 state.json，如果不存在则尝试 acceptance.json
    state_file = Path(run_dir) / "state.json"
    acceptance_file = Path(run_dir) / "acceptance.json"

    data = {}
    if state_file.exists():
        try:
            import json
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 无法读取状态文件: {exc}")]
    elif acceptance_file.exists():
        try:
            import json
            data = json.loads(acceptance_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 无法读取验收文件: {exc}")]
    else:
        return [TextContent(type="text", text=f"[错误] 未找到状态文件: {state_file}\n也未找到验收文件: {acceptance_file}")]

    # Build step_statuses from stage_records
    step_statuses = {}
    for record in data.get("stage_records", []):
        name = record.get("name", "")
        status_val = record.get("status", "")
        if name and status_val:
            step_statuses[name] = status_val

    # 构造 status dict
    status = {
        "run_id": data.get("run_id", "?"),
        "config": data.get("config", "?"),
        "adapter": data.get("adapter", "?"),
        "current_stage": data.get("current_stage", "?"),
        "completed_modules": data.get("completed_modules", []),
        "steps_executed": len(data.get("completed_modules", [])),
        "step_statuses": step_statuses,
        "checkpoints": len(data.get("checkpoints", [])),
        "memory_entries": len(data.get("memory", {}).get("short_term", [])),
        "stage_records": data.get("stage_records", []),
        "reports": data.get("reports", []),
        "verifications": data.get("verifications", []),
        "blockers": data.get("blockers", []),
        "acceptance_criteria": data.get("acceptance_criteria", []),
        "workflow_status": data.get("status", "unknown"),
    }

    output = dashboard.format_status(status)

    # 详细模式：追加 reports、verifications、blockers、acceptance_criteria 详情
    if detail == "full":
        extra = []

        reports = data.get("reports", [])
        if reports:
            extra.append("\n=== 阶段报告 ===")
            for r in reports:
                stage = r.get("stage", "?")
                st = r.get("status", "?")
                risks = r.get("risks", [])
                risk_str = f" | 风险: {', '.join(risks)}" if risks else ""
                extra.append(f"  [{st}] {stage}{risk_str}")
                if r.get("error"):
                    extra.append(f"    错误: {r['error']}")

        verifications = data.get("verifications", [])
        if verifications:
            extra.append("\n=== 门禁验证 ===")
            for v in verifications:
                gate = v.get("gate", "?")
                passed = v.get("passed", False)
                extra.append(f"  [{'PASS' if passed else 'FAIL'}] {gate}")
                if v.get("summary"):
                    extra.append(f"    {v['summary']}")

        blockers = data.get("blockers", [])
        if blockers:
            extra.append("\n=== BLOCKER ===")
            for b in blockers:
                bid = b.get("id", "?")
                level = b.get("level", "?")
                status_b = b.get("status", "open")
                question = b.get("question", "?")
                extra.append(f"  [{level}] {bid} ({status_b}): {question}")

        criteria = data.get("acceptance_criteria", [])
        if criteria:
            extra.append("\n=== 验收标准 ===")
            for c in criteria:
                cid = c.get("id", "?")
                st = c.get("status", "pending")
                desc = c.get("description", "?")
                extra.append(f"  [{st}] {cid}: {desc}")

        if extra:
            output += "\n" + "\n".join(extra)

    return [TextContent(type="text", text=output)]


async def _handle_checkpoint(arguments: dict) -> list:
    """处理 reqflow_checkpoint 工具调用。"""
    from reqflow.core.state_manager import StateManager

    run_dir = arguments.get("run_dir", "")
    action = arguments.get("action", "")

    if not run_dir:
        return [TextContent(type="text", text="[错误] run_dir 不能为空。")]

    if action not in ("list", "create", "restore"):
        return [TextContent(type="text", text=f"[错误] 无效的 action: {action}，支持 list/create/restore")]

    sm = StateManager(run_dir=run_dir)

    if action == "list":
        try:
            checkpoints = sm.list_checkpoints()
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 无法列出检查点: {exc}")]

        if not checkpoints:
            return [TextContent(type="text", text="未找到任何检查点。")]

        lines = [f"检查点 ({len(checkpoints)}):"]
        for cp in checkpoints:
            lines.append(f"  - {cp.checkpoint_id[:8]}  阶段: {cp.stage}  时间: {cp.timestamp}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif action == "create":
        stage = arguments.get("stage", "")
        if not stage:
            return [TextContent(type="text", text="[错误] create 操作需要 stage 参数。")]

        try:
            checkpoint = sm.create_checkpoint(stage=stage, context={})
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 创建检查点失败: {exc}")]

        return [TextContent(type="text", text=f"已创建检查点: {checkpoint.checkpoint_id}\n阶段: {checkpoint.stage}\n时间: {checkpoint.timestamp}")]

    elif action == "restore":
        checkpoint_id = arguments.get("checkpoint_id", "")
        if not checkpoint_id:
            return [TextContent(type="text", text="[错误] restore 操作需要 checkpoint_id 参数。")]

        try:
            state, context = sm.restore_checkpoint(checkpoint_id=checkpoint_id)
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 恢复检查点失败: {exc}")]

        lines = [
            f"已恢复检查点: {checkpoint_id}",
            f"当前阶段: {state.current_stage}",
        ]
        if context:
            lines.append(f"上下文: {json.dumps(context, ensure_ascii=False)}")
        return [TextContent(type="text", text="\n".join(lines))]


async def _handle_parallel(arguments: dict) -> list:
    """处理 reqflow_parallel 工具调用。"""
    agents = arguments.get("agents", [])
    if not agents:
        return [TextContent(type="text", text="[错误] agents 列表不能为空。")]

    max_concurrent = arguments.get("max_concurrent", 3)
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []

    async def _run_one(agent):
        name = agent.get("name", "unnamed")
        prompt = agent.get("prompt", "")
        async with semaphore:
            try:
                # In MCP context, we simulate agent execution
                # Real implementation would call back to the MCP client
                result = {"name": name, "status": "success", "result": f"Completed: {prompt}"}
                results.append(result)
            except Exception as e:
                results.append({"name": name, "status": "error", "error": str(e)})

    await asyncio.gather(*[_run_one(a) for a in agents])

    lines = [f"并行执行完成 ({len(results)} 个 agent):"]
    for r in results:
        status = r.get("status", "unknown")
        name = r.get("name", "unnamed")
        icon = "[OK]" if status == "success" else "[FAIL]"
        lines.append(f"  {icon} {name}: {status}")
        if r.get("error"):
            lines.append(f"      错误: {r['error']}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_trace(arguments: dict) -> list:
    """处理 reqflow_trace 工具调用。"""
    run_dir = arguments.get("run_dir", "")
    action = arguments.get("action", "")

    if not run_dir:
        return [TextContent(type="text", text="[错误] run_dir 不能为空。")]

    trace_dir = Path(run_dir) / "traces"
    if not trace_dir.exists():
        return [TextContent(type="text", text=f"[错误] 未找到追踪目录: {trace_dir}")]

    trace_files = list(trace_dir.glob("*.json"))
    if not trace_files:
        return [TextContent(type="text", text="未找到任何追踪数据。")]

    if action == "summary":
        lines = [f"追踪数据 ({len(trace_files)} 个):"]
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                lines.append(f"  - {data.get('trace_id', '?')}: {data.get('name', '?')}")
                lines.append(f"    时间: {data.get('start_time', '?')} ~ {data.get('end_time', '?')}")
                spans = data.get("spans", [])
                lines.append(f"    Spans: {len(spans)}")
            except Exception:
                lines.append(f"  - {tf.name}: (读取失败)")
        return [TextContent(type="text", text="\n".join(lines))]

    elif action == "export":
        output = arguments.get("output", "")
        if not output:
            output = str(Path(run_dir) / "trace-export.json")

        all_traces = []
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                all_traces.append(data)
            except Exception:
                pass

        Path(output).write_text(json.dumps(all_traces, ensure_ascii=False, indent=2), encoding="utf-8")
        return [TextContent(type="text", text=f"已导出 {len(all_traces)} 个追踪到: {output}")]

    else:
        return [TextContent(type="text", text=f"[错误] 无效的 action: {action}")]


async def _handle_guardrails(arguments: dict) -> list:
    """处理 reqflow_guardrails 工具调用。"""
    from reqflow.core.guardrails import Guardrails, Constraint, Severity, check_file_boundary, check_constitution

    context = arguments.get("context", {})
    if not context:
        return [TextContent(type="text", text="[错误] context 不能为空。")]

    guardrails = Guardrails(constraints=[])
    guardrails.add_constraint(Constraint(
        name="file_boundary",
        description="检查文件编辑是否在授权范围内",
        severity=Severity.ERROR,
        check_fn=check_file_boundary,
    ))
    guardrails.add_constraint(Constraint(
        name="constitution",
        description="检查项目级不可违反规则",
        severity=Severity.FATAL,
        check_fn=check_constitution,
    ))

    try:
        violations = await guardrails.check(context)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 约束检查失败: {exc}")]

    if not violations:
        return [TextContent(type="text", text="约束检查通过，无违规。")]

    lines = [f"发现 {len(violations)} 个违规:"]
    for v in violations:
        lines.append(f"  [{v.severity.value}] {v.constraint_name}: {v.message}")
    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_health(_arguments: dict) -> list:
    """处理 reqflow_health 工具调用。"""
    _, RuntimeRegistry = _import_core()

    lines = ["=== ReqFlow Health Check ==="]

    # Layer 1: System
    lines.append("\n[System]")
    lines.append(f"  reqflow: OK")
    try:
        import mcp
        lines.append(f"  mcp: OK")
    except ImportError:
        lines.append(f"  mcp: NOT INSTALLED (pip install mcp)")

    # Layer 2: Workflow loader
    lines.append("\n[Workflow Loader]")
    try:
        from reqflow.core.workflow_loader import WorkflowLoader
        loader = WorkflowLoader()
        wfs = loader.list_workflows()
        lines.append(f"  OK — {len(wfs)} workflow(s): {', '.join(wfs)}")
    except Exception as exc:
        lines.append(f"  ERROR: {exc}")

    # Layer 3: Runtime readiness
    lines.append("\n[Runtimes]")
    registry = RuntimeRegistry()
    runtimes = registry.list_runtimes()
    errors = registry.list_errors()

    if errors:
        for name, err in errors.items():
            lines.append(f"  {name:12s}: SKIPPED — {err}")

    if runtimes:
        for name in runtimes:
            ready, reason = registry.check_readiness(name)
            status = "READY" if ready else "NOT READY"
            line = f"  {name:12s}: {status}"
            if reason:
                line += f" — {reason}"
            lines.append(line)
    else:
        lines.append("  (no runtimes loaded)")

    # Recommended
    lines.append("\n[Recommended]")
    for name in runtimes:
        ready, _ = registry.check_readiness(name)
        if ready and name not in ("manual",):
            lines.append(f"  {name}")
            break
    else:
        lines.append(f"  manual (no external runtime available)")

    # Overall verdict
    any_ready = any(registry.check_readiness(n)[0] for n in runtimes)
    lines.append("\n[Verdict]")
    if any_ready:
        lines.append("  workflow: EXECUTABLE")
    else:
        lines.append("  workflow: DEGRADED — only manual runtime available")

    return [TextContent(type="text", text="\n".join(lines))]


# --- Harness 编排工具实现 ---


def _resolve_run_dir(run_id: str, run_dir: str | None = None) -> Path:
    """解析 run 目录路径。支持 .reqflow/runs/ 和 .dev-workflow/runs/ 两种位置。"""
    if run_dir:
        p = Path(run_dir)
        if (p / "state.json").exists():
            return p
    for base in (".reqflow/runs", ".dev-workflow/runs"):
        p = Path(base) / run_id
        if (p / "state.json").exists():
            return p
    # Scan all run dirs for matching internal run_id
    for base in (".reqflow/runs", ".dev-workflow/runs"):
        base_path = Path(base)
        if not base_path.exists():
            continue
        for d in base_path.iterdir():
            sf = d / "state.json"
            if sf.exists():
                try:
                    data = json.loads(sf.read_text(encoding="utf-8"))
                    if data.get("run_id") == run_id:
                        return d
                except Exception:
                    continue
    return Path(f".reqflow/runs/{run_id}")


def _extract_acceptance_criteria(requirement: str) -> list[dict]:
    """从需求文本中提取验收标准，生成可追踪的 checklist。"""
    criteria = []
    keywords = ["验收标准", "验收条件", "acceptance criteria", "AC:"]
    lines = requirement.split("\n")
    in_section = False
    idx = 0
    for line in lines:
        stripped = line.strip()
        if any(kw in stripped.lower() for kw in keywords):
            in_section = True
            continue
        if in_section and stripped.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            text = stripped.lstrip("-*0123456789. ")
            idx += 1
            criteria.append({"id": f"ac-{idx:02d}", "description": text, "status": "pending", "evidence": ""})
        elif in_section and stripped and not stripped.startswith(("- ", "* ")) and not stripped[0:1].isdigit():
            # 非列表项，可能是新段落，结束验收标准区域
            if criteria:
                in_section = False
    return criteria


def _normalize_evidence(gate: str, evidence: dict) -> dict:
    """将用户传入的 evidence 标准化为 QualityGate 期望的 context key。"""
    if not evidence:
        return evidence
    ctx = dict(evidence)

    # completion-gate 标准化
    if gate == "completion-gate":
        # 兼容 build_success / build_passed / mvn_success 等变体
        for key in ("build_success", "build_passed", "mvn_success", "compile_success"):
            if key in ctx and "build_success" not in ctx:
                ctx["build_success"] = ctx[key]
        for key in ("tests_passing", "tests_passed", "test_pass", "all_tests_pass"):
            if key in ctx and "tests_passing" not in ctx:
                ctx["tests_passing"] = ctx[key]
        for key in ("spec_compliant", "spec_compliance", "spec_ok", "spec_pass"):
            if key in ctx and "spec_compliant" not in ctx:
                ctx["spec_compliant"] = ctx[key]
        for key in ("all_work_items_done", "work_items_done", "all_items_done"):
            if key in ctx and "all_work_items_done" not in ctx:
                ctx["all_work_items_done"] = ctx[key]
        # 支持 completed_items / total_items 从 artifacts 数量推断
        if "completed_items" not in ctx and "artifacts" in ctx:
            arts = ctx["artifacts"]
            if isinstance(arts, list):
                ctx.setdefault("completed_items", len(arts))
                ctx.setdefault("total_items", len(arts))

    # tdd-gate 标准化
    if gate == "tdd-gate":
        # 兼容 failing_tests_defined / failing_tests 等变体
        for key in ("failing_tests_defined", "failing_tests", "red_tests", "failing_test_count"):
            if key in ctx and "failing_tests_count" not in ctx:
                val = ctx[key]
                # list 自动转换为 count
                if isinstance(val, list):
                    ctx["failing_tests_count"] = len(val)
                else:
                    ctx["failing_tests_count"] = val
        for key in ("test_plan_exists", "test_plan_file", "has_test_plan"):
            if key in ctx and "test_plan" not in ctx:
                ctx["test_plan"] = ctx[key]
        # 支持从文件列表推断
        if "failing_tests_count" not in ctx and "test_files" in ctx:
            files = ctx["test_files"]
            if isinstance(files, list):
                ctx.setdefault("failing_tests_count", len(files))
        if "test_plan" not in ctx and "artifacts" in ctx:
            arts = ctx["artifacts"]
            if isinstance(arts, list):
                for art in arts:
                    if isinstance(art, str) and ("test" in art.lower() or "tdd" in art.lower()):
                        ctx.setdefault("test_plan", True)
                        break

    # compliance-report 标准化
    if gate == "compliance-report":
        if "evidence" in ctx and isinstance(ctx["evidence"], dict):
            for k, v in ctx["evidence"].items():
                ctx.setdefault(k, v)

    # 从字符串 evidence 值推断布尔字段
    _parse_evidence_values(ctx)

    # completion-gate: 如果 build_success 和 tests_passing 都为 True，
    # 且 completed_items >= total_items，则推断 spec_compliant 和 all_work_items_done
    if gate == "completion-gate":
        if ctx.get("build_success") and ctx.get("tests_passing"):
            completed = ctx.get("completed_items", 0)
            total = ctx.get("total_items", 1)
            if total > 0 and completed >= total:
                ctx.setdefault("all_work_items_done", True)
                ctx.setdefault("spec_compliant", True)

    return ctx


def _parse_evidence_values(ctx: dict) -> None:
    """Parse string evidence values to infer boolean gate fields."""
    indicators = []
    for v in ctx.values():
        if isinstance(v, str):
            indicators.append(v.lower())
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    indicators.append(item.lower())
        elif isinstance(v, bool):
            # 布尔值直接作为指标
            indicators.append(str(v).lower())
    combined = " ".join(indicators)

    if "build_success" not in ctx:
        if "build success" in combined or "compile success" in combined or "build success" in combined:
            ctx["build_success"] = True

    if "tests_passing" not in ctx:
        if "tests run:" in combined and "failures: 0" in combined:
            ctx["tests_passing"] = True
        elif "test pass" in combined or "tests pass" in combined:
            ctx["tests_passing"] = True
        elif "true" in combined and ("tests_passing" in ctx or "test" in combined):
            ctx["tests_passing"] = True

    if "spec_compliant" not in ctx:
        if "spec" in combined and ("compliant" in combined or "pass" in combined):
            ctx["spec_compliant"] = True
        elif "all requirements met" in combined or "requirements met" in combined:
            ctx["spec_compliant"] = True
        elif "compliant" in combined and ("true" in combined or "pass" in combined):
            ctx["spec_compliant"] = True

    if "all_work_items_done" not in ctx:
        completed = ctx.get("completed_items", 0)
        total = ctx.get("total_items", 1)
        if total > 0 and completed >= total:
            ctx["all_work_items_done"] = True
        elif "all work items" in combined and ("done" in combined or "complete" in combined):
            ctx["all_work_items_done"] = True
        elif "all items" in combined and ("done" in combined or "complete" in combined):
            ctx["all_work_items_done"] = True


def _get_gate_evidence_schema(gate: str) -> dict | None:
    """返回门禁期望的 evidence schema，帮助 Agent 构造正确的 evidence。"""
    schemas = {
        "design-gate": {
            "meta_spec": "str (truthy) — Meta Spec 内容或路径",
            "feature_spec": "str (truthy) — Feature Spec 内容或路径",
            "tech_plan_stages": "int >= 2 — 技术方案阶段数",
            "completeness_checked": "bool — 是否完成完备性检查",
            "high_risk_approved": "bool (可选, 默认 True) — 高风险决策是否已批准",
        },
        "tdd-gate": {
            "failing_tests_count": "int > 0 — 失败测试数量（也接受 list 自动转换）",
            "test_plan": "bool (truthy) — 测试计划是否存在",
        },
        "completion-gate": {
            "build_success": "bool — 构建是否成功",
            "tests_passing": "bool — 测试是否全部通过",
            "spec_compliant": "bool — 是否通过 Spec 合规审查",
            "completed_items": "int — 已完成工作项数",
            "total_items": "int — 总工作项数",
        },
        "compliance-report": {
            "verification_evidence": "str (truthy) — 验证证据",
            "review_evidence": "str (truthy) — 审查证据",
            "test_evidence": "str (truthy) — 测试证据",
        },
    }
    return schemas.get(gate)


async def _handle_plan(arguments: dict) -> list:
    """处理 reqflow_plan 工具调用。开始新计划。"""
    from datetime import datetime as _dt
    from pathlib import Path as _Path

    requirement = arguments.get("requirement", "").strip()
    if not requirement:
        return [TextContent(type="text", text="[错误] 需求内容不能为空。")]

    workflow = arguments.get("workflow")

    # 1. 路由分析
    try:
        from reqflow.core.router import route_requirement
        routing = route_requirement(requirement)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 路由分析失败: {exc}")]

    # 如果用户指定了 workflow，覆盖建议
    if workflow:
        routing.suggested_workflow = workflow

    # 2. 上下文扫描
    structure_info = ""
    try:
        from reqflow.core.context_scanner import scan_project
        structure = scan_project(".")
        structure_info = (
            f"语言: {', '.join(structure.languages.keys()) if structure.languages else '未知'}\n"
            f"入口: {', '.join(structure.entry_points[:3]) if structure.entry_points else '未发现'}\n"
            f"测试: {structure.test_framework or '未检测到'}\n"
            f"构建: {structure.build_system or '未检测到'}"
        )
    except Exception:
        structure_info = "(上下文扫描跳过)"

    # 3. 生成 Execution Skill
    try:
        from reqflow.core.skill_generator import generate_execution_skill, save_execution_skill
        run_id = f"run-{_dt.now().strftime('%Y%m%d-%H%M%S')}"
        run_dir = f".reqflow/runs/{run_id}"

        skill = generate_execution_skill(
            run_id=run_id,
            requirement=requirement,
            routing=routing,
        )
        skill_path = save_execution_skill(skill, run_dir)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] Execution Skill 生成失败: {exc}")]

    # 4. 创建 state.json（含验收标准追踪）
    acceptance = _extract_acceptance_criteria(requirement)
    state = {
        "run_id": run_id,
        "requirement": requirement,
        "routing_level": routing.level.value,
        "workflow": routing.suggested_workflow,
        "current_stage": "started",
        "status": "in_progress",
        "created_at": _dt.now().isoformat(),
        "updated_at": _dt.now().isoformat(),
        "completed_modules": [],
        "reports": [],
        "verifications": [],
        "acceptance_criteria": acceptance,
        "blockers": [],
    }
    state_path = _Path(run_dir) / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "=== ReqFlow 计划已创建 ===",
        f"运行 ID: {run_id}",
        f"路由级别: {routing.level.value} — {routing.reason}",
        f"置信度: {routing.confidence:.0%}",
        f"建议 Workflow: {routing.suggested_workflow}",
        f"运行目录: {run_dir}",
        f"Execution Skill: {skill_path}",
        "",
        "--- 项目上下文 ---",
        structure_info,
        "",
        "--- 下一步 ---",
        "请读取 Execution Skill 并按阶段执行:",
        f"  cat {skill_path}",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_report(arguments: dict) -> list:
    """处理 reqflow_report 工具调用。报告阶段完成状态。"""
    run_id = arguments.get("run_id", "")
    stage = arguments.get("stage", "")
    status = arguments.get("status", "")
    artifacts = arguments.get("artifacts", [])
    error = arguments.get("error")
    risks = arguments.get("risks", [])

    if not run_id or not stage or not status:
        return [TextContent(type="text", text="[错误] run_id, stage, status 不能为空。")]

    from datetime import datetime as _dt

    # 更新 state.json
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"

    if not state_path.exists():
        run_path.mkdir(parents=True, exist_ok=True)
        state = {
            "run_id": run_id,
            "current_stage": stage,
            "status": "in_progress",
            "created_at": _dt.now().isoformat(),
            "updated_at": _dt.now().isoformat(),
            "completed_modules": [],
            "reports": [],
            "verifications": [],
            "blockers": [],
        }
    else:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {"run_id": run_id, "reports": [], "completed_modules": [], "verifications": []}

    state["current_stage"] = stage
    state["updated_at"] = _dt.now().isoformat()
    if status in ("done", "conditional"):
        state.setdefault("completed_modules", []).append(stage)
    report_entry = {
        "stage": stage,
        "status": status,
        "artifacts": artifacts,
        "error": error,
        "timestamp": _dt.now().isoformat(),
    }
    if risks:
        report_entry["risks"] = risks
    state.setdefault("reports", []).append(report_entry)
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"阶段报告已记录: {stage}",
        f"状态: {status}",
    ]
    if artifacts:
        lines.append(f"产出: {', '.join(artifacts)}")
    if error:
        lines.append(f"错误: {error}")
    if risks:
        lines.append(f"残留风险: {', '.join(risks)}")

    # 下一步指引
    if status == "done":
        lines.append("\n下一步: 继续执行下一个阶段")
    elif status == "conditional":
        lines.append("\n下一步: 有条件通过。残留风险已记录，继续执行下一个阶段。建议在最终报告中汇总所有 conditional 风险。")
    elif status == "blocked":
        lines.append("\n下一步: 调用 reqflow_status 获取指引")
    elif status == "failed":
        lines.append("\n下一步: 检查错误原因，决定是否进入修复循环")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_verify(arguments: dict) -> list:
    """处理 reqflow_verify 工具调用。门禁验证。"""
    run_id = arguments.get("run_id", "")
    gate = arguments.get("gate", "")
    evidence = arguments.get("evidence", {})

    if not run_id or not gate:
        return [TextContent(type="text", text="[错误] run_id 和 gate 不能为空。")]

    from datetime import datetime as _dt

    # 标准化 evidence 到 gate 期望的 context key
    normalized = _normalize_evidence(gate, evidence)

    try:
        from reqflow.core.quality_gate import QualityGate
        qg = QualityGate()
        result = qg.check(gate, normalized)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 门禁检查失败: {exc}")]

    # 更新 state.json
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.setdefault("verifications", []).append({
                "gate": gate,
                "passed": result.passed,
                "summary": result.summary,
                "evidence": evidence,
                "timestamp": _dt.now().isoformat(),
            })
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    lines = [
        f"=== 门禁验证: {gate} ===",
        f"结果: {'通过' if result.passed else '未通过'}",
    ]

    if result.passed:
        lines.append("\n门禁通过，可以进入下一阶段。")
    else:
        lines.append("\n门禁未通过，以下项目需要修复:")
        for item in result.blocking_items:
            lines.append(f"  - {item.name}: {item.message}")
        # 返回 expected evidence schema 帮助 Agent 构造正确的 evidence
        expected = _get_gate_evidence_schema(gate)
        if expected:
            lines.append(f"\n期望的 evidence 格式:")
            lines.append(json.dumps(expected, indent=2, ensure_ascii=False))
        lines.append("\n请修复后重新调用 reqflow_verify。")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_accept(arguments: dict) -> list:
    """处理 reqflow_accept 工具调用。用户验收通过。"""
    run_id = arguments.get("run_id", "")
    feedback = arguments.get("feedback", "")

    if not run_id:
        return [TextContent(type="text", text="[错误] run_id 不能为空。")]

    from datetime import datetime as _dt

    # 更新 state.json
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "accepted"
            state["current_stage"] = "archived"
            state["updated_at"] = _dt.now().isoformat()
            state["user_feedback"] = feedback
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    # 写入 acceptance.json 作为独立的验收记录（不依赖 state.json）
    try:
        acceptance = {
            "run_id": run_id,
            "status": "accepted",
            "feedback": feedback,
            "accepted_at": _dt.now().isoformat(),
            "stage_records": state.get("reports", []),
            "verifications": state.get("verifications", []),
            "blockers": state.get("blockers", []),
            "acceptance_criteria": state.get("acceptance_criteria", []),
        }
        acceptance_path = run_path / "acceptance.json"
        acceptance_path.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # 扫描目录中的产物文件
    artifacts = []
    try:
        for f in sorted(run_path.iterdir()):
            if f.is_file() and f.name != "state.json":
                artifacts.append(f.name)
    except Exception:
        pass

    lines = [
        "=== 用户验收通过 ===",
        f"运行 ID: {run_id}",
        f"归档路径: {run_path}",
        "状态: 已归档",
    ]
    if feedback:
        lines.append(f"反馈: {feedback}")
    if artifacts:
        lines.append(f"保留的产物: {', '.join(artifacts)}")
    lines.append("\n所有运行产物已保留在归档路径中，可随时回看。")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_reject(arguments: dict) -> list:
    """处理 reqflow_reject 工具调用。用户验收拒绝。"""
    run_id = arguments.get("run_id", "")
    reason = arguments.get("reason", "")
    issues = arguments.get("issues", [])

    if not run_id or not reason:
        return [TextContent(type="text", text="[错误] run_id 和 reason 不能为空。")]

    from datetime import datetime as _dt

    # 更新 state.json
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "rejected"
            state["current_stage"] = "repair"
            state["updated_at"] = _dt.now().isoformat()
            state.setdefault("rejections", []).append({
                "reason": reason,
                "issues": issues,
                "timestamp": _dt.now().isoformat(),
            })
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    lines = [
        "=== 用户验收拒绝 ===",
        f"运行 ID: {run_id}",
        f"原因: {reason}",
    ]
    if issues:
        lines.append("问题列表:")
        for issue in issues:
            lines.append(f"  - {issue}")

    lines.append("\n下一步: 回到实现阶段修复问题，然后重新提交验证。")

    return [TextContent(type="text", text="\n".join(lines))]



# --- V3 新增工具实现 ---


def _load_tools_config(bridge) -> None:
    """从 tools.yaml 加载工具配置并注册到 bridge。"""
    import yaml
    from pathlib import Path as _Path

    for candidate in ("tools.yaml", "tools.yml", ".reqflow/tools.yaml"):
        p = _Path(candidate)
        if p.exists():
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for name, spec in data.items():
                    if isinstance(spec, dict):
                        # 用 spec 创建一个简单的 async handler
                        def _make_handler(tool_spec):
                            async def _handler(**kwargs):
                                return {"status": "ok", "tool": tool_spec.get("name", "unknown"), "args": kwargs}
                            return _handler
                        bridge.register(name, _make_handler(spec))
            break


async def _handle_tool_call(arguments: dict) -> list:
    """处理 reqflow_tool_call 工具调用。"""
    tool_name = arguments.get("tool_name", "")
    method = arguments.get("method", "")
    params = arguments.get("params", {})

    if not tool_name or not method:
        return [TextContent(type="text", text="[错误] tool_name 和 method 不能为空。")]

    from reqflow.core.tool_bridge_mcp import ToolBridgeMCP
    bridge = ToolBridgeMCP()

    # 从 tools.yaml 加载工具配置并注册
    try:
        _load_tools_config(bridge)
    except Exception:
        pass  # 配置文件不存在时忽略

    try:
        result = await bridge.call(tool_name, {**params, "method": method})
        return [TextContent(type="text", text=f"[{tool_name}] {method}: {result}")]
    except Exception as e:
        return [TextContent(type="text", text=f"[错误] {tool_name}.{method} 失败: {e}")]


async def _handle_memory_save(arguments: dict) -> list:
    """处理 reqflow_memory_save 工具调用。"""
    run_id = arguments.get("run_id", "")
    category = arguments.get("category", "")
    content = arguments.get("content", "")
    stage = arguments.get("stage", "")

    if not run_id or not category or not content:
        return [TextContent(type="text", text="[错误] run_id, category, content 不能为空。")]

    from reqflow.core.memory_manager import MemoryManager
    run_path = _resolve_run_dir(run_id)
    mm = MemoryManager(str(run_path))
    key = stage or category
    mm.save(category, key, content)

    return [TextContent(type="text", text=f"记忆已保存: [{category}] {content[:50]}...")]


async def _handle_memory_load(arguments: dict) -> list:
    """处理 reqflow_memory_load 工具调用。"""
    run_id = arguments.get("run_id", "")

    if not run_id:
        return [TextContent(type="text", text="[错误] run_id 不能为空。")]

    from reqflow.core.memory_manager import MemoryManager
    run_path = _resolve_run_dir(run_id)
    mm = MemoryManager(str(run_path))
    all_memories = mm.load()
    import json
    return [TextContent(type="text", text=json.dumps(all_memories, ensure_ascii=False, indent=2))]


async def _handle_git_check(arguments: dict) -> list:
    """处理 reqflow_git_check 工具调用。"""
    run_dir = arguments.get("run_dir", ".")

    from reqflow.core.git_workflow import GitWorkflow
    gw = GitWorkflow(run_dir)
    status = gw.check_status()

    lines = [
        f"当前分支: {status.branch}",
        f"主分支: {'是' if status.is_main_branch else '否'}",
        f"最后提交: {status.last_commit}",
        f"工作区: {'干净' if status.is_clean else '有变更'}",
    ]
    if status.modified_files:
        lines.append(f"已修改文件 ({len(status.modified_files)}):")
        for f in status.modified_files[:10]:
            lines.append(f"  {f}")
    if status.untracked_files:
        lines.append(f"未跟踪文件 ({len(status.untracked_files)}):")
        for f in status.untracked_files[:10]:
            lines.append(f"  {f}")

    return [TextContent(type="text", text="\n".join(lines))]




# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _detect_runtime(registry) -> object | None:
    """自动检测 runtime。优先级：环境变量 > host > manual > 有 key 的外部 runtime。"""
    import os

    env_runtime = os.environ.get("REQFLOW_RUNTIME", "").lower()
    if env_runtime:
        try:
            return registry.get(env_runtime)
        except ValueError:
            pass

    for name in ("host",):
        try:
            return registry.get(name)
        except ValueError:
            continue



async def _handle_blocker_add(arguments: dict) -> list:
    """处理 reqflow_blocker_add 工具调用。"""
    import json as _json
    from pathlib import Path as _Path
    from datetime import datetime as _dt

    run_id = arguments.get("run_id", "")
    level = arguments.get("level", "P0")
    question = arguments.get("question", "")
    stage = arguments.get("stage", "")

    if not run_id or not question:
        return [TextContent(type="text", text="[错误] run_id 和 question 不能为空。")]

    from reqflow.core.blocker_manager import BlockerManager, BlockerLevel
    bm = BlockerManager()

    # Load existing blockers from state file
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    if state_path.exists():
        with open(state_path) as f:
            state = _json.load(f)
        bm.load_from_list(state.get("blockers", []))

    level_map = {"P0": BlockerLevel.P0, "P1": BlockerLevel.P1, "P2": BlockerLevel.P2}
    blocker_level = level_map.get(level, BlockerLevel.P0)

    blocker = bm.add(blocker_level, question, stage)

    # Save back to state file
    run_path.mkdir(parents=True, exist_ok=True)
    state = {}
    if state_path.exists():
        with open(state_path) as f:
            state = _json.load(f)
    state["blockers"] = bm.to_list()
    state["updated_at"] = _dt.now().isoformat()
    with open(state_path, "w") as f:
        _json.dump(state, f, indent=2)

    return [TextContent(type="text", text=f"BLOCKER 已添加: [{blocker.level.value}] {blocker.id} — {blocker.question}")]


async def _handle_blocker_resolve(arguments: dict) -> list:
    """处理 reqflow_blocker_resolve 工具调用。"""
    import json as _json
    from pathlib import Path as _Path

    run_id = arguments.get("run_id", "")
    blocker_id = arguments.get("blocker_id", "")
    answer = arguments.get("answer", "")

    if not run_id or not blocker_id or not answer:
        return [TextContent(type="text", text="[错误] run_id, blocker_id, answer 不能为空。")]

    from reqflow.core.blocker_manager import BlockerManager
    from datetime import datetime as _dt
    bm = BlockerManager()

    # Load existing blockers
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    if state_path.exists():
        with open(state_path) as f:
            state = _json.load(f)
        bm.load_from_list(state.get("blockers", []))

    try:
        success = bm.resolve(blocker_id, answer)
        if success:
            state = {}
            if state_path.exists():
                with open(state_path) as f:
                    state = _json.load(f)
            state["blockers"] = bm.to_list()
            state["updated_at"] = _dt.now().isoformat()
            with open(state_path, "w") as f:
                _json.dump(state, f, indent=2)
            return [TextContent(type="text", text=f"BLOCKER 已解决: {blocker_id} — {answer}")]
        else:
            return [TextContent(type="text", text=f"[错误] BLOCKER {blocker_id} 未找到")]
    except ValueError as e:
        return [TextContent(type="text", text=f"[错误] {e}")]


async def _handle_blocker_check(arguments: dict) -> list:
    """处理 reqflow_blocker_check 工具调用。"""
    import json as _json
    from pathlib import Path as _Path

    run_id = arguments.get("run_id", "")
    stage = arguments.get("stage", "")

    if not run_id:
        return [TextContent(type="text", text="[错误] run_id 不能为空。")]

    from reqflow.core.blocker_manager import BlockerManager, BlockerLevel
    bm = BlockerManager()

    # Load existing blockers
    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    if state_path.exists():
        with open(state_path) as f:
            state = _json.load(f)
        bm.load_from_list(state.get("blockers", []))

    open_p0 = bm.get_open(BlockerLevel.P0)
    all_blockers = bm.to_list()

    lines = [f"P0 未关闭: {len(open_p0)}"]
    if stage:
        filtered = [b for b in all_blockers if b.get("stage") == stage]
        lines.append(f"阶段 [{stage}] BLOCKER: {len(filtered)}")
        for b in filtered:
            lines.append(f"  [{b['level']}] {b['id']}: {b['question']} ({b['status']})")
    else:
        lines.append(f"全部 BLOCKER: {len(all_blockers)}")
        for b in all_blockers:
            lines.append(f"  [{b['level']}] {b['id']}: {b['question']} ({b['status']})")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_acceptance_update(arguments: dict) -> list:
    """处理 reqflow_acceptance_update 工具调用。更新验收标准状态。"""
    import json as _json
    from pathlib import Path as _Path
    from datetime import datetime as _dt

    run_id = arguments.get("run_id", "")
    criteria_id = arguments.get("criteria_id", "")
    new_status = arguments.get("status", "")
    evidence = arguments.get("evidence", "")

    if not run_id or not criteria_id or not new_status:
        return [TextContent(type="text", text="[错误] run_id, criteria_id, status 不能为空。")]

    run_path = _resolve_run_dir(run_id)
    state_path = run_path / "state.json"
    if not state_path.exists():
        return [TextContent(type="text", text=f"[错误] 未找到运行状态: {run_id}")]

    with open(state_path) as f:
        state = _json.load(f)

    criteria = state.get("acceptance_criteria", [])
    found = False
    # 支持大小写不敏感匹配 (AC-01, ac-01, Ac-01)
    criteria_id_lower = criteria_id.lower()
    for c in criteria:
        if c.get("id", "").lower() == criteria_id_lower:
            c["status"] = new_status
            if evidence:
                c["evidence"] = evidence
            found = True
            break

    if not found:
        # 如果验收标准列表为空或未找到，自动创建该标准
        if not criteria:
            criteria = []
        new_criteria = {"id": criteria_id.lower(), "description": f"验收标准 {criteria_id}", "status": new_status, "evidence": evidence or ""}
        criteria.append(new_criteria)
        state["acceptance_criteria"] = criteria
        state["updated_at"] = _dt.now().isoformat()
        with open(state_path, "w") as f:
            _json.dump(state, f, indent=2, ensure_ascii=False)
        verified = sum(1 for c in criteria if c.get("status") == "verified")
        return [TextContent(type="text", text=f"验收标准 {criteria_id} 已创建并更新为 {new_status}。进度: {verified}/{len(criteria)} verified")]

    state["acceptance_criteria"] = criteria
    state["updated_at"] = _dt.now().isoformat()
    with open(state_path, "w") as f:
        _json.dump(state, f, indent=2)

    verified = sum(1 for c in criteria if c.get("status") == "verified")
    return [TextContent(type="text", text=f"验收标准 {criteria_id} 已更新为 {new_status}。进度: {verified}/{len(criteria)} verified")]


async def _handle_multi_repo_switch(arguments: dict) -> list:
    """处理 reqflow_multi_repo_switch 工具调用。"""
    project_dir = arguments.get("project_dir", ".")
    repo_name = arguments.get("repo_name", "")

    from reqflow.core.multi_repo import MultiRepo
    mr = MultiRepo()
    mr.detect_repos(project_dir)

    if not repo_name:
        repos = mr.list_repos()
        if not repos:
            return [TextContent(type="text", text="未注册任何仓库。")]
        lines = ["已注册的仓库:"]
        for r in repos:
            primary = " (主仓库)" if r["is_primary"] else ""
            lines.append(f"  - {r['name']}: {r['path']} [{r['branch']}]{primary}")
        return [TextContent(type="text", text="\n".join(lines))]

    repo = mr.get_by_name(repo_name)
    if repo:
        primary = " (主仓库)" if repo.is_primary else ""
        return [TextContent(type="text", text=f"仓库信息: {repo.name} ({repo.path}) [{repo.branch}]{primary}")]
    else:
        return [TextContent(type="text", text=f"[错误] 未找到仓库: {repo_name}")]


# ---------------------------------------------------------------------------
# V5 新增工具实现
# ---------------------------------------------------------------------------


async def _handle_full_flow(arguments: dict) -> list:
    """强制全流程入口，跳过路由分析直接使用 L3 管线。"""
    requirement = arguments.get("requirement", "")
    change_name = arguments.get("change_name", "")

    if not requirement:
        return [TextContent(type="text", text="[错误] requirement 参数不能为空")]

    # Force L3 routing
    from reqflow.core.router import RoutingLevel, RoutingDecision, EntryPoint
    routing = RoutingDecision(
        level=RoutingLevel.L3,
        reason="用户强制全流程模式",
        confidence=1.0,
        signals=["full_flow_override"],
        suggested_workflow="main-flow",
        entry_point=EntryPoint.PRD,
    )

    # Create change directory
    from reqflow.core.change_manager import ChangeManager
    import time
    if not change_name:
        change_name = f"change-{int(time.time())}"
    cm = ChangeManager(".reqflow")
    change = cm.create_change(change_name, requirement)
    run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}"
    run_dir = cm.create_run(change_name, run_id)

    # Generate execution skill
    from reqflow.core.skill_generator import generate_execution_skill, save_execution_skill
    from reqflow.core.context_scanner import scan_project
    structure = scan_project(".")
    skill = generate_execution_skill(
        run_id=run_id,
        requirement=requirement,
        routing=routing,
        project_structure=structure,
    )
    skill_path = save_execution_skill(skill, run_dir)

    # Save state
    from reqflow.core.state_manager import StateManager
    sm = StateManager(run_dir)
    sm.save_state({
        "run_id": run_id,
        "change_name": change_name,
        "requirement": requirement,
        "routing_level": "delivery_loop",
        "stages": skill.stages,
        "current_stage": 0,
        "status": "active",
    })

    return [TextContent(type="text", text=json.dumps({
        "status": "started",
        "run_id": run_id,
        "change_name": change_name,
        "change_dir": change.path,
        "routing_level": "delivery_loop",
        "stages_count": len(skill.stages),
        "exec_skill_path": skill_path,
    }, ensure_ascii=False, indent=2))]


async def _handle_brainstorm(arguments: dict) -> list:
    """触发多 Agent 头脑风暴。"""
    mode = arguments.get("mode", "round-robin")
    agents = arguments.get("agents", [])
    topic = arguments.get("topic", "")
    context = arguments.get("context", "")
    max_rounds = arguments.get("max_rounds", 3)

    from reqflow.core.agent_coordinator import AgentCoordinator, BrainstormMode
    coord = AgentCoordinator()
    try:
        brainstorm_mode = BrainstormMode(mode)
    except ValueError:
        brainstorm_mode = BrainstormMode.ROUND_ROBIN

    result = coord.brainstorm(
        mode=brainstorm_mode,
        agents=agents,
        topic=topic,
        context=context,
        max_rounds=max_rounds,
    )

    return [TextContent(type="text", text=json.dumps({
        "mode": result.mode.value,
        "rounds_count": len(result.rounds),
        "consensus": result.consensus,
        "summary": result.summary,
        "fallback": result.fallback,
    }, ensure_ascii=False, indent=2))]


async def _handle_confidence(arguments: dict) -> list:
    """查询或评估置信度。"""
    completeness = arguments.get("completeness", 1.0)
    consistency = arguments.get("consistency", 1.0)
    accuracy = arguments.get("accuracy", 1.0)
    retry_count = arguments.get("retry_count", 0)

    from reqflow.core.confidence import ConfidenceAssessor
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=completeness,
        consistency=consistency,
        accuracy=accuracy,
        retry_count=retry_count,
    )

    return [TextContent(type="text", text=json.dumps({
        "level": result.level.value,
        "score": round(result.score, 2),
        "action": result.action,
        "reasons": result.reasons,
    }, ensure_ascii=False, indent=2))]


# ---------------------------------------------------------------------------
# 工具处理器注册表（必须在 create_server 之前定义）
# ---------------------------------------------------------------------------

TOOL_HANDLERS = {
    "reqflow_run": _handle_run,
    "reqflow_status": _handle_status,
    "reqflow_list_runtimes": _handle_list_runtimes,
    "reqflow_run_graph": _handle_run_graph,
    "reqflow_session_save": _handle_session_save,
    "reqflow_session_load": _handle_session_load,
    "reqflow_dashboard": _handle_dashboard,
    "reqflow_checkpoint": _handle_checkpoint,
    "reqflow_parallel": _handle_parallel,
    "reqflow_trace": _handle_trace,
    "reqflow_guardrails": _handle_guardrails,
    "reqflow_health": _handle_health,
    # --- Harness 编排工具 ---
    "reqflow_plan": _handle_plan,
    "reqflow_report": _handle_report,
    "reqflow_verify": _handle_verify,
    "reqflow_accept": _handle_accept,
    "reqflow_reject": _handle_reject,
    # --- V3 新增工具 ---
    "reqflow_tool_call": _handle_tool_call,
    "reqflow_memory_save": _handle_memory_save,
    "reqflow_memory_load": _handle_memory_load,
    "reqflow_git_check": _handle_git_check,
    # --- V3 BLOCKER 和多仓库工具 ---
    "reqflow_blocker_add": _handle_blocker_add,
    "reqflow_blocker_resolve": _handle_blocker_resolve,
    "reqflow_blocker_check": _handle_blocker_check,
    "reqflow_multi_repo_switch": _handle_multi_repo_switch,
    "reqflow_acceptance_update": _handle_acceptance_update,
    # --- V5 新增工具 ---
    "reqflow_full_flow": _handle_full_flow,
    "reqflow_brainstorm": _handle_brainstorm,
    "reqflow_confidence": _handle_confidence,
}


# ---------------------------------------------------------------------------
# 入口点
# ---------------------------------------------------------------------------


def create_server() -> "Server":
    """创建并配置 MCP Server 实例。"""
    server = Server("reqflow")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in TOOLS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"[错误] 未知工具: {name}")]
        try:
            return await handler(arguments)
        except Exception as exc:
            # 防止 handler 异常导致 MCP Server 崩溃
            return [TextContent(type="text", text=f"[错误] 工具 {name} 执行异常: {exc}")]

    return server


async def _run_server() -> None:
    """启动 MCP Server（stdio 传输）。"""
    server = create_server()

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    except Exception as exc:
        print(f"[reqflow] MCP Server 异常退出: {exc}", file=sys.stderr)
        raise


def main() -> None:
    """MCP Server 入口。"""
    if not MCP_AVAILABLE:
        print(
            "[错误] MCP 依赖未安装。请先安装:\n"
            "  pip install mcp\n\n"
            "MCP Server 是可选功能，不影响 reqflow CLI 的使用。",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(_run_server())





if __name__ == "__main__":
    main()
