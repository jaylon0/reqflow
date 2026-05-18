# ReqFlow V2 Phase 3: Ecosystem Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add MCP tool bridge for external tool integration, session management for cross-turn persistence, and a terminal dashboard for workflow observability.

**Architecture:** New modules `core/mcp_bridge.py`, `core/session.py`, and `runner/dashboard.py`. MCP is optional dependency. Session uses JSON file storage. Dashboard uses `rich` library.

**Tech Stack:** Python 3.10+, pytest, rich (optional), mcp (optional)

---

## File Structure

```
reqflow/
├── core/
│   ├── mcp_bridge.py         # CREATE: MCP server connection and tool discovery
│   ├── session.py            # CREATE: Session-level state persistence
│   └── runtime_config.py     # MODIFY: add mcp_servers field
├── runner/
│   └── dashboard.py          # CREATE: Terminal TUI dashboard
└── tests/
    ├── test_mcp_bridge.py    # CREATE: MCP bridge tests (mock)
    ├── test_session.py       # CREATE: Session tests
    └── test_dashboard.py     # CREATE: Dashboard tests (basic)
```

---

### Task 1: MCP data structures and bridge

**Files:**
- Create: `reqflow/core/mcp_bridge.py`
- Modify: `reqflow/core/runtime_config.py`
- Test: `reqflow/tests/test_mcp_bridge.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_mcp_bridge.py
import asyncio
from unittest.mock import AsyncMock, patch
from reqflow.core.mcp_bridge import MCPBridge, MCPServerConfig, MCPTool

def test_mcp_server_config():
    config = MCPServerConfig(
        name="database",
        command="mcp-server-postgres",
        args=["--connection-string", "postgresql://localhost/test"],
    )
    assert config.name == "database"
    assert config.command == "mcp-server-postgres"
    assert config.args == ["--connection-string", "postgresql://localhost/test"]

def test_mcp_tool_creation():
    tool = MCPTool(
        name="query",
        server="database",
        description="Execute SQL query",
        parameters={"sql": {"type": "string"}},
    )
    assert tool.name == "query"
    assert tool.server == "database"

def test_mcp_bridge_init():
    configs = [
        MCPServerConfig(name="db", command="mcp-server-db", args=[]),
    ]
    bridge = MCPBridge(configs)
    assert len(bridge.servers) == 1
    assert bridge.servers[0].name == "db"

def test_mcp_bridge_discover_tools_mock():
    """Test tool discovery with mocked MCP connection."""
    configs = [
        MCPServerConfig(name="db", command="mcp-server-db", args=[]),
    ]
    bridge = MCPBridge(configs)

    # Mock the internal _connect method to return tools
    async def mock_connect(server_name):
        return [
            MCPTool(name="query", server=server_name, description="Run query", parameters={}),
            MCPTool(name="list_tables", server=server_name, description="List tables", parameters={}),
        ]

    bridge._connect = mock_connect
    tools = asyncio.run(bridge.discover_tools())
    assert len(tools) == 2
    assert tools[0].name == "query"
    assert tools[1].name == "list_tables"

def test_mcp_bridge_call_tool_mock():
    configs = [
        MCPServerConfig(name="db", command="mcp-server-db", args=[]),
    ]
    bridge = MCPBridge(configs)

    async def mock_call(server, tool, args):
        return {"result": "ok", "rows": 5}

    bridge._call_remote = mock_call
    result = asyncio.run(bridge.call_tool("db", "query", {"sql": "SELECT 1"}))
    assert result["result"] == "ok"
    assert result["rows"] == 5

def test_mcp_bridge_runtime_config():
    """MCPServerConfig can be added to RuntimeConfig."""
    from reqflow.core.runtime_config import RuntimeConfig, MCPServerConfig as RTMCPServerConfig
    config = RuntimeConfig(
        name="test",
        display_name="Test",
        mcp_servers=[RTMCPServerConfig(name="db", command="mcp-db", args=[])],
    )
    assert len(config.mcp_servers) == 1
    assert config.mcp_servers[0].name == "db"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_mcp_bridge.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Add MCPServerConfig to RuntimeConfig**

Add to `reqflow/core/runtime_config.py`:

```python
@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
```

Add to `RuntimeConfig` dataclass:

```python
    # MCP servers (Phase 3)
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)
```

- [ ] **Step 4: Implement MCPBridge**

```python
# reqflow/core/mcp_bridge.py
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
        """Connect to all MCP servers and discover available tools.

        Returns:
            List of all tools from all connected servers.
        """
        all_tools: list[MCPTool] = []
        for server in self.servers:
            try:
                tools = await self._connect(server.name)
                all_tools.extend(tools)
            except Exception:
                pass  # Skip unreachable servers
        self._discovered_tools = all_tools
        return all_tools

    async def call_tool(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on an MCP server.

        Args:
            server: Server name.
            tool: Tool name.
            args: Tool arguments.

        Returns:
            Result dict from the tool call.
        """
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

    # --- Internal methods (override in tests or subclasses) ---

    async def _connect(self, server_name: str) -> list[MCPTool]:
        """Connect to an MCP server and return its tools.

        Override this in production with actual MCP protocol implementation.
        """
        raise NotImplementedError(f"MCP connection not implemented for '{server_name}'")

    async def _call_remote(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call a remote MCP tool.

        Override this in production with actual MCP protocol implementation.
        """
        raise NotImplementedError(f"MCP call not implemented for '{server}'/'{tool}'")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_mcp_bridge.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add reqflow/core/mcp_bridge.py reqflow/core/runtime_config.py reqflow/tests/test_mcp_bridge.py
git commit -m "feat: add MCPBridge with tool discovery and invocation"
```

---

### Task 2: Session management

**Files:**
- Create: `reqflow/core/session.py`
- Test: `reqflow/tests/test_session.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_session.py
import json
from pathlib import Path
from reqflow.core.session import Session

def test_session_create(tmp_path):
    session = Session(session_id="test-1", storage_dir=str(tmp_path))
    assert session.session_id == "test-1"

def test_session_save_get_context(tmp_path):
    session = Session(session_id="test-2", storage_dir=str(tmp_path))
    session.save_context("project", "reqflow")
    session.save_context("requirement", "add auth")
    assert session.get_context("project") == "reqflow"
    assert session.get_context("requirement") == "add auth"
    assert session.get_context("nonexistent") is None

def test_session_persistence(tmp_path):
    session = Session(session_id="test-3", storage_dir=str(tmp_path))
    session.save_context("key", "value")
    session.save()

    # Reload
    session2 = Session(session_id="test-3", storage_dir=str(tmp_path))
    session2.load()
    assert session2.get_context("key") == "value"

def test_session_history(tmp_path):
    session = Session(session_id="test-4", storage_dir=str(tmp_path))
    session.add_history("step1", "analyzed requirement")
    session.add_history("step2", "wrote code")
    assert len(session.history) == 2
    assert session.history[0]["step"] == "step1"

def test_session_summarize(tmp_path):
    session = Session(session_id="test-5", storage_dir=str(tmp_path))
    session.add_history("step1", "a" * 500)
    session.add_history("step2", "b" * 500)
    summary = session.summarize(max_length=100)
    assert len(summary) <= 100

def test_session_list_sessions(tmp_path):
    Session(session_id="s1", storage_dir=str(tmp_path)).save()
    Session(session_id="s2", storage_dir=str(tmp_path)).save()
    sessions = Session.list_sessions(str(tmp_path))
    assert "s1" in sessions
    assert "s2" in sessions
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_session.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement Session**

```python
# reqflow/core/session.py
"""Session management for cross-turn context persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime


class Session:
    """Session-level state persistence across workflow turns."""

    def __init__(self, session_id: str, storage_dir: str):
        self.session_id = session_id
        self.storage_dir = Path(storage_dir)
        self._context: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []

    def save_context(self, key: str, value: Any) -> None:
        """Save a piece of context for this session."""
        self._context[key] = value

    def get_context(self, key: str) -> Any:
        """Retrieve context from this session. Returns None if not found."""
        return self._context.get(key)

    def add_history(self, step: str, result: str) -> None:
        """Add an entry to the session history."""
        self.history.append({
            "step": step,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })

    def summarize(self, max_length: int = 500) -> str:
        """Generate a compressed summary of session history.

        Args:
            max_length: Maximum character length of the summary.

        Returns:
            Truncated summary string.
        """
        if not self.history:
            return ""

        parts = []
        for entry in self.history:
            parts.append(f"[{entry['step']}] {entry['result'][:100]}")

        summary = " | ".join(parts)
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."
        return summary

    def save(self) -> None:
        """Save session state to disk."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "context": self._context,
            "history": self.history,
        }
        path = self._session_path()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load session state from disk."""
        path = self._session_path()
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self._context = data.get("context", {})
        self.history = data.get("history", [])

    @staticmethod
    def list_sessions(storage_dir: str) -> list[str]:
        """List all session IDs in the storage directory."""
        dir_path = Path(storage_dir)
        if not dir_path.is_dir():
            return []
        return sorted(
            p.stem for p in dir_path.glob("session-*.json")
        )

    def _session_path(self) -> Path:
        return self.storage_dir / f"session-{self.session_id}.json"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_session.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/session.py reqflow/tests/test_session.py
git commit -m "feat: add Session for cross-turn context persistence"
```

---

### Task 3: Terminal dashboard

**Files:**
- Create: `reqflow/runner/dashboard.py`
- Test: `reqflow/tests/test_dashboard.py`

- [ ] **Step 1: Write the failing tests**

```python
# reqflow/tests/test_dashboard.py
from reqflow.runner.dashboard import Dashboard

def test_dashboard_init():
    dashboard = Dashboard(run_dir="/tmp/test-dashboard")
    assert dashboard.run_dir == "/tmp/test-dashboard"

def test_dashboard_format_status():
    dashboard = Dashboard(run_dir="/tmp/test-dashboard")
    status = {
        "run_id": "run-abc123",
        "config": "gpt",
        "adapter": "api_gpt",
        "current_stage": "verify",
        "completed_modules": ["analyze", "implement"],
        "steps_executed": 2,
        "step_statuses": {"analyze": "success", "implement": "success"},
        "checkpoints": 1,
        "memory_entries": 3,
    }
    output = dashboard.format_status(status)
    assert "run-abc123" in output
    assert "verify" in output
    assert "analyze" in output

def test_dashboard_format_trace():
    dashboard = Dashboard(run_dir="/tmp/test-dashboard")
    trace_data = {
        "spans": [
            {"name": "workflow", "duration_ms": 1500, "status": "success"},
            {"name": "step:analyze", "duration_ms": 500, "status": "success"},
            {"name": "step:implement", "duration_ms": 1000, "status": "success"},
        ]
    }
    output = dashboard.format_trace(trace_data)
    assert "workflow" in output
    assert "1500" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_dashboard.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement Dashboard**

```python
# reqflow/runner/dashboard.py
"""Terminal dashboard for workflow observability."""

from __future__ import annotations

from typing import Any


class Dashboard:
    """Terminal-based workflow status display.

    Uses plain text formatting for maximum compatibility.
    For rich TUI, import and use rich_render() if rich is installed.
    """

    def __init__(self, run_dir: str):
        self.run_dir = run_dir

    def format_status(self, status: dict[str, Any]) -> str:
        """Format engine status as readable text.

        Args:
            status: Engine.get_status() dict.

        Returns:
            Formatted status string.
        """
        lines = [
            f"=== ReqFlow Dashboard ===",
            f"Run:     {status.get('run_id', 'unknown')}",
            f"Config:  {status.get('config', 'unknown')} ({status.get('adapter', 'unknown')})",
            f"Stage:   {status.get('current_stage', 'none')}",
            f"Steps:   {status.get('steps_executed', 0)} executed",
        ]

        completed = status.get("completed_modules", [])
        if completed:
            lines.append(f"Done:    {', '.join(completed)}")

        step_statuses = status.get("step_statuses", {})
        if step_statuses:
            lines.append(f"\n--- Step Status ---")
            for name, st in step_statuses.items():
                marker = "OK" if st == "success" else "FAIL" if st == "failure" else st.upper()
                lines.append(f"  [{marker:6s}] {name}")

        lines.append(f"\nCheckpoints: {status.get('checkpoints', 0)}")
        lines.append(f"Memory:      {status.get('memory_entries', 0)} entries")

        return "\n".join(lines)

    def format_trace(self, trace_data: dict[str, Any]) -> str:
        """Format trace data as readable text.

        Args:
            trace_data: Trace export dict with 'spans' key.

        Returns:
            Formatted trace string.
        """
        spans = trace_data.get("spans", [])
        if not spans:
            return "No trace data."

        lines = ["=== Trace Timeline ==="]
        for span in spans:
            name = span.get("name", "unknown")
            duration = span.get("duration_ms", 0)
            status = span.get("status", "unknown")
            marker = "OK" if status == "success" else "ERR"
            lines.append(f"  [{marker}] {name} ({duration}ms)")

        total = sum(s.get("duration_ms", 0) for s in spans)
        lines.append(f"\nTotal: {total}ms across {len(spans)} spans")

        return "\n".join(lines)

    def rich_render(self, status: dict[str, Any]) -> None:
        """Render status using rich library (if available).

        Falls back to plain text if rich is not installed.
        """
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="ReqFlow Dashboard")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Run ID", str(status.get("run_id", "")))
            table.add_row("Config", f"{status.get('config', '')} ({status.get('adapter', '')})")
            table.add_row("Stage", str(status.get("current_stage", "")))
            table.add_row("Steps", str(status.get("steps_executed", 0)))
            table.add_row("Checkpoints", str(status.get("checkpoints", 0)))

            console.print(table)
        except ImportError:
            print(self.format_status(status))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_dashboard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/runner/dashboard.py reqflow/tests/test_dashboard.py
git commit -m "feat: add Dashboard for terminal workflow observability"
```
