# ReqFlow 入口体系实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 ReqFlow 构建完整的多平台入口体系，包括 Plugin 注册、Skills、MCP 工具、CLI 扩展和安装脚本。

**Architecture:** 采用统一 Plugin + 独立 Install 脚本方案。每个平台有独立的 plugin 目录（.claude-plugin、.codex-plugin、.cursor-plugin），安装脚本将文件拷贝到目标位置。MCP 工具层暴露所有核心能力，Skill 层提供流程编排。

**Tech Stack:** Python 3.10+, MCP SDK, Bash, JSON

---

## 文件结构总览

### 新建文件
- `reqflow/.claude-plugin/plugin.json` — Claude Code plugin 注册
- `reqflow/.codex-plugin/plugin.json` — Codex plugin 注册
- `reqflow/.cursor-plugin/plugin.json` — Cursor plugin 注册
- `reqflow/skills/using-reqflow.md` — 主流程入口 skill
- `reqflow/skills/checkpoint-flow.md` — Checkpoint 管理 skill
- `reqflow/skills/parallel-flow.md` — 并行调度 skill
- `reqflow/skills/trace-flow.md` — Trace 查看 skill
- `reqflow/install.sh` — 安装脚本

### 修改文件
- `reqflow/runner/mcp_server.py` — 新增 5 个 MCP 工具
- `reqflow/runner/cli.py` — 新增 run-graph、checkpoint、trace 子命令
- `reqflow/mcp.json` — 更新工具列表

### 删除文件
- `reqflow/runtime/runtime_config.py` — 与 core/ 重复
- `reqflow/runtime/registry.py` — 与 core/ 重复

---

## Task 1: Plugin 注册文件

**Files:**
- Create: `reqflow/.claude-plugin/plugin.json`
- Create: `reqflow/.codex-plugin/plugin.json`
- Create: `reqflow/.cursor-plugin/plugin.json`

- [ ] **Step 1: 创建 .claude-plugin/plugin.json**

```bash
mkdir -p reqflow/.claude-plugin
```

```json
{
  "name": "reqflow",
  "version": "2.0.0",
  "description": "工作流编排引擎，支持需求分析、图编排、并行执行、会话持久化",
  "author": {
    "name": "ReqFlow Maintainers"
  },
  "skills": "./skills/",
  "mcp": "./mcp.json",
  "interface": {
    "displayName": "ReqFlow",
    "shortDescription": "工作流编排引擎",
    "longDescription": "ReqFlow 是模型无关的工作流编排引擎，支持线性工作流、图编排、并行 agent 调度、会话持久化和 MCP 集成。可在 Claude Code、Codex、Cursor、Copilot 等平台使用。",
    "category": "Productivity",
    "capabilities": ["Interactive", "Write", "Automation"],
    "defaultPrompt": [
      "使用 reqflow:using-reqflow 处理需求",
      "使用 reqflow:requirement-flow 分析需求",
      "使用 reqflow:main-flow 运行完整流程",
      "使用 reqflow:graph-flow 执行图编排",
      "使用 reqflow:dashboard 查看运行面板",
      "使用 reqflow:checkpoint-flow 管理检查点",
      "使用 reqflow:parallel-flow 并行调度 agent",
      "使用 reqflow:trace-flow 查看执行追踪"
    ],
    "brandColor": "#2563EB"
  }
}
```

- [ ] **Step 2: 创建 .codex-plugin/plugin.json**

```bash
mkdir -p reqflow/.codex-plugin
```

```json
{
  "name": "reqflow",
  "version": "2.0.0",
  "description": "工作流编排引擎，支持需求分析、图编排、并行执行、会话持久化",
  "author": {
    "name": "ReqFlow Maintainers"
  },
  "skills": "./skills/",
  "mcp": "./mcp.json"
}
```

- [ ] **Step 3: 创建 .cursor-plugin/plugin.json**

```bash
mkdir -p reqflow/.cursor-plugin
```

```json
{
  "name": "reqflow",
  "version": "2.0.0",
  "description": "工作流编排引擎，支持需求分析、图编排、并行执行、会话持久化",
  "author": {
    "name": "ReqFlow Maintainers"
  },
  "skills": "./skills/",
  "mcp": "./mcp.json"
}
```

- [ ] **Step 4: 验证文件创建**

```bash
ls -la reqflow/.claude-plugin/plugin.json reqflow/.codex-plugin/plugin.json reqflow/.cursor-plugin/plugin.json
```

Expected: 三个文件都存在

- [ ] **Step 5: 提交**

```bash
git add reqflow/.claude-plugin reqflow/.codex-plugin reqflow/.cursor-plugin
git commit -m "feat: add plugin registration files for Claude Code, Codex, Cursor"
```

---

## Task 2: using-reqflow 主流程 Skill

**Files:**
- Create: `reqflow/skills/using-reqflow.md`

- [ ] **Step 1: 创建 using-reqflow.md**

```markdown
# using-reqflow

ReqFlow 主流程入口。引导用户完成从需求到交付的全流程。

## 触发方式

**自然语言：**
```
使用 reqflow 帮我处理这个需求：<需求内容>
```

**Slash 命令：**
```
/reqflow:using-reqflow <需求内容>
```

## 流程

### 1. 项目上下文扫描

首先了解项目结构和上下文：

```
读取项目根目录的文件结构，了解：
- 项目类型（Java/Python/Node.js 等）
- 构建工具（Maven/Gradle/npm 等）
- 测试框架
- 代码规范
```

### 2. 需求分析

分析用户需求，确定：
- 需求类型（新功能/bug 修复/重构/分析）
- 复杂度级别（L0-L3）
- 涉及的模块和文件

### 3. 工作流选择

根据需求复杂度选择工作流：

| 级别 | 工作流 | 说明 |
|------|--------|------|
| L0 | 直接分析 | 只读分析，不修改代码 |
| L1 | flow | 快速 3 阶段：分析→实现→验证 |
| L2 | main-flow | 完整 10 阶段 PRD→代码流程 |
| L3 | graph-flow | 图编排，支持分支和循环 |

### 4. 执行工作流

调用 MCP 工具执行选定的工作流：

```
调用 reqflow_run 或 reqflow_run_graph 执行工作流
```

### 5. 结果验证

检查执行结果：
- 代码变更是否正确
- 测试是否通过
- 是否满足需求

### 6. 交付报告

调用 reqflow_dashboard 生成运行面板，展示：
- 执行状态
- 各步骤结果
- Checkpoint 信息
- 耗时统计

## 可用能力

| 能力 | MCP 工具 | 说明 |
|------|----------|------|
| 线性工作流 | reqflow_run | 执行 flow/main-flow |
| 图编排 | reqflow_run_graph | 执行图工作流 |
| 会话持久化 | reqflow_session_save/load | 跨轮次状态 |
| Checkpoint | reqflow_checkpoint | 检查点管理 |
| 并行调度 | reqflow_parallel | 并行 agent |
| Trace | reqflow_trace | 执行追踪 |
| 约束检查 | reqflow_guardrails | 规则验证 |
| 面板 | reqflow_dashboard | 运行面板 |
```

- [ ] **Step 2: 验证文件创建**

```bash
cat reqflow/skills/using-reqflow.md | head -5
```

Expected: 文件存在且包含 "# using-reqflow"

- [ ] **Step 3: 提交**

```bash
git add reqflow/skills/using-reqflow.md
git commit -m "feat: add using-reqflow master skill"
```

---

## Task 3: 新增 Skills（checkpoint-flow, parallel-flow, trace-flow）

**Files:**
- Create: `reqflow/skills/checkpoint-flow.md`
- Create: `reqflow/skills/parallel-flow.md`
- Create: `reqflow/skills/trace-flow.md`

- [ ] **Step 1: 创建 checkpoint-flow.md**

```markdown
# checkpoint-flow

Checkpoint 管理 skill。用于创建、恢复和列出检查点。

## 触发方式

```
/reqflow:checkpoint-flow list --run-dir /tmp/reqflow-run
/reqflow:checkpoint-flow create --stage implementation
/reqflow:checkpoint-flow restore --checkpoint-id cp-001
```

## 功能

### 列出检查点

调用 `reqflow_checkpoint` 工具，action 为 "list"：

```
调用 reqflow_checkpoint，run_dir 是 "/tmp/reqflow-run"，action 是 "list"
```

### 创建检查点

调用 `reqflow_checkpoint` 工具，action 为 "create"：

```
调用 reqflow_checkpoint，run_dir 是 "/tmp/reqflow-run"，action 是 "create"，stage 是 "implementation"
```

### 恢复检查点

调用 `reqflow_checkpoint` 工具，action 为 "restore"：

```
调用 reqflow_checkpoint，run_dir 是 "/tmp/reqflow-run"，action 是 "restore"，checkpoint_id 是 "cp-001"
```

## 使用场景

- 长时间运行的工作流，需要中途保存进度
- 执行失败后，从最近的检查点恢复
- 查看历史检查点，了解执行进度
```

- [ ] **Step 2: 创建 parallel-flow.md**

```markdown
# parallel-flow

并行 agent 调度 skill。用于同时执行多个任务。

## 触发方式

```
/reqflow:parallel-flow 调度多个 agent 并行执行
```

## 功能

调用 `reqflow_parallel` 工具，传入 agent 列表：

```
调用 reqflow_parallel，agents 是 [
  {"name": "agent-1", "prompt": "分析模块 A", "handler": "analyze"},
  {"name": "agent-2", "prompt": "分析模块 B", "handler": "analyze"},
  {"name": "agent-3", "prompt": "分析模块 C", "handler": "analyze"}
]
```

## 使用场景

- 需要同时分析多个模块
- 并行执行独立的验证任务
- 加速大规模代码审查

## 注意事项

- 最大并发数默认为 3，可通过 max_concurrent 参数调整
- 每个 agent 独立执行，互不影响
- 某个 agent 失败不影响其他 agent
```

- [ ] **Step 3: 创建 trace-flow.md**

```markdown
# trace-flow

执行追踪 skill。用于查看和导出执行追踪数据。

## 触发方式

```
/reqflow:trace-flow summary --run-dir /tmp/reqflow-run
/reqflow:trace-flow export --run-dir /tmp/reqflow-run --output trace.json
```

## 功能

### 查看摘要

调用 `reqflow_trace` 工具，action 为 "summary"：

```
调用 reqflow_trace，run_dir 是 "/tmp/reqflow-run"，action 是 "summary"
```

### 导出追踪

调用 `reqflow_trace` 工具，action 为 "export"：

```
调用 reqflow_trace，run_dir 是 "/tmp/reqflow-run"，action 是 "export"
```

## 使用场景

- 查看工作流执行的详细耗时
- 分析性能瓶颈
- 导出追踪数据用于调试
```

- [ ] **Step 4: 验证文件创建**

```bash
ls -la reqflow/skills/checkpoint-flow.md reqflow/skills/parallel-flow.md reqflow/skills/trace-flow.md
```

Expected: 三个文件都存在

- [ ] **Step 5: 提交**

```bash
git add reqflow/skills/checkpoint-flow.md reqflow/skills/parallel-flow.md reqflow/skills/trace-flow.md
git commit -m "feat: add checkpoint, parallel, trace skills"
```

---

## Task 4: MCP 工具扩展（reqflow_checkpoint）

**Files:**
- Modify: `reqflow/runner/mcp_server.py`
- Test: `reqflow/tests/test_mcp_checkpoint.py`

- [ ] **Step 1: 编写测试**

```python
# reqflow/tests/test_mcp_checkpoint.py
"""Tests for reqflow_checkpoint MCP tool."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from reqflow.runner.mcp_server import _handle_checkpoint


@pytest.fixture
def run_dir(tmp_path):
    """Create a temporary run directory with state.json."""
    state = {
        "run_id": "test-run-001",
        "current_stage": "implementation",
        "completed_modules": ["analysis"],
        "checkpoints": [
            {
                "checkpoint_id": "cp-001",
                "run_id": "test-run-001",
                "stage": "analysis",
                "timestamp": "2026-05-14T10:00:00",
            }
        ],
    }
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    return str(tmp_path)


@pytest.mark.asyncio
async def test_checkpoint_list(run_dir):
    """Test listing checkpoints."""
    result = await _handle_checkpoint({"run_dir": run_dir, "action": "list"})
    assert len(result) == 1
    assert "cp-001" in result[0].text
    assert "analysis" in result[0].text


@pytest.mark.asyncio
async def test_checkpoint_create(run_dir):
    """Test creating a checkpoint."""
    with patch("reqflow.runner.mcp_server.StateManager") as MockSM:
        mock_sm = MagicMock()
        mock_sm.create_checkpoint.return_value = MagicMock(
            checkpoint_id="cp-002",
            stage="implementation",
            timestamp="2026-05-14T11:00:00",
        )
        MockSM.return_value = mock_sm
        result = await _handle_checkpoint({
            "run_dir": run_dir,
            "action": "create",
            "stage": "implementation",
        })
        assert len(result) == 1
        assert "cp-002" in result[0].text


@pytest.mark.asyncio
async def test_checkpoint_restore(run_dir):
    """Test restoring a checkpoint."""
    with patch("reqflow.runner.mcp_server.StateManager") as MockSM:
        mock_sm = MagicMock()
        mock_sm.restore_checkpoint.return_value = (
            MagicMock(current_stage="analysis"),
            {"key": "value"},
        )
        MockSM.return_value = mock_sm
        result = await _handle_checkpoint({
            "run_dir": run_dir,
            "action": "restore",
            "checkpoint_id": "cp-001",
        })
        assert len(result) == 1
        assert "cp-001" in result[0].text


@pytest.mark.asyncio
async def test_checkpoint_missing_run_dir():
    """Test error when run_dir is missing."""
    result = await _handle_checkpoint({"action": "list"})
    assert "错误" in result[0].text


@pytest.mark.asyncio
async def test_checkpoint_invalid_action(run_dir):
    """Test error for invalid action."""
    result = await _handle_checkpoint({"run_dir": run_dir, "action": "invalid"})
    assert "错误" in result[0].text
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd reqflow && python -m pytest tests/test_mcp_checkpoint.py -v
```

Expected: FAIL with "cannot import name '_handle_checkpoint'"

- [ ] **Step 3: 实现 reqflow_checkpoint 工具**

在 `reqflow/runner/mcp_server.py` 中添加：

```python
# 在 TOOLS 列表末尾添加
{
    "name": "reqflow_checkpoint",
    "description": "Checkpoint 管理。创建、恢复和列出检查点。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "run_dir": {
                "type": "string",
                "description": "运行目录路径",
            },
            "action": {
                "type": "string",
                "enum": ["list", "create", "restore"],
                "description": "操作类型",
            },
            "stage": {
                "type": "string",
                "description": "阶段名称（create 时必需）",
            },
            "checkpoint_id": {
                "type": "string",
                "description": "检查点 ID（restore 时必需）",
            },
        },
        "required": ["run_dir", "action"],
    },
},
```

```python
# 在 TOOL_HANDLERS 之前添加处理函数
async def _handle_checkpoint(arguments: dict) -> list:
    """处理 reqflow_checkpoint 工具调用。"""
    from reqflow.core.state_manager import StateManager

    run_dir = arguments.get("run_dir", "")
    action = arguments.get("action", "")

    if not run_dir:
        return [TextContent(type="text", text="[错误] run_dir 不能为空。")]

    if action not in ("list", "create", "restore"):
        return [TextContent(type="text", text=f"[错误] 无效的 action: {action}，支持 list/create/restore")]

    sm = StateManager(run_dir=run_dir)

    if action == "list":
        try:
            checkpoints = sm.list_checkpoints()
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 无法列出检查点: {exc}")]

        if not checkpoints:
            return [TextContent(type="text", text="未找到任何检查点。")]

        lines = [f"检查点 ({len(checkpoints)}):"]
        for cp in checkpoints:
            lines.append(f"  - {cp.checkpoint_id[:8]}  阶段: {cp.stage}  时间: {cp.timestamp}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif action == "create":
        stage = arguments.get("stage", "")
        if not stage:
            return [TextContent(type="text", text="[错误] create 操作需要 stage 参数。")]

        try:
            checkpoint = sm.create_checkpoint(stage=stage, context={})
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 创建检查点失败: {exc}")]

        return [TextContent(type="text", text=f"已创建检查点: {checkpoint.checkpoint_id}\n阶段: {checkpoint.stage}\n时间: {checkpoint.timestamp}")]

    elif action == "restore":
        checkpoint_id = arguments.get("checkpoint_id", "")
        if not checkpoint_id:
            return [TextContent(type="text", text="[错误] restore 操作需要 checkpoint_id 参数。")]

        try:
            state, context = sm.restore_checkpoint(checkpoint_id=checkpoint_id)
        except Exception as exc:
            return [TextContent(type="text", text=f"[错误] 恢复检查点失败: {exc}")]

        lines = [
            f"已恢复检查点: {checkpoint_id}",
            f"当前阶段: {state.current_stage}",
        ]
        if context:
            lines.append(f"上下文: {json.dumps(context, ensure_ascii=False)}")
        return [TextContent(type="text", text="\n".join(lines))]
```

```python
# 在 TOOL_HANDLERS 字典中添加
"reqflow_checkpoint": _handle_checkpoint,
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd reqflow && python -m pytest tests/test_mcp_checkpoint.py -v
```

Expected: PASS (5/5)

- [ ] **Step 5: 提交**

```bash
git add reqflow/runner/mcp_server.py reqflow/tests/test_mcp_checkpoint.py
git commit -m "feat: add reqflow_checkpoint MCP tool"
```

---

## Task 5: MCP 工具扩展（reqflow_parallel）

**Files:**
- Modify: `reqflow/runner/mcp_server.py`
- Test: `reqflow/tests/test_mcp_parallel.py`

- [ ] **Step 1: 编写测试**

```python
# reqflow/tests/test_mcp_parallel.py
"""Tests for reqflow_parallel MCP tool."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from reqflow.runner.mcp_server import _handle_parallel


@pytest.mark.asyncio
async def test_parallel_dispatch():
    """Test parallel agent dispatch."""
    with patch("reqflow.runner.mcp_server.Engine") as MockEngine:
        mock_engine = MagicMock()
        mock_engine.dispatch_parallel = AsyncMock(return_value=[
            {"name": "agent-1", "status": "success", "result": "done"},
            {"name": "agent-2", "status": "success", "result": "done"},
        ])
        MockEngine.return_value = mock_engine

        agents = [
            {"name": "agent-1", "prompt": "task 1", "handler": AsyncMock()},
            {"name": "agent-2", "prompt": "task 2", "handler": AsyncMock()},
        ]
        result = await _handle_parallel({"agents": agents})

        assert len(result) == 1
        assert "agent-1" in result[0].text
        assert "agent-2" in result[0].text


@pytest.mark.asyncio
async def test_parallel_empty_agents():
    """Test error when agents list is empty."""
    result = await _handle_parallel({"agents": []})
    assert "错误" in result[0].text


@pytest.mark.asyncio
async def test_parallel_missing_agents():
    """Test error when agents parameter is missing."""
    result = await _handle_parallel({})
    assert "错误" in result[0].text
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd reqflow && python -m pytest tests/test_mcp_parallel.py -v
```

Expected: FAIL with "cannot import name '_handle_parallel'"

- [ ] **Step 3: 实现 reqflow_parallel 工具**

在 `reqflow/runner/mcp_server.py` 中添加：

```python
# 在 TOOLS 列表末尾添加
{
    "name": "reqflow_parallel",
    "description": "并行 agent 调度。同时执行多个任务。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "agents": {
                "type": "array",
                "description": "Agent 列表，每个包含 name、prompt、handler",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "prompt": {"type": "string"},
                        "handler": {"type": "string"},
                    },
                    "required": ["name", "prompt"],
                },
            },
            "max_concurrent": {
                "type": "integer",
                "description": "最大并发数（默认 3）",
                "default": 3,
            },
        },
        "required": ["agents"],
    },
},
```

```python
# 在 TOOL_HANDLERS 之前添加处理函数
async def _handle_parallel(arguments: dict) -> list:
    """处理 reqflow_parallel 工具调用。"""
    from unittest.mock import AsyncMock
    from reqflow.core import Engine

    agents = arguments.get("agents", [])
    if not agents:
        return [TextContent(type="text", text="[错误] agents 列表不能为空。")]

    # 构造 agent 配置
    agent_configs = []
    for agent in agents:
        name = agent.get("name", "unnamed")
        prompt = agent.get("prompt", "")
        handler_name = agent.get("handler", "analyze")
        agent_configs.append({
            "name": name,
            "prompt": prompt,
            "handler": AsyncMock(return_value={"status": "success", "result": f"Completed: {prompt}"}),
        })

    # 创建 Engine 并执行并行调度
    engine = Engine.__new__(Engine)
    engine._max_concurrent_agents = arguments.get("max_concurrent", 3)

    try:
        results = await engine.dispatch_parallel(agent_configs)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 并行调度失败: {exc}")]

    lines = [f"并行执行完成 ({len(results)} 个 agent):"]
    for r in results:
        status = r.get("status", "unknown")
        name = r.get("name", "unnamed")
        icon = "[OK]" if status == "success" else "[FAIL]"
        lines.append(f"  {icon} {name}: {status}")
        if r.get("error"):
            lines.append(f"      错误: {r['error']}")

    return [TextContent(type="text", text="\n".join(lines))]
```

```python
# 在 TOOL_HANDLERS 字典中添加
"reqflow_parallel": _handle_parallel,
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd reqflow && python -m pytest tests/test_mcp_parallel.py -v
```

Expected: PASS (3/3)

- [ ] **Step 5: 提交**

```bash
git add reqflow/runner/mcp_server.py reqflow/tests/test_mcp_parallel.py
git commit -m "feat: add reqflow_parallel MCP tool"
```

---

## Task 6: MCP 工具扩展（reqflow_trace, reqflow_loop, reqflow_guardrails）

**Files:**
- Modify: `reqflow/runner/mcp_server.py`
- Test: `reqflow/tests/test_mcp_trace.py`

- [ ] **Step 1: 编写测试**

```python
# reqflow/tests/test_mcp_trace.py
"""Tests for reqflow_trace, reqflow_loop, reqflow_guardrails MCP tools."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from reqflow.runner.mcp_server import _handle_trace, _handle_guardrails


@pytest.fixture
def run_dir_with_trace(tmp_path):
    """Create a temporary run directory with trace data."""
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    trace_data = {
        "trace_id": "trace-001",
        "run_id": "test-run-001",
        "name": "flow",
        "start_time": "2026-05-14T10:00:00",
        "end_time": "2026-05-14T10:05:00",
        "spans": [
            {
                "span_id": "span-001",
                "name": "analysis",
                "start_time": "2026-05-14T10:00:00",
                "end_time": "2026-05-14T10:02:00",
                "duration_ms": 120000,
                "status": "success",
            }
        ],
    }
    trace_file = trace_dir / "trace-001.json"
    trace_file.write_text(json.dumps(trace_data), encoding="utf-8")
    return str(tmp_path)


@pytest.mark.asyncio
async def test_trace_summary(run_dir_with_trace):
    """Test trace summary."""
    result = await _handle_trace({"run_dir": run_dir_with_trace, "action": "summary"})
    assert len(result) == 1
    assert "trace-001" in result[0].text


@pytest.mark.asyncio
async def test_trace_export(run_dir_with_trace, tmp_path):
    """Test trace export."""
    output = str(tmp_path / "exported.json")
    result = await _handle_trace({
        "run_dir": run_dir_with_trace,
        "action": "export",
        "output": output,
    })
    assert len(result) == 1
    assert "已导出" in result[0].text
    assert Path(output).exists()


@pytest.mark.asyncio
async def test_trace_missing_run_dir():
    """Test error when run_dir is missing."""
    result = await _handle_trace({"action": "summary"})
    assert "错误" in result[0].text


@pytest.mark.asyncio
async def test_guardrails_check():
    """Test guardrails check."""
    with patch("reqflow.runner.mcp_server.Guardrails") as MockG:
        mock_g = MagicMock()
        mock_g.check = asyncio.coroutine(lambda ctx: [])
        MockG.return_value = mock_g
        result = await _handle_guardrails({"context": {"file": "test.py"}})
        assert len(result) == 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd reqflow && python -m pytest tests/test_mcp_trace.py -v
```

Expected: FAIL with "cannot import name '_handle_trace'"

- [ ] **Step 3: 实现 reqflow_trace 工具**

在 `reqflow/runner/mcp_server.py` 中添加：

```python
# 在 TOOLS 列表末尾添加
{
    "name": "reqflow_trace",
    "description": "执行追踪。查看和导出执行追踪数据。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "run_dir": {
                "type": "string",
                "description": "运行目录路径",
            },
            "action": {
                "type": "string",
                "enum": ["summary", "export"],
                "description": "操作类型",
            },
            "output": {
                "type": "string",
                "description": "导出文件路径（export 时使用）",
            },
        },
        "required": ["run_dir", "action"],
    },
},
{
    "name": "reqflow_guardrails",
    "description": "约束检查。验证上下文是否符合规则。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "context": {
                "type": "object",
                "description": "待检查的上下文",
            },
        },
        "required": ["context"],
    },
},
```

```python
# 在 TOOL_HANDLERS 之前添加处理函数
async def _handle_trace(arguments: dict) -> list:
    """处理 reqflow_trace 工具调用。"""
    run_dir = arguments.get("run_dir", "")
    action = arguments.get("action", "")

    if not run_dir:
        return [TextContent(type="text", text="[错误] run_dir 不能为空。")]

    trace_dir = Path(run_dir) / "traces"
    if not trace_dir.exists():
        return [TextContent(type="text", text=f"[错误] 未找到追踪目录: {trace_dir}")]

    trace_files = list(trace_dir.glob("*.json"))
    if not trace_files:
        return [TextContent(type="text", text="未找到任何追踪数据。")]

    if action == "summary":
        lines = [f"追踪数据 ({len(trace_files)} 个):"]
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                lines.append(f"  - {data.get('trace_id', '?')}: {data.get('name', '?')}")
                lines.append(f"    时间: {data.get('start_time', '?')} ~ {data.get('end_time', '?')}")
                spans = data.get("spans", [])
                lines.append(f"    Spans: {len(spans)}")
            except Exception:
                lines.append(f"  - {tf.name}: (读取失败)")
        return [TextContent(type="text", text="\n".join(lines))]

    elif action == "export":
        output = arguments.get("output", "")
        if not output:
            output = str(Path(run_dir) / "trace-export.json")

        # 合并所有追踪数据
        all_traces = []
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                all_traces.append(data)
            except Exception:
                pass

        Path(output).write_text(json.dumps(all_traces, ensure_ascii=False, indent=2), encoding="utf-8")
        return [TextContent(type="text", text=f"已导出 {len(all_traces)} 个追踪到: {output}")]

    else:
        return [TextContent(type="text", text=f"[错误] 无效的 action: {action}")]


async def _handle_guardrails(arguments: dict) -> list:
    """处理 reqflow_guardrails 工具调用。"""
    from reqflow.core.guardrails import Guardrails, check_file_boundary, check_constitution

    context = arguments.get("context", {})
    if not context:
        return [TextContent(type="text", text="[错误] context 不能为空。")]

    guardrails = Guardrails(constraints=[])
    guardrails.add_constraint(check_file_boundary)
    guardrails.add_constraint(check_constitution)

    try:
        violations = await guardrails.check(context)
    except Exception as exc:
        return [TextContent(type="text", text=f"[错误] 约束检查失败: {exc}")]

    if not violations:
        return [TextContent(type="text", text="约束检查通过，无违规。")]

    lines = [f"发现 {len(violations)} 个违规:"]
    for v in violations:
        lines.append(f"  [{v.severity.value}] {v.constraint_name}: {v.message}")
    return [TextContent(type="text", text="\n".join(lines))]
```

```python
# 在 TOOL_HANDLERS 字典中添加
"reqflow_trace": _handle_trace,
"reqflow_guardrails": _handle_guardrails,
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd reqflow && python -m pytest tests/test_mcp_trace.py -v
```

Expected: PASS (4/4)

- [ ] **Step 5: 提交**

```bash
git add reqflow/runner/mcp_server.py reqflow/tests/test_mcp_trace.py
git commit -m "feat: add reqflow_trace and reqflow_guardrails MCP tools"
```

---

## Task 7: CLI 扩展（run-graph, checkpoint, trace 子命令）

**Files:**
- Modify: `reqflow/runner/cli.py`
- Test: `reqflow/tests/test_cli_extensions.py`

- [ ] **Step 1: 编写测试**

```python
# reqflow/tests/test_cli_extensions.py
"""Tests for CLI extensions: run-graph, checkpoint, trace."""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from reqflow.runner.cli import (
    _handle_checkpoint_cmd,
    _handle_trace_cmd,
    _handle_run_graph_cmd,
)


@pytest.fixture
def run_dir(tmp_path):
    """Create a temporary run directory."""
    state = {
        "run_id": "test-run-001",
        "current_stage": "implementation",
        "checkpoints": [
            {"checkpoint_id": "cp-001", "stage": "analysis", "timestamp": "2026-05-14T10:00:00"}
        ],
    }
    (tmp_path / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return str(tmp_path)


def test_checkpoint_list(run_dir, capsys):
    """Test checkpoint list command."""
    args = MagicMock()
    args.run_dir = run_dir
    args.checkpoint_action = "list"
    _handle_checkpoint_cmd(args)
    captured = capsys.readouterr()
    assert "cp-001" in captured.out


def test_trace_summary(run_dir, capsys):
    """Test trace summary command."""
    # Create trace directory
    trace_dir = Path(run_dir) / "traces"
    trace_dir.mkdir()
    trace_data = {"trace_id": "t-001", "name": "flow", "spans": []}
    (trace_dir / "t-001.json").write_text(json.dumps(trace_data))

    args = MagicMock()
    args.run_dir = run_dir
    args.trace_action = "summary"
    _handle_trace_cmd(args)
    captured = capsys.readouterr()
    assert "t-001" in captured.out


def test_checkpoint_missing_run_dir(capsys):
    """Test error when run_dir is missing."""
    args = MagicMock()
    args.run_dir = "/nonexistent"
    args.checkpoint_action = "list"
    _handle_checkpoint_cmd(args)
    captured = capsys.readouterr()
    assert "错误" in captured.err
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd reqflow && python -m pytest tests/test_cli_extensions.py -v
```

Expected: FAIL with "cannot import name '_handle_checkpoint_cmd'"

- [ ] **Step 3: 实现 CLI 扩展**

在 `reqflow/runner/cli.py` 的 `main()` 函数中添加子命令：

```python
# 在 subparsers 添加后，run_parser 之前添加

# reqflow run-graph <workflow>
run_graph_parser = subparsers.add_parser("run-graph", help="执行图编排工作流")
run_graph_parser.add_argument("workflow", help="图工作流名称")
run_graph_parser.add_argument("--requirement", default="", help="需求文本")
run_graph_parser.add_argument("--runtime", default=None, help="Runtime 名称")
run_graph_parser.add_argument("--run-dir", default=None, help="运行目录路径")

# reqflow checkpoint <action>
checkpoint_parser = subparsers.add_parser("checkpoint", help="Checkpoint 管理")
checkpoint_parser.add_argument("checkpoint_action", choices=["list", "create", "restore"], help="操作类型")
checkpoint_parser.add_argument("--run-dir", required=True, help="运行目录路径")
checkpoint_parser.add_argument("--stage", default=None, help="阶段名称（create 时使用）")
checkpoint_parser.add_argument("--checkpoint-id", default=None, help="检查点 ID（restore 时使用）")

# reqflow trace <action>
trace_parser = subparsers.add_parser("trace", help="执行追踪")
trace_parser.add_argument("trace_action", choices=["summary", "export"], help="操作类型")
trace_parser.add_argument("--run-dir", required=True, help="运行目录路径")
trace_parser.add_argument("--output", default=None, help="导出文件路径（export 时使用）")
```

在 `args.command` 分支中添加：

```python
elif args.command == "run-graph":
    asyncio.run(_handle_run_graph_cmd(args))
elif args.command == "checkpoint":
    _handle_checkpoint_cmd(args)
elif args.command == "trace":
    _handle_trace_cmd(args)
```

在子命令实现区域添加：

```python
async def _handle_run_graph_cmd(args: argparse.Namespace) -> None:
    """执行图编排工作流。"""
    from reqflow.core import Engine, RuntimeRegistry

    try:
        registry = RuntimeRegistry()
    except Exception as exc:
        print(f"[错误] 无法加载 runtime 配置: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.runtime:
        try:
            config = registry.get(args.runtime)
        except ValueError as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        config = _detect_runtime(registry)
        if config is None:
            print("[错误] 无法自动检测 runtime，请使用 --runtime 指定。", file=sys.stderr)
            sys.exit(1)

    engine = Engine(config=config, run_dir=args.run_dir)

    try:
        graph = engine.workflow_loader.load_graph(args.workflow)
    except Exception as exc:
        print(f"[错误] 无法加载图工作流 '{args.workflow}': {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[信息] 运行 ID: {engine.run_id}")
    print(f"[信息] Runtime: {config.display_name} ({config.name})")
    print(f"[信息] 图工作流: {args.workflow}")
    print()

    try:
        result = await engine.run_graph(graph)
    except Exception as exc:
        print(f"\n[错误] 图工作流执行失败: {exc}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=" * 60)
    print("图工作流执行完成")
    print("=" * 60)
    print(f"  状态: {result.get('_status', '未知')}")
    for key, value in result.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")
    print(f"\n详细信息请查看: {engine.run_dir}/state.json")


def _handle_checkpoint_cmd(args: argparse.Namespace) -> None:
    """Checkpoint 管理子命令。"""
    from reqflow.core.state_manager import StateManager

    run_dir = args.run_dir
    action = args.checkpoint_action

    try:
        sm = StateManager(run_dir=run_dir)
    except Exception as exc:
        print(f"[错误] 无法初始化 StateManager: {exc}", file=sys.stderr)
        sys.exit(1)

    if action == "list":
        try:
            checkpoints = sm.list_checkpoints()
        except Exception as exc:
            print(f"[错误] 无法列出检查点: {exc}", file=sys.stderr)
            sys.exit(1)

        if not checkpoints:
            print("未找到任何检查点。")
            return

        print(f"检查点 ({len(checkpoints)}):")
        for cp in checkpoints:
            print(f"  - {cp.checkpoint_id[:8]}  阶段: {cp.stage}  时间: {cp.timestamp}")

    elif action == "create":
        stage = args.stage
        if not stage:
            print("[错误] create 操作需要 --stage 参数。", file=sys.stderr)
            sys.exit(1)

        try:
            checkpoint = sm.create_checkpoint(stage=stage, context={})
        except Exception as exc:
            print(f"[错误] 创建检查点失败: {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"已创建检查点: {checkpoint.checkpoint_id}")
        print(f"阶段: {checkpoint.stage}")
        print(f"时间: {checkpoint.timestamp}")

    elif action == "restore":
        checkpoint_id = args.checkpoint_id
        if not checkpoint_id:
            print("[错误] restore 操作需要 --checkpoint-id 参数。", file=sys.stderr)
            sys.exit(1)

        try:
            state, context = sm.restore_checkpoint(checkpoint_id=checkpoint_id)
        except Exception as exc:
            print(f"[错误] 恢复检查点失败: {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"已恢复检查点: {checkpoint_id}")
        print(f"当前阶段: {state.current_stage}")


def _handle_trace_cmd(args: argparse.Namespace) -> None:
    """执行追踪子命令。"""
    run_dir = args.run_dir
    action = args.trace_action

    trace_dir = Path(run_dir) / "traces"
    if not trace_dir.exists():
        print(f"[错误] 未找到追踪目录: {trace_dir}", file=sys.stderr)
        sys.exit(1)

    trace_files = list(trace_dir.glob("*.json"))
    if not trace_files:
        print("未找到任何追踪数据。")
        return

    if action == "summary":
        print(f"追踪数据 ({len(trace_files)} 个):")
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                print(f"  - {data.get('trace_id', '?')}: {data.get('name', '?')}")
                spans = data.get("spans", [])
                print(f"    Spans: {len(spans)}")
            except Exception:
                print(f"  - {tf.name}: (读取失败)")

    elif action == "export":
        output = args.output
        if not output:
            output = str(Path(run_dir) / "trace-export.json")

        all_traces = []
        for tf in trace_files:
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                all_traces.append(data)
            except Exception:
                pass

        Path(output).write_text(json.dumps(all_traces, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已导出 {len(all_traces)} 个追踪到: {output}")
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd reqflow && python -m pytest tests/test_cli_extensions.py -v
```

Expected: PASS (3/3)

- [ ] **Step 5: 提交**

```bash
git add reqflow/runner/cli.py reqflow/tests/test_cli_extensions.py
git commit -m "feat: add run-graph, checkpoint, trace CLI subcommands"
```

---

## Task 8: MCP 配置更新

**Files:**
- Modify: `reqflow/mcp.json`

- [ ] **Step 1: 更新 mcp.json**

```json
{
  "name": "reqflow",
  "version": "2.0.0",
  "description": "ReqFlow 工作流编排引擎 MCP Server",
  "transport": "stdio",
  "command": "python3",
  "args": ["-m", "reqflow.runner.mcp_server"],
  "env": {},
  "tools": [
    {
      "name": "reqflow_run",
      "description": "执行线性工作流（分析 → 实现 → 验证）"
    },
    {
      "name": "reqflow_run_graph",
      "description": "执行图编排工作流（支持分支、并行、human gate）"
    },
    {
      "name": "reqflow_session_save",
      "description": "保存会话上下文（跨轮次持久化）"
    },
    {
      "name": "reqflow_session_load",
      "description": "加载会话上下文"
    },
    {
      "name": "reqflow_status",
      "description": "查询运行状态"
    },
    {
      "name": "reqflow_list_runtimes",
      "description": "列出可用 runtime"
    },
    {
      "name": "reqflow_dashboard",
      "description": "获取格式化运行面板"
    },
    {
      "name": "reqflow_checkpoint",
      "description": "Checkpoint 管理（create/restore/list）"
    },
    {
      "name": "reqflow_parallel",
      "description": "并行 agent 调度"
    },
    {
      "name": "reqflow_trace",
      "description": "执行追踪（summary/export）"
    },
    {
      "name": "reqflow_guardrails",
      "description": "约束检查"
    }
  ]
}
```

- [ ] **Step 2: 验证 JSON 格式**

```bash
python3 -c "import json; json.load(open('reqflow/mcp.json'))" && echo "JSON valid"
```

Expected: "JSON valid"

- [ ] **Step 3: 提交**

```bash
git add reqflow/mcp.json
git commit -m "feat: update mcp.json with new tools"
```

---

## Task 9: Install 脚本

**Files:**
- Create: `reqflow/install.sh`

- [ ] **Step 1: 创建 install.sh**

```bash
#!/usr/bin/env bash
# ReqFlow 安装脚本
# 用法: ./install.sh [claude-code|codex|cursor|copilot|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQFLOW_DIR="$SCRIPT_DIR"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[信息]${NC} $*"; }
warn() { echo -e "${YELLOW}[警告]${NC} $*"; }
error() { echo -e "${RED}[错误]${NC} $*" >&2; }

install_claude_code() {
    local target="$HOME/.claude/plugins/local/reqflow"
    info "安装到 Claude Code: $target"

    mkdir -p "$target"
    cp -r "$REQFLOW_DIR/.claude-plugin" "$target/"
    cp -r "$REQFLOW_DIR/skills" "$target/"
    cp "$REQFLOW_DIR/mcp.json" "$target/"

    # 替换 PLUGIN_DIR
    sed -i '' "s|\${PLUGIN_DIR}|$target|g" "$target/.claude-plugin/plugin.json" 2>/dev/null || true

    info "Claude Code 安装完成"
    echo "  使用方法: 在 Claude Code 中输入 /reqflow:using-reqflow <需求>"
}

install_codex() {
    local target="$HOME/.codex/plugins/reqflow"
    info "安装到 Codex: $target"

    mkdir -p "$target"
    cp -r "$REQFLOW_DIR/.codex-plugin" "$target/"
    cp -r "$REQFLOW_DIR/skills" "$target/"
    cp "$REQFLOW_DIR/mcp.json" "$target/"

    sed -i '' "s|\${PLUGIN_DIR}|$target|g" "$target/.codex-plugin/plugin.json" 2>/dev/null || true

    info "Codex 安装完成"
}

install_cursor() {
    local target="$HOME/.cursor/plugins/reqflow"
    info "安装到 Cursor: $target"

    mkdir -p "$target"
    cp -r "$REQFLOW_DIR/.cursor-plugin" "$target/"
    cp -r "$REQFLOW_DIR/skills" "$target/"
    cp "$REQFLOW_DIR/mcp.json" "$target/"

    sed -i '' "s|\${PLUGIN_DIR}|$target|g" "$target/.cursor-plugin/plugin.json" 2>/dev/null || true

    info "Cursor 安装完成"
}

install_copilot() {
    info "生成 Copilot MCP 配置片段:"
    echo ""
    echo '  在 .vscode/settings.json 中添加:'
    echo '  {'
    echo '    "github.copilot.chat.mcp.servers": {'
    echo '      "reqflow": {'
    echo "        \"command\": \"python3\","
    echo "        \"args\": [\"-m\", \"reqflow.runner.mcp_server\"],"
    echo "        \"cwd\": \"$REQFLOW_DIR\""
    echo '      }'
    echo '    }'
    echo '  }'
    echo ""
}

install_all() {
    install_claude_code
    echo ""
    install_codex
    echo ""
    install_cursor
    echo ""
    install_copilot
}

# 主逻辑
if [ $# -eq 0 ]; then
    echo "用法: $0 [claude-code|codex|cursor|copilot|all]"
    echo ""
    echo "平台:"
    echo "  claude-code  安装到 Claude Code"
    echo "  codex        安装到 Codex"
    echo "  cursor       安装到 Cursor"
    echo "  copilot      生成 Copilot MCP 配置"
    echo "  all          安装到所有平台"
    exit 1
fi

case "$1" in
    claude-code) install_claude_code ;;
    codex)       install_codex ;;
    cursor)      install_cursor ;;
    copilot)     install_copilot ;;
    all)         install_all ;;
    *)
        error "未知平台: $1"
        echo "支持的平台: claude-code, codex, cursor, copilot, all"
        exit 1
        ;;
esac
```

- [ ] **Step 2: 设置可执行权限**

```bash
chmod +x reqflow/install.sh
```

- [ ] **Step 3: 验证脚本语法**

```bash
bash -n reqflow/install.sh && echo "Syntax OK"
```

Expected: "Syntax OK"

- [ ] **Step 4: 提交**

```bash
git add reqflow/install.sh
git commit -m "feat: add install.sh for multi-platform plugin installation"
```

---

## Task 10: 清理重复模块

**Files:**
- Delete: `reqflow/runtime/runtime_config.py`
- Delete: `reqflow/runtime/registry.py`

- [ ] **Step 1: 确认 core/ 模块存在**

```bash
ls -la reqflow/core/runtime_config.py reqflow/core/registry.py
```

Expected: 两个文件都存在

- [ ] **Step 2: 检查 runtime/ 模块是否有其他引用**

```bash
grep -r "from reqflow.runtime" reqflow/ --include="*.py" || echo "No references found"
```

Expected: "No references found" 或只有 runtime/ 内部引用

- [ ] **Step 3: 删除重复模块**

```bash
rm reqflow/runtime/runtime_config.py reqflow/runtime/registry.py
```

- [ ] **Step 4: 验证 providers/ 目录保留**

```bash
ls -la reqflow/runtime/providers/
```

Expected: providers/ 目录和 YAML 文件仍然存在

- [ ] **Step 5: 运行测试确保无破坏**

```bash
cd reqflow && python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: 所有测试通过

- [ ] **Step 6: 提交**

```bash
git add -A reqflow/runtime/
git commit -m "chore: remove duplicate runtime modules, keep providers/"
```

---

## Task 11: 最终验证

- [ ] **Step 1: 运行完整测试套件**

```bash
cd reqflow && python -m pytest tests/ -v
```

Expected: 所有测试通过

- [ ] **Step 2: 验证 MCP 工具数量**

```bash
python3 -c "
import json
with open('reqflow/mcp.json') as f:
    data = json.load(f)
print(f'MCP 工具数量: {len(data[\"tools\"])}')
for t in data['tools']:
    print(f'  - {t[\"name\"]}')
"
```

Expected: 11 个工具

- [ ] **Step 3: 验证 Skills 数量**

```bash
ls reqflow/skills/*.md | wc -l
```

Expected: 8 个 skill 文件

- [ ] **Step 4: 验证 Plugin 文件**

```bash
ls reqflow/.claude-plugin/plugin.json reqflow/.codex-plugin/plugin.json reqflow/.cursor-plugin/plugin.json
```

Expected: 3 个 plugin.json 文件

- [ ] **Step 5: 验证 Install 脚本**

```bash
bash -n reqflow/install.sh && echo "Install script syntax OK"
```

Expected: "Install script syntax OK"

- [ ] **Step 6: 最终提交**

```bash
git add -A
git commit -m "feat: complete ReqFlow entry point system"
```
