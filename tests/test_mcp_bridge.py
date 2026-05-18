import asyncio
from reqflow.core.mcp_bridge import MCPBridge, MCPServerConfig, MCPTool

def test_mcp_server_config():
    config = MCPServerConfig(
        name="database",
        command="mcp-server-postgres",
        args=["--connection-string", "postgresql://localhost/test"],
    )
    assert config.name == "database"
    assert config.command == "mcp-server-postgres"

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
    configs = [MCPServerConfig(name="db", command="mcp-server-db", args=[])]
    bridge = MCPBridge(configs)
    assert len(bridge.servers) == 1

def test_mcp_bridge_discover_tools_mock():
    configs = [MCPServerConfig(name="db", command="mcp-server-db", args=[])]
    bridge = MCPBridge(configs)

    async def mock_connect(server_name):
        return [
            MCPTool(name="query", server=server_name, description="Run query", parameters={}),
            MCPTool(name="list_tables", server=server_name, description="List tables", parameters={}),
        ]

    bridge._connect = mock_connect
    tools = asyncio.run(bridge.discover_tools())
    assert len(tools) == 2
    assert tools[0].name == "query"

def test_mcp_bridge_call_tool_mock():
    configs = [MCPServerConfig(name="db", command="mcp-server-db", args=[])]
    bridge = MCPBridge(configs)

    async def mock_call(server, tool, args):
        return {"result": "ok", "rows": 5}

    bridge._call_remote = mock_call
    result = asyncio.run(bridge.call_tool("db", "query", {"sql": "SELECT 1"}))
    assert result["result"] == "ok"

def test_mcp_bridge_get_tools_for_prompt():
    configs = [MCPServerConfig(name="db", command="mcp-server-db", args=[])]
    bridge = MCPBridge(configs)
    bridge._discovered_tools = [
        MCPTool(name="query", server="db", description="Run SQL", parameters={}),
    ]
    prompt = bridge.get_tools_for_prompt()
    assert "query" in prompt
    assert "db" in prompt

def test_mcp_bridge_runtime_config():
    from reqflow.core.runtime_config import RuntimeConfig, MCPServerConfig as RTMCP
    config = RuntimeConfig(
        name="test", display_name="Test",
        mcp_servers=[RTMCP(name="db", command="mcp-db", args=[])],
    )
    assert len(config.mcp_servers) == 1
