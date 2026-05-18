# ReqFlow 剩余问题修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 reqflow 在真实项目测试中暴露的剩余 3 个问题：超时恢复、阶段产物、执行痕迹。

**Architecture:** 在现有框架上增量修复：HostAgentAdapter 增加超时检测和 resume 协议，stage_records 扩展为包含阶段内容的产物记录，agent_execution_log 增加真实执行证据字段。每个 task 独立可测试。

**Tech Stack:** Python 3.10+, pytest

---

## File Structure

```
reqflow/
├── core/
│   ├── engine.py              # Modify: stage artifacts in stage_records, richer execution log
│   ├── state_manager.py       # Modify: add stage_artifacts field to RunState
│   └── adapters/
│       └── host.py            # Modify: timeout detection, resume protocol
├── runner/
│   ├── mcp_server.py          # Modify: timeout/recovery info in status output
│   ├── dashboard.py           # Modify: show stage artifacts and recovery info
│   └── host_task.py           # Modify: add resume support
└── tests/
    ├── test_host_timeout.py   # Create: timeout and resume tests
    ├── test_stage_artifacts.py # Create: stage artifact recording tests
    └── test_execution_traces.py # Create: execution trace detail tests
```

---

### Task 1: Host Adapter 超时检测与 Resume 协议

**Files:**
- Modify: `core/adapters/host.py`
- Create: `tests/test_host_timeout.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_host_timeout.py
import json
import os
import shutil
import time
from pathlib import Path
from reqflow.core.adapters.host import HostAgentAdapter


def test_host_adapter_detects_timeout():
    """Host adapter should detect when task.json has been waiting too long."""
    run_dir = "/tmp/test-host-timeout"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir, timeout_seconds=1)
        # First call creates task.json
        adapter.call(prompt="test task")
        # Wait past timeout
        time.sleep(1.5)
        # Second call should detect timeout
        response = adapter.call(prompt="test task")
        assert "timeout" in response.content.lower() or "超时" in response.content
        assert response.raw.get("status") == "timeout"
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_resume_after_timeout():
    """Host adapter should allow resume after timeout by accepting new result."""
    run_dir = "/tmp/test-host-resume"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir, timeout_seconds=1)
        # Create task and wait for timeout
        adapter.call(prompt="test task")
        time.sleep(1.5)
        adapter.call(prompt="test task")  # triggers timeout

        # Now submit a result (resume)
        result_data = {"status": "success", "summary": "recovered"}
        (Path(run_dir) / "result.json").write_text(json.dumps(result_data))

        # Next call should consume the result
        response = adapter.call(prompt="test task")
        assert "success" in response.content.lower() or "recovered" in response.content.lower()
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_host_adapter_creates_recovery_info_on_timeout():
    """On timeout, host adapter should write recovery info to task.json."""
    run_dir = "/tmp/test-host-recovery-info"
    os.makedirs(run_dir, exist_ok=True)
    try:
        adapter = HostAgentAdapter(run_dir=run_dir, timeout_seconds=1)
        adapter.call(prompt="test task")
        time.sleep(1.5)
        adapter.call(prompt="test task")

        task_file = Path(run_dir) / "task.json"
        task_data = json.loads(task_file.read_text())
        assert "timeout_at" in task_data or "recovery" in task_data
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_timeout.py -v`
Expected: FAIL — HostAgentAdapter doesn't have timeout_seconds parameter or timeout detection

- [ ] **Step 3: Implement timeout detection in HostAgentAdapter**

In `core/adapters/host.py`, update the class:

```python
"""HostAgentAdapter - adapter for host agent runtime with task/result packet protocol."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, TokenUsage


class HostAgentAdapter(ModelAdapter):
    """Adapter that communicates via TaskPacket/ResultPacket file protocol."""

    def __init__(self, run_dir: str | None = None, timeout_seconds: int = 120):
        self._run_dir = run_dir or ".reqflow/runs/default"
        self._step_count = 0
        self._timeout_seconds = timeout_seconds

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
            "created_at": time.time(),
        }
        task_file = Path(self._run_dir) / "task.json"
        task_file.write_text(json.dumps(packet, indent=2, ensure_ascii=False))
        packet["task_file"] = str(task_file)
        return packet

    def _check_timeout(self) -> bool:
        """Check if the current task has timed out."""
        task_file = Path(self._run_dir) / "task.json"
        if not task_file.exists():
            return False
        try:
            task_data = json.loads(task_file.read_text())
            created_at = task_data.get("created_at", 0)
            if created_at and (time.time() - created_at) > self._timeout_seconds:
                return True
        except (json.JSONDecodeError, OSError):
            pass
        return False

    def _mark_timeout(self) -> None:
        """Mark the current task as timed out and add recovery info."""
        task_file = Path(self._run_dir) / "task.json"
        if not task_file.exists():
            return
        try:
            task_data = json.loads(task_file.read_text())
            task_data["timeout_at"] = time.time()
            task_data["recovery"] = {
                "instructions": "Task timed out. To resume: submit a result.json with status and summary, then call again.",
                "result_file": str(Path(self._run_dir) / "result.json"),
                "task_file": str(task_file),
            }
            task_file.write_text(json.dumps(task_data, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, OSError):
            pass

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        self._step_count += 1

        # Check for result packet first
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

        # Check for timeout on existing task
        if self._check_timeout():
            self._mark_timeout()
            return ModelResponse(
                content=f"[TIMEOUT] Host agent 未在 {self._timeout_seconds} 秒内响应。"
                        f"请检查 task.json 并提交 result.json 以恢复执行。",
                tool_calls=[],
                tokens=TokenUsage(),
                raw={"status": "timeout", "timeout_seconds": self._timeout_seconds},
            )

        # Create new task packet
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

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_timeout.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v -k "not test_api_adapter_raises_on_http_error"`
Expected: All pass (skip network-dependent test)

- [ ] **Step 6: Commit**

```bash
git add core/adapters/host.py tests/test_host_timeout.py
git commit -m "feat: host adapter timeout detection and resume protocol"
```

---

### Task 2: Stage Artifacts 产物记录

**Files:**
- Modify: `core/state_manager.py`
- Modify: `core/engine.py`
- Create: `tests/test_stage_artifacts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stage_artifacts.py
import asyncio
import json
import shutil
from pathlib import Path
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_stage_records_include_content():
    """stage_records should include the actual response content, not just metadata."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-artifacts")

    async def mock_run_step(step, context=None):
        from reqflow.core.adapters.base import ModelResponse, TokenUsage
        response = ModelResponse(
            content=f"Output for {step['name']}: detailed analysis results here",
            tool_calls=[],
            tokens=TokenUsage(),
        )
        return StepResult(name=step["name"], status="success", response=response, duration_ms=100)

    engine.run_step = mock_run_step
    steps = [{"name": "analysis", "prompt": "analyze"}, {"name": "implementation", "prompt": "implement"}]

    asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    state = json.loads((Path("/tmp/test-stage-artifacts") / "state.json").read_text())
    assert len(state["stage_records"]) == 2

    first_record = state["stage_records"][0]
    assert first_record["name"] == "analysis"
    assert first_record["status"] == "success"
    assert "content" in first_record
    assert "detailed analysis" in first_record["content"]

    shutil.rmtree("/tmp/test-stage-artifacts", ignore_errors=True)


def test_stage_records_include_error_on_failure():
    """stage_records should include error details when step fails."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-stage-artifacts-fail")

    async def mock_run_step(step, context=None):
        if step["name"] == "failing":
            return StepResult(name="failing", status="failure", error="API returned 401", duration_ms=50)
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step
    steps = [
        {"name": "failing", "prompt": "fail"},
        {"name": "after", "prompt": "after"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))
    assert result["status"] == "failed"

    state = json.loads((Path("/tmp/test-stage-artifacts-fail") / "state.json").read_text())
    fail_record = state["stage_records"][0]
    assert fail_record["status"] == "failure"
    assert "401" in fail_record["error"]

    shutil.rmtree("/tmp/test-stage-artifacts-fail", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_stage_artifacts.py -v`
Expected: FAIL — stage_records doesn't include "content" field

- [ ] **Step 3: Add content field to stage_records in engine**

In `core/engine.py`, update the stage_records append (around line 159):

```python
                self.state_manager.state.stage_records.append({
                    "name": step["name"],
                    "status": step_result.status,
                    "duration_ms": step_result.duration_ms,
                    "error": step_result.error,
                    "content": step_result.response.content[:2000] if step_result.response else "",
                })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_stage_artifacts.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v -k "not test_api_adapter_raises_on_http_error"`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add core/engine.py tests/test_stage_artifacts.py
git commit -m "feat: stage_records include actual response content as artifacts"
```

---

### Task 3: Execution Traces 真实执行证据

**Files:**
- Modify: `core/engine.py`
- Create: `tests/test_execution_traces.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_execution_traces.py
import asyncio
import json
import shutil
from pathlib import Path
from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig


def test_execution_log_includes_step_details():
    """agent_execution_log should include per-step details, not just workflow-level entry."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-exec-traces")

    async def mock_run_step(step, context=None):
        from reqflow.core.adapters.base import ModelResponse, TokenUsage
        response = ModelResponse(
            content=f"Result for {step['name']}",
            tool_calls=[],
            tokens=TokenUsage(input_tokens=100, output_tokens=50),
        )
        return StepResult(name=step["name"], status="success", response=response, duration_ms=200)

    engine.run_step = mock_run_step
    steps = [
        {"name": "analyze", "prompt": "analyze"},
        {"name": "implement", "prompt": "implement"},
    ]

    asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))

    state = json.loads((Path("/tmp/test-exec-traces") / "state.json").read_text())
    log = state["agent_execution_log"]

    # Should have workflow entry + per-step entries
    assert len(log) >= 3

    # Check per-step entries exist
    step_entries = [e for e in log if e.get("type") == "step"]
    assert len(step_entries) == 2
    assert step_entries[0]["step_name"] == "analyze"
    assert step_entries[0]["status"] == "success"
    assert "content_preview" in step_entries[0]

    shutil.rmtree("/tmp/test-exec-traces", ignore_errors=True)


def test_execution_log_includes_failure_evidence():
    """agent_execution_log should include error details for failed steps."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-exec-traces-fail")

    async def mock_run_step(step, context=None):
        if step["name"] == "fail_step":
            return StepResult(name="fail_step", status="failure", error="Connection refused", duration_ms=50)
        return StepResult(name=step["name"], status="success", duration_ms=100)

    engine.run_step = mock_run_step
    steps = [
        {"name": "fail_step", "prompt": "fail"},
    ]

    result = asyncio.run(engine.run_workflow(workflow_steps=steps, requirement="test"))
    assert result["status"] == "failed"

    state = json.loads((Path("/tmp/test-exec-traces-fail") / "state.json").read_text())
    log = state["agent_execution_log"]

    step_entries = [e for e in log if e.get("type") == "step"]
    assert len(step_entries) == 1
    assert step_entries[0]["status"] == "failure"
    assert "Connection refused" in step_entries[0]["error"]

    shutil.rmtree("/tmp/test-exec-traces-fail", ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_execution_traces.py -v`
Expected: FAIL — agent_execution_log only has workflow-level entry, no per-step entries

- [ ] **Step 3: Add per-step execution log entries in engine**

In `core/engine.py`, in `run_workflow`, after the stage_records append (around line 164), add:

```python
                self.state_manager.state.agent_execution_log.append({
                    "type": "step",
                    "step_name": step["name"],
                    "status": step_result.status,
                    "duration_ms": step_result.duration_ms,
                    "error": step_result.error,
                    "content_preview": step_result.response.content[:500] if step_result.response else "",
                    "timestamp": datetime.now().isoformat(),
                })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_execution_traces.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v -k "not test_api_adapter_raises_on_http_error"`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add core/engine.py tests/test_execution_traces.py
git commit -m "feat: per-step execution traces with real evidence"
```

---

### Task 4: Dashboard 展示阶段产物和恢复信息

**Files:**
- Modify: `runner/dashboard.py`
- Modify: `runner/mcp_server.py`
- Create: `tests/test_dashboard_artifacts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dashboard_artifacts.py
import json
import os
import shutil
from pathlib import Path
from reqflow.runner.dashboard import Dashboard


def test_dashboard_shows_stage_artifacts():
    """Dashboard should display stage content previews."""
    run_dir = "/tmp/test-dashboard-artifacts"
    os.makedirs(run_dir, exist_ok=True)
    try:
        state = {
            "run_id": "test-run",
            "current_stage": "done",
            "completed_modules": ["analysis", "implementation"],
            "checkpoints": [],
            "memory": {"short_term": []},
            "stage_records": [
                {"name": "analysis", "status": "success", "duration_ms": 100, "content": "Analyzed requirements and found 3 key points"},
                {"name": "implementation", "status": "failure", "duration_ms": 50, "error": "API 401", "content": ""},
            ],
        }
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        dashboard = Dashboard(run_dir=run_dir)
        status = {
            "run_id": "test-run",
            "config": "host",
            "adapter": "host",
            "current_stage": "done",
            "completed_modules": ["analysis", "implementation"],
            "steps_executed": 2,
            "step_statuses": {"analysis": "success", "implementation": "failure"},
            "checkpoints": 0,
            "memory_entries": 0,
            "stage_records": state["stage_records"],
        }
        output = dashboard.format_status(status)
        assert "Analyzed requirements" in output or "analysis" in output
        assert "FAIL" in output or "failure" in output
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_dashboard_shows_timeout_recovery_info():
    """Dashboard should show recovery instructions when timeout detected."""
    run_dir = "/tmp/test-dashboard-recovery"
    os.makedirs(run_dir, exist_ok=True)
    try:
        dashboard = Dashboard(run_dir=run_dir)
        status = {
            "run_id": "test-run",
            "config": "host",
            "adapter": "host",
            "current_stage": "step2",
            "completed_modules": ["step1"],
            "steps_executed": 2,
            "step_statuses": {"step1": "success", "step2": "timeout"},
            "checkpoints": 0,
            "memory_entries": 0,
            "stage_records": [
                {"name": "step1", "status": "success", "duration_ms": 100},
                {"name": "step2", "status": "timeout", "duration_ms": 120000},
            ],
        }
        output = dashboard.format_status(status)
        assert "timeout" in output.lower() or "超时" in output
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_dashboard_artifacts.py -v`
Expected: FAIL — dashboard doesn't show stage content or timeout recovery

- [ ] **Step 3: Update dashboard to show stage artifacts and recovery**

In `runner/dashboard.py`, update `format_status`:

```python
    def format_status(self, status: dict[str, Any]) -> str:
        """Format engine status as readable text."""
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
                marker = "OK" if st == "success" else "FAIL" if st == "failure" else "TIMEOUT" if st == "timeout" else st.upper()
                lines.append(f"  [{marker:7s}] {name}")

        # Show stage artifacts
        stage_records = status.get("stage_records", [])
        if stage_records:
            lines.append(f"\n--- Stage Artifacts ---")
            for record in stage_records:
                name = record.get("name", "?")
                content = record.get("content", "")
                error = record.get("error", "")
                if content:
                    preview = content[:100] + ("..." if len(content) > 100 else "")
                    lines.append(f"  {name}: {preview}")
                elif error:
                    lines.append(f"  {name}: [ERROR] {error}")

        # Show recovery info if any timeout
        has_timeout = any(st == "timeout" for st in step_statuses.values())
        if has_timeout:
            lines.append(f"\n--- Recovery ---")
            lines.append(f"  检测到超时。请检查 task.json 并提交 result.json 以恢复执行。")
            lines.append(f"  使用: reqflow host-task status <run_dir> 查看详情")

        lines.append(f"\nCheckpoints: {status.get('checkpoints', 0)}")
        lines.append(f"Memory:      {status.get('memory_entries', 0)} entries")

        return "\n".join(lines)
```

- [ ] **Step 4: Update MCP _handle_dashboard to pass stage_records**

In `runner/mcp_server.py`, in `_handle_dashboard`, update the status dict construction:

```python
    status = {
        "run_id": data.get("run_id", "?"),
        "config": data.get("config", "?"),
        "adapter": data.get("adapter", "?"),
        "current_stage": data.get("current_stage", "?"),
        "completed_modules": data.get("completed_modules", []),
        "steps_executed": len(data.get("completed_modules", [])),
        "step_statuses": {},
        "checkpoints": len(data.get("checkpoints", [])),
        "memory_entries": len(data.get("memory", {}).get("short_term", [])),
        "stage_records": data.get("stage_records", []),
    }
```

Also populate step_statuses from stage_records:

```python
    # Build step_statuses from stage_records
    for record in data.get("stage_records", []):
        name = record.get("name", "")
        status_val = record.get("status", "")
        if name and status_val:
            status["step_statuses"][name] = status_val
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_dashboard_artifacts.py -v`
Expected: PASS

- [ ] **Step 6: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v -k "not test_api_adapter_raises_on_http_error"`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add runner/dashboard.py runner/mcp_server.py tests/test_dashboard_artifacts.py
git commit -m "feat: dashboard shows stage artifacts and timeout recovery info"
```

---

### Task 5: Host Task CLI Resume 支持

**Files:**
- Modify: `runner/host_task.py`
- Modify: `tests/test_host_task_cli.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_host_task_cli.py`:

```python
def test_get_status_shows_timeout_info():
    """get_status should indicate when a task has timed out."""
    run_dir = "/tmp/test-host-task-timeout"
    os.makedirs(run_dir, exist_ok=True)
    try:
        import time
        task = {"stage_id": "s1", "prompt": "do something", "created_at": time.time() - 300}
        (Path(run_dir) / "task.json").write_text(json.dumps(task))
        state = {"run_id": "test", "current_stage": "s1", "completed_modules": []}
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        status = get_status(run_dir)
        assert status.get("task_pending") is True
        assert status.get("task_timed_out") is True
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_get_status_no_timeout_for_recent_task():
    """get_status should not flag timeout for recent tasks."""
    run_dir = "/tmp/test-host-task-recent"
    os.makedirs(run_dir, exist_ok=True)
    try:
        import time
        task = {"stage_id": "s1", "prompt": "do something", "created_at": time.time() - 10}
        (Path(run_dir) / "task.json").write_text(json.dumps(task))
        state = {"run_id": "test", "current_stage": "s1", "completed_modules": []}
        (Path(run_dir) / "state.json").write_text(json.dumps(state))

        status = get_status(run_dir)
        assert status.get("task_pending") is True
        assert status.get("task_timed_out", False) is False
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_task_cli.py::test_get_status_shows_timeout_info -v`
Expected: FAIL — get_status doesn't check task timeout

- [ ] **Step 3: Update get_status with timeout detection**

In `runner/host_task.py`, update `get_status`:

```python
"""CLI fallback for host agent interaction via file protocol."""

from __future__ import annotations

import json
import time
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 120


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


def get_status(run_dir: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Get the current run status with timeout detection."""
    state_file = Path(run_dir) / "state.json"
    if not state_file.exists():
        return {"error": f"State file not found: {state_file}"}
    try:
        status = json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"Cannot read state file: {e}"}

    # Check for pending task
    task_file = Path(run_dir) / "task.json"
    if task_file.exists():
        try:
            task_data = json.loads(task_file.read_text())
            status["task_pending"] = True
            created_at = task_data.get("created_at", 0)
            if created_at and (time.time() - created_at) > timeout_seconds:
                status["task_timed_out"] = True
                status["timeout_seconds"] = timeout_seconds
        except (json.JSONDecodeError, OSError):
            pass

    return status
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/test_host_task_cli.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/reqflow && python -m pytest tests/ -v -k "not test_api_adapter_raises_on_http_error"`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add runner/host_task.py tests/test_host_task_cli.py
git commit -m "feat: host task CLI timeout detection and resume support"
```

---

## Self-Review Checklist

| Spec Requirement | Task |
|---|---|
| Issue 5: host-codex 超时 | Task 1 (timeout detection) |
| Issue 6: 超时后缺恢复信息 | Task 1 + Task 4 (recovery info) |
| Issue 8: 没有阶段文档 | Task 2 (stage artifacts) + Task 4 (dashboard display) |
| Issue 9: 没真实执行痕迹 | Task 3 (per-step execution log) |
| Dashboard 展示真实状态 | Task 4 (artifacts + timeout display) |
| Host task CLI resume | Task 5 (timeout in get_status) |
