"""ReqFlow Tool Bridge MCP — 外部工具桥接器。

通过 MCP 协议连接外部工具。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ToolBridgeMCP:
    """外部工具桥接器。"""

    def __init__(self):
        """No args."""
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, handler: Callable) -> None:
        """Register a tool with name and handler function."""
        self._tools[name] = handler
        logger.info("注册工具: %s", name)

    async def call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool by name with arguments dict."""
        handler = self._tools.get(name)
        if not handler:
            raise ValueError(f"工具不存在: {name}")
        return await handler(**arguments)

    def list_tools(self) -> list[str]:
        """List registered tool names."""
        return list(self._tools.keys())
