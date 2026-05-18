"""Agent Registry - generates .claude/agents/*.md files from workflow definitions.

Reads agent_templates from workflow YAML and generates official Claude Code
sub-agent definition files with YAML frontmatter.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Official Claude Code sub-agent frontmatter fields
_FRONTMATTER_FIELDS = {
    "name": str,
    "description": str,
    "tools": list,
    "disallowedTools": list,
    "model": str,
    "permissionMode": str,
    "maxTurns": int,
    "skills": list,
    "mcpServers": (dict, list),
    "hooks": dict,
    "memory": str,
    "background": bool,
    "effort": str,
    "isolation": str,
    "color": str,
    "initialPrompt": str,
}


class AgentRegistry:
    """Manages agent definitions and generates .claude/agents/*.md files."""

    def __init__(self, agents_dir: str | None = None):
        if agents_dir is None:
            agents_dir = ".claude/agents"
        self.agents_dir = Path(agents_dir)
        self._templates: dict[str, dict[str, Any]] = {}

    def load_from_workflow(self, workflow_definition: dict[str, Any]) -> None:
        """Load agent templates from a workflow definition dict.

        Args:
            workflow_definition: Full workflow YAML dict with optional 'agent_templates' key.
        """
        templates = workflow_definition.get("agent_templates", {})
        if not isinstance(templates, dict):
            return
        for name, config in templates.items():
            if isinstance(config, dict):
                self._templates[name] = config

    def register(self, name: str, config: dict[str, Any]) -> None:
        """Register an agent template programmatically.

        Args:
            name: Agent name (lowercase, hyphens).
            config: Agent configuration dict with frontmatter fields + 'prompt' body.
        """
        self._templates[name] = config

    def get(self, name: str) -> dict[str, Any] | None:
        """Get an agent template by name."""
        return self._templates.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._templates.keys())

    def generate_files(self, output_dir: str | None = None) -> list[str]:
        """Generate .claude/agents/*.md files.

        Args:
            output_dir: Override output directory. Defaults to self.agents_dir.

        Returns:
            List of generated file paths.
        """
        target_dir = Path(output_dir) if output_dir else self.agents_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        generated = []
        for name, config in self._templates.items():
            filepath = target_dir / f"{name}.md"
            content = self._render_agent_md(name, config)
            filepath.write_text(content, encoding="utf-8")
            generated.append(str(filepath))

        return generated

    def _render_agent_md(self, name: str, config: dict[str, Any]) -> str:
        """Render an agent definition as markdown with YAML frontmatter.

        Args:
            name: Agent name.
            config: Agent configuration dict.

        Returns:
            Complete .md file content with YAML frontmatter.
        """
        lines = ["---"]

        # Always include name first
        lines.append(f"name: {name}")

        # Write frontmatter fields in canonical order (skip name, already written)
        for field_name in _FRONTMATTER_FIELDS:
            if field_name == "name":
                continue
            if field_name in config:
                value = config[field_name]
                lines.append(self._yaml_field(field_name, value))

        # Write any extra fields not in the standard set
        for key, value in config.items():
            if key not in _FRONTMATTER_FIELDS and key != "prompt":
                lines.append(self._yaml_field(key, value))

        lines.append("---")
        lines.append("")

        # Write prompt body
        prompt = config.get("prompt", "")
        if prompt:
            lines.append(prompt.strip())
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _yaml_field(key: str, value: Any) -> str:
        """Format a single YAML frontmatter field."""
        if isinstance(value, bool):
            return f"{key}: {'true' if value else 'false'}"
        if isinstance(value, (int, float)):
            return f"{key}: {value}"
        if isinstance(value, list):
            if not value:
                return f"{key}: []"
            items = ", ".join(str(v) for v in value)
            return f"{key}: [{items}]"
        if isinstance(value, dict):
            # Inline JSON for complex objects
            return f"{key}: {json.dumps(value, ensure_ascii=False)}"
        # String: quote if contains special chars
        s = str(value)
        if any(c in s for c in ":#{}[]&*?|>',\"\n"):
            return f'{key}: "{s}"'
        return f"{key}: {s}"
