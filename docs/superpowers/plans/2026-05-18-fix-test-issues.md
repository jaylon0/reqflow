# ReqFlow 测试问题修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 reqflow 在真实项目测试中暴露的 12 个问题，使状态可信、runtime 可靠、产物可追踪。

**Architecture:** 分层修复：第一层状态可信度（API adapter raise + engine fail-fast + dashboard + manual EOF）、第二层 Runtime 生命周期（readiness check + 默认策略 + health + host adapter）、第三层产物可观测性（run id 统一 + stage_records + host task CLI）。每个 task 独立可测试。

**Tech Stack:** Python 3.10+, pytest, YAML

---

## File Structure

```
reqflow/
├── core/
│   ├── engine.py              # Modify: fail-fast, stage_records, host adapter registration, run_id
│   ├── registry.py            # Modify: add check_readiness
│   ├── state_manager.py       # Modify: add stage_records to RunState
│   └── adapters/
│       ├── api.py             # Modify: raise on HTTP error
│       ├── manual.py          # Modify: EOF returns blocked
│       └── host.py            # Create: HostAgentAdapter
├── runner/
│   ├── mcp_server.py          # Modify: default runtime, readiness check, reqflow_health
│   ├── cli.py                 # Modify: default runtime
│   ├── dashboard.py           # Modify: per-step status display
│   └── host_task.py           # Create: CLI fallback
├── runtime/providers/
│   ├── host.yaml              # Create
│   └── host-codex.yaml        # Create
└── tests/
    ├── test_fail_fast.py      # Create
    ├── test_runtime_readiness.py  # Create
    ├── test_health.py         # Create
    ├── test_manual_eof.py     # Create
    ├── test_host_adapter.py   # Create
    ├── test_dashboard_real.py # Create
    ├── test_run_id.py         # Create
    ├── test_stage_records.py  # Create
    ├── test_host_task_cli.py  # Create
    └── test_mcp_run_integration.py  # Create
```

---

### Task 1: API Adapter 错误传播

**Files:**
- Modify: `core/adapters/api.py`
- Create: `tests/test_fail_fast.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fail_fast.py
import pytest
from reqflow.core.adapters.api import APIAdapter


def test_api_adapter_raises_on_http_error():
    """API adapter must raise RuntimeError on HTTP errors, not return error response."""
    adapter = APIAdapter(
        api_key="invalid-key",
        base_url="https://httpbin.org",
        model="gpt-4o",
        provider="openai",
    )
    with pytest.raises(RuntimeError, match="API call failed"):
        adapter.call(prompt="test")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_fail_fast.py::test_api_adapter_raises_on_http_error -v`
Expected: FAIL — current code returns ModelResponse instead of raising

- [ ] **Step 3: Fix API adapter**

In `core/adapters/api.py`, replace lines 116-121:

```python
# Before:
        except Exception as e:
            return ModelResponse(
                content=f"API call failed: {e}",
                tokens=TokenUsage(),
                raw={"error": str(e)},
            )

# After:
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}") from e
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_fail_fast.py::test_api_adapter_raises_on_http_error -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/adapters/api.py tests/test_fail_fast.py
git commit -m "fix: API adapter raises on HTTP error instead of returning error response"
```

---

### Task 2: Engine Fail-Fast

**Files:**
- Modify: `core/engine.py`
- Modify: `tests/test_fail_fast.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_fail_fast.py`:

```python
import asyncio
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_engine_stops_on_step_failure():
    """Engine must stop workflow when a step fails, not continue to next steps."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-fail-fast")

    executed_steps = []

    async def mock_run_step(step, context=None):
        executed_steps.append(step["name"])
        if step["name"] == "step1":
            return StepResult(name="step1", status="failure", error="simulated failure")
        return StepResult(name=step["name"], status="success")

    engine.run_step = mock_run_step

    steps = [
        {"name": "step1", "prompt": "first"},
        {"name": "step2", "prompt": "second"},
        {"name": "step3", "prompt": "third"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    assert result["status"] == "failed"
    assert result["failed_at"] == "step1"
    assert "step2" not in executed_steps
    assert "step3" not in executed_steps

    import shutil
    shutil.rmtree("/tmp/test-fail-fast", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_fail_fast.py::test_engine_stops_on_step_failure -v`
Expected: FAIL — engine doesn't have fail-fast logic

- [ ] **Step 3: Implement fail-fast in engine**

In `core/engine.py`, in `run_workflow` method, after the `aborted` check (line ~159), add:

```python
                if step_result.status == "failure":
                    final_result["status"] = "failed"
                    final_result["error"] = step_result.error
                    final_result["failed_at"] = step["name"]
                    break
```

Also change line 166 from:
```python
            final_result["status"] = "completed"
```
to:
```python
            if final_result["status"] not in ("failed", "aborted"):
                final_result["status"] = "completed"
```

- [ ] **Step 4: Run tests to verify**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_fail_fast.py -v`
Expected: PASS (both tests)

- [ ] **Step 5: Run all existing tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add core/engine.py tests/test_fail_fast.py
git commit -m "fix: engine stops on step failure instead of continuing"
```

---

### Task 3: Manual Runtime EOF 修正

**Files:**
- Modify: `core/adapters/manual.py`
- Create: `tests/test_manual_eof.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manual_eof.py
from unittest.mock import patch
from reqflow.core.adapters.manual import ManualAdapter


def test_manual_eof_returns_blocked_content():
    """Manual adapter on EOF should indicate blocked, not empty success."""
    adapter = ManualAdapter()

    with patch("builtins.input", side_effect=EOFError):
        response = adapter.call(prompt="test task")

    assert response.content != ""
    assert "blocked" in response.content.lower() or "eof" in response.content.lower() or "无法" in response.content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_manual_eof.py -v`
Expected: FAIL — current returns empty content on EOF

- [ ] **Step 3: Fix ManualAdapter EOF handling**

In `core/adapters/manual.py`, replace lines 73-75:

```python
# Before:
            except EOFError:
                break

# After:
            except EOFError:
                return ModelResponse(
                    content="[BLOCKED] 非交互模式无法获取人工输入，请使用 host runtime 或显式指定 --runtime。",
                    tool_calls=[],
                    tokens=TokenUsage(),
                    raw={"mode": "manual", "status": "blocked", "reason": "eof"},
                )
```

Also fix `execute_tool` method — find the `except EOFError: break` around line 121 and replace:

```python
# Before:
            except EOFError:
                break

# After:
            except EOFError:
                return ToolResult(
                    success=False,
                    output="",
                    error="[BLOCKED] 非交互模式无法获取人工输入。",
                )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_manual_eof.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/adapters/manual.py tests/test_manual_eof.py
git commit -m "fix: manual adapter returns blocked on EOF instead of empty success"
```

---

### Task 4: Runtime Readiness Check

**Files:**
- Modify: `core/registry.py`
- Create: `tests/test_runtime_readiness.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runtime_readiness.py
import os
from reqflow.core.registry import RuntimeRegistry


def test_runtime_readiness_missing_api_key():
    """Runtime with missing API key should fail readiness check."""
    registry = RuntimeRegistry()
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        ready, reason = registry.check_readiness("gpt")
        assert ready is False
        assert "API key" in reason or "api_key" in reason.lower() or "未配置" in reason
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_runtime_readiness_with_api_key():
    """Runtime with API key set should pass readiness check."""
    registry = RuntimeRegistry()
    old_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    try:
        ready, reason = registry.check_readiness("gpt")
        assert ready is True
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


def test_runtime_readiness_manual_always_ready():
    """Manual runtime should always be ready."""
    registry = RuntimeRegistry()
    ready, reason = registry.check_readiness("manual")
    assert ready is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py -v`
Expected: FAIL — check_readiness doesn't exist

- [ ] **Step 3: Implement check_readiness**

In `core/registry.py`, add to `RuntimeRegistry` class:

```python
    def check_readiness(self, name: str) -> tuple[bool, str]:
        """Check if a runtime is ready to execute."""
        config = self.get(name)

        if config.name in ("manual", "host"):
            return True, ""

        if config.env_key:
            import os
            api_key = config.api_key or os.environ.get(config.env_key, "")
            if not api_key:
                return False, f"未配置 {config.display_name} API key (环境变量 {config.env_key})"

        if config.api_key:
            return True, ""

        if not config.env_key and not config.api_base:
            return True, ""

        return False, f"未配置 {config.display_name} 的 API 凭证"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/registry.py tests/test_runtime_readiness.py
git commit -m "feat: add runtime readiness check"
```

---

### Task 5: Default Runtime Selection

**Files:**
- Modify: `runner/mcp_server.py`
- Modify: `runner/cli.py`
- Modify: `tests/test_runtime_readiness.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_runtime_readiness.py`:

```python
def test_default_runtime_prefers_host_over_api():
    """Default runtime detection should prefer host over external API runtimes."""
    registry = RuntimeRegistry()
    saved_keys = {}
    for provider in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY"):
        saved_keys[provider] = os.environ.pop(provider, None)
    try:
        from reqflow.runner.mcp_server import _detect_runtime
        config = _detect_runtime(registry)
        assert config is not None
        assert config.name not in ("gpt", "gemini", "deepseek"), \
            f"Default runtime should not be external API, got {config.name}"
    finally:
        for k, v in saved_keys.items():
            if v is not None:
                os.environ[k] = v
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py::test_default_runtime_prefers_host_over_api -v`
Expected: FAIL — current detection picks gpt

- [ ] **Step 3: Fix _detect_runtime in mcp_server.py**

Replace the `_detect_runtime` function (lines 745-765) in `runner/mcp_server.py`:

```python
def _detect_runtime(registry) -> object | None:
    """自动检测 runtime。优先级：环境变量 > host > manual > 有 key 的外部 runtime。"""
    import os

    env_runtime = os.environ.get("REQFLOW_RUNTIME", "").lower()
    if env_runtime:
        try:
            return registry.get(env_runtime)
        except ValueError:
            pass

    for name in ("host",):
        try:
            return registry.get(name)
        except ValueError:
            continue

    try:
        return registry.get("manual")
    except ValueError:
        pass

    for name in ("claude", "gpt", "gemini", "deepseek"):
        try:
            config = registry.get(name)
            if config.env_key and os.environ.get(config.env_key):
                return config
            if config.api_key:
                return config
        except ValueError:
            continue

    return None
```

Apply the same fix to `runner/cli.py` `_detect_runtime` function (lines 480-503).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add runner/mcp_server.py runner/cli.py tests/test_runtime_readiness.py
git commit -m "fix: default runtime prefers host over external API"
```

---

### Task 6: Health Check 增强

**Files:**
- Modify: `runner/mcp_server.py`
- Create: `tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_health.py
import os
import asyncio
from reqflow.runner.mcp_server import _handle_health


def test_health_returns_system_and_runtime_info():
    """Health check should return system health AND runtime readiness."""
    result = asyncio.run(_handle_health({}))
    text = result[0].text
    assert "system" in text.lower() or "系统" in text
    assert "runtime" in text.lower()


def test_health_reports_unavailable_runtime():
    """Health check should report which runtimes are NOT ready."""
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        result = asyncio.run(_handle_health({}))
        text = result[0].text
        assert "gpt" in text.lower()
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_health.py -v`
Expected: FAIL — _handle_health doesn't exist

- [ ] **Step 3: Implement reqflow_health**

In `runner/mcp_server.py`, add the tool definition to TOOLS list:

```python
    {
        "name": "reqflow_health",
        "description": "检查 ReqFlow 系统健康状态和 runtime 可用性。",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
```

Add the handler function before TOOL_HANDLERS:

```python
async def _handle_health(_arguments: dict) -> list:
    """处理 reqflow_health 工具调用。"""
    _, RuntimeRegistry = _import_core()

    lines = ["=== ReqFlow Health Check ==="]

    lines.append("\n[System]")
    lines.append(f"  reqflow: OK")
    try:
        import mcp
        lines.append(f"  mcp: OK")
    except ImportError:
        lines.append(f"  mcp: NOT INSTALLED (pip install mcp)")

    lines.append("\n[Runtimes]")
    try:
        registry = RuntimeRegistry()
        for name in registry.list_runtimes():
            ready, reason = registry.check_readiness(name)
            status = "READY" if ready else "NOT READY"
            line = f"  {name:12s}: {status}"
            if reason:
                line += f" — {reason}"
            lines.append(line)
    except Exception as exc:
        lines.append(f"  ERROR: {exc}")

    lines.append("\n[Recommended]")
    try:
        registry = RuntimeRegistry()
        for name in registry.list_runtimes():
            ready, _ = registry.check_readiness(name)
            if ready and name not in ("manual",):
                lines.append(f"  {name}")
                break
        else:
            lines.append(f"  manual (no external runtime available)")
    except Exception:
        lines.append(f"  manual")

    return [TextContent(type="text", text="\n".join(lines))]
```

Add to TOOL_HANDLERS: `"reqflow_health": _handle_health`

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runner/mcp_server.py tests/test_health.py
git commit -m "feat: enhanced health check with runtime readiness"
```

---

### Task 7: Host Runtime YAML + Adapter

**Files:**
- Create: `runtime/providers/host.yaml`
- Create: `runtime/providers/host-codex.yaml`
- Create: `core/adapters/host.py`
- Modify: `core/engine.py`
- Create: `tests/test_host_adapter.py`

- [ ] **Step 1: Create host.yaml**

```yaml
name: host
display_name: "Host Agent Runtime"

capabilities:
  supports_agent_tools: true
  supports_bash: true
  supports_file_edit: true
  supports_image: false
  max_context_tokens: 200000

tool_mapping:
  read_file: "read_file"
  edit_file: "edit_file"
  bash: "bash"
  agent: "agent"

context_format:
  system_prompt_template: "templates/system-prompt-host.md"
  skill_format: "markdown"
  artifact_format: "markdown"

paths:
  run_dir: ".reqflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 2: Create host-codex.yaml**

```yaml
name: host-codex
display_name: "Codex Host Agent"

capabilities:
  supports_agent_tools: true
  supports_bash: true
  supports_file_edit: true
  supports_image: false
  max_context_tokens: 200000

tool_mapping:
  read_file: "read_file"
  edit_file: "edit_file"
  bash: "bash"
  agent: "agent"

context_format:
  system_prompt_template: "templates/system-prompt-host.md"
  skill_format: "markdown"
  artifact_format: "markdown"

paths:
  run_dir: ".reqflow/runs/"
  state_file: "state.json"
  log_file: "execution.log"
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_host_adapter.py
import json
import os
import shutil
from pathlib import Path
from reqflow.core.adapters.host import HostAgentAdapter


def test_host_adapter_creates_task_packet():
    """Host adapter should create a task packet file."""
    run_dir = "/tmp/test-host-adapter"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir)
        packet = adapter.create_task_packet(
            stage_id="test-stage",
            stage_name="Test Stage",
            prompt="Do something",
            required_tools=["bash", "read_file"],
            expected_artifacts=["output.md"],
        )
        assert packet["stage_id"] == "test-stage"
        assert packet["required_tools"] == ["bash", "read_file"]
        assert (Path(run_dir) / "task.json").exists()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_returns_blocked_without_result():
    """Host adapter should return blocked when no result packet exists."""
    run_dir = "/tmp/test-host-no-result"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir)
        response = adapter.call(prompt="test")
        assert "blocked" in response.content.lower() or "task" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_consumes_result_packet():
    """Host adapter should consume result packet and return success."""
    run_dir = "/tmp/test-host-result"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir)
        result_packet = {
            "status": "success",
            "summary": "Task completed",
            "artifacts": ["output.md"],
            "files_changed": ["src/main.py"],
        }
        (Path(run_dir) / "result.json").write_text(json.dumps(result_packet))
        response = adapter.call(prompt="test")
        assert "success" in response.content.lower() or "completed" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_adapter.py -v`
Expected: FAIL — host adapter doesn't exist

- [ ] **Step 5: Implement HostAgentAdapter**

Create `core/adapters/host.py`:

```python
"""HostAgentAdapter - adapter for host agent runtime with task/result packet protocol."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, TokenUsage


class HostAgentAdapter(ModelAdapter):
    """Adapter that communicates via TaskPacket/ResultPacket file protocol."""

    def __init__(self, run_dir: str | None = None):
        self._run_dir = run_dir or ".reqflow/runs/default"
        self._step_count = 0

    @property
    def name(self) -> str:
        return "host"

    def create_task_packet(
        self,
        stage_id: str,
        stage_name: str,
        prompt: str,
        required_tools: list[str] | None = None,
        expected_artifacts: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create and write a task packet for the host agent."""
        packet = {
            "stage_id": stage_id,
            "stage_name": stage_name,
            "prompt": prompt,
            "required_tools": required_tools or [],
            "expected_artifacts": expected_artifacts or [],
            "acceptance_criteria": acceptance_criteria or [],
        }
        task_file = Path(self._run_dir) / "task.json"
        task_file.write_text(json.dumps(packet, indent=2, ensure_ascii=False))
        packet["task_file"] = str(task_file)
        return packet

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        self._step_count += 1

        result_file = Path(self._run_dir) / "result.json"
        if result_file.exists():
            try:
                result_data = json.loads(result_file.read_text())
                status = result_data.get("status", "unknown")
                summary = result_data.get("summary", "")
                artifacts = result_data.get("artifacts", [])
                files_changed = result_data.get("files_changed", [])
                result_file.unlink()

                content_parts = [f"[HOST RESULT] Status: {status}"]
                if summary:
                    content_parts.append(f"Summary: {summary}")
                if artifacts:
                    content_parts.append(f"Artifacts: {', '.join(artifacts)}")
                if files_changed:
                    content_parts.append(f"Files changed: {', '.join(files_changed)}")

                return ModelResponse(
                    content="\n".join(content_parts),
                    tool_calls=[],
                    tokens=TokenUsage(),
                    raw=result_data,
                )
            except (json.JSONDecodeError, OSError):
                pass

        task_packet = self.create_task_packet(
            stage_id=f"step-{self._step_count}",
            stage_name=f"Step {self._step_count}",
            prompt=prompt,
            required_tools=tools or [],
        )

        return ModelResponse(
            content=f"[BLOCKED] 等待 host agent 执行任务。Task packet: {task_packet.get('task_file', 'task.json')}",
            tool_calls=[],
            tokens=TokenUsage(),
            raw={"status": "blocked", "task_packet": task_packet},
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            success=False, output="",
            error="Host adapter delegates tool execution to host agent.",
        )

    def supports_capability(self, capability: str) -> bool:
        return True
```

In `core/engine.py`, in `select_adapter` method, add after the `manual` branch:

```python
        elif name in ("host", "host-codex", "host-claude-code", "host-cursor", "host-copilot"):
            from .adapters.host import HostAgentAdapter
            self._adapter = HostAgentAdapter(run_dir=self.run_dir)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_adapter.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add runtime/providers/host.yaml runtime/providers/host-codex.yaml core/adapters/host.py core/engine.py tests/test_host_adapter.py
git commit -m "feat: add host runtime adapter with task/result packet protocol"
```

---

### Task 8: Dashboard 真实状态

**Files:**
- Modify: `runner/dashboard.py`
- Create: `tests/test_dashboard_real.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dashboard_real.py
import json
import os
import shutil
from pathlib import Path
from reqflow.runner.dashboard import Dashboard


def test_dashboard_shows_failed_status():
    """Dashboard should show failed stages, not just completed count."""
    run_dir = "/tmp/test-dashboard-real"
    os.makedirs(run_dir, exist_ok=True)
    try:
        state = {
            "run_id": "test-run",
            "current_stage": "stage2",
            "completed_modules": ["stage1"],
            "checkpoints": [],
            "memory": {"short_term": []},
        }
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        dashboard = Dashboard(run_dir=run_dir)
        status = {
            "run_id": "test-run",
            "config": "gpt",
            "adapter": "api_gpt",
            "current_stage": "stage2",
            "completed_modules": ["stage1"],
            "steps_executed": 2,
            "step_statuses": {"stage1": "success", "stage2": "failed"},
            "checkpoints": 0,
            "memory_entries": 0,
        }
        output = dashboard.format_status(status)
        assert "fail" in output.lower() or "FAIL" in output or "[FAIL]" in output
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_dashboard_real.py -v`
Expected: FAIL — dashboard doesn't show per-step status

- [ ] **Step 3: Fix dashboard**

In `runner/dashboard.py`, in `format_status` method, after the existing output, append:

```python
        step_statuses = status.get("step_statuses", {})
        if step_statuses:
            lines.append("\n--- Step Status ---")
            for name, st in step_statuses.items():
                icon = {"success": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]", "aborted": "[STOP]"}.get(st, "[?]")
                lines.append(f"  {icon:7s} {name}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_dashboard_real.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runner/dashboard.py tests/test_dashboard_real.py
git commit -m "fix: dashboard shows per-step real status including failures"
```

---

### Task 9: Run ID 统一

**Files:**
- Modify: `core/engine.py`
- Create: `tests/test_run_id.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run_id.py
import shutil
from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig


def test_run_id_matches_dir_name():
    """run_id should match the directory name."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-run-id-consistency")
    assert engine.run_id == "test-run-id-consistency"
    shutil.rmtree("/tmp/test-run-id-consistency", ignore_errors=True)


def test_run_id_auto_generated_is_readable():
    """Auto-generated run_id should be human-readable, not UUID."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config)
    assert "run-" in engine.run_id
    assert len(engine.run_id) < 30  # Not a UUID
    shutil.rmtree(engine.run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_run_id.py -v`
Expected: FAIL — auto-generated run_id uses UUID

- [ ] **Step 3: Fix run_id generation**

In `core/engine.py`, replace lines 43-46:

```python
# Before:
        self.run_dir = run_dir or os.path.join(
            config.paths.run_dir, f"run-{uuid.uuid4().hex[:8]}"
        )
        self.run_id = Path(self.run_dir).name

# After:
        if run_dir:
            self.run_dir = run_dir
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.run_dir = os.path.join(config.paths.run_dir, f"run-{timestamp}")
        self.run_id = Path(self.run_dir).name
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_run_id.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/engine.py tests/test_run_id.py
git commit -m "fix: unify run_id to use directory name instead of UUID"
```

---

### Task 10: Stage Records

**Files:**
- Modify: `core/state_manager.py`
- Modify: `core/engine.py`
- Create: `tests/test_stage_records.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage_records.py
import asyncio
import json
import shutil
from pathlib import Path
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_state_records_stage_details():
    """state.json should contain stage_records with per-stage status."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-records")

    async def mock_run_step(step, context=None):
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step
    steps = [{"name": "step1", "prompt": "first"}, {"name": "step2", "prompt": "second"}]

    asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    state = json.loads((Path("/tmp/test-stage-records") / "state.json").read_text())
    assert "stage_records" in state
    assert len(state["stage_records"]) == 2
    assert state["stage_records"][0]["name"] == "step1"
    assert state["stage_records"][0]["status"] == "success"

    shutil.rmtree("/tmp/test-stage-records", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_stage_records.py -v`
Expected: FAIL — stage_records not in RunState

- [ ] **Step 3: Add stage_records to RunState**

In `core/state_manager.py`, add to `RunState` dataclass:

```python
    stage_records: list[dict[str, Any]] = field(default_factory=list)
```

- [ ] **Step 4: Record stage details in engine**

In `core/engine.py`, in `run_workflow`, after `completed_steps.append(...)` (around line 154), add:

```python
                self.state_manager.state.stage_records.append({
                    "name": step["name"],
                    "status": step_result.status,
                    "duration_ms": step_result.duration_ms,
                    "error": step_result.error,
                })
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_stage_records.py -v`
Expected: PASS

- [ ] **Step 6: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add core/state_manager.py core/engine.py tests/test_stage_records.py
git commit -m "feat: record per-stage details in state.json stage_records"
```

---

### Task 11: MCP reqflow_run 集成

**Files:**
- Modify: `runner/mcp_server.py`
- Create: `tests/test_mcp_run_integration.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mcp_run_integration.py
import os
import asyncio
from reqflow.runner.mcp_server import _handle_run


def test_mcp_run_fails_fast_on_missing_api_key():
    """MCP reqflow_run should fail fast when API key is missing."""
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        result = asyncio.run(_handle_run({"requirement": "test", "runtime": "gpt"}))
        text = result[0].text
        assert "错误" in text or "error" in text.lower() or "未配置" in text
        assert "401" not in text
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_mcp_run_default_uses_host():
    """MCP reqflow_run without runtime should prefer host."""
    result = asyncio.run(_handle_run({"requirement": "test"}))
    text = result[0].text
    assert "gpt" not in text.lower() or "host" in text.lower() or "manual" in text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_mcp_run_integration.py -v`
Expected: FAIL

- [ ] **Step 3: Fix _handle_run**

In `runner/mcp_server.py`, in `_handle_run`, after `config = registry.get(runtime_name)` (line ~318), add readiness check:

```python
        ready, reason = registry.check_readiness(runtime_name)
        if not ready:
            return [TextContent(type="text", text=f"[错误] Runtime '{runtime_name}' 不可用: {reason}")]
```

Also update the output section to show step status icons and failed_at:

```python
    for step in result.get("steps", []):
        icon = {"success": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]", "aborted": "[STOP]"}.get(step.get("status", ""), "[?]")
        lines.append(f"  {icon} {step.get('name', '?')}: {step.get('status', '?')}")

    if result.get("failed_at"):
        lines.append(f"失败阶段: {result['failed_at']}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_mcp_run_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runner/mcp_server.py tests/test_mcp_run_integration.py
git commit -m "fix: MCP reqflow_run does readiness check and fail-fast"
```

---

### Task 12: Host Task CLI Fallback

**Files:**
- Create: `runner/host_task.py`
- Create: `tests/test_host_task_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_host_task_cli.py
import json
import os
import shutil
from pathlib import Path
from reqflow.runner.host_task import get_next_task, submit_result, get_status


def test_get_next_task_returns_packet():
    run_dir = "/tmp/test-host-task-cli"
    os.makedirs(run_dir, exist_ok=True)
    try:
        task = {"stage_id": "s1", "prompt": "do something"}
        (Path(run_dir) / "task.json").write_text(json.dumps(task))
        result = get_next_task(run_dir)
        assert result is not None
        assert result["stage_id"] == "s1"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_next_task_returns_none_when_no_task():
    run_dir = "/tmp/test-host-task-no-task"
    os.makedirs(run_dir, exist_ok=True)
    try:
        result = get_next_task(run_dir)
        assert result is None
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_submit_result_writes_result_json():
    run_dir = "/tmp/test-host-task-submit"
    os.makedirs(run_dir, exist_ok=True)
    try:
        result_data = {"status": "success", "summary": "done"}
        result_file = Path(run_dir) / "input-result.json"
        result_file.write_text(json.dumps(result_data))
        output = submit_result(run_dir, str(result_file))
        assert output["status"] == "ok"
        written = json.loads((Path(run_dir) / "result.json").read_text())
        assert written["status"] == "success"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_status_reads_state():
    run_dir = "/tmp/test-host-task-status"
    os.makedirs(run_dir, exist_ok=True)
    try:
        state = {"run_id": "test", "current_stage": "s1", "completed_modules": []}
        (Path(run_dir) / "state.json").write_text(json.dumps(state))
        status = get_status(run_dir)
        assert status["run_id"] == "test"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_task_cli.py -v`
Expected: FAIL — host_task.py doesn't exist

- [ ] **Step 3: Implement host_task.py**

Create `runner/host_task.py`:

```python
"""CLI fallback for host agent interaction via file protocol."""

from __future__ import annotations

import json
from pathlib import Path


def get_next_task(run_dir: str) -> dict | None:
    """Get the next task packet from the run directory."""
    task_file = Path(run_dir) / "task.json"
    if not task_file.exists():
        return None
    try:
        return json.loads(task_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def submit_result(run_dir: str, result_path: str) -> dict:
    """Submit a result packet to the run directory."""
    result_file = Path(result_path)
    if not result_file.exists():
        return {"status": "error", "error": f"Result file not found: {result_path}"}
    try:
        data = json.loads(result_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"status": "error", "error": f"Cannot read result file: {e}"}

    dest = Path(run_dir) / "result.json"
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return {"status": "ok", "written_to": str(dest)}


def get_status(run_dir: str) -> dict:
    """Get the current run status."""
    state_file = Path(run_dir) / "state.json"
    if not state_file.exists():
        return {"error": f"State file not found: {state_file}"}
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"Cannot read state file: {e}"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_task_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runner/host_task.py tests/test_host_task_cli.py
git commit -m "feat: add host task CLI fallback for file-protocol interaction"
```

---

## Self-Review Checklist

| Spec Requirement | Task |
|---|---|
| 1. gpt runtime 假成功 | Task 1 (API adapter raise) |
| 2. Dashboard 状态误导 | Task 8 (dashboard real status) |
| 3. 缺少 runtime 鉴权前置检查 | Task 4 (readiness check) |
| 4. skill 默认不应走第三方 API | Task 5 (default runtime) |
| 5. host-codex 超时 | Task 7 (host adapter) |
| 6. 超时后缺恢复信息 | Task 7 (host adapter blocked message) |
| 7. run id 不一致 | Task 9 (run id unify) |
| 8. 没有阶段文档 | Task 10 (stage_records) |
| 9. Agent Execution 没真实执行 | Task 7 (host adapter) |
| 10. 阶段失败没阻断 | Task 2 (fail-fast) |
| 11. 交付状态不可信 | Task 2 + Task 8 |
| 12. health 语义混淆 | Task 6 (health enhancement) |
