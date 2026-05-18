"""Thin platform adapters for host agent runtime.

Each adapter does exactly 3 things:
1. Declare platform capabilities and tool mapping
2. Convert TaskPacket -> platform-native format (build_task_payload)
3. Convert platform-native result -> ResultPacket (parse_result)

NO workflow logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..host_agent import (
    HostCapabilities, TaskPacket, ResultPacket,
)
from .host_agent import GenericHostAgentAdapter


@dataclass
class CodexAdapter(GenericHostAgentAdapter):
    """Codex (OpenAI) platform adapter."""
    platform_name: str = "codex"
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=False, browser=False, user_input=True,
    ))

    def build_task_payload(self, task: TaskPacket) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "stage_id": task.stage_id,
            "stage_name": task.stage_name,
            "instruction": task.instruction,
            "tools": [
                {"type": "function", "function": {"name": t}}
                for t in task.required_tools
            ],
            "expected_artifacts": task.expected_artifacts,
            "acceptance_criteria": task.acceptance_criteria,
            "constraints": {"allowed_paths": task.allowed_paths},
            "verification": task.verification_commands,
        }

    def parse_result(self, raw: dict[str, Any]) -> ResultPacket:
        return ResultPacket.from_dict(raw)


@dataclass
class ClaudeCodeAdapter(GenericHostAgentAdapter):
    """Claude Code platform adapter."""
    platform_name: str = "claude-code"
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=True, browser=False, user_input=True,
    ))

    def build_task_payload(self, task: TaskPacket) -> dict[str, Any]:
        tool_map = {
            "read_file": "Read",
            "write_file": "Write",
            "edit_file": "Edit",
            "bash": "Bash",
            "search": "Grep",
            "subagent": "Agent",
        }
        return {
            "task_id": task.task_id,
            "instruction": task.instruction,
            "tools": [tool_map.get(t, t) for t in task.required_tools],
            "expected_artifacts": task.expected_artifacts,
            "acceptance_criteria": task.acceptance_criteria,
            "allowed_paths": task.allowed_paths,
            "verification": task.verification_commands,
        }

    def parse_result(self, raw: dict[str, Any]) -> ResultPacket:
        return ResultPacket.from_dict(raw)


@dataclass
class CursorAdapter(GenericHostAgentAdapter):
    """Cursor platform adapter."""
    platform_name: str = "cursor"
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=False, browser=False, user_input=True,
    ))

    def build_task_payload(self, task: TaskPacket) -> dict[str, Any]:
        return task.to_dict()

    def parse_result(self, raw: dict[str, Any]) -> ResultPacket:
        return ResultPacket.from_dict(raw)


@dataclass
class GeminiCLIAdapter(GenericHostAgentAdapter):
    """Gemini CLI platform adapter."""
    platform_name: str = "gemini-cli"
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=False, browser=False, user_input=True,
    ))

    def build_task_payload(self, task: TaskPacket) -> dict[str, Any]:
        return task.to_dict()

    def parse_result(self, raw: dict[str, Any]) -> ResultPacket:
        return ResultPacket.from_dict(raw)


@dataclass
class CopilotAdapter(GenericHostAgentAdapter):
    """GitHub Copilot Agent platform adapter."""
    platform_name: str = "copilot"
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=False, browser=False, user_input=True,
    ))

    def build_task_payload(self, task: TaskPacket) -> dict[str, Any]:
        return task.to_dict()

    def parse_result(self, raw: dict[str, Any]) -> ResultPacket:
        return ResultPacket.from_dict(raw)


@dataclass
class CodeFlickerAdapter(GenericHostAgentAdapter):
    """CodeFlicker platform adapter."""
    platform_name: str = "codeflicker"
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=False, browser=False, user_input=True,
    ))

    def build_task_payload(self, task: TaskPacket) -> dict[str, Any]:
        return task.to_dict()

    def parse_result(self, raw: dict[str, Any]) -> ResultPacket:
        return ResultPacket.from_dict(raw)
