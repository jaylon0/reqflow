# GitHub Copilot 接入 ReqFlow

## MCP Server 方式

GitHub Copilot 支持 MCP 工具。在 `.vscode/settings.json` 或 Copilot 配置中添加：

```json
{
  "github.copilot.chat.mcp.servers": {
    "reqflow": {
      "command": "python3",
      "args": ["-m", "reqflow.runner.mcp_server"],
      "cwd": "/Users/yuanjulong/Documents/ai_flow"
    }
  }
}
```

## 在 Copilot Chat 中使用

```
@reqflow 为 MathExpress 类添加幂运算支持
```

或：

```
使用 reqflow_run 工具，requirement 是 "为 MathExpress 添加幂运算支持"，workflow 是 "flow"
```

## Agent 模式

在 Copilot Agent 模式下，Copilot 会自动发现 MCP 工具并调用。

## 直接调用 Python API

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
