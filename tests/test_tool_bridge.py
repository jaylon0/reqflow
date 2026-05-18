from reqflow.core.tool_bridge import ToolBridge
from reqflow.core.runtime_config import RuntimeConfig, ToolMapping

def test_tool_bridge_map_names():
    config = RuntimeConfig(name="claude", display_name="Claude")
    bridge = ToolBridge(config)
    assert bridge.map_tool_name("read_file") == "Read"
    assert bridge.map_tool_name("bash") == "Bash"
    assert bridge.map_tool_name("edit_file") == "Edit"

def test_tool_bridge_available_tools():
    config = RuntimeConfig(name="claude", display_name="Claude")
    bridge = ToolBridge(config)
    available = bridge.get_available_tools()
    assert "read_file" in available
    assert "bash" in available

def test_tool_bridge_format_prompt():
    config = RuntimeConfig(name="claude", display_name="Claude")
    bridge = ToolBridge(config)
    prompt = bridge.format_tools_for_prompt()
    assert "Read" in prompt
    assert "Bash" in prompt
