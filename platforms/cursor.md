# Cursor 接入 ReqFlow

## MCP Server 方式

在 Cursor 设置中（Settings → MCP）添加：

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

## 在 Cursor 中使用

Cursor Agent 模式会自动发现 MCP 工具。

直接对话：
```
使用 reqflow 帮我分析 MathExpress.java 的代码结构
```

或指定工具：
```
调用 reqflow_run，requirement 是 "为 MathExpress 添加幂运算支持"，workflow 是 "flow"
```

## 直接读取 AGENT.md

Cursor 可以直接读取 `reqflow/AGENT.md` 理解如何调用：

```
读取 /Users/yuanjulong/Documents/ai_flow/reqflow/AGENT.md，
然后按照其中的 Python API 说明执行工作流
```
