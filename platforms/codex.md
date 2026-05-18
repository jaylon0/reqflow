# Codex CLI 接入 ReqFlow

## MCP Server 方式

在 Codex 配置中添加 MCP server：

```json
{
  "mcpServers": {
    "reqflow": {
      "command": "python3",
      "args": ["-m", "reqflow.runner.mcp_server"],
      "cwd": "/Users/yuanjulong/Documents/ai_flow"
    }
  }
}
```

## 直接使用

Codex 可以直接读取 `AGENT.md` 和源码：

```
读取 /Users/yuanjulong/Documents/ai_flow/reqflow/AGENT.md，
然后使用 reqflow 的 Python API 执行 flow 工作流，
需求是：为 MathExpress 添加幂运算支持
```

## Python API 调用

```python
import asyncio
from reqflow.core import Engine, RuntimeRegistry

async def main():
    registry = RuntimeRegistry()
    config = registry.get("manual")
    engine = Engine(config=config, run_dir="/tmp/reqflow-codex-run")
    result = await engine.run_workflow_by_name("flow", requirement="...")
    print(result["status"])

asyncio.run(main())
```
