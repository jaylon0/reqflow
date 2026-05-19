import asyncio
from reqflow.core.hook_executor import HookExecutor


def test_hook_executor_executes_before_stage_hook():
    """注册 before_stage hook，验证它在 execute_before_stage 时被调用。"""
    executor = HookExecutor()
    called = []

    def my_hook(stage_name, context):
        called.append((stage_name, context))
        return "ok"

    executor.register_hook("test-hook", my_hook, trigger="before_stage", description="test")
    results = asyncio.run(executor.execute_before_stage("design", {"req": "foo"}))

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].hook_name == "test-hook"
    assert results[0].result == "ok"
    assert called == [("design", {"req": "foo"})]


def test_hook_executor_executes_after_stage_hook():
    """注册 after_stage hook，验证它在 execute_after_stage 时被调用。"""
    executor = HookExecutor()
    called = []

    async def my_hook(stage_name, context):
        called.append(stage_name)
        return "done"

    executor.register_hook("post-hook", my_hook, trigger="after_stage")
    results = asyncio.run(executor.execute_after_stage("coding", {}))

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].result == "done"
    assert called == ["coding"]


def test_hook_executor_handles_hook_failure():
    """注册一个会抛异常的 hook，验证优雅处理（不抛出，返回错误信息）。"""
    executor = HookExecutor()

    def bad_hook(stage_name, context):
        raise RuntimeError("hook 炸了")

    executor.register_hook("bad-hook", bad_hook, trigger="before_stage")
    results = asyncio.run(executor.execute_before_stage("test-stage", {}))

    assert len(results) == 1
    assert results[0].success is False
    assert "hook 炸了" in results[0].error


def test_hook_executor_filters_by_trigger():
    """注册 before 和 after 两种 hook，执行 before_stage 时只有 before hook 被调用。"""
    executor = HookExecutor()
    called = []

    def before_hook(stage_name, context):
        called.append("before")

    def after_hook(stage_name, context):
        called.append("after")

    executor.register_hook("before-hook", before_hook, trigger="before_stage")
    executor.register_hook("after-hook", after_hook, trigger="after_stage")

    results = asyncio.run(executor.execute_before_stage("design", {}))

    assert len(results) == 1
    assert results[0].hook_name == "before-hook"
    assert called == ["before"]
