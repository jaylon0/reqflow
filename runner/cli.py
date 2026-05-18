"""ReqFlow CLI entry point.

Provides the ``reqflow`` command with subcommands:
    reqflow run <requirement>      执行 workflow
    reqflow run-graph <workflow>   执行图编排工作流
    reqflow checkpoint <action>    Checkpoint 管理
    reqflow trace <action>         执行追踪
    reqflow list-runtimes          列出可用 runtime
    reqflow status <run-dir>       查看运行状态
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 确保 reqflow 包可导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from reqflow.core import Engine, RuntimeRegistry, WorkflowLoader


def _get_workflow_steps(workflow_name: str) -> list[dict]:
    """从 YAML workflow 文件加载步骤定义。"""
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
# CLI 主入口
# ---------------------------------------------------------------------------


def main() -> None:
    """reqflow CLI main entry."""
    parser = argparse.ArgumentParser(
        prog="reqflow",
        description="ReqFlow - 模型无关的工作流编排引擎",
    )
    subparsers = parser.add_subparsers(dest="command")

    # reqflow run <requirement>
    run_parser = subparsers.add_parser("run", help="执行 workflow")
    run_parser.add_argument(
        "requirement",
        help="需求文本，或指向需求文件的路径",
    )
    run_parser.add_argument(
        "--runtime",
        default=None,
        help="Runtime 名称 (claude, gpt, gemini, deepseek, manual)",
    )
    run_parser.add_argument(
        "--run-dir",
        default=None,
        help="运行目录路径（默认自动生成）",
    )
    run_parser.add_argument(
        "--workflow",
        default="flow",
        choices=["flow", "main-flow"],
        help="Workflow 类型 (默认: flow)",
    )

    # reqflow list-runtimes
    subparsers.add_parser("list-runtimes", help="列出可用 runtime")

    # reqflow status <run-dir>
    status_parser = subparsers.add_parser("status", help="查看运行状态")
    status_parser.add_argument("run_dir", help="运行目录路径")

    # reqflow run-graph <workflow>
    run_graph_parser = subparsers.add_parser("run-graph", help="执行图编排工作流")
    run_graph_parser.add_argument("workflow", help="图工作流名称")
    run_graph_parser.add_argument("--requirement", default="", help="需求文本")
    run_graph_parser.add_argument("--runtime", default=None, help="Runtime 名称")
    run_graph_parser.add_argument("--run-dir", default=None, help="运行目录路径")

    # reqflow checkpoint <action>
    checkpoint_parser = subparsers.add_parser("checkpoint", help="Checkpoint 管理")
    checkpoint_parser.add_argument("checkpoint_action", choices=["list", "create", "restore"], help="操作类型")
    checkpoint_parser.add_argument("--run-dir", required=True, help="运行目录路径")
    checkpoint_parser.add_argument("--stage", default=None, help="阶段名称（create 时使用）")
    checkpoint_parser.add_argument("--checkpoint-id", default=None, help="检查点 ID（restore 时使用）")

    # reqflow trace <action>
    trace_parser = subparsers.add_parser("trace", help="执行追踪")
    trace_parser.add_argument("trace_action", choices=["summary", "export"], help="操作类型")
    trace_parser.add_argument("--run-dir", required=True, help="运行目录路径")
    trace_parser.add_argument("--output", default=None, help="导出文件路径（export 时使用）")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_workflow(args))
    elif args.command == "run-graph":
        asyncio.run(_handle_run_graph_cmd(args))
    elif args.command == "checkpoint":
        _handle_checkpoint_cmd(args)
    elif args.command == "trace":
        _handle_trace_cmd(args)
    elif args.command == "list-runtimes":
        list_runtimes()
    elif args.command == "status":
        show_status(args.run_dir)
    else:
        parser.print_help()


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------


async def run_workflow(args: argparse.Namespace) -> None:
    """执行 workflow 的核心逻辑。"""
    # 1. 读取 requirement（如果是文件路径则读取内容）
    requirement = _read_requirement(args.requirement)
    if not requirement:
        print("[错误] 需求内容为空，请提供有效的需求文本或文件路径。", file=sys.stderr)
        sys.exit(1)

    # 2. 确定 runtime
    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        print(f"[警告] 无法加载 runtime 配置: {exc}", file=sys.stderr)
        registry = None

    if args.runtime:
        if registry is None:
            print("[错误] 无法加载 runtime 注册表，无法指定 runtime。", file=sys.stderr)
            sys.exit(1)
        try:
            config = registry.get(args.runtime)
        except ValueError as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        # 自动检测
        if registry is not None:
            # 简单启发式: 按优先级尝试
            detected = _detect_runtime(registry)
            if detected:
                config = detected
                print(f"[信息] 自动检测到 runtime: {config.name}")
            else:
                print("[错误] 无法自动检测 runtime，请使用 --runtime 指定。", file=sys.stderr)
                sys.exit(1)
        else:
            print("[错误] 无可用 runtime，请使用 --runtime 指定。", file=sys.stderr)
            sys.exit(1)

    # 3. 创建 Engine
    engine = Engine(config=config, run_dir=args.run_dir)
    print(f"[信息] 运行 ID: {engine.run_id}")
    print(f"[信息] Runtime: {config.display_name} ({config.name})")
    print(f"[信息] Workflow: {args.workflow}")
    print(f"[信息] 运行目录: {engine.run_dir}")
    print()

    # 4. 选择 workflow steps（从 YAML 加载）
    steps = _get_workflow_steps(args.workflow)

    # 5. 执行
    print("=" * 60)
    print("开始执行 workflow ...")
    print("=" * 60)

    try:
        result = await engine.run_workflow(workflow_steps=steps, requirement=requirement)
    except Exception as exc:
        print(f"\n[错误] Workflow 执行失败: {exc}", file=sys.stderr)
        sys.exit(1)

    # 6. 输出结果
    print()
    print("=" * 60)
    print("Workflow 执行完成")
    print("=" * 60)
    print(f"  状态: {result.get('status', '未知')}")

    step_results = result.get("steps", [])
    if step_results:
        print("  步骤:")
        for step in step_results:
            status_icon = _status_icon(step.get("status", ""))
            print(f"    {status_icon} {step.get('name', '?')}: {step.get('status', '?')}")

    if result.get("error"):
        print(f"  错误: {result['error']}")

    if result.get("abort_reason"):
        print(f"  中止原因: {result['abort_reason']}")

    print()
    print(f"详细信息请查看: {engine.run_dir}/state.json")


def list_runtimes() -> None:
    """列出所有可用 runtime。"""
    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        print(f"[错误] 无法加载 runtime 配置: {exc}", file=sys.stderr)
        sys.exit(1)

    runtimes = registry.list_runtimes()
    if not runtimes:
        print("未找到任何可用 runtime。")
        return

    print("可用 runtime:")
    for name in runtimes:
        try:
            config = registry.get(name)
            print(f"  - {name:12s}  {config.display_name}")
        except Exception:
            print(f"  - {name:12s}  (配置加载失败)")


def show_status(run_dir: str) -> None:
    """读取 state.json 并展示运行状态。"""
    state_file = Path(run_dir) / "state.json"
    if not state_file.exists():
        print(f"[错误] 未找到状态文件: {state_file}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[错误] 无法读取状态文件: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"运行 ID:    {data.get('run_id', '?')}")
    print(f"当前阶段:   {data.get('current_stage', '?')}")
    print(f"规格状态:   {data.get('spec_status', '?')}")
    print(f"创建时间:   {data.get('created_at', '?')}")
    print(f"更新时间:   {data.get('updated_at', '?')}")

    completed = data.get("completed_modules", [])
    if completed:
        print(f"已完成模块 ({len(completed)}):")
        for mod in completed:
            print(f"  - {mod}")

    checkpoints = data.get("checkpoints", [])
    if checkpoints:
        print(f"检查点 ({len(checkpoints)}):")
        for cp in checkpoints:
            print(f"  - {cp.get('checkpoint_id', '?')[:8]}  阶段: {cp.get('stage', '?')}")


# ---------------------------------------------------------------------------
# CLI 扩展子命令
# ---------------------------------------------------------------------------


async def _handle_run_graph_cmd(args: argparse.Namespace) -> None:
    """执行图编排工作流。"""
    from reqflow.core import Engine, RuntimeRegistry

    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        print(f"[错误] 无法加载 runtime 配置: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.runtime:
        try:
            config = registry.get(args.runtime)
        except ValueError as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        config = _detect_runtime(registry)
        if config is None:
            print("[错误] 无法自动检测 runtime，请使用 --runtime 指定。", file=sys.stderr)
            sys.exit(1)

    engine = Engine(config=config, run_dir=args.run_dir)

    try:
        graph = engine.workflow_loader.load_graph(args.workflow)
    except Exception as exc:
        print(f"[错误] 无法加载图工作流 '{args.workflow}': {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[信息] 运行 ID: {engine.run_id}")
    print(f"[信息] Runtime: {config.display_name} ({config.name})")
    print(f"[信息] 图工作流: {args.workflow}")
    print()

    try:
        result = await engine.run_graph(graph)
    except Exception as exc:
        print(f"\n[错误] 图工作流执行失败: {exc}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=" * 60)
    print("图工作流执行完成")
    print("=" * 60)
    print(f"  状态: {result.get('_status', '未知')}")
    for key, value in result.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")
    print(f"\n详细信息请查看: {engine.run_dir}/state.json")


def _handle_checkpoint_cmd(args: argparse.Namespace) -> None:
    """Checkpoint 管理子命令。"""
    from reqflow.core.state_manager import StateManager

    run_dir = args.run_dir
    action = args.checkpoint_action

    try:
        sm = StateManager(run_dir=run_dir)
    except Exception as exc:
        print(f"[错误] 无法初始化 StateManager: {exc}", file=sys.stderr)
        sys.exit(1)

    if action == "list":
        try:
            checkpoints = sm.list_checkpoints()
        except Exception as exc:
            print(f"[错误] 无法列出检查点: {exc}", file=sys.stderr)
            sys.exit(1)

        if not checkpoints:
            print("未找到任何检查点。")
            return

        print(f"检查点 ({len(checkpoints)}):")
        for cp in checkpoints:
            print(f"  - {cp.checkpoint_id[:8]}  阶段: {cp.stage}  时间: {cp.timestamp}")

    elif action == "create":
        stage = args.stage
        if not stage:
            print("[错误] create 操作需要 --stage 参数。", file=sys.stderr)
            sys.exit(1)

        try:
            checkpoint = sm.create_checkpoint(stage=stage, context={})
        except Exception as exc:
            print(f"[错误] 创建检查点失败: {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"已创建检查点: {checkpoint.checkpoint_id}")
        print(f"阶段: {checkpoint.stage}")
        print(f"时间: {checkpoint.timestamp}")

    elif action == "restore":
        checkpoint_id = args.checkpoint_id
        if not checkpoint_id:
            print("[错误] restore 操作需要 --checkpoint-id 参数。", file=sys.stderr)
            sys.exit(1)

        try:
            state, context = sm.restore_checkpoint(checkpoint_id=checkpoint_id)
        except Exception as exc:
            print(f"[错误] 恢复检查点失败: {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"已恢复检查点: {checkpoint_id}")
        print(f"当前阶段: {state.current_stage}")


def _handle_trace_cmd(args: argparse.Namespace) -> None:
    """执行追踪子命令。"""
    run_dir = args.run_dir
    action = args.trace_action

    trace_dir = Path(run_dir) / "traces"
    if not trace_dir.exists():
        print(f"[错误] 未找到追踪目录: {trace_dir}", file=sys.stderr)
        sys.exit(1)

    trace_files = list(trace_dir.glob("*.json"))
    if not trace_files:
        print("未找到任何追踪数据。")
        return

    if action == "summary":
        print(f"追踪数据 ({len(trace_files)} 个):")
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                print(f"  - {data.get('trace_id', '?')}: {data.get('name', '?')}")
                spans = data.get("spans", [])
                print(f"    Spans: {len(spans)}")
            except Exception:
                print(f"  - {tf.name}: (读取失败)")

    elif action == "export":
        output = args.output
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
        print(f"已导出 {len(all_traces)} 个追踪到: {output}")


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _read_requirement(text_or_path: str) -> str:
    """如果 text_or_path 是文件路径则读取内容，否则原样返回。"""
    path = Path(text_or_path)
    if path.is_file():
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            print(f"[警告] 无法读取文件 {path}: {exc}", file=sys.stderr)
            return text_or_path.strip()
    return text_or_path.strip()


def _detect_runtime(registry: RuntimeRegistry) -> "RuntimeConfig | None":
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


def _status_icon(status: str) -> str:
    """返回状态对应的图标字符。"""
    icons = {
        "success": "[OK]",
        "failure": "[FAIL]",
        "skipped": "[SKIP]",
        "aborted": "[STOP]",
    }
    return icons.get(status, "[?]")


if __name__ == "__main__":
    main()
