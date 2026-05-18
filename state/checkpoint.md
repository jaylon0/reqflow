# Checkpoint System

检查点恢复机制，参考 CrewAI 的 checkpointing 设计。

## 职责

- 每个 stage 完成后自动创建 checkpoint
- 支持从任意 checkpoint resume
- checkpoint 包含 state + context + log

## Checkpoint 结构

```yaml
checkpoint:
  checkpoint_id: <uuid>
  run_id: <run_id>
  stage: <stage_name>
  timestamp: <timestamp>
  state_snapshot: .dev-workflow/runs/<run_id>/checkpoints/<id>/state.json
  context_snapshot: .dev-workflow/runs/<run_id>/checkpoints/<id>/context.json
  log_snapshot: .dev-workflow/runs/<run_id>/checkpoints/<id>/execution.log
```

## Resume 流程

1. 加载指定 checkpoint 的 state_snapshot
2. 恢复 context_snapshot
3. 从该 stage 继续执行
