---
name: flow
description: >
  ReqFlow 主入口。当用户输入需求、PRD、issue、bug 报告、重构请求或自然语言功能描述时触发。
  自动分析需求复杂度，路由到 L0(分析)、L1(轻量修改)、L2(计划性修改)、L3(交付循环) 四个级别之一。
  用户说"分析一下"、"帮我改"、"做个计划"、"跑完整流程"时也应触发。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
---

# reqflow:flow

ReqFlow 主入口 skill。接收用户需求，自动路由到合适的执行级别。

## 触发方式

用户通过以下方式触发：

```text
/reqflow:flow <需求描述>
```

或自然语言：

- "分析一下这个需求"
- "帮我实现这个功能"
- "做个修改计划再动手"
- "跑完整交付流程"
- "修个 bug"
- "看一下这段代码有什么问题"

当用户明确要求完整 PRD-to-code 流程、可恢复运行、跨会话 checkpoint 时，应使用 `main-flow` 而非本 skill。

## 强制规则

- 先路由，再执行。不要跳过路由直接改代码。
- 只问路由决策必需的上下文，不要过度追问。
- L2 和 L3 级别在改代码前必须先展示计划并获得用户确认。
- 外部写操作（部署、发布、数据库变更）必须展示目标/账号/操作/风险并等待确认。
- 如果自动化 provider 不可用，切换到 manual checklist 模式而非假装完成。
- 同一失败指纹出现两次时停止自动重试，转为人工介入。
- 秘钥不得写入项目文件。

## 路由级别

### L0 - analyze-only（只读分析）

**触发条件：**
- 用户要求分析、审查、解释、影响评估或调试假设
- 用户明确说"不要编辑"、"只看看"
- 需求过于模糊，无法安全制定计划

**行为：**
- 只读检查，不修改任何文件
- 输出分析结果和建议
- 如果发现需要进一步操作，建议合适的路由级别

### L1 - light-change（轻量修改）

**触发条件：**
- 本地低风险编辑：文本修改、小样式变更、明显 bug、import/type 修复、简单配置调整
- 影响范围仅限一个或少量本地文件
- 不涉及 API、数据库、消息、服务契约、权限、发布或部署

**行为：**
- 直接实现修改
- 运行针对性的局部检查（lint、单测、typecheck）
- 输出变更摘要

### L2 - planned-change（计划性修改）

**触发条件：**
- 多文件功能开发或重构
- 存在设计权衡
- 工作可以本地验证但默认不需要外部交付
- 上下文不完整但足以提出计划

**行为：**
1. 输出实现计划（涉及文件、修改点、验收标准）
2. 等待用户确认
3. 按计划实现
4. 本地验证（构建、测试）
5. 轻量级审查：需求匹配度 + 编码规范

### L3 - delivery-loop（交付循环）

**触发条件：**
- API 行为或契约变更
- 数据库 schema、查询、迁移、持久化或数据一致性变更
- 消息/事件/任务/cron/RPC/服务契约变更
- 认证、授权、计费、安全、发布、部署、包发布或外部用户可见行为变更
- 用户明确要求部署、发布、验证或完整流程

**行为：**
1. 展示计划，获得确认
2. 实现代码变更
3. 构建并运行测试
4. 部署/发布（如已配置 provider）或进入 manual checklist 模式
5. 验证部署结果
6. 失败修复循环（最多 3 次，相同失败指纹则停止）

## 使用 ReqFlow Core Engine

本 skill 通过 ReqFlow core engine 驱动执行。调用方式：

### 1. 检测运行时

```python
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.registry import RuntimeRegistry

registry = RuntimeRegistry()
config = registry.get("claude")  # 或 gpt、gemini、deepseek、manual
```

### 2. 初始化 Engine

```python
from reqflow.core import Engine

engine = Engine(config=config, run_dir=".dev-workflow/runs/<run-id>")
```

### 3. 执行 workflow

```python
# 单步执行
result = await engine.run_step(
    step={"name": "analyze", "type": "analysis"},
    context={"requirement": "用户需求文本"}
)

# 完整 workflow
result = await engine.run_workflow(
    workflow_steps=[
        {"name": "route", "type": "routing"},
        {"name": "analyze", "type": "analysis"},
        {"name": "implement", "type": "coding"},
        {"name": "verify", "type": "verification"},
    ],
    requirement="用户需求文本"
)
```

### 4. 工具调用

ReqFlow 通过 ToolBridge 抽象工具调用，适配不同运行时：

```python
from reqflow.core.tool_bridge import ToolBridge

bridge = ToolBridge(config.tool_mapping)
# 工具调用会自动映射到当前运行时的原生工具
```

## 交互模式

向用户提问时提供具体选项：

```text
选择执行路径：
1. 只分析（不改代码）
2. 直接修改（低风险）
3. 先出计划再改
4. 完整交付流程
```

Provider 缺失时：

```text
部署 provider 未配置：
1. 配置自动 provider
2. 使用 manual checklist 模式
3. 跳过外部交付
```

## 输出格式

```text
REQUIREMENT_FLOW_STATUS: analyzed|implemented|delivered|blocked
ROUTE_LEVEL: L0|L1|L2|L3
SUMMARY:
- <简明结果>
NEXT_ACTION:
- <用户需要的下一步操作>
```
