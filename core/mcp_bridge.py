"""MCP (Model Context Protocol) tool bridge for external tool integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPServerConfig:
    """Configuration for connecting to an MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class MCPTool:
    """A tool discovered from an MCP server."""
    name: str
    server: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResult:
    """Result from calling an MCP tool."""
    success: bool
    data: Any = None
    error: str | None = None


class MCPBridge:
    """Connects to MCP servers for tool discovery and invocation."""

    def __init__(self, server_configs: list[MCPServerConfig]):
        self.servers = server_configs
        self._discovered_tools: list[MCPTool] = []

    async def discover_tools(self) -> list[MCPTool]:
        """Connect to all MCP servers and discover available tools."""
        all_tools: list[MCPTool] = []
        for server in self.servers:
            try:
                tools = await self._connect(server.name)
                all_tools.extend(tools)
            except Exception:
                pass
        self._discovered_tools = all_tools
        return all_tools

    async def call_tool(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on an MCP server."""
        return await self._call_remote(server, tool, args)

    def get_tools_for_prompt(self) -> str:
        """Format discovered tools as a prompt section for LLM context."""
        if not self._discovered_tools:
            return ""
        lines = ["## Available MCP Tools\n"]
        for tool in self._discovered_tools:
            lines.append(f"- **{tool.name}** (server: {tool.server}): {tool.description}")
            if tool.parameters:
                lines.append(f"  Parameters: {tool.parameters}")
        return "\n".join(lines)

    async def _connect(self, server_name: str) -> list[MCPTool]:
        raise NotImplementedError(f"MCP connection not implemented for '{server_name}'")

    async def _call_remote(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(f"MCP call not implemented for '{server}'/'{tool}'")
