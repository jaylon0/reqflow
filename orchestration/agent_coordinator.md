---
name: agent-coordinator
description: >
  Coordinates supervised agent execution for Java backend work items.
  Dispatches dev, verify, and review subagents using the Agent tool.
  Manages bounded repair loops. Use when main-flow Step 7
  begins and agent/work_items.json exists.
---

> `{baseDir}` means this skill directory. `{pluginRoot}` means `{baseDir}/../..`.

# agent-coordinator

Supervised agent execution coordinator. Dispatches dev, verify, and review
subagents for each work item. Manages bounded repair loops.

本模块整合了 subagent-driven-development 的调度模式。

> 原始 skill 参考: `_external/subagent-driven-development/SKILL.md`

## Subagent 调度模式（来自 subagent-driven-development）

### 核心原则

每个任务分配一个全新 subagent，配合两阶段审查（spec compliance + code quality）= 高质量、快速迭代。

**为什么用 subagent：** 将任务委托给具有隔离上下文的专门 agent。通过精确构造指令和上下文，确保它们保持专注并成功完成任务。它们不应继承你的会话上下文或历史 -- 你精确构造它们需要的内容。这也为你自己的协调工作保留上下文。

**连续执行：** 不要在任务之间暂停与人类伙伴确认。执行计划中的所有任务，不要停止。唯一停止的原因是：无法解决的 BLOCKED 状态、真正阻止进展的歧义、或所有任务完成。

### Subagent 状态处理

实现者 subagent 报告四种状态之一：

- **DONE**: 进入 spec compliance review
- **DONE_WITH_CONCERNS**: 实现者完成工作但标记了疑虑。先读取疑虑再继续。如果关于正确性或范围，在审查前解决。如果是观察（如"文件变大了"），记录并继续审查
- **NEEDS_CONTEXT**: 实现者需要未提供的信息。提供缺失上下文并重新调度
- **BLOCKED**: 实现者无法完成任务。评估阻塞原因：
  1. 上下文问题 -> 提供更多上下文，用相同模型重新调度
  2. 需要更多推理 -> 用更强大的模型重新调度
  3. 任务太大 -> 拆分为更小的部分
  4. 计划本身有误 -> 上升给人类

**绝不** 忽略升级或强制相同模型无变更重试。如果实现者说卡住了，某些东西需要改变。

### 模型选择

使用能处理每个角色的最不强大模型来节省成本和提高速度。

- **机械实现任务**（隔离函数、清晰 spec、1-2 个文件）：用快速便宜模型
- **集成和判断任务**（多文件协调、模式匹配、调试）：用标准模型
- **架构、设计和审查任务**：用最强大的可用模型

### 两阶段审查

1. **Spec Compliance Review** -- 代码是否匹配规格？不多不少
2. **Code Quality Review** -- 实现是否良好构建？

**审查流程：**
- Spec reviewer 发现问题 -> 实现者修复 -> spec reviewer 再审查
- Code quality reviewer 发现问题 -> 实现者修复 -> code quality reviewer 再审查
- 直到两个审查都通过才标记任务完成

**绝不：**
- 跳过审查（spec compliance 或 code quality）
- 在 spec compliance 通过前开始 code quality review
- 在任一审查有开放问题时进入下一个任务
- 让实现者自审替代实际审查（两者都需要）

## Mandatory Rules

- Do not edit production source code from the coordinator role.
- Dispatch subagents using the Agent tool (subagent_type=claude).
- Do NOT read subagent internal conversation content -- only use structured results.
- Verify and review agents dispatch in parallel after dev completes.
- Repair dispatches a new dev agent with prior findings in the prompt.
- Update state.json and agent/main-log.md after every dispatch/complete/repair.
- Update dispatch_history in state.json.agent_execution after each dispatch.
- Max repair rounds: read from state.json.agent_execution.max_repair_rounds (default 3).
- Mark work item as fail when max repair rounds exceeded.
- Write structured reports to agent/reports/<item-id>/.

## Iron Laws

1. **File-as-Memory:** All agent outputs must be persisted to files. Do not rely on conversation context for state. Work items, reports, and lessons must be written to `agent/` artifacts.

2. **Isolation-as-Norm:** Each subagent sees only what the coordinator provides in its prompt. Do not assume subagents have knowledge of other agents' work, prior conversations, or external state. Pass file paths, not file contents, in prompts.

3. **Log-as-Insurance:** Write to `agent/main-log.md` after every dispatch, completion, and repair. Timestamp format: ISO 8601. This log is the single source of truth for debugging agent execution.

## Coordinator Discipline

The coordinator is an orchestrator, not an implementor:

- **Do NOT** read subagent output file contents -- extract status from structured output only
- **Do NOT** edit production source code -- dispatch to dev agent
- **Do NOT** run tests yourself -- dispatch to verify agent
- **Do NOT** review code yourself -- dispatch to review agent
- **DO** maintain state.json, main-log.md, and work_items.json
- **DO** route information between agents (test results -> repair prompt)
- **DO** make go/no-go decisions based on structured outputs

Context protection: passing file paths instead of file contents keeps the coordinator's context window clean. If a subagent needs to read a file, give it the path -- don't read and paste the content.

## Prompt Construction Rules

When building prompts for subagents, follow these rules:

1. **Pass paths, not contents:** Include file paths in the prompt. Let the subagent read the file itself. Never paste file contents into the prompt.

2. **Pass only what's needed:** A dev agent needs: work item JSON, context pack path, coding standards path. It does NOT need: other work items' status, state.json internals, or coordinator logs.

3. **Structured instruction:** Each prompt must include:
   - Clear task description (what to do)
   - Input file paths (where to read)
   - Output format (what to return)
   - Constraints (what NOT to do)

4. **Repair prompts are minimal:** When resuming for repair, only include the specific failures/findings. Do not re-describe the original task -- the agent remembers.

## Work Item States

```text
pending | in_progress | pass | fail | blocked | low_quality_pass
```

`low_quality_pass` is allowed only after max repair rounds and must be recorded
as a risk in `agent/compliance-report.md`.

## Agent Templates

| Agent | Template | Role |
|-------|----------|------|
| dev-agent | `agents/java-module-dev-agent.md` | Implement one work item |
| verify-agent | `agents/java-module-verify-agent.md` | Read-only verification |
| review-agent | `agents/java-module-review-agent.md` | Read-only code review |
| repair-agent | `agents/repair-agent.md` | Fix specific failures from verify/review |
| context-agent | `agents/context-agent.md` | Build context pack for work item |
| intelligence-agent | `agents/intelligence-agent.md` | Scenario detection, work item decomposition |
| spec-agent | `agents/spec-agent.md` | Delta spec creation, constitution check |

## Per-Work-Item Loop

For each item in agent/work_items.json with status "pending":

### 0. Build Context (Optional)

If context pack does not exist for this work item:
- Dispatch context-agent to build it:
  ```
  Agent(
    description="Context: {item_id}",
    prompt="Build context pack for work item {item_id}. Read agent/work_items.json for details.",
    subagent_type="claude",
    model="haiku"
  )
  ```
- Store output at `agent/context-packs/<item-id>.md`

### 1. Initialize

- Read agent/work_items.json
- For the current work item, set status to "in_progress"
- Create report directory: agent/reports/<item-id>/
- Read context pack from agent/context-packs/<id>.md if it exists
- Write dispatch log: action=init, summary="Starting {item_id}"

### 2. Dispatch Dev Agent

- Load prompt template from `{baseDir}/prompts/dev-agent.md`
- Replace template variables: {work_item_json}, {context_pack_content}, {coding_standards}
- {coding_standards}: Load from plugin's coding-standards skill if available,
  otherwise use project's CLAUDE.md or AGENTS.md coding guidelines
- Model selection:
  - Use "opus" if: scenario involves database schema changes, multi-service coordination,
    security-sensitive code, or >5 acceptance criteria
  - Use "sonnet" for: standard API changes, simple service logic, test additions,
    or <=5 acceptance criteria
- Dispatch via Agent tool:
  ```
  Agent(
    description="Dev: {item_id} -- {title}",
    prompt=<filled dev-agent.md>,
    subagent_type="claude",
    model=<selected model>
  )
  ```
- Record agent_id from result
- Write dispatch log: action=dev-dispatch, agent_id=<id>
- Update work item execution_record.dev_agent_id
- **Capture agent_id** from the Agent tool result -- this is required for resume-based repair loops
- Store in work item: `execution_record.dev_agent_id = agent_id`

> **Note:** Prompt templates (`prompts/dev-agent.md`, `prompts/verify-agent.md`,
> `prompts/review-agent.md`) are created in a separate task. If they do not
> exist yet, construct the prompts inline using the template variable descriptions
> in this skill.

**If dev agent returns status=failed:**
- Record the failure in dispatch log
- Route to Repair Loop (section 5) with the dev failure as the finding

### 3. Dispatch Verify + Review (Parallel)

After dev agent returns with status=success:

**Verify agent:**
- Load prompt template from `{baseDir}/prompts/verify-agent.md`
- Replace: {work_item_json}, {files_changed}
- Dispatch via Agent tool
- Record agent_id

**Review agent:**
- Load prompt template from `{baseDir}/prompts/review-agent.md`
- Replace: {work_item_json}, {files_changed}
- Dispatch via Agent tool
- Record agent_id

Both dispatch in a single message with two Agent tool calls.

### 4. Evaluate Results

Collect structured JSON results from both agents.

**Pass conditions:**
- verify agent: status=pass AND build_result=pass AND test_result=pass
- review agent: status=pass AND spec_compliance.status=pass AND code_quality.status=pass

**If all pass:**
- Update work item status to pass
- Write JSON reports: agent/reports/<item-id>/dev.json, verify.json, review.json
- Update the .md report stubs (dev-report.md, verify-report.md, review-report.md) with results
- Write dispatch log: action=complete

**If any fail:**
- Go to Repair Loop (section 5)

### 4b. Update Lessons Learned

After a work item completes (pass or fail):
- Read existing `agent/lessons-learned.md`
- If the work item had repair rounds, extract the root cause pattern
- Append new lesson if the pattern is reusable (not project-specific)
- Format: `- [{item_id}] {lesson description}`
- Skip if no new lessons (don't write empty entries)

Lesson granularity guide:
- Too specific: "UserService.java line 42 needed @Transactional" -- only helps this file
- Too broad: "Always check error handling" -- no actionable guidance
- Just right: "Spring @Transactional must be on the public method, not the private helper" -- reusable pattern

### 5. Repair Loop

Check current repair round against max_repair_rounds.

**If round < max:**
- Increment repair round
- Choose repair strategy:
  - **Option A: Resume dev agent** (preferred when runtime supports resume):
    ```
    Agent(
      resume: "{dev_agent_id}",
      subagent_type="claude",
      prompt: "
        VERIFY FAILURES:
        {specific verify failures}

        REVIEW FINDINGS:
        {specific review findings}

        Fix these specific issues in the files you previously modified.
        Do not repeat the same approach. Output the same structured format.
      "
    )
    ```
  - **Option B: Dispatch repair agent** (when resume is not available or agent is too polluted):
    ```
    Agent(
      description="Repair: {item_id} round {N}",
      prompt=<filled repair-agent.md with failures and findings>,
      subagent_type="claude",
      model="sonnet"
    )
    ```
- Write dispatch log: action=repair, round=N, strategy=resume|repair-agent
- Go back to step 3 (parallel verify+review)

**If round >= max:**
- Update work item status to fail
- Write all reports
- Write dispatch log: action=max-repair-exceeded
- Add blocker to state.json.pending_confirmations

## Output Format

After processing all work items:

```text
AGENT_COORDINATOR_STATUS: complete|blocked
WORK_ITEMS_PROCESSED: <count>
WORK_ITEMS_PASSED: <count>
WORK_ITEMS_FAILED: <count>
ARTIFACTS:
- agent/work_items.json
- agent/main-log.md
- agent/reports/<id>/*.json
BLOCKERS:
- <blocker or empty>
NEXT_ACTION:
- <action>
```

## Agent Output Contracts

All subagents must return structured results. The coordinator extracts results from the agent's final response.

**Dev Agent Output:**
```
DEV_STATUS: success|failed
FILES_CHANGED:
- path/to/file1.java
- path/to/file2.java
SUMMARY: One-line description of what was implemented
BLOCKERS: (empty or list)
```

**Verify Agent Output:**
```
VERIFY_STATUS: pass|fail
BUILD_RESULT: pass|fail
TEST_RESULT: pass|fail
FAILURES: (empty or list of specific failures)
```

**Review Agent Output:**
```
REVIEW_STATUS: pass|fail
SPEC_COMPLIANCE: pass|fail
CODE_QUALITY: pass|fail
FINDINGS: (empty or list of specific findings)
```

**Rules:**
- Status values are strictly `pass` or `fail` -- no "partial", "mostly", or "conditional"
- File paths only -- never embed file contents in the output
- Findings must be specific: file path + line number + issue description

## Knowledge Hooks

When present, load before dispatching:
- `coding-standards` -- include in dev agent prompt
- `infra-components` -- include in dev agent prompt
- `context-pack-builder` -- generate per-item context packs
- `dynamic-checklist` -- generate per-item checklists

## Red Flags

**绝不：**
- 在 main/master 分支上开始实现（除非人类明确同意）
- 跳过审查（spec compliance 或 code quality）
- 带着未修复的问题继续
- 并行调度多个实现 subagent（冲突）
- 让 subagent 读计划文件（提供完整文本代替）
- 跳过场景设置上下文（subagent 需要理解任务位置）
- 忽略 subagent 问题（在让他们继续前回答）
- 在 spec compliance 上接受"差不多"（spec reviewer 发现问题 = 未完成）
- 跳过审查循环（reviewer 发现问题 = implementer 修复 = 再审查）
- 让实现者自审替代实际审查（两者都需要）
- **在 spec compliance 通过前开始 code quality review**（顺序错误）
- 在任一审查有开放问题时进入下一个任务
