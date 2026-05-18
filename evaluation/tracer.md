# Execution Tracer

执行追踪系统，参考 OpenAI Agents SDK 的 hierarchical trace/span 模型。

## Trace 结构

```yaml
trace:
  run_id: <id>
  spans:
    - span_id: <id>
      parent_id: <parent>
      name: "agent.dev-agent.work-item-3"
      input: <context_pack>
      output: <dev_report>
      duration_ms: <n>
      tokens: {input: <n>, output: <n>}
      status: success|failure
```

## 职责

- 记录每次 agent 调用的输入、输出、耗时、token 用量
- 支持 trace 导出用于调试和优化
- 与 state 层的 session 配合，提供完整的执行历史
