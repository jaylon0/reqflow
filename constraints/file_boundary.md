# File Boundary Control

文件编辑边界控制，防止子智能体越权编辑。吸收自 freeze (garrytan)。

> 原始 skill 参考: `_external/freeze/SKILL.md`

## 核心机制

将文件编辑锁定到特定目录。任何 Edit 或 Write 操作目标在允许路径之外将被**阻断**（不仅是警告）。

## 规则

- 子智能体只能编辑 authorized scope 内的文件
- 主智能体可以显式扩展 scope
- 任何 scope 外的编辑尝试被阻断并记录
- Freeze 仅适用于 Edit 和 Write 工具 -- Read、Bash、Glob、Grep 不受影响
- 这防止意外编辑，不是安全边界 -- Bash 命令如 `sed` 仍可修改边界外文件

## 边界定义

```yaml
file_boundary:
  authorized_scope:
    - "src/main/java/service/**"
    - "src/test/java/service/**"
  denied_scope:
    - "src/main/java/config/**"
    - ".dev-workflow/**"
  expansion_policy: "coordinator_approval"
```

## 工作原理

Hook 从 Edit/Write 工具输入 JSON 中读取 `file_path`，然后检查路径是否以 freeze 目录开头。如果不是，返回 `permissionDecision: "deny"` 阻断操作。

Freeze 边界通过状态文件在会话中持续。Hook 脚本在每次 Edit/Write 调用时读取它。

## 设置流程

1. 询问用户要限制编辑到哪个目录
2. 解析为绝对路径：
```bash
FREEZE_DIR=$(cd "<user-provided-path>" 2>/dev/null && pwd)
```
3. 确保尾部斜杠并保存到 freeze 状态文件：
```bash
FREEZE_DIR="${FREEZE_DIR%/}/"
echo "$FREEZE_DIR" > "$STATE_DIR/freeze-dir.txt"
```

## 关键细节

- 尾部 `/` 防止 `/src` 匹配 `/src-old`
- Freeze 仅适用于 Edit 和 Write 工具 -- Read、Bash、Glob、Grep 不受影响
- 这是防意外编辑，不是安全边界 -- Bash 命令如 `sed` 仍可修改边界外文件
- 要停用，运行 `/unfreeze` 或结束会话

## 与 agent 模板配合

每个 agent 模板的 frontmatter 中声明默认 scope，主智能体在调度时注入实际 scope。

## 实现方式

### PreToolUse Hook

```yaml
hooks:
  PreToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "bash check-freeze.sh"
          statusMessage: "Checking freeze boundary..."
    - matcher: "Write"
      hooks:
        - type: command
          command: "bash check-freeze.sh"
          statusMessage: "Checking freeze boundary..."
```

### 边界检查脚本逻辑

```bash
#!/bin/bash
# 从工具输入中提取 file_path
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path')
FREEZE_DIR=$(cat "$STATE_DIR/freeze-dir.txt")

# 检查路径是否在 freeze 目录内
if [[ "$FILE_PATH" != "$FREEZE_DIR"* ]]; then
  echo '{"permissionDecision": "deny", "reason": "File outside freeze boundary: '"$FREEZE_DIR"'"}'
  exit 0
fi
```
