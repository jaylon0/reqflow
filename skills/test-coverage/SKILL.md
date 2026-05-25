---
name: test-coverage
description: >
  测试覆盖率分析。检查测试覆盖情况，发现未覆盖的代码路径和边界情况。
  使用语句覆盖、分支覆盖、路径覆盖等指标。
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
---

# test-coverage

测试覆盖率分析 Skill。检查测试覆盖情况，发现未覆盖的代码路径。

## 核心理念

**测试覆盖率是代码质量的重要指标，但不是唯一指标。**

不仅要检查"有多少代码被测试覆盖"，还要检查"测试是否有效"。

## 触发方式

**Slash 命令：**
```
/reqflow:test-coverage <目标代码路径或描述>
```

**自然语言：**
- "检查测试覆盖率"
- "分析测试覆盖情况"
- "找出未覆盖的代码路径"

## 覆盖率指标

### 覆盖率层级

```
覆盖率层级:
├── 语句覆盖 (Statement Coverage)
│   └── 每条语句是否至少执行一次
├── 分支覆盖 (Branch Coverage)
│   └── 每个 if/else 分支是否至少执行一次
├── 条件覆盖 (Condition Coverage)
│   └── 每个布尔子表达式是否取过 true 和 false
├── 路径覆盖 (Path Coverage)
│   └── 每个可能的执行路径是否至少执行一次
└── 修改条件/判定覆盖 (MC/DC)
    └── 每个条件都能独立影响判定结果
```

### 覆盖率目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 语句覆盖 | ≥ 80% | 基础要求 |
| 分支覆盖 | ≥ 70% | 重要分支必须覆盖 |
| 路径覆盖 | ≥ 60% | 关键路径必须覆盖 |
| 单元测试 | ≥ 70% | 核心业务逻辑 |
| 集成测试 | ≥ 50% | 模块间交互 |
| E2E 测试 | ≥ 30% | 关键用户流程 |

## 执行流程

### 步骤 1: 收集覆盖率数据

运行测试并收集覆盖率报告：

```bash
# Python
pytest --cov=src --cov-report=html --cov-report=term-missing

# JavaScript/TypeScript
npx jest --coverage

# Java
mvn jacoco:report

# Go
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### 步骤 2: 分析覆盖率报告

解析覆盖率报告，识别未覆盖的代码：

```markdown
## 覆盖率分析报告

### 总体覆盖率
| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| 语句覆盖 | X% | 80% | ✅/❌ |
| 分支覆盖 | X% | 70% | ✅/❌ |
| 路径覆盖 | X% | 60% | ✅/❌ |

### 模块覆盖率
| 模块 | 语句覆盖 | 分支覆盖 | 状态 |
|------|----------|----------|------|
| auth | 85% | 75% | ✅ |
| user | 70% | 60% | ⚠️ |
| order | 60% | 50% | ❌ |
| payment | 90% | 85% | ✅ |
```

### 步骤 3: 识别未覆盖路径

```markdown
### 未覆盖代码路径

#### [模块名] 未覆盖路径

**文件:** `src/auth/login.py`
**行号:** 45-52
**代码:**
```python
def login(username, password):
    user = db.find_user(username)
    if user is None:
        return {"error": "User not found"}  # 未覆盖

    if not user.verify_password(password):
        return {"error": "Invalid password"}  # 未覆盖

    if user.is_locked:
        return {"error": "Account locked"}  # 未覆盖

    return {"token": user.generate_token()}  # 已覆盖
```

**未覆盖分支:**
1. 用户不存在 (行 46-47)
2. 密码错误 (行 49-50)
3. 账户锁定 (行 52-53)

**建议测试用例:**
```python
def test_login_user_not_found():
    result = login("nonexistent", "password")
    assert result == {"error": "User not found"}

def test_login_invalid_password():
    result = login("valid_user", "wrong_password")
    assert result == {"error": "Invalid password"}

def test_login_account_locked():
    result = login("locked_user", "password")
    assert result == {"error": "Account locked"}
```
```

### 步骤 4: 生成测试建议

```markdown
## 测试建议

### 优先级 P0 (必须覆盖)
1. [未覆盖路径] → [测试用例] → [预期覆盖提升]

### 优先级 P1 (应该覆盖)
1. [未覆盖路径] → [测试用例] → [预期覆盖提升]

### 优先级 P2 (建议覆盖)
1. [未覆盖路径] → [测试用例] → [预期覆盖提升]

### 测试用例模板
```python
# 测试文件: tests/test_[模块名].py

class Test[模块名]:
    def test_[功能]_happy_path(self):
        """正常路径测试"""
        pass

    def test_[功能]_error_path(self):
        """异常路径测试"""
        pass

    def test_[功能]_boundary(self):
        """边界情况测试"""
        pass

    def test_[功能]_edge_case(self):
        """边缘情况测试"""
        pass
```
```

### 步骤 5: 覆盖率提升计划

```markdown
## 覆盖率提升计划

### 当前状态
- 语句覆盖: X%
- 分支覆盖: X%
- 路径覆盖: X%

### 目标状态
- 语句覆盖: 80%
- 分支覆盖: 70%
- 路径覆盖: 60%

### 提升路径
1. [阶段 1] 补充 P0 测试用例 (预计提升 X%)
2. [阶段 2] 补充 P1 测试用例 (预计提升 X%)
3. [阶段 3] 补充 P2 测试用例 (预计提升 X%)

### 工作量估算
- P0 测试用例: X 个，预计 Y 小时
- P1 测试用例: X 个，预计 Y 小时
- P2 测试用例: X 个，预计 Y 小时
- 总计: X 个测试用例，预计 Y 小时
```

## 覆盖率工具

### Python
```bash
# 安装
pip install pytest-cov

# 运行
pytest --cov=src --cov-report=html --cov-report=term-missing

# 配置 (pyproject.toml)
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"

# 配置 (.coveragerc)
[run]
source = src
omit = tests/*

[report]
fail_under = 80
show_missing = true
```

### JavaScript/TypeScript
```bash
# 安装
npm install --save-dev jest @testing-library/react

# 运行
npx jest --coverage

# 配置 (jest.config.js)
module.exports = {
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

### Java
```bash
# Maven
mvn jacoco:report

# Gradle
gradle jacocoTestReport

# 配置 (pom.xml)
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.8</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

## 与其他 Skill 的协作

- **测试生成阶段**: 根据覆盖率分析结果生成测试用例
- **代码审查阶段**: 在代码审查前调用，将覆盖率发现纳入审查报告
- **交付验证阶段**: 作为验证的一部分，确认覆盖率达标

## 强制规则

- **必须运行实际测试** — 不能只看代码估算覆盖率，必须运行测试工具获取真实数据
- **必须识别未覆盖路径** — 不能只说"覆盖率低"，要指出具体哪些代码路径未覆盖
- **必须生成测试用例** — 不能只说"需要测试"，要给出具体的测试代码
- **必须设定目标** — 不能只说"提高覆盖率"，要设定具体的目标百分比
- **必须制定计划** — 不能只说"需要改进"，要给出具体的提升计划和工作量估算

## 输出格式

```
TEST_COVERAGE_STATUS: analyzing|completed|blocked
STATEMENT_COVERAGE: X%
BRANCH_COVERAGE: X%
PATH_COVERAGE: X%
UNCOVERED_PATHS: X
TEST_CASES_GENERATED: X
COVERAGE_TARGET: X%
NEXT_ACTION: [建议的下一步操作]
```
