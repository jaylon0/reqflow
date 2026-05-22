---
name: main-flow
description: >
  完整 PRD-to-code 流程。10 阶段管线，支持 checkpoint 恢复、loop 修复循环、
  图编排、并行 Agent 调度。适用于 API 行为变更、DB schema 变更、安全相关变更。
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Agent
---

# main-flow

完整 PRD-to-code 交付流程，10 阶段管线。

## 触发方式

```
/reqflow:main-flow <PRD 或需求描述>
```

## 10 阶段

0. 启动/恢复运行 — 初始化 state.json
1. PRD 理解 — 提取功能点、约束、验收标准
2. Spec Governance — spec 变更合规检查
3. Workflow Intelligence — 场景检测、画像、工作项分解
4. Java Context Discovery — 代码图、语义索引、影响分析
5. Technical Plan — 架构选型、接口设计、数据模型
6. Implementation Plan — 模块拆分、依赖排序、上下文包
7. Agent Execution — 调度 dev/verify/review Agent，修复循环
8. Code Review — 质量门禁、编码规范检查
9. Delivery Verification — API/UI/RPC 验证
10. Archive and Evolution — 归档、演进建议

## Graph 编排模式

main-flow 支持 Graph YAML 定义，替代线性 stages：

```yaml
graph:
  entry: "analyze"
  nodes:
    - id: "analyze"
      type: "agent"
    - id: "gate"
      type: "decision"
    - id: "implement"
      type: "agent"
    - id: "verify"
      type: "agent"
  edges:
    - source: "analyze"
      target: "gate"
    - source: "gate"
      target: "implement"
      condition: "confidence >= 0.7"
    - source: "gate"
      target: "clarify"
      condition: "confidence < 0.7"
    - source: "clarify"
      target: "implement"
    - source: "implement"
      target: "verify"
```

## Loop 修复循环

Stage 9 验证失败时进入 loop engine：
```
observe → classify → localize → patch → verify → review → decide
```
最多 3 轮，相同失败指纹则停止。

## Checkpoint 恢复

每个 checkpoint 阶段会保存 state.json。中断后可从断点恢复：
```python
engine = Engine(config=config, run_dir="<之前的run-dir>")
# 自动从上次 checkpoint 继续
```

## Session 跨轮次

使用 Session 保存跨轮次上下文：
```python
session = Session(session_id="main-flow-run-1", storage_dir=".reqflow/sessions")
session.save_context("prd_summary", "...")
session.add_history("stage_1", "PRD 分析完成")
session.save()
```

## ⛔ MCP 即时输出规则

每次调用 MCP 工具后，必须立即在对话中输出：

1. **工具名 + 输入参数摘要**（一行，📡 前缀）
2. **返回结果摘要**（一行，用 ✅/❌ 标记）
3. **失败时输出失败原因和修复计划**

格式：
```
📡 reqflow_report(stage="PRD理解") → ✅ 已记录
📡 reqflow_verify(gate="tdd-gate") → ❌ 未通过: failing_tests_count 缺失
🔧 修复计划: 编写失败测试后重新提交
```

⛔ 禁止静默调用 MCP 工具不输出。

## ⛔ Agent 真实派遣规则

多 Agent 协作必须通过 Claude Code 的 Agent tool 真实派遣 subagent，不得自己扮演多个角色。

每个阶段的 agent 角色矩阵由 Execution Skill 定义。派遣时：
- 同一阶段的 agents 必须并行派遣（同一条消息中多个 Agent tool call）
- 每个 agent 的 prompt 必须包含：角色定义、任务描述、上下文、输出格式
- 主 agent 不得"代替"任何子 agent 回答
- 子 agent 超时或失败时，按降级策略处理

## ⛔ 阶段报告结构

每个阶段完成后必须在对话中输出完整报告：

```
### 📋 阶段报告：{stage_name}
**状态:** ✅ 完成 | ⚠️ 有警告 | ❌ 失败
#### 产出清单
#### 置信度（6 维度 + Unicode 可视化）
#### Agent 共识
#### MCP 执行追踪
#### 问题与风险
#### 趋势
#### 下一步
#### 阶段确认面板
```

## ⛔ 阶段确认面板

每个阶段结束时必须展示确认选项（auto_pilot 自动选择第一选项但仍展示）：

```
### 📋 阶段确认：{stage_name}
| 选项 | 操作 | 说明 |
|------|------|------|
| ✅ 确认通过 | 进入下一阶段 | 产出已验证 |
| 🔄 重新执行 | 重新运行本阶段 | 发现问题 |
| ✏️ 修改需求 | 调整需求后重新分析 | 需求变化 |
| ⏭ 跳过 | 直接进入下一阶段 | 不推荐 |
```

## ⛔ 验收决策面板

所有阶段完成后必须展示完整验收决策面板：

```
### 🏁 验收决策面板
**当前状态:** 全部阶段完成，等待你的验收决定。
#### 已交付产物清单
#### 质量摘要
#### 请做出决定
| 选项 | 操作 | 后续流程 |
|------|------|----------|
| ✅ 通过验收 | reqflow_accept | 归档、清理、流程结束 |
| ❌ 拒绝验收 | reqflow_reject | 修复循环（最多 3 轮） |
| 🔧 部分验收 | reqflow_accept + scope | 部分归档 |
| ⏸ 暂挂 | 不调用工具 | 保持状态 |
```
