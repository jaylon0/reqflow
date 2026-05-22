---
name: quality-gates
description: >
  质量门禁 — 硬约束，不通过就不能进入下一阶段。
  确保每个阶段的产出符合质量标准。
---

# 质量门禁

## 核心原则

**门禁是硬约束，没有例外。**

## 门禁类型

### design-gate（设计门禁）
**触发时机:** 设计阶段完成后
**检查内容:**
- Meta Spec 是否定义了系统级约束？
- Feature Spec 是否描述了 Delta 变化？
- 技术方案是否包含多阶段规划？
- 是否进行了完备性检查？
- 所有高风险设计决策是否已获批准？

### tdd-gate（TDD 门禁）
**触发时机:** 实现计划完成后
**检查内容:**
- 可测试工作项是否有失败测试？
- 测试计划是否存在？

### completion-gate（完成门禁）
**触发时机:** 实现完成后
**检查内容:**
- 所有工作项是否完成？
- 测试是否全部通过？
- 是否通过 Spec 合规审查？
- 构建是否成功？

### compliance-report（合规报告）
**触发时机:** 交付验证阶段
**检查内容:**
- 是否有验证证据？
- 是否有审查证据？
- 是否有测试证据？

## 门禁执行

```python
from reqflow.core.quality_gate import QualityGate

gate = QualityGate()
result = gate.check("design-gate", {
    "meta_spec": True,
    "feature_spec": True,
    "tech_plan_stages": 3,
    "completeness_checked": True,
})

if result.passed:
    print("门禁通过")
else:
    print("门禁未通过:")
    for item in result.blocking_items:
        print(f"  - {item.name}: {item.message}")
```

## 反合理化表

| Agent 可能的借口 | 系统的回应 |
|-----------------|-----------|
| "应该能工作了" | 运行验证命令，提供证据 |
| "太简单了不需要测试" | 简单代码也会出错，测试只需 30 秒 |
| "我很有信心" | 信心不是证据 |
| "这次就破例一下" | 没有例外 |
| "后续再补测试" | 立即通过的测试什么都证明不了 |

## 门禁失败诊断

门禁失败时，MCP 工具返回精确的诊断信息：
- 缺失字段列表及期望类型
- 类型错误字段及实际值
- 修复建议和示例调用

格式示例：
```
门禁未通过:
缺失字段:
  - failing_tests_count: 失败测试数量 (要求 int > 0)
  - test_plan: 测试计划是否存在 (要求 bool (truthy))
请修正后重新调用 reqflow_verify(gate="tdd-gate", evidence={...})
```

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
