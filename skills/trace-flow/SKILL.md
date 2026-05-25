---
name: trace-flow
description: Use when needing to view or export execution trace data and timeline from workflow runs
---

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
