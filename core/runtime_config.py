"""RuntimeConfig interface for model-agnostic runtime abstraction."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Capabilities:
    supports_agent_tools: bool = True
    supports_bash: bool = True
    supports_file_edit: bool = True
    supports_image: bool = False
    supports_subagent: bool = False
    max_context_tokens: int = 200000


@dataclass
class ToolMapping:
    read_file: str = "Read"
    edit_file: str = "Edit"
    bash: str = "Bash"
    agent: Optional[str] = "Agent"


@dataclass
class ContextFormat:
    system_prompt_template: str = "templates/system-prompt.md"
    skill_format: str = "markdown"
    artifact_format: str = "markdown"


@dataclass
class RuntimePaths:
    run_dir: str = ".dev-workflow/runs/"
    state_file: str = "state.json"
    log_file: str = "execution.log"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class RuntimeConfig:
    name: str
    display_name: str
    capabilities: Capabilities = field(default_factory=Capabilities)
    tool_mapping: ToolMapping = field(default_factory=ToolMapping)
    context_format: ContextFormat = field(default_factory=ContextFormat)
    paths: RuntimePaths = field(default_factory=RuntimePaths)
    # API fields (Phase 1)
    api_key: str = ""
    api_base: str = ""
    model: str = ""
    env_key: str = ""
    # MCP servers (Phase 3)
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)
