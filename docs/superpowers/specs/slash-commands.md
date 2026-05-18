# Command Triggers

Requirement Flow exposes short command entries that thinly wrap the underlying skills.

Agent runtimes load slash commands differently:

- Claude loads plugin-local `commands/*.md` directly.
- Codex v0.130.0 does not register plugin-provided slash commands in the TUI. Use the plugin skill names or natural-language triggers instead.
- CodeFlicker global installs should expose the plugin through the local plugin registry. If slash commands are supported by the runtime, prefer the same short command names as Claude; otherwise use natural-language skill triggers.

The plugin intentionally keeps command and skill names aligned for cross-agent consistency. Some runtimes may show both `main-flow` command and `main-flow` skill; keep this duplication unless a runtime cannot load the plugin.

## Primary Entry

```text
/requirement-flow-plugin:flow
```

Use this for normal requirement handling. It routes the request and then chooses analysis, light implementation, planned implementation, or full delivery.

## Direct Entries

```text
/requirement-flow-plugin:init
/requirement-flow-plugin:adapter
/requirement-flow-plugin:plan
/requirement-flow-plugin:check
/requirement-flow-plugin:support
/requirement-flow-plugin:main-flow
/requirement-flow-plugin:loop
```

## Codex Entries

Codex should be invoked with skill names because `/requirement-flow-plugin:*` is intercepted by the TUI slash dispatcher before the model sees it.

| Intent | Codex trigger |
|---|---|
| Normal requirement flow | `使用 requirement-flow-plugin:requirement-flow 处理这个需求: ...` |
| Full PRD-to-code flow | `使用 requirement-flow-plugin:main-flow 运行完整 PRD 到代码流程: ...` |
| Repair loop | `使用 requirement-flow-plugin:loop-engine 处理这个失败: ...` |
| Project context setup | `使用 requirement-flow-plugin:context-bootstrap 扫描当前项目` |
| Provider adapter | `使用 requirement-flow-plugin:adapter-factory 生成 <platform> 适配器` |
| Acceptance plan | `使用 requirement-flow-plugin:test-plan 为这个需求生成验收计划` |
| Verification | `使用 requirement-flow-plugin:build/verify-api/verify-ui/verify-message/verify-rpc 执行验证` |
| Support router | `使用 requirement-flow-plugin:support-router 选择辅助能力` |
| Direct support skill | `使用 requirement-flow-plugin:support-diagnose 诊断这个失败` |

## Command Mapping

| Command | Underlying skill |
|---|---|
| `flow` | `requirement-flow` |
| `main-flow` | `main-flow` |
| `loop` | `loop-engine` |
| `init` | `context-bootstrap` |
| `adapter` | `adapter-factory` |
| `plan` | `test-plan` |
| `check` | `build`, `verify-api`, `verify-ui`, `verify-message`, or `verify-rpc` |
| `support` | `support-router` or a matching auxiliary support skill |

The full skill names remain available for direct skill invocation. Claude slash command names should stay short and user-facing.

## CodeFlicker Entries

Use the global plugin entry first:

```text
requirement-flow-plugin flow <requirement>
requirement-flow-plugin main-flow <PRD or requirement>
requirement-flow-plugin loop <failure or finding>
```

If the current CodeFlicker build routes through natural language instead of slash commands, use:

```text
使用 requirement-flow-plugin:requirement-flow 处理这个需求: ...
使用 requirement-flow-plugin:main-flow 运行完整 PRD 到代码流程: ...
使用 requirement-flow-plugin:loop-engine 处理这个失败: ...
```

## Support Entries

Support entries are opt-in auxiliary capabilities. They should not run by default during the main Requirement Flow route unless a main workflow skill explicitly calls for the method.

Examples:

```text
使用 requirement-flow-plugin:support-tdd 为这个需求先写验收测试
使用 requirement-flow-plugin:support-grill-me 帮我把这个方案问清楚
使用 requirement-flow-plugin:support-to-issues 把这个方案拆成任务
```

## Interaction

The plugin should ask concrete questions when the route, context, or provider is incomplete. Prefer options over open-ended prompts.

Examples:

```text
Choose delivery path:
1. Analyze only
2. Implement local change
3. Plan then implement
4. Full delivery flow
```

```text
Deployment provider is missing:
1. Configure automatic provider
2. Use manual checklist mode
3. Skip external delivery for this run
```
