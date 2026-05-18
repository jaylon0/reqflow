# Claude Code 接入 ReqFlow

## 方式 1: MCP Server（推荐）

在 `~/.claude/settings.json` 中添加：

```json
{
  "mcpServers": {
    "reqflow": {
      "command": "python3",
      "args": ["-m", "reqflow.runner.mcp_server"],
      "cwd": "/Users/yuanjulong/Documents/ai_flow",
      "env": {}
    }
  }
}
```

重启 Claude Code 后，可用以下工具：
- `reqflow_run` — 执行工作流
- `reqflow_run_graph` — 图编排工作流
- `reqflow_session_save/load` — 会话持久化
- `reqflow_status` — 查看状态
- `reqflow_dashboard` — 格式化面板

## 方式 2: Skill 文件

将 `reqflow/skills/` 目录链接到 Claude Code 插件目录：

```bash
ln -s /Users/yuanjulong/Documents/ai_flow/reqflow/skills \
      ~/.claude/plugins/cache/local-requirement-flow/requirement-flow-plugin/2.0.0/skills
```

然后可用：
- `/reqflow:requirement-flow <需求>`
- `/reqflow:main-flow <PRD>`
- `/reqflow:graph-flow <工作流>`
- `/reqflow:dashboard <run-dir>`

## 方式 3: 直接对话

直接告诉 Claude Code：

```
使用 reqflow 的 Python API 帮我执行一个工作流：
1. 从 reqflow/workflows/flow.yaml 加载工作流
2. 用 manual runtime 执行
3. 需求是：为 MathExpress 添加幂运算支持
```

Claude Code 会自己读 AGENT.md 和源码来理解如何调用。
