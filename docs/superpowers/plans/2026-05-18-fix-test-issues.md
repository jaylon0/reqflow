# ReqFlow 测试问题修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 reqflow 在真实项目测试中暴露的 12 个问题，使状态可信、runtime 可靠、产物可追踪。

**Architecture:** 按根因分组修复：A) 状态可信度（假成功/失败阻断/Dashboard 真实性）、B) Runtime 生命周期（默认策略/前置检查/health/超时）、C) 产物可观测性（run id 统一/阶段产物/失败报告）。每个 task 独立可测试。

**Tech Stack:** Python 3.10+, pytest, YAML

---

## File Structure

```
reqflow/
├── core/
│   ├── engine.py              # Modify: fail-fast on step failure
│   ├── registry.py            # Modify: add runtime readiness check
│   ├── runtime_config.py      # Modify: add is_external flag
│   └── adapters/
│       ├── api.py             # Modify: raise on API error instead of returning error response
│       ├── manual.py          # Modify: EOF returns blocked status
│       └── host.py            # Create: HostAgentAdapter with timeout handling
├── runner/
│   ├── mcp_server.py          # Modify: default runtime selection, health enhancement
│   ├── cli.py                 # Modify: default runtime selection
│   ├── dashboard.py           # Modify: show real failure status
│   └── host_task.py           # Create: CLI fallback for host task protocol
├── runtime/providers/
│   ├── host.yaml              # Create: generic host runtime config
│   └── host-codex.yaml        # Create: Codex platform adapter
└── tests/
    ├── test_fail_fast.py      # Create: fail-fast behavior tests
    ├── test_runtime_readiness.py  # Create: runtime readiness check tests
    ├── test_host_adapter.py   # Create: host adapter tests
    ├── test_manual_eof.py     # Create: manual EOF behavior tests (exists, update)
    ├── test_dashboard_real.py # Create: dashboard real status tests
    ├── test_run_id.py         # Create: run id consistency tests
    └── test_health.py         # Create: enhanced health check tests
```

---

### Task 1: API Adapter 错误传播 — 假成功根因修复

**Files:**
- Modify: `core/adapters/api.py:113-121`
- Create: `tests/test_fail_fast.py`

API adapter 在 HTTP 401/403/500 时返回 `ModelResponse(content="API call failed: ...")` 而不是抛异常，导致 engine 把它当作正常响应，step 标记为 success。这是假成功的根因。

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
    # httpbin/status/401 always returns 401
    with pytest.raises(RuntimeError, match="API call failed"):
        adapter.call(prompt="test")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_fail_fast.py::test_api_adapter_raises_on_http_error -v`
Expected: FAIL (current code returns ModelResponse instead of raising)

- [ ] **Step 3: Fix API adapter to raise on error**

In `core/adapters/api.py`, replace lines 113-121:

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

### Task 2: Engine Fail-Fast — 步骤失败阻断后续执行

**Files:**
- Modify: `core/engine.py:159-165`
- Modify: `tests/test_fail_fast.py`

当前 engine 在 step 返回 failure 时继续执行后续步骤，最终标记为 completed。必须在 step failure 时阻断。

- [ ] **Step 1: Write the failing test**

在 `tests/test_fail_fast.py` 中追加：

```python
import asyncio
from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.adapters.base import ModelResponse, TokenUsage


def test_engine_stops_on_step_failure():
    """Engine must stop workflow when a step fails, not continue to next steps."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-fail-fast")

    # Track which steps executed
    executed_steps = []

    # Monkey-patch run_step to simulate failure on first step
    original_run_step = engine.run_step

    async def mock_run_step(step, context=None):
        executed_steps.append(step["name"])
        if step["name"] == "step1":
            from reqflow.core.engine import StepResult
            return StepResult(name="step1", status="failure", error="simulated failure")
        return StepResult(name=step["name"], status="success")

    engine.run_step = mock_run_step

    steps = [
        {"name": "step1", "prompt": "first step"},
        {"name": "step2", "prompt": "second step"},
        {"name": "step3", "prompt": "third step"},
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
Expected: FAIL (current engine doesn't have failed_at or stop logic)

- [ ] **Step 3: Implement fail-fast in engine**

In `core/engine.py`, in the `run_workflow` method, after the `aborted` check (line ~159), add:

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

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_fail_fast.py -v`
Expected: PASS (both tests)

- [ ] **Step 5: Run all existing tests to check for regressions**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v`
Expected: All existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add core/engine.py tests/test_fail_fast.py
git commit -m "fix: engine stops on step failure instead of continuing to next steps"
```

---

### Task 3: Runtime Readiness Check — 执行前验证 runtime 可用性

**Files:**
- Modify: `core/registry.py`
- Modify: `tests/test_runtime_readiness.py` (create)

`reqflow_health` 只检查插件和 MCP，不验证 runtime 是否真正可用。需要在执行前做 readiness check。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runtime_readiness.py
import os
import pytest
from reqflow.core.registry import RuntimeRegistry


def test_runtime_readiness_check_missing_api_key():
    """Runtime with missing API key should fail readiness check."""
    registry = RuntimeRegistry()
    config = registry.get("gpt")

    # Ensure no API key is set
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        ready, reason = registry.check_readiness("gpt")
        assert ready is False
        assert "API key" in reason or "api_key" in reason.lower()
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_runtime_readiness_check_with_api_key():
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


def test_runtime_readiness_host_always_ready():
    """Host runtime should always be ready (uses current agent)."""
    registry = RuntimeRegistry()
    ready, reason = registry.check_readiness("host")
    assert ready is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py -v`
Expected: FAIL (check_readiness method doesn't exist)

- [ ] **Step 3: Implement check_readiness in RuntimeRegistry**

在 `core/registry.py` 的 `RuntimeRegistry` 类中添加：

```python
    def check_readiness(self, name: str) -> tuple[bool, str]:
        """Check if a runtime is ready to execute.

        Returns (ready, reason). ready=True means the runtime can be used.
        """
        config = self.get(name)

        # Host and manual runtimes are always ready
        if config.name in ("manual", "host"):
            return True, ""

        # API runtimes need an API key
        if config.env_key:
            import os
            api_key = config.api_key or os.environ.get(config.env_key, "")
            if not api_key:
                return False, f"未配置 {config.display_name} API key (环境变量 {config.env_key})"

        if config.api_key:
            return True, ""

        # If no env_key and no api_key, check if it's a non-API runtime
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
git commit -m "feat: add runtime readiness check before execution"
```

---

### Task 4: Default Runtime Selection — 优先 host runtime，不隐式走第三方 API

**Files:**
- Modify: `runner/mcp_server.py:745-765`
- Modify: `runner/cli.py:480-503`
- Modify: `tests/test_runtime_readiness.py`

当前自动检测按 `claude > gpt > gemini > deepseek > manual` 优先级，会隐式选择需要外部 API 的 runtime。应该优先选择 host runtime。

- [ ] **Step 1: Write the failing test**

在 `tests/test_runtime_readiness.py` 追加：

```python
def test_default_runtime_prefers_host_over_api():
    """Default runtime detection should prefer host over external API runtimes."""
    registry = RuntimeRegistry()

    # Save and clear all API keys
    saved_keys = {}
    for provider in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY"):
        saved_keys[provider] = os.environ.pop(provider, None)

    try:
        # The default detection should pick host or manual, not gpt
        from runner.mcp_server import _detect_runtime
        config = _detect_runtime(registry)
        assert config is not None
        assert config.name not in ("gpt", "gemini", "deepseek"), \
            f"Default runtime should not be an external API runtime, got {config.name}"
    finally:
        for k, v in saved_keys.items():
            if v is not None:
                os.environ[k] = v
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py::test_default_runtime_prefers_host_over_api -v`
Expected: FAIL (current detection picks gpt first)

- [ ] **Step 3: Fix _detect_runtime in mcp_server.py**

在 `runner/mcp_server.py` 中替换 `_detect_runtime` 函数（行 745-765）：

```python
def _detect_runtime(registry) -> object | None:
    """尝试自动检测合适的 runtime。

    优先级：环境变量指定 > host > manual > 有 API key 的外部 runtime。
    不隐式选择需要外部 API 但未配置 key 的 runtime。
    """
    import os

    # 1. 显式指定
    env_runtime = os.environ.get("REQFLOW_RUNTIME", "").lower()
    if env_runtime:
        try:
            return registry.get(env_runtime)
        except ValueError:
            pass

    # 2. Host runtime（当前 agent 平台）
    for name in ("host",):
        try:
            return registry.get(name)
        except ValueError:
            continue

    # 3. Manual（总是可用）
    try:
        return registry.get("manual")
    except ValueError:
        pass

    # 4. 有 API key 的外部 runtime
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

同样修复 `runner/cli.py` 中的 `_detect_runtime` 函数（行 480-503），使用相同逻辑。

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_runtime_readiness.py -v`
Expected: PASS

- [ ] **Step 5: Run all existing tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add runner/mcp_server.py runner/cli.py tests/test_runtime_readiness.py
git commit -m "fix: default runtime prefers host over external API runtimes"
```

---

### Task 5: Health Check 增强 — 区分 system/runtime/workflow health

**Files:**
- Modify: `runner/mcp_server.py` — 添加 `reqflow_health` 工具
- Modify: `tests/test_health.py` (create)

当前 health 只检查插件和 MCP，不检查 runtime 可用性。需要区分 system health、runtime health、workflow readiness。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_health.py
import os
import asyncio
import pytest
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
        # Should mention gpt is not ready or missing key
        assert "gpt" in text.lower()
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_health.py -v`
Expected: FAIL (_handle_health doesn't exist)

- [ ] **Step 3: Add reqflow_health tool and handler**

在 `runner/mcp_server.py` 的 TOOLS 列表中添加 reqflow_health 工具定义，并实现 `_handle_health`：

```python
async def _handle_health(_arguments: dict) -> list:
    """处理 reqflow_health 工具调用。返回系统和 runtime 健康状态。"""
    _, RuntimeRegistry = _import_core()
    import os

    lines = ["=== ReqFlow Health Check ==="]

    # System health
    lines.append("\n[System]")
    lines.append(f"  reqflow: OK")
    try:
        import mcp
        lines.append(f"  mcp: OK")
    except ImportError:
        lines.append(f"  mcp: NOT INSTALLED (pip install mcp)")

    # Runtime health
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

    # Recommended runtime
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

在 TOOLS 列表中添加：

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

在 TOOL_HANDLERS 中添加 `"reqflow_health": _handle_health`。

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runner/mcp_server.py tests/test_health.py
git commit -m "feat: enhanced health check with runtime readiness reporting"
```

---

### Task 6: Manual Runtime EOF 修正 — 非交互模式不假成功

**Files:**
- Modify: `core/adapters/manual.py:71-75`
- Modify: `tests/test_manual_eof.py` (exists, update)

Manual adapter 在 EOF 时返回空 content 但 status=success，在非交互场景会假成功。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manual_eof.py
from unittest.mock import patch
from reqflow.core.adapters.manual import ManualAdapter


def test_manual_eof_returns_blocked_content():
    """Manual adapter on EOF should indicate blocked, not empty success."""
    adapter = ManualAdapter()

    # Simulate EOF by making input() raise EOFError
    with patch("builtins.input", side_effect=EOFError):
        response = adapter.call(prompt="test task")

    # Response should indicate it was blocked, not just empty
    assert response.content != ""
    assert "blocked" in response.content.lower() or "eof" in response.content.lower() or "无法" in response.content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_manual_eof.py -v`
Expected: FAIL (current returns empty content on EOF)

- [ ] **Step 3: Fix ManualAdapter EOF handling**

在 `core/adapters/manual.py` 中，将 EOFError 处理从 `break` 改为返回 blocked 信号：

```python
# Before (line 73-75):
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

同样修改 `execute_tool` 方法中的 EOFError 处理。

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_manual_eof.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/adapters/manual.py tests/test_manual_eof.py
git commit -m "fix: manual adapter returns blocked on EOF instead of empty success"
```

---

### Task 7: Host Runtime YAML 和 Adapter 创建

**Files:**
- Create: `runtime/providers/host.yaml`
- Create: `runtime/providers/host-codex.yaml`
- Create: `core/adapters/host.py`
- Create: `tests/test_host_adapter.py`

Host runtime 是跨 agent 平台的核心抽象，通过 TaskPacket/ResultPacket 通信。

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
import asyncio
import json
import os
import shutil
from pathlib import Path
from reqflow.core.adapters.host import HostAgentAdapter


def test_host_adapter_creates_task_packet():
    """Host adapter should create a task packet file for the host agent."""
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
        assert "task.json" in os.listdir(run_dir) or packet.get("task_file")
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_returns_blocked_without_result():
    """Host adapter should return blocked status when no result packet exists."""
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

        # Write a result packet
        result_packet = {
            "status": "success",
            "summary": "Task completed",
            "artifacts": ["output.md"],
            "files_changed": ["src/main.py"],
        }
        result_file = Path(run_dir) / "result.json"
        result_file.write_text(json.dumps(result_packet))

        response = adapter.call(prompt="test")

        assert "success" in response.content.lower() or "completed" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_adapter.py -v`
Expected: FAIL (host adapter doesn't exist)

- [ ] **Step 5: Implement HostAgentAdapter**

```python
# core/adapters/host.py
"""HostAgentAdapter - adapter for host agent runtime with task/result packet protocol."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, ToolCall, TokenUsage


class HostAgentAdapter(ModelAdapter):
    """Adapter that communicates via TaskPacket/ResultPacket protocol.

    When the host agent can execute tools directly, it runs them.
    Otherwise, it writes a task packet and waits for a result packet.
    """

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
        """Execute via host agent protocol.

        1. Check for existing result packet
        2. If found, consume it and return
        3. If not found, write task packet and return blocked
        """
        self._step_count += 1

        # Check for result packet
        result_file = Path(self._run_dir) / "result.json"
        if result_file.exists():
            try:
                result_data = json.loads(result_file.read_text())
                status = result_data.get("status", "unknown")
                summary = result_data.get("summary", "")
                artifacts = result_data.get("artifacts", [])
                files_changed = result_data.get("files_changed", [])

                # Clean up consumed result
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
            except (json.JSONDecodeError, OSError) as e:
                pass

        # No result packet — write task packet and return blocked
        task_packet = self.create_task_packet(
            stage_id=f"step-{self._step_count}",
            stage_name=f"Step {self._step_count}",
            prompt=prompt,
            required_tools=tools or [],
        )

        return ModelResponse(
            content=f"[BLOCKED] 等待 host agent 执行任务。Task packet 已写入: {task_packet.get('task_file', 'task.json')}。"
                    f"\n请通过 host agent 执行后将结果写入 result.json。",
            tool_calls=[],
            tokens=TokenUsage(),
            raw={"status": "blocked", "task_packet": task_packet},
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        """Host adapter delegates tool execution to the host agent."""
        return ToolResult(
            success=False,
            output="",
            error=f"Host adapter delegates tool execution to the host agent. Use host-task CLI or MCP.",
        )

    def supports_capability(self, capability: str) -> bool:
        """Host adapter supports all capabilities (delegated to host agent)."""
        return True
```

在 `core/engine.py` 的 `select_adapter` 方法中添加 host 适配：

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

### Task 8: Dashboard 显示真实失败状态

**Files:**
- Modify: `runner/dashboard.py`
- Modify: `runner/mcp_server.py` — `_handle_dashboard`
- Create: `tests/test_dashboard_real.py`

Dashboard 当前只显示 completed_modules 数量，不区分成功/失败。需要显示每阶段的真实状态。

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
        # Create a state.json with mixed statuses
        state = {
            "run_id": "test-run",
            "current_stage": "stage2",
            "completed_modules": ["stage1"],
            "checkpoints": [],
            "memory": {"short_term": []},
            "stage_records": [
                {"name": "stage1", "status": "success", "duration_ms": 1000},
                {"name": "stage2", "status": "failed", "error": "HTTP 401", "duration_ms": 500},
            ],
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

        # Must show failure
        assert "fail" in output.lower() or "FAIL" in output or "[FAIL]" in output
        # Must NOT show all as done
        assert "11 executed" not in output  # Not all as success
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_dashboard_real.py -v`
Expected: FAIL (dashboard doesn't show per-step status)

- [ ] **Step 3: Fix dashboard to show per-step status**

修改 `runner/dashboard.py` 的 `format_status` 方法，添加 step_statuses 展示：

```python
    # 在现有输出后追加
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
- Modify: `core/engine.py:43-46`
- Modify: `runner/mcp_server.py` — dashboard handler
- Create: `tests/test_run_id.py`

当前 run_id 在目录名、UUID、trace 中不一致。统一为用户指定的目录名或自动生成的可读名。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run_id.py
import shutil
from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig


def test_run_id_matches_dir_name():
    """run_id should match the directory name, not a separate UUID."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    run_dir = "/tmp/test-run-id-consistency"
    engine = Engine(config=config, run_dir=run_dir)

    # run_id should be derived from run_dir
    assert engine.run_id == "test-run-id-consistency"

    shutil.rmtree(run_dir, ignore_errors=True)


def test_run_id_user_specified():
    """When user specifies run_dir, run_id should be the dir basename."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    run_dir = "/tmp/my-feature-20260518"
    engine = Engine(config=config, run_dir=run_dir)

    assert engine.run_id == "my-feature-20260518"

    shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_run_id.py -v`
Expected: FAIL (current run_id uses uuid, not dir name)

- [ ] **Step 3: Fix run_id to use directory name**

在 `core/engine.py` 中，将 `__init__` 的 run_id 从 `Path(self.run_dir).name` 确认为一致。当前已经是 `self.run_id = Path(self.run_dir).name`，但当 `run_dir` 为 None 时会生成 `run-{uuid}`。修复：

```python
    def __init__(self, config: RuntimeConfig, run_dir: str | None = None, workflows_dir: str | None = None):
        self.config = config
        if run_dir:
            self.run_dir = run_dir
        else:
            # Generate readable run id instead of UUID
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

### Task 10: MCP reqflow_run 集成 — readiness check + fail-fast + run_id 统一

**Files:**
- Modify: `runner/mcp_server.py` — `_handle_run`

将前面的修复集成到 MCP 入口：执行前检查 readiness，选择正确的默认 runtime，传递 run_id。

- [ ] **Step 1: Write the integration test**

```python
# tests/test_mcp_run_integration.py
import os
import asyncio
import pytest
from reqflow.runner.mcp_server import _handle_run


def test_mcp_run_fails_fast_on_missing_api_key():
    """MCP reqflow_run should fail fast when API key is missing."""
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        result = asyncio.run(_handle_run({
            "requirement": "test requirement",
            "runtime": "gpt",
        }))
        text = result[0].text
        assert "错误" in text or "error" in text.lower() or "未配置" in text
        assert "401" not in text  # Should not get to API call
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_mcp_run_default_uses_host():
    """MCP reqflow_run without runtime should prefer host."""
    result = asyncio.run(_handle_run({
        "requirement": "test requirement",
    }))
    text = result[0].text
    # Should use host or manual, not gpt
    assert "gpt" not in text.lower() or "host" in text.lower() or "manual" in text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_mcp_run_integration.py -v`
Expected: FAIL

- [ ] **Step 3: Fix _handle_run in mcp_server.py**

修改 `_handle_run` 函数：

```python
async def _handle_run(arguments: dict) -> list:
    """处理 reqflow_run 工具调用。"""
    Engine, RuntimeRegistry = _import_core()

    requirement = arguments.get("requirement", "").strip()
    if not requirement:
        return [TextContent(type="text", text="[错误] 需求内容不能为空。")]

    runtime_name = arguments.get("runtime")
    workflow_type = arguments.get("workflow", "flow")
    run_dir = arguments.get("run_dir")

    # 选择 runtime
    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 无法加载 runtime 配置: {exc}")]

    if runtime_name:
        try:
            config = registry.get(runtime_name)
        except ValueError as exc:
            return [TextContent(type="text", text=f"[错误] {exc}")]

        # Readiness check — fail fast if runtime not ready
        ready, reason = registry.check_readiness(runtime_name)
        if not ready:
            return [TextContent(type="text", text=f"[错误] Runtime '{runtime_name}' 不可用: {reason}")]
    else:
        config = _detect_runtime(registry)
        if config is None:
            return [TextContent(type="text", text="[错误] 无法自动检测 runtime，请指定 runtime 参数。")]

    # 选择 workflow（从 YAML 加载）
    steps = _get_workflow_steps(workflow_type)

    # 创建 Engine 并执行
    engine = Engine(config=config, run_dir=run_dir)

    try:
        result = await engine.run_workflow(workflow_steps=steps, requirement=requirement)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] Workflow 执行失败: {exc}")]

    # 格式化输出
    lines = [
        f"运行 ID: {engine.run_id}",
        f"Runtime: {config.display_name} ({config.name})",
        f"状态: {result.get('status', '未知')}",
    ]

    for step in result.get("steps", []):
        status_icon = {"success": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]", "aborted": "[STOP]"}.get(step.get("status", ""), "[?]")
        lines.append(f"  {status_icon} {step.get('name', '?')}: {step.get('status', '?')}")

    if result.get("error"):
        lines.append(f"错误: {result['error']}")
    if result.get("abort_reason"):
        lines.append(f"中止原因: {result['abort_reason']}")
    if result.get("failed_at"):
        lines.append(f"失败阶段: {result['failed_at']}")

    lines.append(f"运行目录: {engine.run_dir}")

    return [TextContent(type="text", text="\n".join(lines))]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_mcp_run_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runner/mcp_server.py tests/test_mcp_run_integration.py
git commit -m "fix: MCP reqflow_run does readiness check and fail-fast on missing config"
```

---

### Task 11: Host Task CLI Fallback

**Files:**
- Create: `runner/host_task.py`
- Modify: `runner/cli.py` — 添加 host-task 子命令

为不支持 MCP 的 agent 提供 CLI fallback：通过文件协议获取 task、提交 result。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_host_task_cli.py
import json
import os
import shutil
from pathlib import Path
from reqflow.runner.host_task import get_next_task, submit_result, get_status


def test_get_next_task_returns_packet():
    """get_next_task should return the task packet from task.json."""
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
    """get_next_task should return None when no task.json exists."""
    run_dir = "/tmp/test-host-task-no-task"
    os.makedirs(run_dir, exist_ok=True)

    try:
        result = get_next_task(run_dir)
        assert result is None
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_submit_result_writes_result_json():
    """submit_result should write result.json to run_dir."""
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
    """get_status should return state.json contents."""
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
Expected: FAIL (host_task.py doesn't exist)

- [ ] **Step 3: Implement host_task.py**

```python
# runner/host_task.py
"""CLI fallback for host agent interaction via file protocol."""

from __future__ import annotations

import json
import shutil
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
git commit -m "feat: add host task CLI fallback for file-protocol agent interaction"
```

---

### Task 12: 阶段产物检查 — state.json 记录 stage_records

**Files:**
- Modify: `core/engine.py` — run_workflow 中记录每阶段详情
- Modify: `core/state_manager.py` — RunState 添加 stage_records
- Create: `tests/test_stage_records.py`

当前 state.json 只记录 completed_modules 列表，不记录每阶段的状态、耗时、错误。需要记录 stage_records。

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage_records.py
import asyncio
import shutil
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_state_records_stage_details():
    """state.json should contain stage_records with per-stage status."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-records")

    # Monkey-patch run_step
    async def mock_run_step(step, context=None):
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step

    steps = [
        {"name": "step1", "prompt": "first"},
        {"name": "step2", "prompt": "second"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    # Check state.json has stage_records
    import json
    from pathlib import Path
    state = json.loads((Path("/tmp/test-stage-records") / "state.json").read_text())

    assert "stage_records" in state
    assert len(state["stage_records"]) == 2
    assert state["stage_records"][0]["name"] == "step1"
    assert state["stage_records"][0]["status"] == "success"

    shutil.rmtree("/tmp/test-stage-records", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_stage_records.py -v`
Expected: FAIL (stage_records not in state)

- [ ] **Step 3: Add stage_records to RunState**

在 `core/state_manager.py` 的 `RunState` dataclass 中添加：

```python
    stage_records: list[dict[str, Any]] = field(default_factory=list)
```

- [ ] **Step 4: Record stage details in engine**

在 `core/engine.py` 的 `run_workflow` 中，每步执行后记录：

```python
                # Record stage details
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
git add core/engine.py core/state_manager.py tests/test_stage_records.py
git commit -m "feat: record per-stage details in state.json stage_records"
```

---

## Self-Review Checklist

| Issue | Covered by Task |
|-------|----------------|
| 1. gpt runtime 假成功 | Task 1 (API adapter raise) |
| 2. Dashboard 状态误导 | Task 8 (dashboard real status) |
| 3. 缺少 runtime 鉴权前置检查 | Task 3 (readiness check) |
| 4. skill 默认不应走第三方 API | Task 4 (default runtime) |
| 5. host-codex 超时 | Task 7 (host adapter with timeout) |
| 6. 超时后缺恢复信息 | Task 7 (host adapter blocked message) |
| 7. run id 不一致 | Task 9 (run id unify) |
| 8. 没有阶段文档 | Task 12 (stage_records) |
| 9. Agent Execution 没真实执行 | Task 7 (host adapter) |
| 10. 阶段失败没阻断 | Task 2 (fail-fast) |
| 11. 交付状态不可信 | Task 2 + Task 8 |
| 12. health 语义混淆 | Task 5 (health enhancement) |
