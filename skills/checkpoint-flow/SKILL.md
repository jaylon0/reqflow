---
name: checkpoint-flow
description: Use when needing to create, restore, or list checkpoints - supports session persistence and resumable workflows
---

# checkpoint-flow

Checkpoint 管理 skill。用于创建、恢复和列出检查点。

## 触发方式

```
/reqflow:checkpoint-flow list --run-dir /tmp/reqflow-run
/reqflow:checkpoint-flow create --stage implementation
/reqflow:checkpoint-flow restore --checkpoint-id cp-001
```

## 功能

### 列出检查点

调用 `reqflow_checkpoint` 工具，action 为 "list"：

```
调用 reqflow_checkpoint，run_dir 是 "/tmp/reqflow-run"，action 是 "list"
```

### 创建检查点

调用 `reqflow_checkpoint` 工具，action 为 "create"：

```
调用 reqflow_checkpoint，run_dir 是 "/tmp/reqflow-run"，action 是 "create"，stage 是 "implementation"
```

### 恢复检查点

调用 `reqflow_checkpoint` 工具，action 为 "restore"：

```
调用 reqflow_checkpoint，run_dir 是 "/tmp/reqflow-run"，action 是 "restore"，checkpoint_id 是 "cp-001"
```

## 使用场景

- 长时间运行的工作流，需要中途保存进度
- 执行失败后，从最近的检查点恢复
- 查看历史检查点，了解执行进度
