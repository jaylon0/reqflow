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
