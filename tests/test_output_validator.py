"""Tests for core.output_validator."""

from __future__ import annotations

import pytest

from core.models import (
    StageOutput,
    StageAnalysis,
    AgentReport,
    DebateResult,
    DebateRound,
    DebateOpinion,
    Artifact,
)
from core.output_validator import OutputValidator


@pytest.fixture
def validator():
    return OutputValidator()


def _make_analysis(summary_len: int = 200) -> StageAnalysis:
    return StageAnalysis(
        summary="A" * summary_len + " /path/to/file.py Controller def test",
        findings=["finding1", "finding2", "finding3"],
    )


def _make_report(conclusion_len: int = 100) -> AgentReport:
    return AgentReport(
        role="research-agent",
        task="调研",
        conclusion="B" * conclusion_len,
        confidence=0.85,
    )


def _make_debate() -> DebateResult:
    return DebateResult(
        topic="测试",
        rounds=[
            DebateRound(round_num=1, opinions=[
                DebateOpinion(role="dev", agent="A", conclusion="go", confidence=0.8),
            ]),
            DebateRound(round_num=2, opinions=[
                DebateOpinion(role="dev", agent="A", conclusion="still go", confidence=0.9),
            ]),
        ],
        consensus="C" * 150,
        convergence_score=0.9,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_output_passes(validator):
    output = StageOutput(
        stage_id="analysis",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
    )
    result = validator.validate("analysis", output)
    assert result.passed


# ---------------------------------------------------------------------------
# Status checks
# ---------------------------------------------------------------------------

def test_stage_failed_returns_immediately(validator):
    output = StageOutput(stage_id="analysis", status="failed")
    result = validator.validate("analysis", output)
    assert not result.passed
    assert any(i.code == "stage_failed" for i in result.issues)


# ---------------------------------------------------------------------------
# Analysis validation
# ---------------------------------------------------------------------------

def test_missing_analysis_fails(validator):
    output = StageOutput(stage_id="analysis", status="completed")
    result = validator.validate("analysis", output)
    assert not result.passed
    assert any(i.code == "missing_analysis" for i in result.issues)


def test_short_analysis_fails(validator):
    output = StageOutput(
        stage_id="analysis",
        status="completed",
        analysis=StageAnalysis(summary="太短了", findings=["f1", "f2", "f3"]),
    )
    result = validator.validate("analysis", output)
    assert not result.passed
    assert any(i.code == "analysis_too_short" for i in result.issues)


def test_generic_analysis_fails(validator):
    """Analysis without concrete references should fail."""
    output = StageOutput(
        stage_id="analysis",
        status="completed",
        analysis=StageAnalysis(
            summary="这是一段很长的分析但是没有任何具体的文件路径或代码引用" * 10,
            findings=["f1", "f2", "f3"],
        ),
    )
    result = validator.validate("analysis", output)
    assert any(i.code == "analysis_generic" for i in result.issues)


def test_insufficient_findings_fails(validator):
    output = StageOutput(
        stage_id="analysis",
        status="completed",
        analysis=_make_analysis(),
        # only 2 findings, need 3
        agent_reports=[],
    )
    # Override findings
    output.analysis.findings = ["f1", "f2"]
    result = validator.validate("analysis", output)
    assert any(i.code == "findings_insufficient" for i in result.issues)


# ---------------------------------------------------------------------------
# Agent report validation
# ---------------------------------------------------------------------------

def test_short_agent_conclusion_fails(validator):
    output = StageOutput(
        stage_id="analysis",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report(conclusion_len=10)],
    )
    result = validator.validate("analysis", output)
    assert not result.passed
    assert any(i.code == "agent_conclusion_short" for i in result.issues)


def test_invalid_confidence_fails(validator):
    report = AgentReport(
        role="dev",
        task="task",
        conclusion="X" * 60,
        confidence=1.5,  # out of range
    )
    output = StageOutput(
        stage_id="analysis",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[report],
    )
    result = validator.validate("analysis", output)
    assert any(i.code == "invalid_confidence" for i in result.issues)


# ---------------------------------------------------------------------------
# Debate validation
# ---------------------------------------------------------------------------

def test_debate_required_stage_fails_without_debate(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
    )
    result = validator.validate("PRD理解", output)
    assert not result.passed
    assert any(i.code == "missing_debate" for i in result.issues)


def test_debate_with_few_rounds_fails(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
        debate_result=DebateResult(
            topic="测试",
            rounds=[DebateRound(round_num=1, opinions=[])],
            consensus="C" * 150,
            convergence_score=0.9,
        ),
    )
    result = validator.validate("PRD理解", output)
    assert not result.passed
    assert any(i.code == "debate_rounds_insufficient" for i in result.issues)


def test_short_consensus_fails(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
        debate_result=DebateResult(
            topic="t",
            rounds=[DebateRound(1, []), DebateRound(2, [])],
            consensus="太短",
            convergence_score=0.9,
        ),
    )
    result = validator.validate("PRD理解", output)
    assert any(i.code == "consensus_short" for i in result.issues)


def test_low_convergence_fails(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
        debate_result=DebateResult(
            topic="t",
            rounds=[DebateRound(1, []), DebateRound(2, [])],
            consensus="C" * 150,
            convergence_score=0.3,
        ),
    )
    result = validator.validate("PRD理解", output)
    assert any(i.code == "low_convergence" for i in result.issues)


def test_valid_debate_passes(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
        debate_result=_make_debate(),
    )
    result = validator.validate("PRD理解", output)
    # Should pass debate checks (other checks may still fail depending on skills)
    assert not any(i.code.startswith("debate") or i.code.startswith("consensus") or i.code == "missing_debate"
                   for i in result.issues)


# ---------------------------------------------------------------------------
# Skill validation
# ---------------------------------------------------------------------------

def test_missing_required_skill_fails(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
        debate_result=_make_debate(),
        skills_used=[],
    )
    result = validator.validate("PRD理解", output)
    assert any(i.code == "missing_required_skill" for i in result.issues)


def test_required_skill_present_passes(validator):
    output = StageOutput(
        stage_id="PRD理解",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
        debate_result=_make_debate(),
        skills_used=["prd-review"],
    )
    result = validator.validate("PRD理解", output)
    assert not any(i.code == "missing_required_skill" for i in result.issues)


# ---------------------------------------------------------------------------
# Non-debate stage
# ---------------------------------------------------------------------------

def test_non_debate_stage_skips_debate_check(validator):
    """A stage not in DEBATE_REQUIRED_STAGES should not require debate."""
    output = StageOutput(
        stage_id="context_discovery",
        status="completed",
        analysis=_make_analysis(),
        agent_reports=[_make_report()],
    )
    result = validator.validate("context_discovery", output)
    assert not any(i.code == "missing_debate" for i in result.issues)
