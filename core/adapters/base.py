"""ModelAdapter protocol - the core abstraction for model-agnostic execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens: TokenUsage = field(default_factory=TokenUsage)
    raw: Any = None  # Original response from the model/runtime


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    raw: Any = None


class ModelAdapter(Protocol):
    """Protocol that all model adapters must implement."""

    @property
    def name(self) -> str:
        """Adapter identifier (e.g., 'claude_code', 'gpt', 'manual')."""
        ...

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        """Send a prompt to the model and get a response.

        Args:
            prompt: The user prompt / task description.
            tools: List of canonical tool names the model may use.
            context: Additional context (e.g., context pack content).
            system_prompt: System prompt override.
        """
        ...

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        """Execute a tool call and return the result.

        Args:
            tool_name: Canonical tool name (e.g., 'read_file', 'bash').
            args: Tool arguments.
        """
        ...

    def supports_capability(self, capability: str) -> bool:
        """Check if the adapter supports a specific capability.

        Capabilities: 'agent_tools', 'bash', 'file_edit', 'image', 'parallel'.
        """
        ...
