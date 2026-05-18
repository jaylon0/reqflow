# Code Review

代码审查双向流程，吸收自 superpowers requesting-code-review + receiving-code-review。

> 原始 skill 参考: `_external/requesting-code-review/SKILL.md`, `_external/receiving-code-review/SKILL.md`

## 核心原则

- **审查早，审查频** -- Review early, review often
- **验证后再实施** -- Verify before implementing
- **技术正确性高于社交舒适** -- Technical correctness over social comfort

## 流程

### 1. Request Review（请求审查）

**何时必须审查：**
- subagent-driven development 中每个任务完成后
- 完成主要功能后
- 合并到 main 前

**何时可选但有价值：**
- 卡住时（新视角）
- 重构前（基线检查）
- 修复复杂 bug 后

**如何请求：**

1. 获取 git SHAs:
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

2. 调度 code reviewer subagent，填充模板：
   - `{DESCRIPTION}` - 构建内容的简要摘要
   - `{PLAN_OR_REQUIREMENTS}` - 应该做什么
   - `{BASE_SHA}` - 起始提交
   - `{HEAD_SHA}` - 结束提交

3. 根据反馈行动：
   - 立即修复 Critical 问题
   - 继续前修复 Important 问题
   - 记录 Minor 问题供以后
   - 如果 reviewer 错了可以反驳（带推理）

### 2. Receive Review（接收审查）

**响应模式：**

```
收到代码审查反馈时:

1. READ: 完整阅读反馈，不要反应
2. UNDERSTAND: 用自己的话重述需求（或提问）
3. VERIFY: 对照代码库现实检查
4. EVALUATE: 对 THIS 代码库技术上合理吗？
5. RESPOND: 技术确认或有理反驳
6. IMPLEMENT: 一次一项，每个都测试
```

**禁止的响应：**
- "You're absolutely right!"（表演性同意）
- "Great point!" / "Excellent feedback!"（表演性）
- "Let me implement that now"（验证前）

**应该的响应：**
- 重述技术要求
- 问澄清问题
- 用技术推理反驳错误
- 直接开始工作（行动 > 言语）

**处理不清晰反馈：**
```
如果有任何项目不清晰:
  停止 - 不要实施任何东西
  对不清晰项目请求澄清

原因: 项目可能相关。部分理解 = 错误实施。
```

**实施顺序：**
```
对多项目反馈:
  1. 先澄清任何不清晰的
  2. 然后按此顺序实施:
     - 阻塞问题（破坏、安全）
     - 简单修复（拼写、导入）
     - 复杂修复（重构、逻辑）
  3. 每个修复单独测试
  4. 验证无回归
```

### 3. Address Feedback（处理反馈）

- 开发智能体接收审查反馈
- 修复 critical 和 major issues
- 记录 decisions（接受/拒绝/延迟）

## 何时反驳

当以下情况时反驳：
- 建议破坏现有功能
- 审查者缺乏完整上下文
- 违反 YAGNI（未使用的功能）
- 对此技术栈技术上不正确
- 存在遗留/兼容性原因
- 与人类伙伴的架构决策冲突

**如何反驳：**
- 使用技术推理，不是防御性
- 问具体问题
- 引用工作的测试/代码
- 如果是架构问题请人类伙伴介入

**YAGNI 检查：**
```
如果审查者建议"properly implementing":
  grep 代码库找实际使用

  如果未使用: "This endpoint isn't called. Remove it (YAGNI)?"
  如果有使用: 那么 properly implement
```

## 确认正确反馈

当反馈确实正确时：
```
"Fixed. [简要描述改了什么]"
"Good catch - [具体问题]. Fixed in [位置]."
[直接修复并在代码中显示]

不要:
"绝对正确！"
"好观点！"
"感谢指出！"
```

## 纠正你的反驳

如果你反驳了但错了：
```
"You were right - I checked [X] and it does [Y]. Implementing now."
"Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing."
```

事实陈述，继续前进。不要长篇道歉或辩护。

## 审查维度

| 维度 | 检查内容 |
|------|---------|
| 功能正确性 | 是否满足需求 |
| 代码规范 | 是否符合 coding-standards |
| 测试覆盖 | 是否有充分测试 |
| 安全性 | 是否有安全漏洞 |
| 性能 | 是否有性能问题 |

## 红旗信号

**绝不：**
- 因为"很简单"跳过审查
- 忽略 Critical 问题
- 带着未修复的 Important 问题继续
- 与有效的技术反馈争论

**如果审查者错了：**
- 用技术推理反驳
- 展示证明它工作的代码/测试
- 请求澄清

## GitHub 线程回复

回复 GitHub 上的 inline review comments 时，在评论线程中回复（`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`），不是作为顶级 PR 评论。
