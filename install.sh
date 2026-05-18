#!/usr/bin/env bash
# ReqFlow 安装脚本
# 用法: ./install.sh [claude-code|codex|cursor|copilot|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQFLOW_DIR="$SCRIPT_DIR"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[信息]${NC} $*"; }
warn() { echo -e "${YELLOW}[警告]${NC} $*"; }
error() { echo -e "${RED}[错误]${NC} $*" >&2; }

install_claude_code() {
    local target="$HOME/.claude/plugins/local/reqflow"
    info "安装到 Claude Code: $target"

    mkdir -p "$target"
    cp -r "$REQFLOW_DIR/.claude-plugin" "$target/"
    cp -r "$REQFLOW_DIR/skills" "$target/"
    cp "$REQFLOW_DIR/mcp.json" "$target/"

    # 替换 PLUGIN_DIR
    sed -i '' "s|\${PLUGIN_DIR}|$target|g" "$target/.claude-plugin/plugin.json" 2>/dev/null || true

    info "Claude Code 安装完成"
    echo "  使用方法: 在 Claude Code 中输入 /reqflow:using-reqflow <需求>"
}

install_codex() {
    local target="$HOME/.codex/plugins/reqflow"
    info "安装到 Codex: $target"

    mkdir -p "$target"
    cp -r "$REQFLOW_DIR/.codex-plugin" "$target/"
    cp -r "$REQFLOW_DIR/skills" "$target/"
    cp "$REQFLOW_DIR/mcp.json" "$target/"

    sed -i '' "s|\${PLUGIN_DIR}|$target|g" "$target/.codex-plugin/plugin.json" 2>/dev/null || true

    info "Codex 安装完成"
}

install_cursor() {
    local target="$HOME/.cursor/plugins/reqflow"
    info "安装到 Cursor: $target"

    mkdir -p "$target"
    cp -r "$REQFLOW_DIR/.cursor-plugin" "$target/"
    cp -r "$REQFLOW_DIR/skills" "$target/"
    cp "$REQFLOW_DIR/mcp.json" "$target/"

    sed -i '' "s|\${PLUGIN_DIR}|$target|g" "$target/.cursor-plugin/plugin.json" 2>/dev/null || true

    info "Cursor 安装完成"
}

install_copilot() {
    info "生成 Copilot MCP 配置片段:"
    echo ""
    echo '  在 .vscode/settings.json 中添加:'
    echo '  {'
    echo '    "github.copilot.chat.mcp.servers": {'
    echo '      "reqflow": {'
    echo "        \"command\": \"python3\","
    echo "        \"args\": [\"-m\", \"reqflow.runner.mcp_server\"],"
    echo "        \"cwd\": \"$REQFLOW_DIR\""
    echo '      }'
    echo '    }'
    echo '  }'
    echo ""
}

install_all() {
    install_claude_code
    echo ""
    install_codex
    echo ""
    install_cursor
    echo ""
    install_copilot
}

# 主逻辑
if [ $# -eq 0 ]; then
    echo "用法: $0 [claude-code|codex|cursor|copilot|all]"
    echo ""
    echo "平台:"
    echo "  claude-code  安装到 Claude Code"
    echo "  codex        安装到 Codex"
    echo "  cursor       安装到 Cursor"
    echo "  copilot      生成 Copilot MCP 配置"
    echo "  all          安装到所有平台"
    exit 1
fi

case "$1" in
    claude-code) install_claude_code ;;
    codex)       install_codex ;;
    cursor)      install_cursor ;;
    copilot)     install_copilot ;;
    all)         install_all ;;
    *)
        error "未知平台: $1"
        echo "支持的平台: claude-code, codex, cursor, copilot, all"
        exit 1
        ;;
esac
