# ReqFlow V2 Phase 1: Core Engine Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ReqFlow a truly executable engine that can call LLMs via API, has proper test coverage, and supports parallel agent dispatch.

**Architecture:** Extend existing `core/adapters/api.py` with RuntimeConfig integration and async support. Restructure tests into per-module pytest files. Add `asyncio.gather` for parallel verify+review in engine.py.

**Tech Stack:** Python 3.10+, urllib3, pytest, asyncio

---

## File Structure

```
reqflow/
├── core/
│   ├── adapters/
│   │   ├── api.py              # MODIFY: RuntimeConfig integration, async, env var support
│   │   └── base.py             # READ ONLY: ModelAdapter protocol
│   ├── runtime_config.py       # MODIFY: add api_key, api_base, model, env_key fields
│   ├── registry.py             # MODIFY: load api_key/api_base/model from YAML
│   └── engine.py               # MODIFY: parallel agent dispatch, API adapter wiring
├── runtime/
│   └── providers/
│       ├── gpt.yaml            # MODIFY: add api_base, model, env_key
│       ├── gemini.yaml         # MODIFY: add api_base, model, env_key
│       └── deepseek.yaml       # MODIFY: add api_base, model, env_key
└── tests/
    ├── conftest.py             # CREATE: shared fixtures
    ├── test_engine.py          # CREATE: engine tests
    ├── test_workflow_loader.py # CREATE: workflow loader tests
    ├── test_state_manager.py   # CREATE: state manager tests
    ├── test_tracer.py          # CREATE: tracer tests
    ├── test_guardrails.py      # CREATE: guardrails tests
    ├── test_tool_bridge.py     # CREATE: tool bridge tests
    ├── test_context_adapter.py # CREATE: context adapter tests
    ├── test_api_adapter.py     # CREATE: API adapter tests (mock HTTP)
    └── integration/
        └── test_fin_ktms.py    # MOVE: existing integration test
```

---

### Task 1: Extend RuntimeConfig with API fields

**Files:**
- Modify: `reqflow/core/runtime_config.py`
- Test: `tests/test_runtime_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runtime_config.py
from reqflow.core.runtime_config import RuntimeConfig

def test_runtime_config_has_api_fields():
    config = RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
        env_key="OPENAI_API_KEY",
    )
    assert config.api_key == "sk-test"
    assert config.api_base == "https://api.openai.com/v1"
    assert config.model == "gpt-4o"
    assert config.env_key == "OPENAI_API_KEY"

def test_runtime_config_defaults():
    config = RuntimeConfig(name="manual", display_name="Manual")
    assert config.api_key == ""
    assert config.api_base == ""
    assert config.model == ""
    assert config.env_key == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_runtime_config.py -v`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'api_key'`

- [ ] **Step 3: Add API fields to RuntimeConfig**

```python
# reqflow/core/runtime_config.py — add to RuntimeConfig dataclass
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
    env_key: str = ""  # env var name to read API key from
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_runtime_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/runtime_config.py reqflow/tests/test_runtime_config.py
git commit -m "feat: add API fields to RuntimeConfig"
```

---

### Task 2: Update provider YAML with API config

**Files:**
- Modify: `reqflow/runtime/providers/gpt.yaml`
- Modify: `reqflow/runtime/providers/gemini.yaml`
- Modify: `reqflow/runtime/providers/deepseek.yaml`
- Test: `tests/test_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_registry.py
from reqflow.core.registry import RuntimeRegistry

def test_registry_loads_api_config():
    registry = RuntimeRegistry()
    config = registry.get("gpt")
    assert config.api_base == "https://api.openai.com/v1"
    assert config.model == "gpt-4o"
    assert config.env_key == "OPENAI_API_KEY"

def test_registry_loads_deepseek_config():
    registry = RuntimeRegistry()
    config = registry.get("deepseek")
    assert config.api_base == "https://api.deepseek.com/v1"
    assert config.model == "deepseek-chat"
    assert config.env_key == "DEEPSEEK_API_KEY"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_registry.py -v`
Expected: FAIL (api_base/model/env_key are empty strings)

- [ ] **Step 3: Update provider YAML files**

```yaml
# reqflow/runtime/providers/gpt.yaml
name: gpt
display_name: "GPT-4o"
api_base: "https://api.openai.com/v1"
model: "gpt-4o"
env_key: "OPENAI_API_KEY"
capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  max_context_tokens: 128000
```

```yaml
# reqflow/runtime/providers/gemini.yaml
name: gemini
display_name: "Gemini Pro"
api_base: "https://generativelanguage.googleapis.com/v1beta"
model: "gemini-2.0-flash"
env_key: "GEMINI_API_KEY"
capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  max_context_tokens: 1000000
```

```yaml
# reqflow/runtime/providers/deepseek.yaml
name: deepseek
display_name: "DeepSeek"
api_base: "https://api.deepseek.com/v1"
model: "deepseek-chat"
env_key: "DEEPSEEK_API_KEY"
capabilities:
  supports_agent_tools: false
  supports_bash: false
  supports_file_edit: false
  max_context_tokens: 64000
```

- [ ] **Step 4: Update registry.py to load new YAML fields**

In `reqflow/core/registry.py`, find where `RuntimeConfig` is constructed from YAML data and add:

```python
config = RuntimeConfig(
    name=data["name"],
    display_name=data.get("display_name", data["name"]),
    api_key=os.environ.get(data.get("env_key", ""), ""),
    api_base=data.get("api_base", ""),
    model=data.get("model", ""),
    env_key=data.get("env_key", ""),
    ...
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_registry.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add reqflow/runtime/providers/gpt.yaml reqflow/runtime/providers/gemini.yaml reqflow/runtime/providers/deepseek.yaml reqflow/core/registry.py reqflow/tests/test_registry.py
git commit -m "feat: add API config to provider YAML and registry"
```

---

### Task 3: Fix APIAdapter with RuntimeConfig integration

**Files:**
- Modify: `reqflow/core/adapters/api.py`
- Test: `tests/test_api_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api_adapter.py
import json
from unittest.mock import patch, MagicMock
from reqflow.core.adapters.api import APIAdapter
from reqflow.core.runtime_config import RuntimeConfig

def test_api_adapter_from_config():
    config = RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    adapter = APIAdapter.from_config(config)
    assert adapter.api_key == "sk-test"
    assert adapter.base_url == "https://api.openai.com/v1"
    assert adapter.model == "gpt-4o"
    assert adapter.name == "api_gpt"

def test_api_adapter_reads_env_key():
    config = RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        env_key="OPENAI_API_KEY",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env-test"}):
        adapter = APIAdapter.from_config(config)
        assert adapter.api_key == "sk-env-test"

def test_api_adapter_call_returns_model_response():
    config = RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    adapter = APIAdapter.from_config(config)

    mock_response = {
        "choices": [{"message": {"content": "Hello!", "tool_calls": []}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = adapter.call(prompt="Say hello", tools=None, context=None)
        assert result.content == "Hello!"
        assert result.tokens.input_tokens == 10
        assert result.tokens.output_tokens == 5

def test_api_adapter_supports_capability():
    config = RuntimeConfig(name="gpt", display_name="GPT-4o", api_key="sk-test")
    adapter = APIAdapter.from_config(config)
    assert adapter.supports_capability("bash") is True
    assert adapter.supports_capability("agent_tools") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_api_adapter.py -v`
Expected: FAIL with `AttributeError: type object 'APIAdapter' has no attribute 'from_config'`

- [ ] **Step 3: Add from_config classmethod and fix APIAdapter**

Add to `reqflow/core/adapters/api.py`:

```python
@classmethod
def from_config(cls, config: RuntimeConfig) -> "APIAdapter":
    """Create APIAdapter from RuntimeConfig."""
    api_key = config.api_key
    if not api_key and config.env_key:
        api_key = os.environ.get(config.env_key, "")
    return cls(
        api_key=api_key,
        base_url=config.api_base or cls._default_base_url(None, config.name),
        model=config.model or "gpt-4o",
        provider=config.name,
    )
```

Update `__init__` to accept `RuntimeConfig` via `from_config`, and update `select_adapter` in engine.py to use it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_api_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/adapters/api.py reqflow/tests/test_api_adapter.py
git commit -m "feat: APIAdapter.from_config with RuntimeConfig integration"
```

---

### Task 4: Update Engine.select_adapter to use RuntimeConfig

**Files:**
- Modify: `reqflow/core/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py
from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.adapters.api import APIAdapter
from reqflow.core.adapters.manual import ManualAdapter

def test_engine_selects_api_adapter_for_gpt():
    config = RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    engine = Engine(config=config, run_dir="/tmp/test-engine-select")
    adapter = engine.select_adapter()
    assert isinstance(adapter, APIAdapter)
    assert adapter.model == "gpt-4o"

def test_engine_selects_manual_adapter_fallback():
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-engine-manual")
    adapter = engine.select_adapter()
    assert isinstance(adapter, ManualAdapter)

import shutil
shutil.rmtree("/tmp/test-engine-select", ignore_errors=True)
shutil.rmtree("/tmp/test-engine-manual", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_engine.py::test_engine_selects_api_adapter_for_gpt -v`
Expected: FAIL (APIAdapter created without config params)

- [ ] **Step 3: Update select_adapter in engine.py**

Replace the `select_adapter` method:

```python
def select_adapter(self) -> ModelAdapter:
    """Select adapter based on RuntimeConfig. Falls back to ManualAdapter."""
    if self._adapter is not None:
        return self._adapter

    name = self.config.name.lower()

    if name == "claude":
        self._adapter = ClaudeCodeAdapter()
    elif name in ("gpt", "gemini", "deepseek"):
        self._adapter = APIAdapter.from_config(self.config)
    elif name == "manual":
        self._adapter = ManualAdapter()
    else:
        self._adapter = ManualAdapter()

    return self._adapter
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/engine.py reqflow/tests/test_engine.py
git commit -m "feat: Engine.select_adapter uses RuntimeConfig for API adapter"
```

---

### Task 5: Add parallel agent dispatch to Engine

**Files:**
- Modify: `reqflow/core/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py — add this test
import asyncio
from unittest.mock import AsyncMock, patch

async def test_engine_parallel_dispatch():
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-engine-parallel")

    # Mock two agents that each take some time
    async def mock_agent_1(prompt, **kwargs):
        await asyncio.sleep(0.1)
        return {"status": "pass", "result": "verify ok"}

    async def mock_agent_2(prompt, **kwargs):
        await asyncio.sleep(0.1)
        return {"status": "pass", "result": "review ok"}

    results = await engine.dispatch_parallel([
        {"name": "verify", "handler": mock_agent_1, "prompt": "verify code"},
        {"name": "review", "handler": mock_agent_2, "prompt": "review code"},
    ])

    assert len(results) == 2
    assert results[0]["status"] == "pass"
    assert results[1]["status"] == "pass"

    import shutil
    shutil.rmtree("/tmp/test-engine-parallel", ignore_errors=True)

# To run: pytest tests/test_engine.py::test_engine_parallel_dispatch -v
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_engine.py::test_engine_parallel_dispatch -v`
Expected: FAIL with `AttributeError: 'Engine' object has no attribute 'dispatch_parallel'`

- [ ] **Step 3: Add dispatch_parallel method to Engine**

Add to `reqflow/core/engine.py`:

```python
async def dispatch_parallel(
    self, agents: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Dispatch multiple agents in parallel using asyncio.gather.

    Each agent dict must have:
        name: str
        handler: async callable(prompt, **kwargs) -> dict
        prompt: str
        kwargs: optional extra args

    Returns list of results in the same order as input.
    """
    max_concurrent = getattr(self, "_max_concurrent_agents", 3)
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _run_one(agent: dict[str, Any]) -> dict[str, Any]:
        async with semaphore:
            handler = agent["handler"]
            prompt = agent["prompt"]
            kwargs = agent.get("kwargs", {})
            return await handler(prompt, **kwargs)

    return await asyncio.gather(*[_run_one(a) for a in agents])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/test_engine.py::test_engine_parallel_dispatch -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add reqflow/core/engine.py reqflow/tests/test_engine.py
git commit -m "feat: add Engine.dispatch_parallel for concurrent agent execution"
```

---

### Task 6: Restructure existing tests into pytest modules

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_state_manager.py`
- Create: `tests/test_tracer.py`
- Create: `tests/test_guardrails.py`
- Create: `tests/test_tool_bridge.py`
- Create: `tests/test_context_adapter.py`
- Create: `tests/test_workflow_loader.py`
- Move: `tests/test_tdd_fin_ktms.py` → `tests/integration/test_fin_ktms.py`

- [ ] **Step 1: Create conftest.py with shared fixtures**

```python
# tests/conftest.py
import pytest
import shutil
from pathlib import Path
from reqflow.core.runtime_config import RuntimeConfig, Capabilities

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
    )

@pytest.fixture
def tmp_run_dir(tmp_path):
    run_dir = str(tmp_path / "test-run")
    yield run_dir
    shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Create test_state_manager.py**

Extract StateManager tests from `test_tdd_fin_ktms.py::test_state_manager_checkpoint` into standalone pytest:

```python
# tests/test_state_manager.py
from reqflow.core.state_manager import StateManager

def test_state_initial(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    assert sm.state.run_id
    assert sm.state.current_stage == ""

def test_update_stage(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    sm.update_stage("analyze")
    assert sm.state.current_stage == "analyze"

def test_complete_module(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    sm.complete_module("mod_a")
    sm.complete_module("mod_b")
    assert "mod_a" in sm.state.completed_modules
    assert "mod_b" in sm.state.completed_modules

def test_checkpoint_create_restore(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    cp = sm.create_checkpoint("test_stage", context={"key": "value"})
    assert cp.checkpoint_id
    assert cp.stage == "test_stage"
    restored_state, restored_ctx = sm.restore_checkpoint(cp.checkpoint_id)
    assert restored_ctx["key"] == "value"

def test_persistence(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    sm.update_stage("persist_test")
    sm.complete_module("mod_x")
    sm.save_state()
    sm2 = StateManager(tmp_run_dir)
    assert sm2.state.current_stage == "persist_test"
    assert "mod_x" in sm2.state.completed_modules
```

- [ ] **Step 3: Create test_tracer.py**

```python
# tests/test_tracer.py
import json
from pathlib import Path
from reqflow.core.tracer import Tracer

def test_span_lifecycle(tmp_path):
    tracer = Tracer("test-run", output_dir=str(tmp_path / "traces"))
    root = tracer.start_span("root", input_data={"test": True})
    child = tracer.start_span("child", parent_id=root.span_id)
    tracer.end_span(child.span_id, output="done", status="success")
    tracer.end_span(root.span_id, output="complete", status="success")
    summary = tracer.get_summary()
    assert summary["total_spans"] == 2
    assert summary["failed_spans"] == 0

def test_export(tmp_path):
    tracer = Tracer("test-run", output_dir=str(tmp_path / "traces"))
    span = tracer.start_span("export_test")
    tracer.end_span(span.span_id, output="ok", status="success")
    trace_file = tracer.export()
    assert Path(trace_file).exists()
    data = json.loads(Path(trace_file).read_text())
    assert len(data["spans"]) == 1
```

- [ ] **Step 4: Create test_guardrails.py**

```python
# tests/test_guardrails.py
import asyncio
from reqflow.core.guardrails import Guardrails, Constraint, Severity, check_file_boundary

async def test_guardrails_no_constraints():
    g = Guardrails()
    violations = await g.check({"file_path": "/any/file.java"})
    assert violations == []

async def test_guardrails_file_boundary_allowed():
    g = Guardrails()
    g.add_constraint(Constraint(
        name="file_boundary",
        description="scope check",
        severity=Severity.FATAL,
        check_fn=check_file_boundary,
    ))
    violations = await g.check({
        "file_path": "/project/common/src/Main.java",
        "authorized_scope": ["/project/common/*"],
    })
    fatal = [v for v in violations if v.severity == Severity.FATAL]
    assert len(fatal) == 0

async def test_guardrails_file_boundary_denied():
    g = Guardrails()
    g.add_constraint(Constraint(
        name="file_boundary",
        description="scope check",
        severity=Severity.ERROR,
        check_fn=check_file_boundary,
    ))
    violations = await g.check({
        "file_path": "/project/web/src/Controller.java",
        "authorized_scope": ["/project/common/*"],
    })
    errors = [v for v in violations if v.severity in (Severity.ERROR, Severity.FATAL)]
    assert len(errors) > 0

def test_is_fatal():
    g = Guardrails()
    assert g.is_fatal([]) is False
```

- [ ] **Step 5: Create test_tool_bridge.py**

```python
# tests/test_tool_bridge.py
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
```

- [ ] **Step 6: Create test_context_adapter.py**

```python
# tests/test_context_adapter.py
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

def test_format_context_json():
    config = RuntimeConfig(name="gpt", display_name="GPT")
    adapter = ContextAdapter(config)
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
```

- [ ] **Step 7: Create test_workflow_loader.py**

```python
# tests/test_workflow_loader.py
from reqflow.core.workflow_loader import WorkflowLoader

def test_load_flow():
    loader = WorkflowLoader()
    stages = loader.get_stages("flow")
    assert len(stages) == 3
    assert stages[0]["name"] == "分析"
    assert stages[1]["name"] == "实现"
    assert stages[2]["name"] == "验证"

def test_load_main_flow():
    loader = WorkflowLoader()
    stages = loader.get_stages("main-flow")
    assert len(stages) == 11

def test_list_workflows():
    loader = WorkflowLoader()
    workflows = loader.list_workflows()
    assert "flow" in workflows
    assert "main-flow" in workflows

def test_load_nonexistent():
    loader = WorkflowLoader()
    try:
        loader.get_stages("nonexistent")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass

def test_get_loop_config():
    loader = WorkflowLoader()
    loop = loader.get_loop_config("main-flow")
    assert loop is not None
    assert "state_machine" in loop
```

- [ ] **Step 8: Move integration test**

```bash
mkdir -p reqflow/tests/integration
mv reqflow/tests/test_tdd_fin_ktms.py reqflow/tests/integration/test_fin_ktms.py
```

- [ ] **Step 9: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/ -v --ignore=reqflow/tests/integration`
Expected: All unit tests PASS

- [ ] **Step 10: Commit**

```bash
git add reqflow/tests/
git commit -m "test: restructure tests into per-module pytest files"
```

---

### Task 7: Verify end-to-end with full test suite

**Files:**
- None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m pytest reqflow/tests/ -v`
Expected: All tests PASS (unit + integration)

- [ ] **Step 2: Verify CLI still works**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -m reqflow.runner list-runtimes`
Expected: Lists all 5 runtimes with API config

- [ ] **Step 3: Verify API adapter wiring**

Run: `cd /Users/yuanjulong/Documents/ai_flow && python3 -c "
from reqflow.core import Engine, RuntimeRegistry
registry = RuntimeRegistry()
config = registry.get('gpt')
print(f'api_base: {config.api_base}')
print(f'model: {config.model}')
print(f'env_key: {config.env_key}')
engine = Engine(config=config, run_dir='/tmp/test-api-wire')
adapter = engine.select_adapter()
print(f'adapter: {adapter.name}')
import shutil; shutil.rmtree('/tmp/test-api-wire', ignore_errors=True)
"`
Expected: api_base, model, env_key populated; adapter name = "api_gpt"

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: Phase 1 complete - core engine with API, tests, parallel dispatch"
```
