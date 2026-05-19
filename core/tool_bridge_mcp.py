"""ReqFlow Tool Bridge MCP — 外部工具桥接器。

通过 MCP 协议连接外部工具。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class ExternalTool:
    name: str
    description: str
    type: str  # mcp_server | cli | skill
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    success: bool
    output: Any = None
    error: str = ""


class ToolBridgeMCP:
    """外部工具桥接器。"""

    def __init__(self, config_path: str = "tools.yaml"):
        self.config_path = config_path
        self._tools: dict[str, ExternalTool] = {}

    def load_config(self) -> None:
        """从 tools.yaml 加载工具配置。"""
        if not os.path.exists(self.config_path):
            logger.warning("工具配置文件不存在: %s", self.config_path)
            return

        if not HAS_YAML:
            logger.warning("PyYAML 未安装，无法加载 tools.yaml")
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        for name, tool_config in config.get("tools", {}).items():
            tool = ExternalTool(
                name=name,
                description=tool_config.get("description", ""),
                type=tool_config.get("type", "mcp_server"),
                command=tool_config.get("command", ""),
                args=tool_config.get("args", []),
                env=tool_config.get("env", {}),
            )
            self._tools[name] = tool
            logger.info("加载工具: %s (%s)", name, tool.type)

    def register(self, tool: ExternalTool) -> None:
        """手动注册工具。"""
        self._tools[tool.name] = tool

    def call(self, tool_name: str, method: str, params: dict[str, Any] = None) -> ToolCallResult:
        """调用外部工具。"""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolCallResult(success=False, error=f"工具不存在: {tool_name}")

        if tool.type == "mcp_server":
            return self._call_mcp(tool, method, params or {})
        elif tool.type == "cli":
            return self._call_cli(tool, method, params or {})
        elif tool.type == "skill":
            return self._call_skill(tool, method, params or {})
        else:
            return ToolCallResult(success=False, error=f"未知工具类型: {tool.type}")

    def _call_mcp(self, tool: ExternalTool, method: str, params: dict) -> ToolCallResult:
        """通过 MCP 协议调用。"""
        # TODO: 实际 MCP 协议调用
        logger.info("MCP 调用: %s.%s(%s)", tool.name, method, params)
        return ToolCallResult(success=True, output=f"[MCP] {tool.name}.{method} called")

    def _call_cli(self, tool: ExternalTool, method: str, params: dict) -> ToolCallResult:
        """通过 CLI 调用。"""
        import subprocess
        try:
            cmd = [tool.command] + tool.args + [method] + [str(v) for v in params.values()]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return ToolCallResult(success=result.returncode == 0, output=result.stdout, error=result.stderr)
        except Exception as e:
            return ToolCallResult(success=False, error=str(e))

    def _call_skill(self, tool: ExternalTool, method: str, params: dict) -> ToolCallResult:
        """通过 Skill 调用。"""
        skill_path = tool.command
        if os.path.exists(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolCallResult(success=True, output=content)
        return ToolCallResult(success=False, error=f"Skill 文件不存在: {skill_path}")

    def list_tools(self) -> list[ExternalTool]:
        """列出所有注册的工具。"""
        return list(self._tools.values())

    def check_health(self, tool_name: str) -> bool:
        """检查工具健康状态。"""
        tool = self._tools.get(tool_name)
        if not tool:
            return False
        if tool.type == "cli":
            return os.path.isfile(tool.command) or bool(os.popen(f"which {tool.command}").read().strip())
        return True
