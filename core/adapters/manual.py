"""ManualAdapter - human-in-the-loop adapter for manual execution."""

from __future__ import annotations

import json
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, ToolCall, TokenUsage


class ManualAdapter(ModelAdapter):
    """Adapter that outputs instructions for manual human execution.

    This is the fallback adapter when no model API is available.
    It formats tasks as checklists and waits for human input.
    """

    def __init__(self):
        self._step_count = 0

    @property
    def name(self) -> str:
        return "manual"

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Format the task as a manual checklist."""
        self._step_count += 1

        lines = [
            "=" * 60,
            f"MANUAL MODE - Step {self._step_count}",
            "=" * 60,
            "",
        ]

        if system_prompt:
            lines.append(f"[Context] {system_prompt}")
            lines.append("")

        if context:
            lines.append("[Context Pack]")
            lines.append(context)
            lines.append("")

        lines.append("[Task]")
        lines.append(prompt)
        lines.append("")

        if tools:
            lines.append("[Tools to Use]")
            for tool in tools:
                lines.append(f"  - {tool}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("Please complete the above task and enter the result below.")
        lines.append("Type 'done' when finished, 'skip' to skip, or 'quit' to abort.")
        lines.append("-" * 60)

        # Print to terminal
        print("\n".join(lines))

        # Wait for human input
        result_lines = []
        while True:
            try:
                line = input(">>> ")
            except EOFError:
                return ModelResponse(
                    content="[BLOCKED] 非交互模式无法获取人工输入，请使用 host runtime 或显式指定 --runtime。",
                    tool_calls=[],
                    tokens=TokenUsage(),
                    raw={"mode": "manual", "status": "blocked", "reason": "eof"},
                )
            if line.strip().lower() in ("done", "skip", "quit"):
                break
            result_lines.append(line)

        result = "\n".join(result_lines)

        return ModelResponse(
            content=result,
            tool_calls=[],
            tokens=TokenUsage(),
            raw={"mode": "manual", "step": self._step_count},
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        """Format tool call as manual instruction."""
        lines = [
            "",
            "=" * 40,
            f"MANUAL TOOL EXECUTION: {tool_name}",
            "=" * 40,
        ]

        if tool_name == "bash":
            lines.append(f"Command: {args.get('command', '')}")
        elif tool_name == "read_file":
            lines.append(f"Read file: {args.get('file_path', '')}")
        elif tool_name == "edit_file":
            lines.append(f"Edit file: {args.get('file_path', '')}")
            lines.append(f"Replace: {args.get('old_string', '')}")
            lines.append(f"With: {args.get('new_string', '')}")
        elif tool_name == "write_file":
            lines.append(f"Write file: {args.get('file_path', '')}")
            lines.append(f"Content: {args.get('content', '')[:200]}...")
        else:
            lines.append(f"Tool: {tool_name}")
            lines.append(f"Args: {json.dumps(args, indent=2)}")

        lines.append("-" * 40)
        lines.append("Execute the above and enter result (or 'done' to skip):")

        print("\n".join(lines))

        result_lines = []
        while True:
            try:
                line = input(">>> ")
            except EOFError:
                return ToolResult(
                    success=False,
                    output="",
                    error="[BLOCKED] 非交互模式无法获取人工输入。",
                )
            if line.strip().lower() in ("done", "skip"):
                break
            result_lines.append(line)

        return ToolResult(
            success=True,
            output="\n".join(result_lines),
            raw={"tool": tool_name, "mode": "manual"},
        )

    def supports_capability(self, capability: str) -> bool:
        """Manual mode has no automated capabilities."""
        return False
