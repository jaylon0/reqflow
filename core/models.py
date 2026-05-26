"""Core data models for the Engine-driven architecture.

Defines structured data that flows between Engine, StageExecutor,
OutputValidator, and other components. All Agent outputs must follow
these structured formats (not free text).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Basic building blocks
# ---------------------------------------------------------------------------

@dataclass
class Artifact:
    """File or directory artifact produced by a stage."""
    name: str = ""
    path: str = ""
    type: str = ""          # file | directory
    description: str = ""


@dataclass
class Risk:
    """Risk identified during analysis."""
    level: str = "low"      # low | medium | high
    description: str = ""


@dataclass
class Blocker:
    """Blocker that prevents progress."""
    level: str = "P2"       # P0 | P1 | P2
    description: str = ""
    resolved: bool = False


@dataclass
class Decision:
    """Decision made during a stage."""
    topic: str = ""
    choice: str = ""
    reasoning: str = ""
    alternatives: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage-level analysis
# ---------------------------------------------------------------------------

@dataclass
class StageAnalysis:
    """Structured analysis output from a stage.

    summary must be >= 100 chars; findings must have >= 3 items.
    """
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent reports
# ---------------------------------------------------------------------------

@dataclass
class AgentReport:
    """Structured report from a single agent.

    conclusion must be >= 50 chars.
    """
    role: str = ""
    task: str = ""
    conclusion: str = ""
    confidence: float = 0.0         # 0-1
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    skills_requested: list[str] = field(default_factory=list)
    skill_summaries: list[str] = field(default_factory=list)
    iterations: int = 0


# ---------------------------------------------------------------------------
# Debate structures
# ---------------------------------------------------------------------------

@dataclass
class DebateOpinion:
    """Opinion from a single agent in a debate round."""
    role: str = ""
    agent: str = ""
    conclusion: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    cross_commentary: str = ""


@dataclass
class DebateRound:
    """A single round of debate."""
    round_num: int = 0
    opinions: list[DebateOpinion] = field(default_factory=list)
    convergence: float = 0.0        # 0-1


@dataclass
class DebateResult:
    """Result of a multi-round debate.

    consensus must be >= 100 chars.
    """
    topic: str = ""
    rounds: list[DebateRound] = field(default_factory=list)
    consensus: str = ""
    dissenting: list[str] = field(default_factory=list)
    convergence_score: float = 0.0  # 0-1


# ---------------------------------------------------------------------------
# Stage output (main container)
# ---------------------------------------------------------------------------

@dataclass
class StageOutput:
    """Complete output of a stage execution.

    This is the primary data container that flows from StageExecutor
    to OutputValidator and back to Engine.
    """
    stage_id: str = ""
    status: str = "pending"         # pending | running | completed | failed | blocked
    analysis: StageAnalysis = field(default_factory=StageAnalysis)
    agent_reports: list[AgentReport] = field(default_factory=list)
    debate_result: DebateResult | None = None
    artifacts: list[Artifact] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    skills_requested: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (JSON-safe)."""
        data = asdict(self)
        # Remove None debate_result to keep output clean
        if data.get("debate_result") is None:
            data.pop("debate_result", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StageOutput:
        """Deserialize from a plain dict."""
        d = dict(data)

        # Nested objects
        if "analysis" in d and isinstance(d["analysis"], dict):
            analysis_data = d["analysis"]
            analysis_data.setdefault("decisions", [])
            decisions = [Decision(**dec) for dec in analysis_data.pop("decisions", [])]
            d["analysis"] = StageAnalysis(**analysis_data)
            d["analysis"].decisions = decisions

        if "agent_reports" in d:
            reports = []
            for r in d["agent_reports"]:
                r = dict(r)
                r["risks"] = [Risk(**ri) for ri in r.pop("risks", [])]
                reports.append(AgentReport(**r))
            d["agent_reports"] = reports

        if "debate_result" in d and d["debate_result"] is not None:
            dr = dict(d["debate_result"])
            rounds = []
            for rnd in dr.pop("rounds", []):
                rnd = dict(rnd)
                rnd["opinions"] = [DebateOpinion(**o) for o in rnd.pop("opinions", [])]
                rounds.append(DebateRound(**rnd))
            d["debate_result"] = DebateResult(**dr)
            d["debate_result"].rounds = rounds

        if "artifacts" in d:
            d["artifacts"] = [Artifact(**a) for a in d["artifacts"]]

        if "risks" in d:
            d["risks"] = [Risk(**r) for r in d["risks"]]

        if "blockers" in d:
            d["blockers"] = [Blocker(**b) for b in d["blockers"]]

        return cls(**d)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationIssue:
    """Single validation issue."""
    code: str = ""
    message: str = ""
    severity: str = "warning"       # warning | error


@dataclass
class ValidationResult:
    """Result of output validation."""
    passed: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage and Run state
# ---------------------------------------------------------------------------

@dataclass
class StageState:
    """Persistent state for a single stage."""
    stage_id: str = ""
    status: str = "pending"         # pending | running | completed | failed | blocked
    output: StageOutput | None = None
    validation: ValidationResult | None = None
    started_at: str = ""
    completed_at: str = ""
    attempts: int = 0
    skills_used: list[str] = field(default_factory=list)


@dataclass
class RunState:
    """Persistent state for an entire run.

    Tracks all stages, their statuses, and overall run progress.
    """
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requirement: str = ""
    routing_level: str = ""
    status: str = "active"          # active | completed | failed | blocked | rejected
    current_stage: str = ""
    stages: list[StageState] = field(default_factory=list)
    rejection_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def completed_stages(self) -> list[StageState]:
        """Return stages with status 'completed'."""
        return [s for s in self.stages if s.status == "completed"]

    @property
    def total_stages(self) -> int:
        """Total number of stages."""
        return len(self.stages)

    def mark_stage_completed(
        self,
        stage_id: str,
        output: StageOutput | None = None,
        validation: ValidationResult | None = None,
    ) -> None:
        """Mark a stage as completed by its ID."""
        for s in self.stages:
            if s.stage_id == stage_id:
                s.status = "completed"
                s.completed_at = datetime.now().isoformat()
                if output is not None:
                    s.output = output
                if validation is not None:
                    s.validation = validation
                return
        raise ValueError(f"Stage '{stage_id}' not found")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (JSON-safe)."""
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunState:
        """Deserialize from a plain dict."""
        d = dict(data)

        if "stages" in d:
            stages = []
            for s in d["stages"]:
                s = dict(s)
                # Reconstruct nested StageOutput
                output_data = s.pop("output", None)
                output = StageOutput.from_dict(output_data) if output_data else None
                # Reconstruct nested ValidationResult
                val_data = s.pop("validation", None)
                validation = None
                if val_data:
                    val_data = dict(val_data)
                    val_data["issues"] = [
                        ValidationIssue(**i) for i in val_data.pop("issues", [])
                    ]
                    validation = ValidationResult(**val_data)
                s["output"] = output
                s["validation"] = validation
                stages.append(StageState(**s))
            d["stages"] = stages

        return cls(**d)


# ---------------------------------------------------------------------------
# Stage definition (workflow blueprint)
# ---------------------------------------------------------------------------

@dataclass
class AgentRole:
    """Defines an agent's role within a stage."""
    role: str = ""
    task: str = ""


@dataclass
class Stage:
    """Stage definition in a workflow blueprint."""
    id: str = ""
    name: str = ""
    skill: str = ""
    task: str = ""
    agents: list[AgentRole] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    optional_skills: list[str] = field(default_factory=list)
    methodology_skills: list[str] = field(default_factory=list)
    requires_debate: bool = False
    expected_artifacts: list[str] = field(default_factory=list)
