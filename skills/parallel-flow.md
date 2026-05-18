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
