import json
from reqflow.core.context_adapter import ContextAdapter
from reqflow.core.runtime_config import RuntimeConfig

def test_format_context_markdown():
    config = RuntimeConfig(name="claude", display_name="Claude")
    adapter = ContextAdapter(config)
    context = {"project": "test", "requirement": "add auth"}
    output = adapter.format_context(context)
    assert "test" in output
    assert "add auth" in output

def test_format_context_json(gpt_config):
    adapter = ContextAdapter(gpt_config)
    context = {"project": "test", "requirement": "add auth"}
    output = adapter.format_context(context)
    parsed = json.loads(output)
    assert parsed["project"] == "test"

def test_truncate_to_fit():
    config = RuntimeConfig(name="claude", display_name="Claude")
    adapter = ContextAdapter(config)
    long_text = "x" * 100000
    truncated = adapter.truncate_to_fit(long_text, reserved_tokens=1000)
    assert len(truncated) <= len(long_text)
