"""Tests for core.agent_lifecycle."""

from __future__ import annotations

import asyncio
import json

import pytest

from core.agent_lifecycle import (
    AgentLifecycleManager,
    AgentLimits,
    MaxIterationsExceeded,
)
from core.models import AgentRole


async def good_handler(prompt: str) -> str:
    """Handler that returns valid output quickly."""
    return json.dumps({
        "agent_role": "test-agent",
        "task": "test",
        "conclusion": "这是一个测试结论，需要至少五十个字才能通过验证检查。" * 2,
        "confidence": 0.9,
        "findings": ["f1"],
        "recommendations": ["r1"],
        "iterations": 1,
    })


@pytest.fixture
def agent():
    return AgentRole(role="test-agent", task="test task")


@pytest.fixture
def manager():
    return AgentLifecycleManager(agent_handler=good_handler)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_execute_returns_report(manager, agent):
    report = await manager.execute_with_limits(agent, "test prompt")
    assert report.role == "test-agent"
    assert report.confidence == 0.9


async def test_execute_with_default_limits(manager, agent):
    report = await manager.execute_with_limits(agent, "test prompt")
    assert report.conclusion != ""


async def test_execute_with_custom_limits(manager, agent):
    limits = AgentLimits(max_iterations=5, max_execution_time=10, max_retry_limit=1)
    report = await manager.execute_with_limits(agent, "test prompt", limits)
    assert report.role == "test-agent"


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


async def slow_handler(prompt: str) -> str:
    """Handler that takes too long."""
    await asyncio.sleep(10)
    return json.dumps({"agent_role": "slow", "task": "t", "conclusion": "done", "confidence": 0.5})


async def test_timeout_returns_report():
    manager = AgentLifecycleManager(agent_handler=slow_handler)
    agent = AgentRole(role="slow", task="slow task")
    limits = AgentLimits(max_execution_time=1, max_retry_limit=0)

    report = await manager.execute_with_limits(agent, "test", limits)
    assert "超时" in report.conclusion
    assert report.confidence == 0.0


# ---------------------------------------------------------------------------
# Retry on failure
# ---------------------------------------------------------------------------


async def test_retries_on_failure():
    call_count = 0

    async def flaky_handler(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("Transient error")
        return json.dumps({
            "agent_role": "flaky",
            "task": "t",
            "conclusion": "成功了" * 20,
            "confidence": 0.8,
            "iterations": 1,
        })

    manager = AgentLifecycleManager(agent_handler=flaky_handler)
    agent = AgentRole(role="flaky", task="flaky task")
    limits = AgentLimits(max_retry_limit=2)

    report = await manager.execute_with_limits(agent, "test", limits)
    assert call_count == 2
    assert report.confidence == 0.8


async def test_exhausted_retries_returns_error_report():
    async def always_fail(prompt: str) -> str:
        raise RuntimeError("Permanent error")

    manager = AgentLifecycleManager(agent_handler=always_fail)
    agent = AgentRole(role="fail", task="fail task")
    limits = AgentLimits(max_retry_limit=1)

    report = await manager.execute_with_limits(agent, "test", limits)
    assert "重试耗尽" in report.conclusion
    assert report.confidence == 0.0


# ---------------------------------------------------------------------------
# Non-JSON fallback
# ---------------------------------------------------------------------------


async def test_handles_non_json_output():
    async def text_handler(prompt: str) -> str:
        return "This is plain text, not JSON"

    manager = AgentLifecycleManager(agent_handler=text_handler)
    agent = AgentRole(role="text", task="text task")

    report = await manager.execute_with_limits(agent, "test")
    assert report.role == "text"
    assert report.confidence == 0.3
    assert "plain text" in report.conclusion


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


async def test_empty_output():
    async def empty_handler(prompt: str) -> str:
        return ""

    manager = AgentLifecycleManager(agent_handler=empty_handler)
    agent = AgentRole(role="empty", task="empty task")

    report = await manager.execute_with_limits(agent, "test")
    assert report.conclusion == "无输出"


async def test_zero_retry_limit():
    """With max_retry_limit=0, should still execute once."""
    manager = AgentLifecycleManager(agent_handler=good_handler)
    agent = AgentRole(role="test", task="test")
    limits = AgentLimits(max_retry_limit=0)

    report = await manager.execute_with_limits(agent, "test", limits)
    assert report.confidence == 0.9
