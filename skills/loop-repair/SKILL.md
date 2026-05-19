---
name: loop-repair
description: >
  循环修复 — 失败时的修复循环引擎。
  observe → classify → localize → patch → verify → review → decide
---

# 循环修复

## 核心原则

**失败不可怕，可怕的是重复失败。**

## 状态机

```
observe → classify → localize → patch → verify → review → decide
```

### observe（观察）
- 收集失败信息
- 识别错误类型
- 记录失败指纹

### classify（分类）
- 逻辑错误
- 类型错误
- 依赖错误
- 配置错误
- 环境错误

### localize（定位）
- 定位到具体文件和行号
- 分析上下文
- 识别影响范围

### patch（修复）
- 编写最小修复
- 不引入新问题
- 保持代码风格一致

### verify（验证）
- 运行相关测试
- 验证修复有效
- 检查是否引入回归

### review（审查）
- 审查修复质量
- 检查是否符合规范
- 评估是否需要重构

### decide（决策）
- 修复成功 → 继续下一个工作项
- 修复失败 → 再次尝试（最多 3 次）
- 3 次失败 → 升级到用户

## 停止条件

1. 同一 failure_fingerprint 重复出现 → 停止
2. 修复范围超出 authorized_scope → 停止
3. 重试次数超过 max_retries（3 次） → 停止
4. 需要人工决策 → 停止

## 循环记录

每次循环记录到：
```
.dev-workflow/runs/<run-id>/loops/<loop-id>.md
```

记录内容：
- failure_fingerprint
- 之前的尝试
- authorized_scope
- 变更的文件
- 验证结果
- 需要的人工决策

## 3 次尝试规则

借鉴 Karpathy 的规则：
- 同一问题失败 3 次 → 升级到用户
- 不再尝试，等待人工介入
- 记录所有尝试和失败原因

## 沟通语言

始终使用中文与用户沟通。技术术语和代码标识符保持原样。
