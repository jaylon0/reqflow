---
name: requirement-flow
description: >
  ReqFlow 主入口。接收需求、PRD、issue、bug、重构请求，自动路由到合适的执行级别。
  支持 Claude Code、Codex、Copilot、Cursor 等任意 Agent 平台。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
---

# requirement-flow

ReqFlow V2 主入口 skill。接收用户需求，自动路由到合适的执行级别。

## 触发方式

**Claude Code:**
```
/reqflow:requirement-flow <需求描述>
```

**Codex / Copilot / Cursor (通过 MCP):**
```
reqflow_run(requirement="<需求描述>", workflow="flow")
```

**自然语言触发:**
- "分析一下这个需求"
- "帮我实现这个功能"
- "做个修改计划再动手"
- "跑完整流程"
- "修个 bug"

## 路由级别

### L0 - 只读分析
- 只检查，不修改
- 输出分析结果和建议

### L1 - 轻量修改
- 单文件、低风险
- 直接实现 + 局部检查

### L2 - 计划性修改
- 多文件功能开发
- 先出计划 → 确认 → 实现 → 验证

### L3 - 交付循环
- API/DB/消息/安全相关变更
- 计划 → 实现 → 构建 → 部署 → 验证 → 修复循环

## V2 新能力

### Graph 编排
支持分支、条件路由、并行 fan-out、human gate：
```python
from reqflow.core.graph import Node, Edge, Graph, GraphEngine

graph = Graph(
    nodes={"analyze": ..., "gate": ..., "implement": ..., "verify": ...},
    edges=[
        Edge(source="analyze", target="gate"),
        Edge(source="gate", target="implement", condition=lambda s: s.get("confidence", 0) >= 0.7),
        Edge(source="gate", target="clarify", condition=lambda s: s.get("confidence", 0) < 0.7),
    ],
    entry="analyze",
    exit=["verify"],
)
engine = Engine(config=config)
result = await engine.run_graph(graph)
```

### Session 持久化
跨轮次上下文保存：
```python
from reqflow.core.session import Session

session = Session(session_id="my-project", storage_dir=".reqflow/sessions")
session.save_context("requirement", "添加幂运算支持")
session.save_context("target_file", "MathExpress.java")
session.save()

# 下次恢复
session2 = Session(session_id="my-project", storage_dir=".reqflow/sessions")
session2.load()
print(session2.get_context("requirement"))
```

### MCP 工具桥接
连接外部 MCP 服务器获取工具：
```python
from reqflow.core.mcp_bridge import MCPBridge, MCPServerConfig

bridge = MCPBridge([MCPServerConfig(name="db", command="mcp-server-pg", args=["--conn", "..."])])
tools = await bridge.discover_tools()
```

### 并行 Agent 调度
```python
results = await engine.dispatch_parallel([
    {"name": "verify", "handler": verify_agent, "prompt": "验证代码"},
    {"name": "review", "handler": review_agent, "prompt": "审查代码"},
])
```

## 使用 ReqFlow Core Engine

### 1. 选择 Runtime
```python
from reqflow.core import RuntimeRegistry
registry = RuntimeRegistry()
config = registry.get("manual")  # 或 "gpt", "gemini", "deepseek"
```

### 2. 创建 Engine
```python
from reqflow.core import Engine
engine = Engine(config=config, run_dir=".reqflow/runs/<run-id>")
```

### 3. 执行工作流
```python
# 线性工作流
result = await engine.run_workflow_by_name("flow", requirement="用户需求")

# 图工作流
graph = engine.workflow_loader.load_graph("graph-example")
result = await engine.run_graph(graph)
```

## 强制规则

- 先路由，再执行
- L2/L3 必须先展示计划并获得确认
- 外部写操作必须等待确认
- 同一失败指纹出现两次时停止自动重试
- 秘钥不得写入项目文件

## 输出格式

```
REQUIREMENT_FLOW_STATUS: analyzed|implemented|delivered|blocked
ROUTE_LEVEL: L0|L1|L2|L3
SUMMARY:
- <简明结果>
NEXT_ACTION:
- <用户需要的下一步操作>
```
