---
name: refactor
description: 代码重构。识别重构机会，安全地改善代码结构。
triggers:
  - 重构代码
  - 简化逻辑
  - refactor
  - 代码优化
  - 清理代码
tools: [Bash, Read, Write, Edit, Grep, Glob]
user-invocable: true
---

# refactor

代码重构。识别重构机会，安全地改善代码结构。

## 触发条件

- 代码重复需要提取
- 函数过长需要拆分
- 命名不清晰需要改进
- 结构混乱需要整理

## 方法论

### Step 1: 理解现有代码

1. 功能是什么
2. 结构如何
3. 依赖关系

### Step 2: 识别重构机会

| 问题 | 重构手法 |
|------|----------|
| 重复代码 | Extract Method/Function |
| 过长函数 | Split Function |
| 复杂条件 | Simplify Conditional |
| 命名不清 | Rename |
| 过多参数 | Introduce Parameter Object |
| 依恋情结 | Move Method/Field |

### Step 3: 安全重构

```
⛔ 重构铁律：保持行为不变
```

1. 小步修改（每次只改一点）
2. 每步验证（运行测试）
3. 随时可回滚

### Step 4: 验证

1. 运行测试确认行为不变
2. 检查代码覆盖率
3. 确认性能无回退

## 输出格式

```
## 重构报告

### 重构目标
[要解决什么问题]

### 重构前
[原始代码和问题]

### 重构后
[改进后的代码]

### 验证结果
[测试结果、覆盖率]
```

## 注意事项

- ⛔ 不要在重构时添加新功能
- ⛔ 不要在重构时改变行为
- 要保持测试通过
- 要小步提交
