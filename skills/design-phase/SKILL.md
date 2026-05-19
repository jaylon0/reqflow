---
name: design-phase
description: >
  设计阶段 — Meta Spec → Feature Spec → Code 三阶段设计流程。
  确保在动手之前完成充分设计。
---

# 设计阶段

## 核心原则

**先定义约束，再定义变化，最后实现。**

## 阶段 1: Meta Spec（元规格）

定义系统级约束和架构原则：

```markdown
# Meta Spec: <系统名称>

## 架构原则
- 原则 1
- 原则 2

## 技术约束
- 约束 1
- 约束 2

## 接口规范
- 规范 1
- 规范 2
```

Meta Spec 一次定义，多次复用。它定义了"系统的边界"。

## 阶段 2: Feature Spec（功能规格）

基于 Meta Spec，定义具体功能的 Delta 变化：

```markdown
## ADDED Requirements

### Requirement: <需求名称>
<需求描述>

#### Scenario: <场景名称>
- GIVEN <前置条件>
- WHEN <触发条件>
- THEN <预期结果>

## MODIFIED Requirements

### Requirement: <已有需求名称>
<修改后的描述>
(Previously: <原描述>)

## REMOVED Requirements

### Requirement: <废弃需求名称>
(已被 <新需求> 替代)
```

Delta 格式的优势：
- 清晰 — 精确显示什么在变化
- 冲突避免 — 两个变更可以修改同一个 spec 的不同需求
- 审查高效 — 审查者只看变化部分

## 阶段 3: 技术方案

基于 Feature Spec，制定技术方案：

### 3.1 3-5 阶段规划
```
阶段 1: 理解 — 阅读相关代码，识别关键约束
阶段 2: 设计 — 定义接口、数据流
阶段 3: 验证 — 与用户确认设计
阶段 4: 实现 — TDD 方式实现
阶段 5: 集成 — 集成测试
```

### 3.2 8 步研究协议（如果遇到未知领域）
```
1. 明确问题
2. 搜索现有方案
3. 评估方案
4. 阅读文档
5. 阅读示例
6. 最小实验
7. 验证假设
8. 记录结论
```

## 设计门禁

设计完成后，必须通过设计门禁：

```
reqflow_verify(
    run_id="<run-id>",
    gate="design-gate",
    evidence={
        "meta_spec": true,
        "feature_spec": true,
        "tech_plan_stages": 3,
        "completeness_checked": true,
    }
)
```

门禁不通过 → 回到相应阶段重新设计。

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
