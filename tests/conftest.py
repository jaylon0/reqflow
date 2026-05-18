# tests/conftest.py
import pytest
import shutil
from pathlib import Path
from reqflow.core.runtime_config import RuntimeConfig, Capabilities, ContextFormat

@pytest.fixture
def manual_config():
    return RuntimeConfig(name="manual", display_name="Manual")

@pytest.fixture
def claude_config():
    return RuntimeConfig(
        name="claude",
        display_name="Claude Code",
        capabilities=Capabilities(
            supports_agent_tools=True,
            supports_bash=True,
            supports_file_edit=True,
            max_context_tokens=200000,
        ),
    )

@pytest.fixture
def gpt_config():
    return RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
        context_format=ContextFormat(artifact_format="json"),
    )

@pytest.fixture
def tmp_run_dir(tmp_path):
    run_dir = str(tmp_path / "test-run")
    yield run_dir
    shutil.rmtree(run_dir, ignore_errors=True)
