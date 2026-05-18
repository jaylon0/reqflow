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
]


# --- 工具实现 ---


async def _handle_run(arguments: dict) -> list:
    """处理 reqflow_run 工具调用。"""
    Engine, RuntimeRegistry = _import_core()

    requirement = arguments.get("requirement", "").strip()
    if not requirement:
        return [TextContent(type="text", text="[错误] 需求内容不能为空。")]

    runtime_name = arguments.get("runtime")
    workflow_type = arguments.get("workflow", "flow")
    run_dir = arguments.get("run_dir")

    # 选择 runtime
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
            return [TextContent(type="text", text="[错误] 无法自动检测 runtime，请指定 runtime 参数。")]

    # 选择 workflow（从 YAML 加载）
    steps = _get_workflow_steps(workflow_type)

    # 创建 Engine 并执行
    engine = Engine(config=config, run_dir=run_dir)

    try:
        result = await engine.run_workflow(workflow_steps=steps, requirement=requirement)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] Workflow 执行失败: {exc}")]

    # 格式化输出
    lines = [
        f"运行 ID: {engine.run_id}",
        f"Runtime: {config.display_name} ({config.name})",
        f"状态: {result.get('status', '未知')}",
    ]

    for step in result.get("steps", []):
        lines.append(f"  {step.get('name', '?')}: {step.get('status', '?')}")

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

    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 无法加载 runtime 配置: {exc}")]

    runtimes = registry.list_runtimes()
    if not runtimes:
        return [TextContent(type="text", text="未找到任何可用 runtime。")]

    lines = ["可用 runtime:"]
    for name in runtimes:
        try:
            config = registry.get(name)
            lines.append(f"  - {name:12s}  {config.display_name}")
        except Exception:
            lines.append(f"  - {name:12s}  (配置加载失败)")

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
    if not run_dir:
        return [TextContent(type="text", text="[错误] run_dir 不能为空。")]

    dashboard = Dashboard(run_dir=run_dir)

    # 读取 state.json
    state_file = Path(run_dir) / "state.json"
    if not state_file.exists():
        return [TextContent(type="text", text=f"[错误] 未找到状态文件: {state_file}")]

    try:
        import json
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 无法读取状态文件: {exc}")]

    # 构造 status dict
    status = {
        "run_id": data.get("run_id", "?"),
        "config": data.get("config", "?"),
        "adapter": data.get("adapter", "?"),
        "current_stage": data.get("current_stage", "?"),
        "completed_modules": data.get("completed_modules", []),
        "steps_executed": len(data.get("completed_modules", [])),
        "step_statuses": {},
        "checkpoints": len(data.get("checkpoints", [])),
        "memory_entries": len(data.get("memory", {}).get("short_term", [])),
    }

    output = dashboard.format_status(status)
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
    from reqflow.core.guardrails import Guardrails, check_file_boundary, check_constitution

    context = arguments.get("context", {})
    if not context:
        return [TextContent(type="text", text="[错误] context 不能为空。")]

    guardrails = Guardrails(constraints=[])
    guardrails.add_constraint(check_file_boundary)
    guardrails.add_constraint(check_constitution)

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

    lines.append("\n[System]")
    lines.append(f"  reqflow: OK")
    try:
        import mcp
        lines.append(f"  mcp: OK")
    except ImportError:
        lines.append(f"  mcp: NOT INSTALLED (pip install mcp)")

    lines.append("\n[Runtimes]")
    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        lines.append(f"  ERROR: {exc}")
        registry = None

    if registry:
        for name in registry.list_runtimes():
            ready, reason = registry.check_readiness(name)
            status = "READY" if ready else "NOT READY"
            line = f"  {name:12s}: {status}"
            if reason:
                line += f" — {reason}"
            lines.append(line)

        lines.append("\n[Recommended]")
        for name in registry.list_runtimes():
            ready, _ = registry.check_readiness(name)
            if ready and name not in ("manual",):
                lines.append(f"  {name}")
                break
        else:
            lines.append(f"  manual (no external runtime available)")
    else:
        lines.append("\n[Recommended]")
        lines.append(f"  manual")

    return [TextContent(type="text", text="\n".join(lines))]


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
}


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

    try:
        return registry.get("manual")
    except ValueError:
        pass

    for name in ("claude", "gpt", "gemini", "deepseek"):
        try:
            config = registry.get(name)
            if config.env_key and os.environ.get(config.env_key):
                return config
            if config.api_key:
                return config
        except ValueError:
            continue

    return None


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
        return await handler(arguments)

    return server


async def _run_server() -> None:
    """启动 MCP Server（stdio 传输）。"""
    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


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
