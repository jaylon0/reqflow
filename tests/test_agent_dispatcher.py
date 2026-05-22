"""Tests for AgentDispatcher — role matrix and prompt templates."""

import pytest
from core.agent_dispatcher import AgentDispatcher, AgentRole


def test_get_agents_for_stage():
    """Should return agent list for a given stage."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("PRD理解")
    assert len(agents) >= 2
    roles = [a.role for a in agents]
    assert "research-agent" in roles
    assert "architecture-agent" in roles


def test_required_vs_optional():
    """Agents should have required flag."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("PRD理解")
    required = [a for a in agents if a.required]
    assert len(required) >= 1


def test_build_prompt():
    """Should build a complete prompt for an agent."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("PRD理解")
    prompt = dispatcher.build_prompt(
        agents[0],
        context="测试需求：写一个测试接口",
        stage_name="PRD理解",
    )
    assert agents[0].role in prompt
    assert "测试需求" in prompt
    assert "输出要求" in prompt


def test_timeout_strategy():
    """Should return timeout handling instructions."""
    dispatcher = AgentDispatcher()
    strategy = dispatcher.get_timeout_strategy()
    assert "60s" in strategy
    assert "SKIPPED" in strategy
    assert "BLOCKER" in strategy


def test_format_dispatch_plan():
    """Should format a dispatch plan for a stage."""
    dispatcher = AgentDispatcher()
    plan = dispatcher.format_dispatch_plan("PRD理解", context="测试上下文")
    assert "Agent 派遣" in plan
    assert "research-agent" in plan
    assert "Agent tool" in plan


def test_stages_without_agents():
    """Some stages should have no agents (e.g., startup)."""
    dispatcher = AgentDispatcher()
    agents = dispatcher.get_agents("启动")
    assert len(agents) == 0
