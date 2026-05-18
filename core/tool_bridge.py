"""ToolBridge - unified tool interface across different model runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapters.base import ToolResult
from .runtime_config import RuntimeConfig


# Canonical tool definitions
CANONICAL_TOOLS = {
    "read_file": {
        "description": "Read the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file"},
            },
            "required": ["file_path"],
        },
    },
    "edit_file": {
        "description": "Edit a file by replacing exact text",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file"},
                "old_string": {"type": "string", "description": "Exact text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
            },
            "required": ["file_path", "old_string", "new_string"],
        },
    },
    "write_file": {
        "description": "Write content to a file (create or overwrite)",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["file_path", "content"],
        },
    },
    "bash": {
        "description": "Execute a shell command",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in milliseconds", "default": 120000},
            },
            "required": ["command"],
        },
    },
    "agent": {
        "description": "Dispatch a sub-agent for a focused task",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Short description of the task"},
                "prompt": {"type": "string", "description": "Full task prompt for the sub-agent"},
                "model": {"type": "string", "description": "Model to use (haiku, sonnet, opus)"},
            },
            "required": ["description", "prompt"],
        },
    },
}


class ToolBridge:
    """Bridges canonical tools to runtime-specific implementations."""

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self._tool_mapping = {
            "read_file": config.tool_mapping.read_file,
            "edit_file": config.tool_mapping.edit_file,
            "write_file": config.tool_mapping.edit_file,
            "bash": config.tool_mapping.bash,
            "agent": config.tool_mapping.agent,
        }

    def map_tool_name(self, canonical_name: str) -> str | None:
        """Map a canonical tool name to the runtime's tool name."""
        return self._tool_mapping.get(canonical_name)

    def get_tool_descriptions(self) -> list[dict[str, Any]]:
        """Generate tool descriptions in the runtime's format."""
        fmt = self.config.context_format.skill_format

        descriptions = []
        for canonical_name, tool_def in CANONICAL_TOOLS.items():
            runtime_name = self.map_tool_name(canonical_name)
            if runtime_name is None:
                continue  # Tool not available in this runtime

            if fmt == "json":
                # Function calling format (GPT, Gemini)
                descriptions.append({
                    "name": runtime_name,
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"],
                })
            else:
                # Markdown format (Claude, Manual)
                descriptions.append({
                    "name": runtime_name,
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"],
                })

        return descriptions

    def get_available_tools(self) -> list[str]:
        """List canonical tool names available in this runtime."""
        available = []
        for canonical_name in CANONICAL_TOOLS:
            if self.map_tool_name(canonical_name) is not None:
                available.append(canonical_name)
        return available

    def format_tools_for_prompt(self) -> str:
        """Format tool descriptions as a prompt section."""
        lines = ["## Available Tools\n"]
        for canonical_name in self.get_available_tools():
            tool_def = CANONICAL_TOOLS[canonical_name]
            runtime_name = self.map_tool_name(canonical_name)
            lines.append(f"### {runtime_name}")
            lines.append(f"{tool_def['description']}\n")
            params = tool_def["parameters"]["properties"]
            for param_name, param_def in params.items():
                lines.append(f"- `{param_name}`: {param_def.get('description', '')}")
            lines.append("")
        return "\n".join(lines)
