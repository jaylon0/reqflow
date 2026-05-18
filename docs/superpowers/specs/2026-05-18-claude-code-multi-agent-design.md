# Claude Code 多智能体设计体系

> 所有内容基于 Anthropic 官方源码文档 + Boris Cherny 公开访谈原文，禁止杜撰。
> 每条设计结论均附原文引用 + 官方源链接。

---

## 一、理念溯源：Boris Cherny 规模化夜间 Sub Agent 工作流

### 1.1 核心原文依据

**来源：** Sequoia Capital "Training Data" 播客，AI Ascent 2026（2026年5月4日）
**主讲人：** Boris Cherny（Claude Code 创始人/负责人），主持人 Lauren Reeder
**视频：** https://www.youtube.com/watch?v=SlGRN8jh2RI

| 核心观点 | 原文/验证状态 | 来源 |
|----------|--------------|------|
| 夜间规模化 | "Usually, every night, I have like a few thousand that are doing kind of deeper work" | LinkedIn 原文转载、Business Insider 报道 |
| 白天运行 | "a few 100 agents going" | 同上 |
| 会话架构 | "five to 10 sessions," each containing multiple agents | Business Insider 直接引用 |
| 150 PR/天 | "last week I submitted 150 PRs in a day" | 多家媒体广泛报道（Epsilla、samtash.com 等） |
| 手机管控 | "Personally, I write a lot of my code from the iOS app" | Boris 自己的 X/Twitter 帖子（8.1M 浏览） |
| 编码已解决 | "coding is solved" | 多源交叉验证（theneuron.ai、epsilla.com 等） |
| 自 2025.10 未手写代码 | 未手写一行代码 | finance.biggo.com、podscan.fm |

### 1.2 /loop 与 Routines 验证状态

**⚠️ 注意区分：** Boris 未在公开访谈中直接引用 "/loop" 或 "Routines" 这两个术语。媒体报道中将其归因于 Boris 的工作流是编辑推断。但 /loop 和 Routines 确实是 Claude Code 的官方功能（见下文第二章）。

**可信度分级：**
- ✅ 官方原生功能：/loop、Routines 均为 Claude Code 官方文档明确记载的功能
- ⚠️ Boris 公开实践：规模化夜间 Agent 是 Boris 原话，但具体使用 /loop+Routines 的推断未经本人直接确认
- ❌ 社区误传："20-30 PR/天" 基准数字在任何来源中均未找到，仅有 "150 PR/天" 峰值

---

## 二、Claude Code Sub-Agent 官方规范（完整字段定义）

### 2.1 定义格式

**官方文档来源：** https://code.claude.com/docs/en/sub-agents

Sub-Agent 使用独立 `.md` 文件 + YAML Frontmatter 定义，存放在 `.claude/agents/` 目录下。

**⚠️ 纠正常见误解：** 不存在单一的 "agents.md" 文件格式。每个 Agent 是一个独立的 `.md` 文件。

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback.
```

### 2.2 YAML Frontmatter 完整字段定义

**来源：** code.claude.com/docs/en/sub-agents（官方文档）

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `name` | ✅ | string | 唯一标识符，小写+连字符 |
| `description` | ✅ | string | Claude 何时应委派给此 Agent |
| `tools` | ❌ | string[] | 工具白名单（省略则继承所有工具） |
| `disallowedTools` | ❌ | string[] | 工具黑名单 |
| `model` | ❌ | string | `sonnet`、`opus`、`haiku`、完整模型 ID、或 `inherit` |
| `permissionMode` | ❌ | string | `default`、`acceptEdits`、`auto`、`dontAsk`、`bypassPermissions`、`plan` |
| `maxTurns` | ❌ | int | 最大 Agent 轮次 |
| `skills` | ❌ | string[] | 预加载到上下文的 Skills |
| `mcpServers` | ❌ | object | 可用的 MCP 服务器 |
| `hooks` | ❌ | object | 生命周期钩子（作用域限定于此 Agent） |
| `memory` | ❌ | string | 持久内存范围：`user`、`project`、`local` |
| `background` | ❌ | boolean | `true` 则始终作为后台任务运行 |
| `effort` | ❌ | string | `low`、`medium`、`high`、`xhigh`、`max` |
| `isolation` | ❌ | string | `worktree` 为隔离 git worktree |
| `color` | ❌ | string | UI 显示颜色 |
| `initialPrompt` | ❌ | string | 作为主 Agent 运行时自动提交的首轮 prompt |

### 2.3 优先级与生效范围

**来源：** code.claude.com/docs/en/sub-agents（官方文档）

优先级从高到低：
1. **Managed settings** — 组织级（通过管理后台配置）
2. **`--agents` CLI flag** — 当前会话级（JSON 格式）
3. **`.claude/agents/`** — 项目级
4. **`~/.claude/agents/`** — 用户级（所有项目）
5. **Plugin `agents/` 目录** — 插件级

### 2.4 CLI 临时定义（JSON）

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer.",
    "prompt": "You are a senior code reviewer.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

### 2.5 内置 Sub-Agent

**来源：** code.claude.com/docs/en/sub-agents

| 名称 | 模型 | 工具 | 用途 |
|------|------|------|------|
| `Explore` | Haiku | 只读 | 快速代码搜索 |
| `Plan` | inherit | 只读 | 方案设计 |
| `general-purpose` | inherit | 全部 | 通用任务 |

### 2.6 关键约束

**来源：** 官方文档明确记载

> **Subagents cannot spawn other subagents — no nesting.**

Sub-Agent 不能嵌套创建 Sub-Agent。这是架构硬约束。

---

## 三、四大生产级 Agent 完整模板

### 3.1 代码审查 Agent

**来源：** 官方 code-review 插件模式（github.com/anthropics/claude-code/tree/main/plugins）

```markdown
---
name: code-reviewer
description: 审查代码质量、安全性、最佳实践。当需要代码审查时委派。
tools: Read, Glob, Grep
model: sonnet
permissionMode: plan
memory: project
---

You are a senior code reviewer. When invoked:

1. Read the changed files
2. Check for:
   - Security vulnerabilities (OWASP Top 10)
   - Performance issues
   - Code style consistency
   - Error handling completeness
   - Test coverage gaps
3. Output format:
   - [CRITICAL] Must fix before merge
   - [IMPORTANT] Should fix
   - [SUGGESTION] Nice to have
   - [PRAISE] Good patterns to keep

Be specific: file path, line number, exact issue, suggested fix.
```

### 3.2 测试生成 Agent

```markdown
---
name: test-generator
description: 为指定代码生成全面的测试用例。当需要补充测试覆盖时委派。
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
permissionMode: acceptEdits
memory: project
---

You are a test engineer. When invoked:

1. Read the target code
2. Identify test scenarios:
   - Happy path
   - Edge cases
   - Error conditions
   - Boundary values
3. Write tests following the project's existing test patterns
4. Run tests to verify they pass
5. Report coverage summary

Follow TDD: write failing test first, then verify it passes.
```

### 3.3 文档生成 Agent

```markdown
---
name: doc-generator
description: 为代码生成文档。当需要补充文档时委派。
tools: Read, Write, Glob, Grep
model: haiku
permissionMode: acceptEdits
memory: project
---

You are a technical writer. When invoked:

1. Read the target code
2. Generate:
   - API documentation (function signatures, parameters, return types)
   - Usage examples
   - Architecture overview (if analyzing multiple files)
3. Output format: Markdown, matching existing doc style in the project
4. Do NOT add comments to code unless explicitly asked
```

### 3.4 安全审计 Agent

```markdown
---
name: security-auditor
description: 审计代码安全性。当需要安全检查时委派。
tools: Read, Glob, Grep
model: opus
permissionMode: plan
memory: project
---

You are a security auditor. When invoked:

1. Scan for OWASP Top 10 vulnerabilities:
   - Injection (SQL, Command, XSS)
   - Broken Authentication
   - Sensitive Data Exposure
   - XML External Entities
   - Broken Access Control
   - Security Misconfiguration
   - Cross-Site Scripting
   - Insecure Deserialization
   - Using Components with Known Vulnerabilities
   - Insufficient Logging
2. Check for:
   - Hardcoded secrets/credentials
   - Unsafe file operations
   - Command injection vectors
   - Path traversal risks
3. Output:
   - [CRITICAL] Immediate security risk
   - [HIGH] Should fix before release
   - [MEDIUM] Fix in next sprint
   - [LOW] Consider fixing

Include: file path, line number, vulnerability type, CVSS score estimate, remediation.
```

---

## 四、规模化 Sub Agents 核心架构

### 4.1 Chief-of-Staff 主代理模式

**来源：** 官方 Agent SDK 文档（code.claude.com/docs/en/agent-sdk/overview）+ 官方 cookbooks（github.com/anthropics/claude-cookbooks）

```
┌─────────────────────────────────────────────┐
│           Chief-of-Staff Agent              │
│  (主会话，运行 Opus，负责任务拆解与调度)       │
├─────────────────────────────────────────────┤
│  1. 接收需求                                  │
│  2. 拆解为独立子任务                           │
│  3. 并行调度 Sub-Agents                       │
│  4. 汇总结果，决定下一步                       │
└──────┬──────────┬──────────┬────────────────┘
       │          │          │
   ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
   │Sub-1  │ │Sub-2  │ │Sub-3  │
   │Sonnet │ │Sonnet │ │Haiku  │
   │实现    │ │测试    │ │搜索   │
   └───────┘ └───────┘ └───────┘
```

**关键约束（官方文档明确记载）：**
- Sub-Agent 不能嵌套创建 Sub-Agent
- 每个 Sub-Agent 是独立上下文，不继承父会话历史
- 后台 Sub-Agent 通过 `background: true` 配置

### 4.2 Agent SDK 编程式调度

**来源：** code.claude.com/docs/en/agent-sdk/overview + github.com/anthropics/claude-agent-sdk-python

```python
from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition, query

options = ClaudeAgentOptions(
    system_prompt="You are a project manager. Break tasks into sub-tasks and delegate.",
    allowed_tools=["Read", "Glob", "Grep", "Agent"],
    agents={
        "code-reviewer": AgentDefinition(
            description="Expert code reviewer.",
            prompt="Analyze code quality and suggest improvements.",
            tools=["Read", "Glob", "Grep"],
        ),
        "test-writer": AgentDefinition(
            description="Write comprehensive tests.",
            prompt="Write tests for the given code.",
            tools=["Read", "Write", "Bash"],
        ),
    },
    permission_mode="auto",
)

# 流式执行
async for message in query(prompt="Review and test the auth module", options=options):
    print(message)
```

### 4.3 并行 Sub-Agent 调度模式

**来源：** 官方 code-review 插件（5 个并行 Sonnet Agent）、feature-dev 插件（7 阶段顺序工作流）

```markdown
# 并行模式（code-review 插件）
5 个 Sonnet Agent 并行审查不同方面：
- Security reviewer
- Performance reviewer
- Style reviewer
- Architecture reviewer
- Test coverage reviewer

# 顺序模式（feature-dev 插件）
7 个阶段顺序执行：
1. code-explorer（理解现有代码）
2. code-architect（设计方案）
3. code-reviewer（审查方案）
4. implementer（实现代码）
5. test-writer（写测试）
6. code-reviewer（审查实现）
7. integrator（集成验证）
```

---

## 五、/loop 与 Routines 夜间调度设计

### 5.1 /loop 命令（会话内循环）

**来源：** code.claude.com/docs/en/scheduled-tasks（官方文档）

```bash
# 带间隔的循环
/loop 5m check if the deployment finished

# 不带间隔（Claude 动态选择 1min-1hr）
/loop continue working on the refactoring

# 不带 prompt（内置维护 prompt）
/loop

# 自定义 loop.md
# .claude/loop.md 或 ~/.claude/loop.md
```

**关键特性：**
- 会话内有效，最小间隔 1 分钟
- 7 天自动过期
- `--resume` 可恢复未过期的 loop
- 底层工具：`CronCreate`、`CronList`、`CronDelete`（5 字段 cron 表达式）

### 5.2 Routines（云端定时任务）

**来源：** code.claude.com/docs/en/routines（官方文档）

```bash
# 创建 Routine
/schedule

# 三种触发方式
# 1. Cron 定时（最小 1 小时）
Schedule: 0 2 * * *  # 每天凌晨 2 点

# 2. API 触发
POST /v1/claude_code/routines/{id}/fire
Header: Authorization: Bearer <token>
Beta: experimental-cc-routine-2026-04-01

# 3. GitHub 事件触发
Event: pull_request opened
```

**关键特性：**
- 运行在 Anthropic 云端基础设施
- 全自主执行，无权限提示
- 支持 Pro、Max、Team、Enterprise 计划
- 触发方式可组合

### 5.3 /loop vs Routines vs Desktop 对比

**来源：** code.claude.com/docs/en/scheduled-tasks 官方对比表

| 特性 | Routines（云端） | Desktop | /loop（会话内） |
|------|-----------------|---------|----------------|
| 运行位置 | Anthropic 云端 | 本地机器 | 当前会话 |
| 最小间隔 | 1 小时 | 1 分钟 | 1 分钟 |
| 持久性 | 永久 | 持久 | 会话内 |
| 无需机器 | ✅ | ❌ | ❌ |
| 适合夜间 | ✅ 最佳 | ✅ 需保持开机 | ❌ 需保持会话 |

### 5.4 Boris 夜间模式落地方案

**推断（非 Boris 原话，基于官方功能组合）：**

```
白天：
  - 5-10 个 Claude 会话并行
  - 每个会话运行 /loop 或手动调度
  - 数百个 Agent 处理日常开发

夜间：
  - Routines 定时触发（凌晨批量启动）
  - 每个 Routine 创建 Chief-of-Staff Agent
  - Chief-of-Staff 拆解任务，调度数十个 Sub-Agents
  - 合计数千个 Sub-Agents 并行执行
  - 手机 Claude App 远程监控
```

---

## 六、批量 Agent 权限与安全设计

### 6.1 三类权限模式

**来源：** code.claude.com/docs/en/sub-agents（官方文档）

| 权限模式 | 说明 | 适用场景 |
|----------|------|----------|
| `plan` | 只读，不执行任何修改 | 代码审查、安全审计 |
| `acceptEdits` | 可写文件，不可执行命令 | 文档生成、代码重构 |
| `auto` | 全自主，包括命令执行 | 测试运行、CI/CD |
| `bypassPermissions` | 跳过所有权限检查 | 受信任的自动化任务 |
| `dontAsk` | 不询问，拒绝无权限操作 | 批量后台任务 |

### 6.2 工具权限白名单

```markdown
# 只读 Agent（审查类）
tools: Read, Glob, Grep

# 生成 Agent（文档/代码）
tools: Read, Write, Edit, Glob, Grep

# 执行 Agent（测试/构建）
tools: Read, Write, Edit, Bash, Glob, Grep

# 全能 Agent（可信任务）
tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch
```

### 6.3 Hooks 安全校验

**来源：** code.claude.com/docs/en/hooks（官方文档）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "echo 'Checking command safety...'",
        "description": "Block dangerous commands"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": "echo 'File written successfully'",
        "description": "Log file changes"
      }
    ]
  }
}
```

### 6.4 夜间任务防中断方案

**来源：** 官方文档 + Boris 实践推断

1. **Routines 优先** — 云端运行，不受本地机器影响
2. **background: true** — Sub-Agent 作为后台任务，不阻塞主会话
3. **worktree isolation** — 每个 Agent 在独立 worktree 工作，避免冲突
4. **permissionMode: auto** — 批量任务预授权，无需人工确认

---

## 七、资料查询核验 Agent 设计

```markdown
---
name: data-verify-research-agent
description: 专属 Claude Code Agent 体系资料查询、溯源核验、权威校验。核查 Boris Cherny 公开访谈原文、Anthropic 官方 GitHub 文档、源码示例真实性，过滤社区非官方、过期、杜撰内容，输出带精准原文+源链接的可信资料。
model: sonnet
color: purple
tools: Read, Grep, Glob, Bash, WebSearch, WebFetch
memory: project
permissionMode: plan
---

You are a research verification agent. Your job is to verify every claim about Claude Code's architecture and Boris Cherny's statements.

## Verification Protocol

### Step 1: Source Classification
For each claim, classify the source:
- [OFFICIAL] Anthropic official docs, GitHub repos, API reference
- [FOUNDER] Boris Cherny's verified public statements (X/Twitter, interviews)
- [COMMUNITY] Third-party blogs, tutorials, community plugins
- [UNVERIFIED] No source found

### Step 2: Cross-Reference
- Check official docs at code.claude.com/docs
- Check GitHub repos: anthropics/claude-code, anthropics/claude-agent-sdk-python, anthropics/claude-cookbooks
- Check founder's public posts

### Step 3: Output Format
For each verified item:
```
[OFFICIAL/FOUNDER/COMMUNITY] Claim text
  Source: URL or document reference
 原文: "exact quote if available"
 时效: Current as of YYYY-MM-DD
```

### Step 4: Red Flags
Reject if:
- No source can be found
- Source is community-only without official backing
- Content contradicts official documentation
- Content is outdated (check document version dates)

## Key Verification Targets
1. agents.md format → Actually `.claude/agents/*.md` with YAML frontmatter
2. Sub-agent nesting → Officially NOT supported
3. /loop minimum interval → 1 minute (session-scoped)
4. Routines minimum interval → 1 hour (cloud-based)
5. Boris's "thousands of agents" → Verified from Sequoia interview
6. 150 PRs/day → Widely reported but paraphrased, not direct quote
```

---

## 八、官方源链接索引

| 资源 | 链接 | 说明 |
|------|------|------|
| Claude Code 主仓库 | https://github.com/anthropics/claude-code | 官方源码 |
| Agent SDK (Python) | https://github.com/anthropics/claude-agent-sdk-python | 官方 Python SDK |
| Agent SDK (TS) | https://github.com/anthropics/claude-agent-sdk | 官方 TypeScript SDK |
| Cookbooks | https://github.com/anthropics/claude-cookbooks | 官方实践手册 |
| Sub-Agents 文档 | https://code.claude.com/docs/en/sub-agents | 官方 Sub-Agent 规范 |
| Agent SDK 文档 | https://code.claude.com/docs/en/agent-sdk/overview | 官方 SDK 文档 |
| Routines 文档 | https://code.claude.com/docs/en/routines | 官方 Routines 文档 |
| /loop 文档 | https://code.claude.com/docs/en/scheduled-tasks | 官方定时任务文档 |
| Hooks 文档 | https://code.claude.com/docs/en/hooks | 官方 Hooks 文档 |
| Boris 访谈视频 | https://www.youtube.com/watch?v=SlGRN8jh2RI | Sequoia AI Ascent 2026 |
| Boris 访谈 Spotify | https://open.spotify.com/episode/2aa3d61HFoNWi057Py11jd | 播客版本 |
| 官方插件目录 | https://github.com/anthropics/claude-code/tree/main/plugins | 13 个官方插件 |

---

## 九、可信度分级总结

| 内容层级 | 说明 | 标记 |
|----------|------|------|
| 官方原生设计 | Anthropic 官方文档、源码明确记载 | ✅ [OFFICIAL] |
| Boris 公开实践 | Boris 在公开场合的直接引语 | ⚠️ [FOUNDER] |
| 社区补充方案 | 第三方实践，未经官方确认 | 📎 [COMMUNITY] |
| 推断/组合 | 基于官方功能的合理推断 | 🔮 [INFERRED] |

本文档中：
- Agent 定义格式、字段、优先级 → ✅ [OFFICIAL]
- Boris 夜间数千 Agent → ⚠️ [FOUNDER]（直接引语）
- Boris 使用 /loop+Routines → 🔮 [INFERRED]（功能存在，但 Boris 未直接确认使用）
- 150 PR/天 → ⚠️ [FOUNDER]（广泛报道，但为记者转述非直接引语）
- 20-30 PR/天基准 → ❌ [UNVERIFIED]（任何来源均未找到此数字）
