"""Tests for DebateProtocol and ConvergenceDetector."""

from __future__ import annotations

import pytest
import json
from unittest.mock import AsyncMock

from core.convergence_detector import ConvergenceDetector
from core.debate_protocol import DebateProtocol
from core.models import AgentRole, DebateResult


# ---------------------------------------------------------------------------
# ConvergenceDetector tests
# ---------------------------------------------------------------------------


class TestConvergenceDetector:
    """Tests for ConvergenceDetector."""

    def test_no_rounds_returns_not_converged(self):
        detector = ConvergenceDetector()
        result = detector.check([])
        assert result["converged"] is False
        assert result["reason"] == "no_rounds"

    def test_below_min_rounds(self):
        detector = ConvergenceDetector(min_rounds=2)
        rounds = [
            {
                "round_num": 1,
                "opinions": [
                    {"role": "dev", "conclusion": "We should use Python", "confidence": 0.8},
                ],
            }
        ]
        result = detector.check(rounds)
        assert result["converged"] is False
        assert "below_min_rounds" in result["reason"]

    def test_max_rounds_hard_stop(self):
        detector = ConvergenceDetector(max_rounds=3)
        rounds = [
            {
                "round_num": i,
                "opinions": [
                    {"role": "dev", "conclusion": f"Opinion {i}", "confidence": 0.5},
                ],
            }
            for i in range(1, 4)
        ]
        result = detector.check(rounds)
        assert result["converged"] is True
        assert "max_rounds_reached" in result["reason"]

    def test_convergence_with_similar_texts(self):
        detector = ConvergenceDetector(
            min_rounds=2,
            similarity_threshold=0.5,
            sycophancy_threshold=1.01,  # Disable sycophancy detection for this test
        )
        rounds = [
            {
                "round_num": 1,
                "opinions": [
                    {"role": "dev", "conclusion": "Use Python for the backend because it is great", "confidence": 0.8},
                ],
            },
            {
                "round_num": 2,
                "opinions": [
                    {"role": "dev", "conclusion": "Use Python for the backend because it is great", "confidence": 0.9},
                ],
            },
        ]
        result = detector.check(rounds)
        assert result["converged"] is True
        assert result["reason"] == "convergence_achieved"

    def test_anti_sycophancy_detection(self):
        """Detect when all agents agree too quickly."""
        detector = ConvergenceDetector(
            min_rounds=2,
            similarity_threshold=0.5,
            sycophancy_threshold=0.95,
        )
        identical_text = "This is the exact same conclusion from everyone"
        rounds = [
            {
                "round_num": 1,
                "opinions": [
                    {"role": "dev", "conclusion": identical_text, "confidence": 0.9},
                    {"role": "qa", "conclusion": identical_text, "confidence": 0.9},
                ],
            },
            {
                "round_num": 2,
                "opinions": [
                    {"role": "dev", "conclusion": identical_text, "confidence": 0.95},
                    {"role": "qa", "conclusion": identical_text, "confidence": 0.95},
                ],
            },
        ]
        result = detector.check(rounds)
        assert result["converged"] is False
        assert result["reason"] == "sycophancy_detected"

    def test_jaccard_similarity_identical(self):
        sim = ConvergenceDetector._jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_jaccard_similarity_different(self):
        sim = ConvergenceDetector._jaccard_similarity("hello", "world")
        assert sim < 0.5

    def test_jaccard_similarity_empty(self):
        assert ConvergenceDetector._jaccard_similarity("", "test") == 0.0
        assert ConvergenceDetector._jaccard_similarity("test", "") == 0.0


# ---------------------------------------------------------------------------
# DebateProtocol tests
# ---------------------------------------------------------------------------


def _make_mock_handler(responses: list[str]) -> AsyncMock:
    """Create a mock agent handler that returns responses in sequence."""
    handler = AsyncMock()
    handler.side_effect = responses
    return handler


def _opinion_json(role: str, conclusion: str, confidence: float = 0.8, cross: str = "") -> str:
    """Helper to generate opinion JSON."""
    data = {
        "role": role,
        "conclusion": conclusion,
        "confidence": confidence,
        "reasoning": f"Reasoning for {role}",
    }
    if cross:
        data["cross_commentary"] = cross
    return json.dumps(data)


class TestDebateProtocol:
    """Tests for DebateProtocol."""

    @pytest.mark.asyncio
    async def test_debate_runs_minimum_rounds(self):
        """Debate should run at least min_rounds."""
        # Two agents, very different opinions -> won't converge early
        # Need enough responses for multiple rounds (2 agents per round)
        handler = _make_mock_handler([
            # Round 1
            _opinion_json("dev", "I think we should use Python because it is great for data processing and analysis"),
            _opinion_json("qa", "I believe Java is better because of type safety and enterprise support features"),
            # Round 2
            _opinion_json("dev", "After hearing QA, I still prefer Python for its simplicity and rich libraries"),
            _opinion_json("qa", "I understand dev's point but Java's type system prevents many runtime errors effectively"),
            # Round 3 (in case needed)
            _opinion_json("dev", "Python's ecosystem is unmatched for rapid prototyping and scientific computing needs"),
            _opinion_json("qa", "Java's performance and scalability make it ideal for large enterprise applications"),
            # Round 4
            _opinion_json("dev", "We can use type hints in Python to get some of the safety benefits of static typing"),
            _opinion_json("qa", "That's fair, but Java's compile-time checks are still more comprehensive and reliable"),
            # Round 5
            _opinion_json("dev", "I acknowledge Java's strengths but Python's developer productivity is hard to beat"),
            _opinion_json("qa", "I agree Python is more productive for small projects but Java scales better"),
        ])

        protocol = DebateProtocol(
            agent_handler=handler,
            convergence_detector=ConvergenceDetector(min_rounds=2, max_rounds=5, similarity_threshold=0.99),
        )

        agents = [
            AgentRole(role="dev", task="Defend Python"),
            AgentRole(role="qa", task="Defend Java"),
        ]

        result = await protocol.run_debate("Choose a language", agents)
        assert len(result.rounds) >= 2

    @pytest.mark.asyncio
    async def test_debate_stops_at_max_rounds(self):
        """Debate should stop at max_rounds even without convergence."""
        # Generate enough responses for max_rounds * 2 agents
        responses = []
        for i in range(10):
            for role in ["dev", "qa"]:
                responses.append(_opinion_json(role, f"Opinion round {i} from {role} - completely different text"))

        handler = _make_mock_handler(responses)

        protocol = DebateProtocol(
            agent_handler=handler,
            convergence_detector=ConvergenceDetector(min_rounds=2, max_rounds=3, similarity_threshold=0.99),
        )

        agents = [
            AgentRole(role="dev", task="Task A"),
            AgentRole(role="qa", task="Task B"),
        ]

        result = await protocol.run_debate("Test topic", agents, max_rounds=3)
        assert len(result.rounds) <= 3

    @pytest.mark.asyncio
    async def test_debate_returns_debate_result(self):
        """Debate should return a proper DebateResult."""
        handler = _make_mock_handler([
            _opinion_json("dev", "We should proceed with the current approach and refactor later"),
            _opinion_json("qa", "We should add more tests before proceeding with any changes"),
        ])

        protocol = DebateProtocol(
            agent_handler=handler,
            convergence_detector=ConvergenceDetector(min_rounds=1, max_rounds=2, similarity_threshold=0.99),
        )

        agents = [
            AgentRole(role="dev", task="Development perspective"),
            AgentRole(role="qa", task="Quality perspective"),
        ]

        result = await protocol.run_debate("Should we refactor?", agents, max_rounds=1)
        assert isinstance(result, DebateResult)
        assert result.topic == "Should we refactor?"
        assert len(result.rounds) >= 1
        assert result.consensus  # Should have some consensus text

    @pytest.mark.asyncio
    async def test_debate_convergence_stops_early(self):
        """Debate should stop when convergence is detected."""
        # Similar but not identical opinions -> should converge
        handler = _make_mock_handler([
            # Round 1
            _opinion_json("dev", "Python is the best choice for this project because of its simplicity and readability"),
            _opinion_json("qa", "Python is the best choice for this project because of its simplicity and readability"),
            # Round 2
            _opinion_json("dev", "Python is the best choice for this project because of its simplicity and readability"),
            _opinion_json("qa", "Python is the best choice for this project because of its simplicity and readability"),
            # Round 3 (in case needed)
            _opinion_json("dev", "Python is the best choice for this project because of its simplicity and readability"),
            _opinion_json("qa", "Python is the best choice for this project because of its simplicity and readability"),
            # Round 4
            _opinion_json("dev", "Python is the best choice for this project because of its simplicity and readability"),
            _opinion_json("qa", "Python is the best choice for this project because of its simplicity and readability"),
            # Round 5
            _opinion_json("dev", "Python is the best choice for this project because of its simplicity and readability"),
            _opinion_json("qa", "Python is the best choice for this project because of its simplicity and readability"),
        ])

        protocol = DebateProtocol(
            agent_handler=handler,
            convergence_detector=ConvergenceDetector(
                min_rounds=1,
                max_rounds=5,
                similarity_threshold=0.8,
                sycophancy_threshold=1.01,  # Disable sycophancy detection
            ),
        )

        agents = [
            AgentRole(role="dev", task="Dev perspective"),
            AgentRole(role="qa", task="QA perspective"),
        ]

        result = await protocol.run_debate("Language choice", agents)
        # Should stop early due to convergence (round 2)
        assert len(result.rounds) < 5
        assert result.convergence_score > 0.5
