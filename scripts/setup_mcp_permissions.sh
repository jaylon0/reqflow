#!/bin/bash
# setup_mcp_permissions.sh — 自动配置 Claude Code 的 MCP 工具权限
# 用法: bash scripts/setup_mcp_permissions.sh

set -e

SETTINGS_FILE="$HOME/.claude/settings.local.json"

echo "=== ReqFlow MCP 权限配置 ==="
echo ""

# 检查文件是否存在
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "创建 $SETTINGS_FILE ..."
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "permissions": {
    "allow": [
      "mcp__reqflow__*"
    ]
  }
}
EOF
    echo "✅ 已创建并配置 permissions.allow"
    echo ""
    echo "已添加规则:"
    echo "  mcp__reqflow__*  (允许所有 reqflow MCP 工具)"
    echo ""
    echo "请重启 Claude Code 使配置生效。"
    exit 0
fi

# 文件已存在，检查是否已有 mcp__reqflow__* 规则
if grep -q "mcp__reqflow__\*" "$SETTINGS_FILE" 2>/dev/null; then
    echo "✅ permissions.allow 中已存在 mcp__reqflow__* 规则，无需修改。"
    exit 0
fi

# 使用 Python 安全地修改 JSON（避免 jq 依赖）
python3 -c "
import json
import sys

with open('$SETTINGS_FILE', 'r') as f:
    data = json.load(f)

# 确保 permissions.allow 存在
if 'permissions' not in data:
    data['permissions'] = {}
if 'allow' not in data['permissions']:
    data['permissions']['allow'] = []

allow_list = data['permissions']['allow']

# 添加规则（如果不存在）
if 'mcp__reqflow__*' not in allow_list:
    allow_list.append('mcp__reqflow__*')
    with open('$SETTINGS_FILE', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('✅ 已添加 mcp__reqflow__* 到 permissions.allow')
else:
    print('✅ permissions.allow 中已存在 mcp__reqflow__* 规则')
"

echo ""
echo "已配置的规则:"
python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    data = json.load(f)
for rule in data.get('permissions', {}).get('allow', []):
    print(f'  - {rule}')
"

echo ""
echo "请重启 Claude Code 使配置生效。"
