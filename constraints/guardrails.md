# Guardrails

并行约束验证 + 快速失败机制，参考 OpenAI Agents SDK。

## 设计

约束检查与 agent 执行并行运行，检查不通过时立即失败，不等 agent 完成。

## 执行模式

```python
async def run_with_guardrails(agent_task, constraints):
    agent_result, constraint_results = await asyncio.gather(
        agent_task,
        run_constraints(constraints)
    )
    if any_failed(constraint_results):
        return FAIL_FAST
    return agent_result
```

## 约束类型

| 约束 | 检查时机 | 失败行为 |
|------|---------|---------|
| constitution | 每次 agent 调用前 | 立即阻断 |
| file_boundary | 每次文件编辑时 | 立即阻断 |
| design_gate | 实现前 | 需要审批 |
| tdd_gate | 行为变更前 | 提示使用 TDD |
