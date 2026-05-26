"""Tests for core.stage_executor."""

from __future__ import annotations

import json

import pytest

from core.models import AgentRole, RunState, Stage
from core.stage_executor import StageExecutor


async def mock_agent_handler(prompt: str) -> str:
    """Mock agent returning valid JSON."""
    return json.dumps({
        "agent_role": "research-agent",
        "task": "调研",
        "conclusion": "这是一个测试结论，至少五十个字的长度要求。" * 2,
        "confidence": 0.85,
        "findings": ["发现1", "发现2"],
        "recommendations": ["建议1"],
        "risks": [{"level": "low", "description": "低风险"}],
        "skills_requested": [],
    })


@pytest.fixture
def executor():
    return StageExecutor(agent_handler=mock_agent_handler)


@pytest.fixture
def stage():
    return Stage(
        id="analysis",
        name="分析",
        skill="analysis",
        task="分析需求",
        agents=[AgentRole(role="research-agent", task="调研")],
        required_skills=["prd-review"],
        optional_skills=[],
        methodology_skills=[],
    )


@pytest.fixture
def state():
    return RunState(run_id="test", requirement="需求", routing_level="L3")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_returns_stage_output(executor, stage, state):
    output = await executor.execute(stage, "测试 prompt", state)
    assert output.stage_id == "analysis"
    assert output.status == "completed"
    assert output.analysis is not None


@pytest.mark.asyncio
async def test_execute_parses_agent_report(executor, stage, state):
    output = await executor.execute(stage, "测试", state)
    assert len(output.agent_reports) == 1
    report = output.agent_reports[0]
    assert report.role == "research-agent"
    assert report.confidence == 0.85
    assert len(report.findings) == 2


@pytest.mark.asyncio
async def test_execute_collects_findings(executor, stage, state):
    output = await executor.execute(stage, "测试", state)
    assert len(output.analysis.findings) == 2


@pytest.mark.asyncio
async def test_execute_records_skills_used(executor, stage, state):
    output = await executor.execute(stage, "测试", state)
    assert "prd-review" in output.skills_used


@pytest.mark.asyncio
async def test_execute_collects_risks(executor, stage, state):
    output = await executor.execute(stage, "测试", state)
    assert len(output.risks) == 1
    assert output.risks[0].level == "low"


@pytest.mark.asyncio
async def test_execute_extracts_first_recommendation_as_next_step(executor, stage, state):
    output = await executor.execute(stage, "测试", state)
    assert len(output.analysis.next_steps) == 1
    assert output.analysis.next_steps[0] == "建议1"


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------


async def handler_with_markdown(prompt: str) -> str:
    """Agent wraps JSON in markdown code block."""
    return '''
Here is my analysis:

```json
{
    "agent_role": "dev",
    "task": "build",
    "conclusion": "经过详细分析后得出结论，这个方案是可行的，需要进一步验证具体实现细节和技术选型。",
    "confidence": 0.9,
    "findings": ["f1", "f2", "f3"],
    "recommendations": ["r1"],
    "risks": [],
    "skills_requested": ["debug"]
}
```

That's my report.
'''


@pytest.mark.asyncio
async def test_extracts_json_from_markdown():
    executor = StageExecutor(agent_handler=handler_with_markdown)
    stage = Stage(
        id="test", name="test", skill="test", task="test",
        agents=[AgentRole(role="dev", task="build")],
        required_skills=[], optional_skills=[], methodology_skills=[],
    )
    state = RunState(run_id="t", requirement="", routing_level="L3")
    output = await executor.execute(stage, "测试", state)
    assert output.agent_reports[0].role == "dev"
    assert output.agent_reports[0].confidence == 0.9
    assert output.skills_requested == ["debug"]


# ---------------------------------------------------------------------------
# Non-JSON fallback
# ---------------------------------------------------------------------------


async def bad_handler(prompt: str) -> str:
    """Returns plain text, not JSON."""
    return "这不是 JSON，是自由文本输出"


@pytest.mark.asyncio
async def test_handles_non_json_output():
    executor = StageExecutor(agent_handler=bad_handler)
    stage = Stage(
        id="test", name="test", skill="test", task="test",
        agents=[AgentRole(role="agent", task="task")],
        required_skills=[], optional_skills=[], methodology_skills=[],
    )
    state = RunState(run_id="t", requirement="", routing_level="L3")
    output = await executor.execute(stage, "测试", state)
    assert output.status == "completed"
    report = output.agent_reports[0]
    assert report.confidence == 0.3  # degraded confidence
    assert "自由文本" in report.conclusion


async def empty_handler(prompt: str) -> str:
    """Returns empty string."""
    return ""


@pytest.mark.asyncio
async def test_handles_empty_output():
    executor = StageExecutor(agent_handler=empty_handler)
    stage = Stage(
        id="test", name="test", skill="test", task="test",
        agents=[AgentRole(role="agent", task="task")],
        required_skills=[], optional_skills=[], methodology_skills=[],
    )
    state = RunState(run_id="t", requirement="", routing_level="L3")
    output = await executor.execute(stage, "测试", state)
    assert output.status == "completed"
    assert output.agent_reports[0].conclusion == "无输出"


# ---------------------------------------------------------------------------
# No agents (single-agent mode)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_agent_mode():
    executor = StageExecutor(agent_handler=mock_agent_handler)
    stage = Stage(
        id="solo", name="solo", skill="solo", task="solo task",
        agents=[],  # no agents defined -> single agent mode
        required_skills=[], optional_skills=[], methodology_skills=[],
    )
    state = RunState(run_id="t", requirement="", routing_level="L3")
    output = await executor.execute(stage, "测试", state)
    assert output.status == "completed"
    assert len(output.agent_reports) == 1
    # mock handler returns "research-agent" in JSON, so that's what we get
    assert output.agent_reports[0].role == "research-agent"


# ---------------------------------------------------------------------------
# Multi-agent parallel dispatch
# ---------------------------------------------------------------------------


async def multi_handler(prompt: str) -> str:
    """Handler that returns different roles based on prompt content."""
    if "security" in prompt:
        role = "security-agent"
    else:
        role = "dev-agent"
    return json.dumps({
        "agent_role": role,
        "task": "task",
        "conclusion": "这是一个多agent测试结论，需要至少五十个字才能通过验证检查。" * 2,
        "confidence": 0.8,
        "findings": ["finding"],
        "recommendations": [],
        "risks": [],
        "skills_requested": [],
    })


@pytest.mark.asyncio
async def test_multi_agent_dispatch():
    executor = StageExecutor(agent_handler=multi_handler)
    stage = Stage(
        id="multi", name="multi", skill="multi", task="multi task",
        agents=[
            AgentRole(role="dev-agent", task="开发"),
            AgentRole(role="security-agent", task="安全审计"),
        ],
        required_skills=[], optional_skills=[], methodology_skills=[],
    )
    state = RunState(run_id="t", requirement="", routing_level="L3")
    output = await executor.execute(stage, "测试", state)
    assert output.status == "completed"
    assert len(output.agent_reports) == 2
    roles = {r.role for r in output.agent_reports}
    assert "dev-agent" in roles
    assert "security-agent" in roles


# ---------------------------------------------------------------------------
# execute_with_repair
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_with_repair(executor, stage):
    output = await executor.execute_with_repair(stage, "修复 prompt")
    assert output.status == "completed"
    assert output.stage_id == "analysis"
