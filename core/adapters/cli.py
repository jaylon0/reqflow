"""CLIAdapter - calls external model CLI tools via subprocess."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, TokenUsage


class CLIAdapter(ModelAdapter):
    """Adapter that invokes external model CLI tools as subprocesses.

    Supports any CLI that reads a prompt from arguments or stdin and
    writes a response to stdout.  Examples: ``claude``, ``codex``, etc.
    """

    def __init__(
        self,
        command: str = "claude",
        args: list[str] | None = None,
        timeout: int = 300,
    ) -> None:
        self._command = command
        self._args: list[str] = args if args is not None else []
        self._timeout = timeout

    @property
    def name(self) -> str:
        return f"cli:{self._command}"

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Build a full prompt and invoke the CLI subprocess."""
        full_prompt = self._build_prompt(prompt, tools=tools, context=context, system_prompt=system_prompt)

        cmd = [self._command, *self._args, full_prompt]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except FileNotFoundError:
            return ModelResponse(
                content="",
                tokens=TokenUsage(),
                raw={"error": f"Command not found: {self._command}"},
            )
        except subprocess.TimeoutExpired:
            return ModelResponse(
                content="",
                tokens=TokenUsage(),
                raw={"error": f"Command timed out after {self._timeout}s"},
            )
        except OSError as exc:
            return ModelResponse(
                content="",
                tokens=TokenUsage(),
                raw={"error": str(exc)},
            )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        content = stdout if stdout else stderr
        return ModelResponse(
            content=content,
            tokens=TokenUsage(),
            raw={
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            },
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        """Execute a tool via a dedicated CLI invocation.

        In CLI mode, tool calls are expressed as prompt instructions.
        This method formats a tool-specific prompt and delegates to
        :meth:`call`.
        """
        prompt_lines = [
            f"Execute the following tool and return only its output.",
            f"Tool: {tool_name}",
            f"Arguments:",
        ]

        try:
            args_json = json.dumps(args, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            args_json = str(args)

        prompt_lines.append(args_json)

        response = self.call("\n".join(prompt_lines))

        has_error = response.raw and response.raw.get("returncode", 0) != 0

        return ToolResult(
            success=not has_error,
            output=response.content,
            error=response.raw.get("stderr") if response.raw else None,
            raw=response.raw,
        )

    def supports_capability(self, capability: str) -> bool:
        """Report which capabilities are typically available via CLI.

        * ``bash`` and ``file_edit`` are generally supported by model CLIs
          that wrap coding agents.
        * ``agent_tools`` depends on the specific CLI and is reported as
          unsupported by default.
        """
        if capability in ("bash", "file_edit"):
            return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(
        prompt: str,
        *,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Assemble the final prompt string sent to the CLI.

        The parts are concatenated with clear delimiters so the receiving
        model can distinguish system instructions, context, and the user
        prompt regardless of its specific format.
        """
        parts: list[str] = []

        if system_prompt:
            parts.append(system_prompt)

        if context:
            parts.append(context)

        if tools:
            tool_list = ", ".join(tools)
            parts.append(f"Available tools: {tool_list}")

        parts.append(prompt)

        return "\n\n".join(parts)
