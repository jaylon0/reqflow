"""ClaudeCodeAdapter - embedded adapter for Claude Code environment."""

from __future__ import annotations

from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, ToolCall, TokenUsage


class ClaudeCodeAdapter(ModelAdapter):
    """Adapter that runs inside Claude Code and uses its native tools.

    This adapter doesn't call an external API. Instead, it generates
    structured instructions that Claude Code executes using its built-in
    tools (Agent, Bash, Read, Edit).
    """

    def __init__(self):
        self._last_response: ModelResponse | None = None

    @property
    def name(self) -> str:
        return "claude_code"

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Generate a structured prompt for Claude Code to execute.

        In Claude Code, this doesn't actually call a model - it formats
        the request as instructions that Claude Code will execute.
        """
        # Build the instruction
        parts = []
        if system_prompt:
            parts.append(f"[System]\n{system_prompt}\n")
        if context:
            parts.append(f"[Context]\n{context}\n")
        parts.append(f"[Task]\n{prompt}\n")
        if tools:
            parts.append(f"[Available Tools]\n{', '.join(tools)}\n")

        instruction = "\n".join(parts)

        # In Claude Code, this instruction becomes the prompt
        # The actual execution happens through Claude Code's tool system
        self._last_response = ModelResponse(
            content=instruction,
            tool_calls=[],
            tokens=TokenUsage(),
        )
        return self._last_response

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        """Execute a tool using Claude Code's native tools.

        In Claude Code, tool execution is handled by the runtime.
        This method generates the tool call instruction.
        """
        # Map canonical names to Claude Code tool names
        tool_map = {
            "read_file": "Read",
            "edit_file": "Edit",
            "write_file": "Write",
            "bash": "Bash",
            "agent": "Agent",
        }

        cc_tool = tool_map.get(tool_name, tool_name)

        # Generate tool call instruction
        if tool_name == "read_file":
            instruction = f"Read file: {args.get('file_path', '')}"
        elif tool_name == "edit_file":
            instruction = f"Edit file: {args.get('file_path', '')}"
        elif tool_name == "write_file":
            instruction = f"Write file: {args.get('file_path', '')}"
        elif tool_name == "bash":
            instruction = f"Run command: {args.get('command', '')}"
        elif tool_name == "agent":
            instruction = f"Dispatch agent: {args.get('description', '')}"
        else:
            instruction = f"Execute {cc_tool}: {args}"

        return ToolResult(
            success=True,
            output=instruction,
            raw={"tool": cc_tool, "args": args},
        )

    def supports_capability(self, capability: str) -> bool:
        """Claude Code supports all capabilities."""
        capabilities = {
            "agent_tools": True,
            "bash": True,
            "file_edit": True,
            "image": True,
            "parallel": True,
        }
        return capabilities.get(capability, False)
