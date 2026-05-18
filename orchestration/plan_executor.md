# Plan Executor

计划编写与执行方法论，吸收自 superpowers writing-plans + executing-plans + dispatching-parallel-agents。

> 原始 skill 参考: `_external/dispatching-parallel-agents/SKILL.md`

## 计划编写原则

1. 每个步骤是单一动作（2-5分钟）
2. 包含完整代码，不留占位符
3. 精确文件路径
4. 精确命令和预期输出

## 执行模式

### 串行执行（默认）
按任务顺序逐个执行，每个任务完成后验证再继续。

### 并行执行 -- Dispatching Parallel Agents

**核心原则：** 每个独立问题域分配一个 agent。让它们并发工作。

#### 何时使用

**使用场景：**
- 3+ 个测试文件因不同根因失败
- 多个子系统独立故障
- 每个问题可以在没有其他问题上下文的情况下理解
- 调查之间没有共享状态

**不使用场景：**
- 故障相关（修一个可能修其他）
- 需要理解完整系统状态
- Agent 会互相干扰（编辑相同文件、使用相同资源）
- 探索性调试 -- 你还不知道什么坏了

#### 四步模式

**Step 1: 识别独立域**

按故障分组：
- File A tests: Tool approval flow
- File B tests: Batch completion behavior
- File C tests: Abort functionality

每个域独立 -- 修复 tool approval 不影响 abort tests。

**Step 2: 创建聚焦的 Agent 任务**

每个 agent 获得：
- **特定范围：** 一个测试文件或子系统
- **清晰目标：** 让这些测试通过
- **约束：** 不改其他代码
- **预期输出：** 发现和修复的摘要

**Step 3: 并行调度**

```python
async def dispatch_parallel(items, coordinator):
    tasks = [coordinator.dispatch(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

**Step 4: 审查与集成**

Agent 返回后：
- 读每个摘要
- 验证修复不冲突
- 运行完整测试套件
- 集成所有变更

#### Agent Prompt 结构

好的 agent prompt 是：
1. **聚焦** -- 一个清晰的问题域
2. **自包含** -- 理解问题所需的所有上下文
3. **输出明确** -- agent 应该返回什么？

```markdown
Fix the 3 failing tests in src/agents/agent-tool-abort.test.ts:

1. "should abort tool with partial output capture" - expects 'interrupted at' in message
2. "should handle mixed completed and aborted tools" - fast tool aborted instead of completed
3. "should properly track pendingToolCount" - expects 3 results but gets 0

These are timing/race condition issues. Your task:

1. Read the test file and understand what each test verifies
2. Identify root cause - timing issues or actual bugs?
3. Fix by:
   - Replacing arbitrary timeouts with event-based waiting
   - Fixing bugs in abort implementation if found
   - Adjusting test expectations if testing changed behavior

Do NOT just increase timeouts - find the real issue.

Return: Summary of what you found and what you fixed.
```

#### 常见错误

| 错误 | 正确做法 |
|------|---------|
| **太宽泛:** "Fix all the tests" | **具体:** "Fix agent-tool-abort.test.ts" |
| **无上下文:** "Fix the race condition" | **有上下文:** 粘贴错误信息和测试名 |
| **无约束:** Agent 可能重构一切 | **有约束:** "Do NOT change production code" |
| **模糊输出:** "Fix it" | **明确:** "Return summary of root cause and changes" |

#### 并行调度验证

Agent 返回后：
1. **审查每个摘要** -- 理解什么变了
2. **检查冲突** -- Agent 是否编辑了相同代码？
3. **运行完整套件** -- 验证所有修复一起工作
4. **抽查** -- Agent 可能犯系统性错误

## 检查点

每个任务完成后自动创建 checkpoint，支持从任意点 resume。
