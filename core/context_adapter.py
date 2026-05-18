"""ContextAdapter - format context for different model runtimes."""

from __future__ import annotations

from typing import Any

from .runtime_config import RuntimeConfig


class ContextAdapter:
    """Adapts context packs and system prompts for different model runtimes."""

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.max_tokens = config.capabilities.max_context_tokens

    def format_context(self, context_pack: dict[str, Any]) -> str:
        """Format a context pack into the runtime's preferred format."""
        fmt = self.config.context_format.artifact_format

        if fmt == "json":
            return self._format_json(context_pack)
        else:
            return self._format_markdown(context_pack)

    def _format_markdown(self, context_pack: dict[str, Any]) -> str:
        """Format context pack as markdown."""
        lines = ["# Context Pack\n"]

        for key, value in context_pack.items():
            if value is None:
                continue
            if isinstance(value, list):
                lines.append(f"## {key.replace('_', ' ').title()}\n")
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            lines.append(f"- **{k}**: {v}")
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            elif isinstance(value, dict):
                lines.append(f"## {key.replace('_', ' ').title()}\n")
                for k, v in value.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")
            else:
                lines.append(f"## {key.replace('_', ' ').title()}\n")
                lines.append(str(value))
                lines.append("")

        return "\n".join(lines)

    def _format_json(self, context_pack: dict[str, Any]) -> str:
        """Format context pack as JSON."""
        import json
        return json.dumps(context_pack, indent=2, ensure_ascii=False)

    def format_system_prompt(self, workflow_step: str, extra_context: str = "") -> str:
        """Generate a system prompt for the given workflow step."""
        lines = [
            f"You are ReqFlow, a workflow automation agent.",
            f"Current step: {workflow_step}",
            f"Runtime: {self.config.display_name}",
            "",
        ]

        # Add capability context
        caps = self.config.capabilities
        if caps.supports_agent_tools:
            lines.append("You can dispatch sub-agents for focused tasks.")
        if caps.supports_bash:
            lines.append("You can execute shell commands.")
        if caps.supports_file_edit:
            lines.append("You can read and edit files directly.")

        if extra_context:
            lines.append("")
            lines.append(extra_context)

        return "\n".join(lines)

    def truncate_to_fit(self, content: str, reserved_tokens: int = 10000) -> str:
        """Truncate content to fit within the model's context window.

        Uses a rough estimate of 4 chars per token.
        """
        if self.max_tokens <= 0:
            return content

        max_chars = (self.max_tokens - reserved_tokens) * 4
        if len(content) <= max_chars:
            return content

        # Truncate and add indicator
        truncated = content[:max_chars]
        truncated += f"\n\n[... truncated - original {len(content)} chars, showing first {max_chars} chars]"
        return truncated

    def format_for_manual_mode(self, context_pack: dict[str, Any]) -> str:
        """Format context as a checklist for manual execution."""
        lines = ["# Manual Execution Checklist\n"]
        lines.append("Please complete the following steps and report results:\n")

        step_num = 1
        for key, value in context_pack.items():
            if value is None:
                continue
            lines.append(f"## Step {step_num}: {key.replace('_', ' ').title()}")
            if isinstance(value, list):
                for item in value:
                    lines.append(f"- [ ] {item}")
            elif isinstance(value, dict):
                for k, v in value.items():
                    lines.append(f"- [ ] {k}: {v}")
            else:
                lines.append(f"- [ ] {value}")
            lines.append("")
            step_num += 1

        return "\n".join(lines)
