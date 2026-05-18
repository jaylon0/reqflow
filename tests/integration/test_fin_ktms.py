"""ReqFlow Phase 4 验证：用 fin-ktms 项目进行 TDD 测试。

测试目标：MathExpress（数学表达式求值器）
验证 ReqFlow 的核心组件在真实 Java 项目上能正确工作。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reqflow.core import Engine, RuntimeRegistry, ContextAdapter, ToolBridge, Guardrails
from reqflow.core.state_manager import StateManager
from reqflow.core.tracer import Tracer
from reqflow.core.context_adapter import ContextAdapter
from reqflow.core.guardrails import Constraint, Severity, check_file_boundary

# 项目路径
PROJECT_DIR = Path("/Users/yuanjulong/Documents/kuaishou-java/fin-ktms")
TARGET_FILE = PROJECT_DIR / "common/common-utils/src/main/java/com/kj/tms/common/utils/MathExpress.java"
TEST_DIR = PROJECT_DIR / "common/common-utils/src/test/java/com/kj/tms/common/utils"


def test_context_adapter_with_java_code():
    """验证 ContextAdapter 能正确格式化 Java 项目上下文。"""
    print("\n=== 测试 1: ContextAdapter 格式化 Java 上下文 ===")

    config = RuntimeRegistry().get("claude")
    adapter = ContextAdapter(config)

    context_pack = {
        "project": "fin-ktms",
        "language": "Java 1.8",
        "framework": "Spring 5.2.1 + MyBatis",
        "target_class": "MathExpress",
        "target_file": str(TARGET_FILE),
        "requirements": [
            "为 MathExpress 类添加幂运算 (^) 支持",
            "添加取模运算 (%) 支持",
            "确保 BigDecimal 精度不丢失",
        ],
        "existing_patterns": [
            "使用逆波兰表达式解析",
            "BigDecimal 精确计算",
            "支持负数和括号",
        ],
    }

    # Markdown 格式
    md_output = adapter.format_context(context_pack)
    assert "fin-ktms" in md_output
    assert "MathExpress" in md_output
    assert "BigDecimal" in md_output
    print(f"  Markdown 格式: {len(md_output)} 字符 ✓")

    # JSON 格式
    config_json = RuntimeRegistry().get("gpt")
    adapter_json = ContextAdapter(config_json)
    json_output = adapter_json.format_context(context_pack)
    parsed = json.loads(json_output)
    assert parsed["project"] == "fin-ktms"
    print(f"  JSON 格式: {len(json_output)} 字符 ✓")

    # 截断测试
    truncated = adapter.truncate_to_fit(md_output * 100, reserved_tokens=5000)
    assert len(truncated) <= len(md_output) * 100
    print(f"  截断测试: 正常 ✓")

    # Manual 模式格式
    manual_output = adapter.format_for_manual_mode(context_pack)
    assert "- [ ]" in manual_output
    print(f"  Manual 模式: {len(manual_output)} 字符 ✓")

    print("  ContextAdapter 测试全部通过 ✓")


def test_tool_bridge_with_java_tools():
    """验证 ToolBridge 能正确映射 Java 开发工具。"""
    print("\n=== 测试 2: ToolBridge 工具映射 ===")

    config = RuntimeRegistry().get("claude")
    bridge = ToolBridge(config)

    # 可用工具
    available = bridge.get_available_tools()
    assert "read_file" in available
    assert "bash" in available
    print(f"  可用工具: {available} ✓")

    # 工具名映射
    assert bridge.map_tool_name("read_file") == "Read"
    assert bridge.map_tool_name("bash") == "Bash"
    assert bridge.map_tool_name("edit_file") == "Edit"
    print(f"  工具名映射: 正常 ✓")

    # Prompt 格式化
    prompt = bridge.format_tools_for_prompt()
    assert "Read" in prompt
    assert "Bash" in prompt
    print(f"  Prompt 格式化: {len(prompt)} 字符 ✓")

    # GPT 配置
    gpt_config = RuntimeRegistry().get("gpt")
    gpt_bridge = ToolBridge(gpt_config)
    gpt_available = gpt_bridge.get_available_tools()
    print(f"  GPT 工具: {gpt_available} ✓")

    print("  ToolBridge 测试全部通过 ✓")


async def test_guardrails_with_file_boundary():
    """验证 Guardrails 文件边界检查。"""
    print("\n=== 测试 3: Guardrails 文件边界检查 ===")

    guardrails = Guardrails()

    # 添加文件边界约束
    guardrails.add_constraint(Constraint(
        name="file_boundary",
        description="只允许编辑 common-utils 模块",
        severity=Severity.FATAL,
        check_fn=check_file_boundary,
    ))

    # 测试：在授权范围内的文件
    context_ok = {
        "file_path": str(TARGET_FILE),
        "authorized_scope": [str(PROJECT_DIR / "common/*")],
    }
    violations = await guardrails.check(context_ok)
    fatal = [v for v in violations if v.severity == Severity.FATAL]
    assert len(fatal) == 0, f"不应有 FATAL 违规: {fatal}"
    print(f"  授权范围内文件: 无违规 ✓")

    # 测试：超出授权范围的文件
    context_bad = {
        "file_path": str(PROJECT_DIR / "web/src/main/java/com/kj/tms/web/controller/SomeController.java"),
        "authorized_scope": [str(PROJECT_DIR / "common/*")],
    }
    violations = await guardrails.check(context_bad)
    errors = [v for v in violations if v.severity in (Severity.ERROR, Severity.FATAL)]
    assert len(errors) > 0, "应有违规"
    print(f"  超出授权范围: 检测到 {errors[0].severity.value} 违规 ✓")

    # 测试：被拒绝的文件
    context_denied = {
        "file_path": str(PROJECT_DIR / "common/common-utils/src/main/java/com/kj/tms/common/utils/MathExpress.java"),
        "denied_scope": ["**/pom.xml", "**/*.xml"],
    }
    violations = await guardrails.check(context_denied)
    fatal = [v for v in violations if v.severity == Severity.FATAL]
    assert len(fatal) == 0, "Java 文件不应被 XML 拒绝规则拦截"
    print(f"  拒绝规则不误报: 正常 ✓")

    print("  Guardrails 测试全部通过 ✓")


def test_state_manager_checkpoint():
    """验证 StateManager 状态持久化和 checkpoint。"""
    print("\n=== 测试 4: StateManager 状态管理 ===")

    run_dir = "/tmp/reqflow-tdd-test-state"
    sm = StateManager(run_dir)

    # 初始状态
    assert sm.state.run_id
    assert sm.state.current_stage == ""
    print(f"  初始状态: run_id={sm.state.run_id[:8]}... ✓")

    # 更新阶段
    sm.update_stage("tdd_red")
    assert sm.state.current_stage == "tdd_red"
    print(f"  阶段更新: {sm.state.current_stage} ✓")

    # 完成模块
    sm.complete_module("MathExpress_test")
    sm.complete_module("MathExpress_impl")
    assert "MathExpress_test" in sm.state.completed_modules
    assert "MathExpress_impl" in sm.state.completed_modules
    print(f"  模块完成: {sm.state.completed_modules} ✓")

    # 创建 checkpoint
    cp = sm.create_checkpoint("tdd_green", context={
        "test_file": "MathExpressTest.java",
        "result": "3 passed, 0 failed",
    })
    assert cp.checkpoint_id
    assert cp.stage == "tdd_green"
    print(f"  Checkpoint: {cp.checkpoint_id[:8]}... ✓")

    # 记忆
    sm.state.memory.add_short_term("test_count", "3")
    sm.state.memory.add_long_term("BigDecimal 精度要用 MathContext", "tdd-test", "java")
    sm.state.memory.add_entity("MathExpress", "class", str(TARGET_FILE))
    assert len(sm.state.memory.short_term) > 0
    assert len(sm.state.memory.long_term) > 0
    assert len(sm.state.memory.entity) > 0
    print(f"  记忆系统: short={len(sm.state.memory.short_term)}, long={len(sm.state.memory.long_term)}, entity={len(sm.state.memory.entity)} ✓")

    # 智能体执行日志
    sm.log_agent_execution("dev-agent", "编写 MathExpress 测试", "完成", 1500)
    assert len(sm.state.agent_execution_log) > 0
    print(f"  执行日志: {len(sm.state.agent_execution_log)} 条 ✓")

    # 保存并重新加载
    sm.save_state()
    sm2 = StateManager(run_dir)
    assert sm2.state.current_stage == "tdd_red"
    assert "MathExpress_test" in sm2.state.completed_modules
    print(f"  持久化重载: 正常 ✓")

    # 恢复 checkpoint
    restored_state, restored_ctx = sm2.restore_checkpoint(cp.checkpoint_id)
    assert restored_ctx["test_file"] == "MathExpressTest.java"
    print(f"  Checkpoint 恢复: 正常 ✓")

    # 清理
    import shutil
    shutil.rmtree(run_dir, ignore_errors=True)

    print("  StateManager 测试全部通过 ✓")


def test_tracer_with_java_workflow():
    """验证 Tracer 追踪 Java 开发工作流。"""
    print("\n=== 测试 5: Tracer 工作流追踪 ===")

    tracer = Tracer("tdd-test-run", output_dir="/tmp/reqflow-tdd-trace")

    # 模拟 TDD 工作流
    root = tracer.start_span("tdd_workflow", input_data={"target": "MathExpress"})

    # Red 阶段
    red_span = tracer.start_span("tdd:red", input_data={"action": "write failing test"})
    tracer.end_span(red_span.span_id, output={"tests": 3, "failed": 3}, status="success")

    # Green 阶段
    green_span = tracer.start_span("tdd:green", input_data={"action": "implement to pass"})
    tracer.end_span(green_span.span_id, output={"tests": 3, "failed": 0}, status="success")

    # Refactor 阶段
    refactor_span = tracer.start_span("tdd:refactor", input_data={"action": "refactor"})
    tracer.end_span(refactor_span.span_id, output={"tests": 3, "failed": 0}, status="success")

    tracer.end_span(root.span_id, output="TDD cycle complete", status="success")

    # 验证
    summary = tracer.get_summary()
    assert summary["total_spans"] == 4
    assert summary["failed_spans"] == 0
    print(f"  Spans: {summary['total_spans']} 总计, {summary['failed_spans']} 失败 ✓")

    # 导出
    trace_file = tracer.export()
    assert Path(trace_file).exists()
    trace_data = json.loads(Path(trace_file).read_text())
    assert len(trace_data["spans"]) == 4
    print(f"  导出: {trace_file} ✓")

    # 清理
    import shutil
    shutil.rmtree("/tmp/reqflow-tdd-trace", ignore_errors=True)

    print("  Tracer 测试全部通过 ✓")


async def test_engine_tdd_workflow():
    """验证 Engine 完整 TDD 工作流。"""
    print("\n=== 测试 6: Engine TDD 工作流 ===")

    registry = RuntimeRegistry()
    config = registry.get("manual")
    engine = Engine(config=config, run_dir="/tmp/reqflow-tdd-engine")

    # TDD 工作流步骤
    tdd_steps = [
        {
            "name": "analyze",
            "prompt": f"分析 MathExpress 类的代码结构和现有功能。目标文件: {TARGET_FILE}",
            "checkpoint": True,
        },
        {
            "name": "tdd_red",
            "prompt": "编写一个失败的单元测试：测试 MathExpress 对幂运算表达式 '2^3' 的处理。预期结果应为 8。",
            "checkpoint": True,
        },
        {
            "name": "tdd_green",
            "prompt": "修改 MathExpress 类，添加幂运算 (^) 支持，使失败的测试通过。",
            "checkpoint": True,
        },
        {
            "name": "tdd_refactor",
            "prompt": "重构 MathExpress 类，提取公共方法，改善代码可读性。确保所有测试仍然通过。",
            "checkpoint": True,
        },
        {
            "name": "verify",
            "prompt": "运行所有测试，验证幂运算功能正确，原有四则运算不受影响。",
        },
    ]

    result = await engine.run_workflow(
        workflow_steps=tdd_steps,
        requirement="为 MathExpress 类添加幂运算 (^) 支持，使用 TDD 方式开发",
    )

    # 验证结果
    assert result["status"] == "completed", f"状态应为 completed，实际: {result['status']}"
    assert len(result["steps"]) == 5
    print(f"  状态: {result['status']} ✓")
    print(f"  步骤: {len(result['steps'])} 个 ✓")

    for step in result["steps"]:
        assert step["status"] == "success", f"步骤 {step['name']} 失败"
        print(f"    - {step['name']}: {step['status']} ✓")

    # 验证状态持久化
    status = engine.get_status()
    assert len(status["completed_modules"]) == 5
    assert status["checkpoints"] == 4  # 4 个 checkpoint 步骤
    assert status["memory_entries"] == 5
    print(f"  完成模块: {len(status['completed_modules'])} ✓")
    print(f"  Checkpoints: {status['checkpoints']} ✓")
    print(f"  记忆条目: {status['memory_entries']} ✓")

    # 验证 state.json
    state_file = Path(engine.run_dir) / "state.json"
    assert state_file.exists()
    state_data = json.loads(state_file.read_text())
    assert state_data["current_stage"] == "workflow_start"
    print(f"  state.json: 存在 ✓")

    # 验证 trace 导出
    trace_dir = Path(engine.run_dir) / "traces"
    assert trace_dir.exists()
    trace_files = list(trace_dir.glob("trace-*.json"))
    assert len(trace_files) > 0
    print(f"  Trace 文件: {len(trace_files)} 个 ✓")

    # 清理
    import shutil
    shutil.rmtree("/tmp/reqflow-tdd-engine", ignore_errors=True)

    print("  Engine TDD 工作流测试全部通过 ✓")


async def test_engine_multi_runtime():
    """验证多 runtime 配置。"""
    print("\n=== 测试 7: 多 Runtime 配置 ===")

    registry = RuntimeRegistry()
    runtimes = registry.list_runtimes()

    for name in runtimes:
        config = registry.get(name)
        engine = Engine(config=config, run_dir=f"/tmp/reqflow-runtime-{name}")

        # 验证组件创建
        assert engine.tool_bridge is not None
        assert engine.context_adapter is not None
        assert engine.state_manager is not None
        assert engine.tracer is not None
        assert engine.guardrails is not None

        # 验证适配器选择
        adapter = engine.select_adapter()
        assert adapter is not None

        caps = config.capabilities
        print(f"  {name:12s} → {adapter.name:20s} | bash={caps.supports_bash} agent={caps.supports_agent_tools} ctx={caps.max_context_tokens}")

        # 清理
        import shutil
        shutil.rmtree(f"/tmp/reqflow-runtime-{name}", ignore_errors=True)

    print(f"  共 {len(runtimes)} 个 runtime 验证通过 ✓")


def test_java_project_scan():
    """扫描 Java 项目结构，验证上下文发现能力。"""
    print("\n=== 测试 8: Java 项目结构扫描 ===")

    # 模块结构
    modules = [d.name for d in PROJECT_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    print(f"  模块: {modules}")

    # Java 文件统计
    java_files = list(PROJECT_DIR.rglob("*.java"))
    main_files = [f for f in java_files if "src/main" in str(f)]
    test_files = [f for f in java_files if "src/test" in str(f)]
    print(f"  Java 文件: {len(java_files)} 总计, {len(main_files)} 主代码, {len(test_files)} 测试")

    # 关键类发现
    services = list(PROJECT_DIR.rglob("*Service.java"))
    controllers = list(PROJECT_DIR.rglob("*Controller.java"))
    mappers = list(PROJECT_DIR.rglob("*Mapper.java"))
    dtos = list(PROJECT_DIR.rglob("*Dto.java"))
    print(f"  Service: {len(services)}, Controller: {len(controllers)}, Mapper: {len(mappers)}, DTO: {len(dtos)}")

    # 目标类信息
    assert TARGET_FILE.exists()
    content = TARGET_FILE.read_text()
    methods = [line.strip() for line in content.split("\n") if "public" in line and "(" in line and "class" not in line]
    print(f"  MathExpress 公共方法: {len(methods)} 个")
    for m in methods[:5]:
        print(f"    - {m[:80]}")

    # 测试目录状态
    if TEST_DIR.exists():
        existing_tests = list(TEST_DIR.glob("*.java"))
        print(f"  现有测试: {len(existing_tests)} 个")
    else:
        print(f"  测试目录不存在: {TEST_DIR}")

    print("  项目扫描完成 ✓")


async def main():
    """运行所有验证测试。"""
    print("=" * 60)
    print("ReqFlow Phase 4 验证：fin-ktms TDD 测试")
    print("=" * 60)

    test_java_project_scan()
    test_context_adapter_with_java_code()
    test_tool_bridge_with_java_tools()
    await test_guardrails_with_file_boundary()
    test_state_manager_checkpoint()
    test_tracer_with_java_workflow()
    await test_engine_tdd_workflow()
    await test_engine_multi_runtime()

    print("\n" + "=" * 60)
    print("全部 8 项验证测试通过 ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
