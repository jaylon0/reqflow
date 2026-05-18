# Session Management

会话级持久上下文管理，维护 agent loop 内的工作状态。

## 职责

- 管理当前会话的工作上下文
- 维护跨轮次的对话历史摘要
- 支持子智能体 resume 时的上下文恢复

## 会话状态

```yaml
session:
  session_id: <uuid>
  working_context:
    current_task: <task_description>
    relevant_files: []
    decisions_made: []
  conversation_summary: ""
  created_at: <timestamp>
  last_active: <timestamp>
```

## 与 state.json 的关系

- state.json 是 run 级别的持久状态
- session 是会话级别的工作上下文
- session 在 run 结束后可选择保留或丢弃
