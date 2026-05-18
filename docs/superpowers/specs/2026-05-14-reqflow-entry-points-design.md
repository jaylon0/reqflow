# ReqFlow 入口体系设计

## 概述

ReqFlow 需要暴露统一的入口体系，支持多种 agent 平台（Claude Code、Codex、Cursor、Copilot 等）。核心目标：

1. **Plugin 入口**（最深）— slash 命令 + 自然语言触发 + MCP 工具
2. **MCP 入口** — 独立 MCP 配置，任何支持 MCP 的 agent
3. **Python API 入口** — 直接调用 `Engine`
4. **CLI 入口** — `python -m reqflow.runner.cli`

## 架构方案

采用 **统一 Plugin + 独立 Install 脚本** 方案（方案 A）：

- 每个平台有独立的 plugin 目录
- 安装脚本将 plugin 文件拷贝到用户机器上对应的位置（拷贝，不链接）
- 用户安装后可以删除原项目目录

## Plugin 结构

### 目录布局

```
reqflow/
├── .claude-plugin/
│   └── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── .cursor-plugin/
│   └── plugin.json
├── skills/
│   ├── using-reqflow.md
│   ├── requirement-flow.md
│   ├── main-flow.md
│   ├── graph-flow.md
│   ├── dashboard.md
│   ├── checkpoint-flow.md
│   ├── parallel-flow.md
│   └── trace-flow.md
├── install.sh
├── mcp.json
└── ...
```

### plugin.json 设计

**Claude Code:**
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

**Codex:**
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

**Cursor:**
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

## Install Script

### 用法

```bash
# 安装到指定平台
./install.sh claude-code
./install.sh codex
./install.sh cursor
./install.sh copilot

# 安装所有平台
./install.sh all
```

### 安装目标路径

| 平台 | 目标路径 |
|------|---------|
| Claude Code | `~/.claude/plugins/local/reqflow/` |
| Codex | `~/.codex/plugins/reqflow/` |
| Cursor | `~/.cursor/plugins/reqflow/` |
| Copilot | 生成 `.vscode/settings.json` 片段 |

### 安装过程

1. 拷贝 plugin 目录到目标路径（拷贝，不链接）
2. 拷贝 skills 目录
3. 替换 `${PLUGIN_DIR}` 为实际安装路径
4. 拷贝 reqflow Python 包（或提示 pip install）
5. 替换所有 `${PLUGIN_DIR}` 占位符为实际安装路径（sed 替换）
6. 打印安装成功信息和使用说明

## using-reqflow 主流程

### 流程设计

```
using-reqflow
├── 1. 项目上下文扫描（context-bootstrap）
├── 2. 需求分析与分解（requirement-analysis）
├── 3. 工作流选择（workflow-selection）
│   ├── 线性工作流（flow.yaml）
│   ├── 图编排工作流（graph-*.yaml）
│   └── 自定义工作流
├── 4. 执行工作流（engine.run / engine.run_graph）
├── 5. 结果验证（verification）
└── 6. 交付报告（dashboard）
```

### 触发方式

**自然语言触发：**
```
使用 reqflow 帮我处理这个需求：为 MathExpress 添加幂运算支持
```

**Slash 命令触发：**
```
/reqflow:using-reqflow 为 MathExpress 添加幂运算支持
```

**MCP 工具触发：**
```
调用 reqflow_run，requirement 是 "为 MathExpress 添加幂运算支持"，workflow 是 "flow"
```

## 调用链路架构

```
用户触发 (slash 命令 / 自然语言 / MCP 工具)
    │
    ▼
┌─────────────────────────────────────────┐
│ Skill 层 (using-reqflow.md)             │  ← 纯流程指令 (markdown)
│ 告诉 agent 做什么、按什么顺序            │
└─────────────────────────────────────────┘
    │
    ▼ 调用
┌─────────────────────────────────────────┐
│ MCP 工具层 (reqflow_run 等)             │  ← Python 代码执行
│ mcp_server.py → Engine → 具体模块       │
└─────────────────────────────────────────┘
    │
    ▼ 执行
┌─────────────────────────────────────────┐
│ Core 层 (Engine, Graph, Session 等)     │  ← 核心逻辑
│ workflow_loader, guardrails, tracer     │
└─────────────────────────────────────────┘
```

**两种模式：**

- **MCP 驱动**：agent 调用 MCP 工具 → 执行 Python 代码 → 返回结果
- **Skill 驱动**：agent 按指令行动 → 可调用 MCP 工具辅助 → 也可直接操作

`using-reqflow` 是 Skill 驱动的主入口，内部调用 MCP 工具执行实际工作流。

## MCP 配置

### MCP 工具列表（完整）

**基础工具：**

| 工具名 | 描述 |
|--------|------|
| `reqflow_run` | 执行线性工作流 |
| `reqflow_run_graph` | 执行图编排工作流 |
| `reqflow_session_save` | 保存会话上下文 |
| `reqflow_session_load` | 加载会话上下文 |
| `reqflow_status` | 查询运行状态 |
| `reqflow_list_runtimes` | 列出可用 runtime |
| `reqflow_dashboard` | 获取格式化运行面板 |

**新增工具：**

| 工具名 | 描述 |
|--------|------|
| `reqflow_checkpoint` | Checkpoint 管理 (create/restore/list) |
| `reqflow_parallel` | 并行 agent 调度 |
| `reqflow_trace` | Trace 导出/摘要 |
| `reqflow_loop` | 循环子图执行 |
| `reqflow_guardrails` | 约束检查 |

### MCP 配置方式

**嵌入 plugin.json（推荐）：**
```json
{
  "mcp": {
    "command": "python3",
    "args": ["-m", "reqflow.runner.mcp_server"],
    "cwd": "${PLUGIN_DIR}"
  }
}
```

**独立 mcp.json（备用）：**
```json
{
  "name": "reqflow",
  "transport": "stdio",
  "command": "python3",
  "args": ["-m", "reqflow.runner.mcp_server"],
  "cwd": "/path/to/reqflow"
}
```

## Python API

```python
import asyncio
from reqflow.core import Engine, RuntimeRegistry

async def main():
    registry = RuntimeRegistry()
    config = registry.get("manual")
    engine = Engine(config=config)
    result = await engine.run_workflow_by_name("flow", requirement="...")
    print(result["status"])

asyncio.run(main())
```

## CLI

```bash
# 线性工作流
python -m reqflow.runner.cli run --workflow flow --requirement "为 MathExpress 添加幂运算支持"

# 图编排工作流
python -m reqflow.runner.cli run-graph --workflow graph-example --requirement "分析需求"

# Checkpoint 管理
python -m reqflow.runner.cli checkpoint list --run-dir /tmp/reqflow-run
python -m reqflow.runner.cli checkpoint create --stage "implementation"
python -m reqflow.runner.cli checkpoint restore --checkpoint-id cp-001

# Trace 查看
python -m reqflow.runner.cli trace summary --run-dir /tmp/reqflow-run
python -m reqflow.runner.cli trace export --run-dir /tmp/reqflow-run --output trace.json
```

## 多平台支持

| 平台 | 入口方式 |
|------|---------|
| Claude Code | Plugin（slash 命令 + 自然语言）+ MCP |
| Codex | Plugin + MCP |
| Cursor | Plugin + MCP |
| Copilot | MCP（VS Code 配置）|
| 其他 MCP agent | MCP 配置 |

## 清理项

**文件清理：**
- `__pycache__/` — Python 编译缓存
- `.pytest_cache/` — 测试缓存
- `.DS_Store` — macOS 系统文件
- `2026-05-14-111843-this-session-is-being-continued-from-a-previous-c.txt` — 上下文恢复文件
- `.codeflicker/` — 不确定用途，待确认

**模块清理：**
- `reqflow/runtime/runtime_config.py` — 与 `reqflow/core/runtime_config.py` 重复，删除
- `reqflow/runtime/registry.py` — 与 `reqflow/core/registry.py` 重复，删除
- `reqflow/runtime/` — 保留 `providers/` 目录（YAML 配置），删除 Python 模块

**待实现：**
- `mcp_bridge.py` — 当前是 stub，需要实现或标记为 experimental
