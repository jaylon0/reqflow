"""HostAgentRuntime protocol and dataclasses.

This module defines the structured contract between reqflow (orchestrator)
and host agents (executors). The protocol replaces the text-based ModelAdapter
interaction with structured TaskPacket/ResultPacket exchange.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class HostCapabilities:
    """What a host agent platform can do."""
    read_file: bool = True
    write_file: bool = True
    edit_file: bool = True
    bash: bool = True
    search: bool = True
    subagent: bool = False
    browser: bool = False
    user_input: bool = True

    def missing_for(self, required_tools: list[str]) -> list[str]:
        """Return list of required tools that this platform cannot provide."""
        mapping = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "edit_file": self.edit_file,
            "bash": self.bash,
            "search": self.search,
            "subagent": self.subagent,
            "browser": self.browser,
            "user_input": self.user_input,
        }
        return [t for t in required_tools if not mapping.get(t, False)]


@dataclass
class HealthStatus:
    """Health check result for a host agent."""
    platform: str
    status: str  # ok | degraded | unavailable
    capabilities: HostCapabilities = field(default_factory=HostCapabilities)
    missing: list[str] = field(default_factory=list)


@dataclass
class ArtifactInfo:
    """Metadata about a produced artifact file."""
    path: str
    exists: bool = False
    size_bytes: int = 0
    checksum: str = ""
    created_at: str = ""


@dataclass
class CommandInfo:
    """Record of a command that was executed."""
    command: str
    exit_code: int = 0
    output: str = ""


@dataclass
class VerificationResult:
    """Result of running verification commands."""
    passed: bool = False
    commands: list[CommandInfo] = field(default_factory=list)
    details: str = ""


@dataclass
class TaskPacket:
    """Structured task sent from reqflow to host agent.

    This is NOT a prompt. It is an execution contract that specifies
    what to do, what tools to use, what artifacts to produce, and
    how to verify success.
    """
    task_id: str
    stage_id: int
    stage_name: str
    instruction: str                # Natural language for the model
    required_tools: list[str]       # Tools the agent MUST use
    expected_artifacts: list[str]   # Files that must exist after execution
    acceptance_criteria: list[str]  # What "done" means
    allowed_paths: list[str]        # Constraint: paths the agent may touch
    verification_commands: list[str] # Commands to verify success
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON/file storage."""
        return {
            "task_id": self.task_id,
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "instruction": self.instruction,
            "required_tools": self.required_tools,
            "expected_artifacts": self.expected_artifacts,
            "acceptance_criteria": self.acceptance_criteria,
            "allowed_paths": self.allowed_paths,
            "verification_commands": self.verification_commands,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskPacket:
        """Deserialize from dict."""
        return cls(**data)


@dataclass
class ResultPacket:
    """Structured result returned from host agent to reqflow.

    status=success is ONLY valid when all expected_artifacts exist
    with size > 0 AND all verification_commands pass.
    Missing capabilities MUST return status=blocked.
    """
    task_id: str
    status: str                     # success | failed | blocked | skipped
    summary: str
    artifacts: list[ArtifactInfo] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    commands_run: list[CommandInfo] = field(default_factory=list)
    verification_result: VerificationResult = field(default_factory=VerificationResult)
    findings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    missing_capabilities: list[str] = field(default_factory=list)
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON/file storage."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "summary": self.summary,
            "artifacts": [
                {"path": a.path, "exists": a.exists, "size_bytes": a.size_bytes,
                 "checksum": a.checksum, "created_at": a.created_at}
                for a in self.artifacts
            ],
            "files_changed": self.files_changed,
            "commands_run": [
                {"command": c.command, "exit_code": c.exit_code, "output": c.output}
                for c in self.commands_run
            ],
            "verification_result": {
                "passed": self.verification_result.passed,
                "commands": [
                    {"command": c.command, "exit_code": c.exit_code, "output": c.output}
                    for c in self.verification_result.commands
                ],
                "details": self.verification_result.details,
            },
            "findings": self.findings,
            "blockers": self.blockers,
            "missing_capabilities": self.missing_capabilities,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResultPacket:
        """Deserialize from dict."""
        artifacts = [ArtifactInfo(**a) for a in data.get("artifacts", [])]
        commands_run = [CommandInfo(**c) for c in data.get("commands_run", [])]
        vr_data = data.get("verification_result", {})
        vr_commands = [CommandInfo(**c) for c in vr_data.get("commands", [])]
        verification = VerificationResult(
            passed=vr_data.get("passed", False),
            commands=vr_commands,
            details=vr_data.get("details", ""),
        )
        return cls(
            task_id=data["task_id"],
            status=data["status"],
            summary=data.get("summary", ""),
            artifacts=artifacts,
            files_changed=data.get("files_changed", []),
            commands_run=commands_run,
            verification_result=verification,
            findings=data.get("findings", []),
            blockers=data.get("blockers", []),
            missing_capabilities=data.get("missing_capabilities", []),
            duration_ms=data.get("duration_ms", 0),
        )


class HostAgentRuntime(Protocol):
    """Protocol that host agent adapters must implement.

    This is NOT ModelAdapter. ModelAdapter sends prompts to models.
    HostAgentRuntime sends structured tasks to agent platforms and
    receives structured results.
    """

    @property
    def platform(self) -> str:
        """Platform identifier: codex / claude-code / cursor / etc."""
        ...

    @property
    def capabilities(self) -> HostCapabilities:
        """What this agent platform can do."""
        ...

    async def execute_task(self, task: TaskPacket) -> ResultPacket:
        """Execute a structured task and return a structured result.

        If the agent cannot execute (missing capabilities, no response channel),
        returns ResultPacket with status=blocked. NEVER returns success when
        work was not actually done.
        """
        ...

    def check_health(self) -> HealthStatus:
        """Check if this host agent is available and capable."""
        ...
