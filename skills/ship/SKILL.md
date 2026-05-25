---
name: ship
description: 发布流程。预检查、版本管理、创建 PR、合并验证。
triggers:
  - 创建 PR
  - 准备发布
  - ship it
  - create PR
  - 发布
tools: [Bash, Read, Write, Edit, Grep, Glob, Git]
user-invocable: true
---

# ship

发布流程。预检查、版本管理、创建 PR、合并验证。

## 触发条件

- 代码准备发布
- 需要创建 PR
- 版本号需要更新
- CHANGELOG 需要补充

## 方法论

### Step 1: 预检查

1. 测试通过
2. 代码审查完成
3. 无未解决的 BLOCKER
4. 代码风格检查通过

### Step 2: 版本管理

1. 确定版本号（semver）
   - MAJOR: 不兼容的 API 变更
   - MINOR: 向后兼容的功能新增
   - PATCH: 向后兼容的 bug 修复
2. 更新 CHANGELOG
3. 更新版本号（如果有）

### Step 3: 创建 PR

1. 清晰的标题
2. 详细的描述
3. 关联 issue
4. 添加 reviewers

### Step 4: 合并验证

1. CI 通过
2. 无冲突
3. 审查通过

## 输出格式

```
## 发布报告

### 版本信息
- 版本号: x.y.z
- 变更类型: MAJOR/MINOR/PATCH

### 变更内容
[CHANGELOG 内容]

### PR 信息
- 标题: [PR 标题]
- 描述: [PR 描述]
- 关联 issue: [issue 编号]

### 检查清单
- [ ] 测试通过
- [ ] 代码审查
- [ ] CHANGELOG 更新
- [ ] 版本号更新
```

## 注意事项

- 要确保测试通过再发布
- 要更新 CHANGELOG
- 要遵循 semver 规范
- 要关联 issue
