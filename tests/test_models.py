"""Tests for core.models — data models for Engine-driven architecture."""

from __future__ import annotations

import pytest

from core.models import (
    AgentReport,
    AgentRole,
    Artifact,
    Blocker,
    DebateOpinion,
    DebateResult,
    DebateRound,
    Decision,
    Risk,
    RunState,
    Stage,
    StageAnalysis,
    StageOutput,
    StageState,
    ValidationIssue,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# StageOutput
# ---------------------------------------------------------------------------

class TestStageOutput:
    def test_creation_defaults(self):
        out = StageOutput(stage_id="L0")
        assert out.stage_id == "L0"
        assert out.status == "pending"
        assert out.analysis.summary == ""
        assert out.agent_reports == []
        assert out.debate_result is None
        assert out.artifacts == []
        assert out.risks == []
        assert out.blockers == []
        assert out.skills_used == []
        assert out.skills_requested == []

    def test_creation_with_data(self):
        analysis = StageAnalysis(
            summary="A" * 120,
            findings=["f1", "f2", "f3", "f4"],
        )
        report = AgentReport(
            role="analyst",
            task="analyze",
            conclusion="B" * 60,
            confidence=0.85,
        )
        out = StageOutput(
            stage_id="L1",
            status="completed",
            analysis=analysis,
            agent_reports=[report],
            artifacts=[Artifact(name="spec.md", path="/tmp/spec.md", type="file")],
            risks=[Risk(level="medium", description="scope creep")],
            skills_used=["code-analysis"],
        )
        assert out.stage_id == "L1"
        assert len(out.agent_reports) == 1
        assert out.agent_reports[0].confidence == 0.85
        assert len(out.risks) == 1

    def test_to_dict(self):
        out = StageOutput(
            stage_id="L2",
            status="completed",
            analysis=StageAnalysis(summary="S" * 110, findings=["a", "b", "c"]),
        )
        d = out.to_dict()
        assert isinstance(d, dict)
        assert d["stage_id"] == "L2"
        assert d["status"] == "completed"
        assert d["analysis"]["summary"] == "S" * 110
        # debate_result None should be omitted
        assert "debate_result" not in d

    def test_to_dict_with_debate(self):
        debate = DebateResult(
            topic="architecture",
            consensus="C" * 110,
            convergence_score=0.9,
        )
        out = StageOutput(stage_id="L3", debate_result=debate)
        d = out.to_dict()
        assert "debate_result" in d
        assert d["debate_result"]["topic"] == "architecture"

    def test_round_trip_serialization(self):
        """StageOutput: to_dict -> from_dict round-trip."""
        original = StageOutput(
            stage_id="L1",
            status="completed",
            analysis=StageAnalysis(
                summary="X" * 120,
                findings=["finding one", "finding two", "finding three"],
                decisions=[
                    Decision(
                        topic="db",
                        choice="postgres",
                        reasoning="relational",
                        alternatives=["mysql", "sqlite"],
                    )
                ],
                next_steps=["implement", "test"],
            ),
            agent_reports=[
                AgentReport(
                    role="dev",
                    task="build",
                    conclusion="Y" * 60,
                    confidence=0.9,
                    risks=[Risk(level="high", description="data loss")],
                )
            ],
            debate_result=DebateResult(
                topic="tech stack",
                rounds=[
                    DebateRound(
                        round_num=1,
                        opinions=[
                            DebateOpinion(role="dev", agent="A", conclusion="go", confidence=0.8, reasoning="fast"),
                        ],
                        convergence=0.7,
                    )
                ],
                consensus="Z" * 110,
                dissenting=["minor concern"],
                convergence_score=0.85,
            ),
            artifacts=[Artifact(name="out.py", path="/out.py", type="file", description="output")],
            risks=[Risk(level="medium", description="perf")],
            blockers=[Blocker(level="P1", description="dep missing")],
            skills_used=["code-gen"],
            skills_requested=["testing"],
        )

        d = original.to_dict()
        restored = StageOutput.from_dict(d)

        assert restored.stage_id == original.stage_id
        assert restored.status == original.status
        assert restored.analysis.summary == original.analysis.summary
        assert len(restored.analysis.findings) == 3
        assert restored.analysis.decisions[0].choice == "postgres"
        assert len(restored.analysis.decisions[0].alternatives) == 2
        assert len(restored.agent_reports) == 1
        assert restored.agent_reports[0].risks[0].level == "high"
        assert restored.debate_result is not None
        assert restored.debate_result.topic == "tech stack"
        assert len(restored.debate_result.rounds) == 1
        assert restored.debate_result.rounds[0].opinions[0].agent == "A"
        assert len(restored.artifacts) == 1
        assert restored.artifacts[0].name == "out.py"
        assert len(restored.risks) == 1
        assert len(restored.blockers) == 1
        assert restored.skills_used == ["code-gen"]
        assert restored.skills_requested == ["testing"]


# ---------------------------------------------------------------------------
# AgentReport
# ---------------------------------------------------------------------------

class TestAgentReport:
    def test_conclusion_min_length(self):
        """AgentReport with short conclusion should still be constructable (validation is external)."""
        report = AgentReport(conclusion="short")
        assert len(report.conclusion) < 50

    def test_conclusion_valid(self):
        report = AgentReport(conclusion="A" * 50)
        assert len(report.conclusion) >= 50

    def test_defaults(self):
        report = AgentReport()
        assert report.role == ""
        assert report.confidence == 0.0
        assert report.findings == []
        assert report.iterations == 0


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_passed_default(self):
        vr = ValidationResult()
        assert vr.passed is True
        assert vr.issues == []

    def test_with_issues(self):
        vr = ValidationResult(
            passed=False,
            issues=[
                ValidationIssue(code="E001", message="missing summary", severity="error"),
                ValidationIssue(code="W002", message="low confidence", severity="warning"),
            ],
        )
        assert vr.passed is False
        assert len(vr.issues) == 2
        assert vr.issues[0].severity == "error"


# ---------------------------------------------------------------------------
# RunState stage tracking
# ---------------------------------------------------------------------------

class TestRunState:
    def test_completed_stages_empty(self):
        rs = RunState(requirement="build feature X")
        assert rs.completed_stages == []
        assert rs.total_stages == 0

    def test_completed_stages_filtering(self):
        rs = RunState(
            requirement="build feature X",
            stages=[
                StageState(stage_id="L0", status="completed"),
                StageState(stage_id="L1", status="running"),
                StageState(stage_id="L2", status="completed"),
                StageState(stage_id="L3", status="pending"),
            ],
        )
        assert rs.total_stages == 4
        completed = rs.completed_stages
        assert len(completed) == 2
        assert [s.stage_id for s in completed] == ["L0", "L2"]

    def test_mark_stage_completed(self):
        rs = RunState(
            stages=[
                StageState(stage_id="L0", status="running"),
                StageState(stage_id="L1", status="pending"),
            ],
        )
        rs.mark_stage_completed("L0")
        assert rs.stages[0].status == "completed"
        assert rs.stages[0].completed_at != ""
        assert rs.stages[1].status == "pending"

    def test_mark_stage_completed_not_found(self):
        rs = RunState(stages=[StageState(stage_id="L0")])
        with pytest.raises(ValueError, match="Stage 'L99' not found"):
            rs.mark_stage_completed("L99")

    def test_round_trip_serialization(self):
        """RunState: to_dict -> from_dict round-trip."""
        original = RunState(
            run_id="run-001",
            requirement="add auth",
            routing_level="L1",
            status="active",
            current_stage="L1",
            stages=[
                StageState(
                    stage_id="L0",
                    status="completed",
                    output=StageOutput(
                        stage_id="L0",
                        status="completed",
                        analysis=StageAnalysis(
                            summary="A" * 110,
                            findings=["a", "b", "c"],
                        ),
                    ),
                    validation=ValidationResult(passed=True),
                    attempts=1,
                    skills_used=["req-analysis"],
                ),
                StageState(stage_id="L1", status="running"),
            ],
        )

        d = original.to_dict()
        restored = RunState.from_dict(d)

        assert restored.run_id == "run-001"
        assert restored.requirement == "add auth"
        assert restored.total_stages == 2
        assert restored.stages[0].output is not None
        assert restored.stages[0].output.analysis.summary == "A" * 110
        assert restored.stages[0].validation.passed is True
        assert restored.stages[1].output is None


# ---------------------------------------------------------------------------
# Stage definition
# ---------------------------------------------------------------------------

class TestStage:
    def test_creation(self):
        s = Stage(
            id="L1",
            name="design",
            skill="system-design",
            task="Design the system",
            agents=[AgentRole(role="architect", task="design")],
            requires_debate=True,
            expected_artifacts=["design.md"],
        )
        assert s.id == "L1"
        assert s.requires_debate is True
        assert len(s.agents) == 1

    def test_defaults(self):
        s = Stage()
        assert s.id == ""
        assert s.requires_debate is False
        assert s.agents == []
        assert s.required_skills == []
