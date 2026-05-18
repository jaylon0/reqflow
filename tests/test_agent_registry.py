import os
import shutil
from pathlib import Path

from reqflow.core.agent_registry import AgentRegistry


def test_agent_registry_loads_from_workflow():
    """AgentRegistry should load agent_templates from workflow definition."""
    registry = AgentRegistry()
    workflow = {
        "agent_templates": {
            "dev-agent": {
                "description": "Development agent",
                "model": "sonnet",
                "tools": ["Read", "Write", "Bash"],
                "permissionMode": "acceptEdits",
                "prompt": "You are a developer agent.",
            },
            "review-agent": {
                "description": "Code review agent",
                "model": "sonnet",
                "tools": ["Read", "Grep", "Glob"],
                "permissionMode": "plan",
                "prompt": "You are a code reviewer.",
            },
        }
    }
    registry.load_from_workflow(workflow)
    assert "dev-agent" in registry.list_agents()
    assert "review-agent" in registry.list_agents()
    assert len(registry.list_agents()) == 2


def test_agent_registry_generates_files():
    """AgentRegistry should generate .claude/agents/*.md files."""
    output_dir = "/tmp/test-agent-registry-gen"
    os.makedirs(output_dir, exist_ok=True)
    try:
        registry = AgentRegistry()
        registry.register("test-agent", {
            "description": "Test agent",
            "model": "sonnet",
            "tools": ["Read", "Grep"],
            "prompt": "You are a test agent.",
        })
        generated = registry.generate_files(output_dir)
        assert len(generated) == 1
        assert "test-agent.md" in generated[0]

        content = Path(generated[0]).read_text()
        assert "---" in content
        assert "name: test-agent" in content
        assert "description: Test agent" in content
        assert "model: sonnet" in content
        assert "You are a test agent." in content
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_agent_registry_generates_multiple_files():
    """AgentRegistry should generate multiple agent files."""
    output_dir = "/tmp/test-agent-registry-multi"
    os.makedirs(output_dir, exist_ok=True)
    try:
        registry = AgentRegistry()
        registry.register("agent-a", {
            "description": "Agent A",
            "prompt": "Agent A prompt.",
        })
        registry.register("agent-b", {
            "description": "Agent B",
            "prompt": "Agent B prompt.",
        })
        generated = registry.generate_files(output_dir)
        assert len(generated) == 2

        names = [Path(f).name for f in generated]
        assert "agent-a.md" in names
        assert "agent-b.md" in names
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_agent_registry_frontmatter_fields():
    """AgentRegistry should render all supported frontmatter fields."""
    registry = AgentRegistry()
    registry.register("full-agent", {
        "description": "Full agent with all fields",
        "model": "opus",
        "tools": ["Read", "Write", "Bash"],
        "disallowedTools": ["WebFetch"],
        "permissionMode": "auto",
        "maxTurns": 10,
        "memory": "project",
        "background": True,
        "effort": "high",
        "isolation": "worktree",
        "color": "blue",
        "prompt": "Full agent body.",
    })

    output_dir = "/tmp/test-agent-registry-fields"
    os.makedirs(output_dir, exist_ok=True)
    try:
        generated = registry.generate_files(output_dir)
        content = Path(generated[0]).read_text()

        assert "name: full-agent" in content
        assert "model: opus" in content
        assert "permissionMode: auto" in content
        assert "maxTurns: 10" in content
        assert "memory: project" in content
        assert "background: true" in content
        assert "effort: high" in content
        assert "isolation: worktree" in content
        assert "color: blue" in content
        assert "Full agent body." in content
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
