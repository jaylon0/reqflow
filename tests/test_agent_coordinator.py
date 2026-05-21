from core.agent_coordinator import AgentCoordinator, BrainstormMode


def test_round_robin():
    coord = AgentCoordinator()
    result = coord.brainstorm(
        mode=BrainstormMode.ROUND_ROBIN,
        agents=["research-agent", "architecture-agent"],
        topic="PRD 理解",
        context="需要理解用户标签管理功能的需求",
        max_rounds=2,
    )
    assert result.mode == BrainstormMode.ROUND_ROBIN
    assert len(result.rounds) <= 2
    assert result.consensus is not None


def test_panel_of_experts():
    coord = AgentCoordinator()
    result = coord.brainstorm(
        mode=BrainstormMode.PANEL_OF_EXPERTS,
        agents=["architecture-agent", "security-agent", "performance-agent"],
        topic="技术方案评估",
        context="评估用户标签管理的技术方案",
    )
    assert result.mode == BrainstormMode.PANEL_OF_EXPERTS


def test_critique_refine():
    coord = AgentCoordinator()
    result = coord.brainstorm(
        mode=BrainstormMode.CRITIQUE_REFINE,
        agents=["review-agent", "dev-agent"],
        topic="代码审查",
        context="审查用户标签模块的代码质量",
    )
    assert result.mode == BrainstormMode.CRITIQUE_REFINE


def test_consensus_detection():
    coord = AgentCoordinator()
    result = coord.detect_consensus(
        opinions=[
            {"agent": "a1", "vote": "agree"},
            {"agent": "a2", "vote": "agree"},
            {"agent": "a3", "vote": "disagree"},
        ],
        method="majority",
    )
    assert result["consensus"] == "agree"
    assert result["ratio"] > 0.5


def test_fallback_on_timeout():
    coord = AgentCoordinator()
    result = coord.brainstorm(
        mode=BrainstormMode.ROUND_ROBIN,
        agents=["unavailable-agent"],
        topic="test",
        context="test",
        max_rounds=1,
    )
    # Should fallback gracefully
    assert result.fallback is True or len(result.rounds) > 0
