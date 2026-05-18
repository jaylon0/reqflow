# @reqflow/cli npm 包实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 @reqflow/cli npm 包，将 ReqFlow Python 代码 bundle 进 npm，用户通过 `npx @reqflow/cli setup claude-code` 一键安装。

**Architecture:** npm 包包含完整的 Python 代码和 plugin 文件。CLI 入口调用 Python 子进程执行核心逻辑，安装脚本负责拷贝 plugin 文件到各平台目录。

**Tech Stack:** Node.js, Python, npm

---

## 文件结构

```
reqflow-npm/
├── package.json
├── bin/
│   └── reqflow.js
├── lib/
│   ├── installer.js
│   └── python-runner.js
├── python/
│   └── reqflow/              # 完整 Python 包（从 reqflow/ 拷贝）
├── plugins/
│   ├── claude-code/
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   ├── codex/
│   │   └── .codex-plugin/
│   │       └── plugin.json
│   └── cursor/
│       └── .cursor-plugin/
│           └── plugin.json
├── skills/                   # 从 reqflow/skills/ 拷贝
├── mcp.json
├── install.sh
└── README.md
```

---

## Task 1: 初始化 npm 包

**Files:**
- Create: `reqflow-npm/package.json`
- Create: `reqflow-npm/bin/reqflow.js`
- Create: `reqflow-npm/README.md`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p reqflow-npm/bin reqflow-npm/lib reqflow-npm/python reqflow-npm/plugins/claude-code reqflow-npm/plugins/codex reqflow-npm/plugins/cursor reqflow-npm/skills
```

- [ ] **Step 2: 创建 package.json**

```json
{
  "name": "@reqflow/cli",
  "version": "2.0.0",
  "description": "ReqFlow - 模型无关的工作流编排引擎 CLI",
  "main": "lib/installer.js",
  "bin": {
    "reqflow": "./bin/reqflow.js"
  },
  "scripts": {
    "postinstall": "node scripts/postinstall.js"
  },
  "keywords": [
    "workflow",
    "orchestration",
    "agent",
    "mcp",
    "claude",
    "codex",
    "cursor"
  ],
  "author": "ReqFlow Maintainers",
  "license": "MIT",
  "engines": {
    "node": ">=18.0.0"
  },
  "files": [
    "bin/",
    "lib/",
    "python/",
    "plugins/",
    "skills/",
    "mcp.json",
    "install.sh",
    "README.md"
  ]
}
```

- [ ] **Step 3: 创建 bin/reqflow.js**

```javascript
#!/usr/bin/env node

const { program } = require('commander');
const { setupPlatform, setupAll } = require('../lib/installer');
const { runPython } = require('../lib/python-runner');

program
  .name('reqflow')
  .description('ReqFlow - 模型无关的工作流编排引擎')
  .version('2.0.0');

program
  .command('setup <platform>')
  .description('安装 ReqFlow plugin 到指定平台')
  .action(async (platform) => {
    const validPlatforms = ['claude-code', 'codex', 'cursor', 'copilot', 'all'];
    if (!validPlatforms.includes(platform)) {
      console.error(`[错误] 未知平台: ${platform}`);
      console.error(`支持的平台: ${validPlatforms.join(', ')}`);
      process.exit(1);
    }

    try {
      if (platform === 'all') {
        await setupAll();
      } else {
        await setupPlatform(platform);
      }
    } catch (err) {
      console.error(`[错误] 安装失败: ${err.message}`);
      process.exit(1);
    }
  });

program
  .command('run')
  .description('执行 ReqFlow 工作流')
  .requiredOption('--workflow <name>', '工作流名称')
  .option('--requirement <text>', '需求文本')
  .option('--runtime <name>', 'Runtime 名称')
  .action(async (opts) => {
    try {
      await runPython('cli', ['run', opts.requirement || '', '--workflow', opts.workflow, ...(opts.runtime ? ['--runtime', opts.runtime] : [])]);
    } catch (err) {
      console.error(`[错误] 执行失败: ${err.message}`);
      process.exit(1);
    }
  });

program
  .command('list-runtimes')
  .description('列出可用 runtime')
  .action(async () => {
    try {
      await runPython('cli', ['list-runtimes']);
    } catch (err) {
      console.error(`[错误] ${err.message}`);
      process.exit(1);
    }
  });

program.parse();
```

- [ ] **Step 4: 创建 README.md**

```markdown
# @reqflow/cli

ReqFlow - 模型无关的工作流编排引擎

## 安装

```bash
# 一键安装到 Claude Code
npx @reqflow/cli setup claude-code

# 安装到 Codex
npx @reqflow/cli setup codex

# 安装到 Cursor
npx @reqflow/cli setup cursor

# 安装到所有平台
npx @reqflow/cli setup all
```

## 使用

```bash
# 执行工作流
npx @reqflow/cli run --workflow flow --requirement "为 MathExpress 添加幂运算支持"

# 列出 runtime
npx @reqflow/cli list-runtimes
```

## 在 Agent 中使用

安装后，在 Claude Code 中：
```
/reqflow:using-reqflow <需求内容>
```
```

- [ ] **Step 5: 验证**

```bash
cd reqflow-npm && node bin/reqflow.js --help
```

Expected: 显示帮助信息

- [ ] **Step 6: 提交**

```bash
git add reqflow-npm/
git commit -m "feat: initialize @reqflow/cli npm package"
```

---

## Task 2: 安装逻辑 (installer.js)

**Files:**
- Create: `reqflow-npm/lib/installer.js`

- [ ] **Step 1: 创建 installer.js**

```javascript
const fs = require('fs');
const path = require('path');
const os = require('os');

const PACKAGE_DIR = path.resolve(__dirname, '..');

const PLATFORMS = {
  'claude-code': {
    target: path.join(os.homedir(), '.claude', 'plugins', 'local', 'reqflow'),
    pluginDir: '.claude-plugin',
    name: 'Claude Code',
  },
  'codex': {
    target: path.join(os.homedir(), '.codex', 'plugins', 'reqflow'),
    pluginDir: '.codex-plugin',
    name: 'Codex',
  },
  'cursor': {
    target: path.join(os.homedir(), '.cursor', 'plugins', 'reqflow'),
    pluginDir: '.cursor-plugin',
    name: 'Cursor',
  },
};

function copyDirSync(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function replacePluginDir(filePath, pluginDir) {
  let content = fs.readFileSync(filePath, 'utf-8');
  content = content.replace(/\$\{PLUGIN_DIR\}/g, pluginDir);
  fs.writeFileSync(filePath, content, 'utf-8');
}

function installToPlatform(platformKey) {
  const platform = PLATFORMS[platformKey];
  if (!platform) {
    throw new Error(`未知平台: ${platformKey}`);
  }

  console.log(`[信息] 安装到 ${platform.name}: ${platform.target}`);

  // 1. 创建目标目录
  fs.mkdirSync(platform.target, { recursive: true });

  // 2. 拷贝 plugin 文件
  const pluginSrc = path.join(PACKAGE_DIR, 'plugins', platformKey, platform.pluginDir);
  const pluginDest = path.join(platform.target, platform.pluginDir);
  if (fs.existsSync(pluginSrc)) {
    copyDirSync(pluginSrc, pluginDest);
  }

  // 3. 拷贝 skills
  const skillsSrc = path.join(PACKAGE_DIR, 'skills');
  const skillsDest = path.join(platform.target, 'skills');
  if (fs.existsSync(skillsSrc)) {
    copyDirSync(skillsSrc, skillsDest);
  }

  // 4. 拷贝 mcp.json
  const mcpSrc = path.join(PACKAGE_DIR, 'mcp.json');
  const mcpDest = path.join(platform.target, 'mcp.json');
  if (fs.existsSync(mcpSrc)) {
    fs.copyFileSync(mcpSrc, mcpDest);
  }

  // 5. 拷贝 Python 代码
  const pythonSrc = path.join(PACKAGE_DIR, 'python');
  const pythonDest = path.join(platform.target, 'python');
  if (fs.existsSync(pythonSrc)) {
    copyDirSync(pythonSrc, pythonDest);
  }

  // 6. 替换 ${PLUGIN_DIR}
  const pluginJsonPath = path.join(pluginDest, 'plugin.json');
  if (fs.existsSync(pluginJsonPath)) {
    replacePluginDir(pluginJsonPath, platform.target);
  }

  console.log(`[信息] ${platform.name} 安装完成`);
  console.log(`  使用方法: 在 ${platform.name} 中输入 /reqflow:using-reqflow <需求>`);
}

function installCopilot() {
  console.log('[信息] 生成 Copilot MCP 配置片段:');
  console.log('');
  console.log('  在 .vscode/settings.json 中添加:');
  console.log('  {');
  console.log('    "github.copilot.chat.mcp.servers": {');
  console.log('      "reqflow": {');
  console.log(`        "command": "python3",`);
  console.log(`        "args": ["-m", "reqflow.runner.mcp_server"],`);
  console.log(`        "cwd": "${path.join(PACKAGE_DIR, 'python')}"`);
  console.log('      }');
  console.log('    }');
  console.log('  }');
  console.log('');
}

async function setupPlatform(platform) {
  if (platform === 'copilot') {
    installCopilot();
    return;
  }
  installToPlatform(platform);
}

async function setupAll() {
  for (const platform of Object.keys(PLATFORMS)) {
    installToPlatform(platform);
    console.log('');
  }
  installCopilot();
}

module.exports = { setupPlatform, setupAll, installToPlatform, installCopilot };
```

- [ ] **Step 2: 验证模块可加载**

```bash
cd reqflow-npm && node -e "const i = require('./lib/installer'); console.log('OK')"
```

Expected: "OK"

- [ ] **Step 3: 提交**

```bash
git add reqflow-npm/lib/installer.js
git commit -m "feat: add installer.js for plugin installation"
```

---

## Task 3: Python Runner (python-runner.js)

**Files:**
- Create: `reqflow-npm/lib/python-runner.js`

- [ ] **Step 1: 创建 python-runner.js**

```javascript
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const PYTHON_DIR = path.resolve(__dirname, '..', 'python');

function findPython() {
  const candidates = ['python3', 'python'];
  for (const cmd of candidates) {
    try {
      const result = require('child_process').execSync(`${cmd} --version`, { encoding: 'utf-8' });
      if (result.includes('Python 3')) {
        return cmd;
      }
    } catch (e) {
      // not found, try next
    }
  }
  throw new Error('未找到 Python 3。请安装 Python 3.10+ 后重试。');
}

async function runPython(module, args = []) {
  const python = findPython();
  const scriptPath = path.join(PYTHON_DIR, 'reqflow', 'runner', `${module}.py`);

  if (!fs.existsSync(scriptPath)) {
    throw new Error(`Python 模块不存在: ${scriptPath}`);
  }

  return new Promise((resolve, reject) => {
    const proc = spawn(python, ['-m', `reqflow.runner.${module}`, ...args], {
      cwd: PYTHON_DIR,
      stdio: 'inherit',
      env: {
        ...process.env,
        PYTHONPATH: PYTHON_DIR,
      },
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Python 进程退出码: ${code}`));
      }
    });

    proc.on('error', (err) => {
      reject(new Error(`启动 Python 失败: ${err.message}`));
    });
  });
}

module.exports = { runPython, findPython };
```

- [ ] **Step 2: 验证模块可加载**

```bash
cd reqflow-npm && node -e "const r = require('./lib/python-runner'); console.log('OK')"
```

Expected: "OK"

- [ ] **Step 3: 提交**

```bash
git add reqflow-npm/lib/python-runner.js
git commit -m "feat: add python-runner.js for Python execution"
```

---

## Task 4: Bundle Python 代码和 Plugin 文件

**Files:**
- Copy: `reqflow/` → `reqflow-npm/python/reqflow/`
- Copy: `reqflow/.claude-plugin/` → `reqflow-npm/plugins/claude-code/.claude-plugin/`
- Copy: `reqflow/.codex-plugin/` → `reqflow-npm/plugins/codex/.codex-plugin/`
- Copy: `reqflow/.cursor-plugin/` → `reqflow-npm/plugins/cursor/.cursor-plugin/`
- Copy: `reqflow/skills/` → `reqflow-npm/skills/`
- Copy: `reqflow/mcp.json` → `reqflow-npm/mcp.json`

- [ ] **Step 1: 拷贝 Python 代码**

```bash
cp -r reqflow/ reqflow-npm/python/reqflow/
rm -rf reqflow-npm/python/reqflow/.pytest_cache
rm -rf reqflow-npm/python/reqflow/__pycache__
find reqflow-npm/python -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find reqflow-npm/python -name "*.pyc" -delete 2>/dev/null || true
```

- [ ] **Step 2: 拷贝 Plugin 文件**

```bash
mkdir -p reqflow-npm/plugins/claude-code
cp -r reqflow/.claude-plugin reqflow-npm/plugins/claude-code/

mkdir -p reqflow-npm/plugins/codex
cp -r reqflow/.codex-plugin reqflow-npm/plugins/codex/

mkdir -p reqflow-npm/plugins/cursor
cp -r reqflow/.cursor-plugin reqflow-npm/plugins/cursor/
```

- [ ] **Step 3: 拷贝 Skills 和 MCP 配置**

```bash
cp -r reqflow/skills/* reqflow-npm/skills/
cp reqflow/mcp.json reqflow-npm/mcp.json
```

- [ ] **Step 4: 拷贝 install.sh**

```bash
cp reqflow/install.sh reqflow-npm/install.sh
```

- [ ] **Step 5: 验证文件完整性**

```bash
echo "Python 包:" && ls reqflow-npm/python/reqflow/core/*.py | wc -l
echo "Skills:" && ls reqflow-npm/skills/*.md | wc -l
echo "Plugin 文件:" && ls reqflow-npm/plugins/claude-code/.claude-plugin/plugin.json reqflow-npm/plugins/codex/.codex-plugin/plugin.json reqflow-npm/plugins/cursor/.cursor-plugin/plugin.json
echo "MCP 配置:" && python3 -c "import json; print(len(json.load(open('reqflow-npm/mcp.json'))['tools']), 'tools')"
```

Expected: Python 包文件数 > 10, Skills = 8, Plugin 文件 = 3, MCP = 11 tools

- [ ] **Step 6: 提交**

```bash
git add reqflow-npm/
git commit -m "feat: bundle Python code and plugin files"
```

---

## Task 5: npm 发布准备

**Files:**
- Create: `reqflow-npm/.npmignore`
- Modify: `reqflow-npm/package.json` (if needed)

- [ ] **Step 1: 创建 .npmignore**

```
.pytest_cache/
__pycache__/
*.pyc
*.pyo
.DS_Store
node_modules/
tests/
docs/
```

- [ ] **Step 2: 安装依赖并测试**

```bash
cd reqflow-npm && npm install commander && npm pack --dry-run
```

Expected: 显示包内容列表，无错误

- [ ] **Step 3: 本地测试 CLI**

```bash
cd reqflow-npm && node bin/reqflow.js --help
```

Expected: 显示帮助信息

- [ ] **Step 4: 提交**

```bash
git add reqflow-npm/
git commit -m "feat: prepare npm package for publishing"
```

---

## Task 6: 最终验证

- [ ] **Step 1: 验证 CLI 命令**

```bash
cd reqflow-npm && node bin/reqflow.js --help
node bin/reqflow.js setup --help
```

Expected: 帮助信息正确显示

- [ ] **Step 2: 验证 npm pack**

```bash
cd reqflow-npm && npm pack --dry-run 2>&1 | head -30
```

Expected: 包含所有必要文件

- [ ] **Step 3: 验证 Python 代码可执行**

```bash
cd reqflow-npm/python && python3 -c "from reqflow.core import Engine; print('OK')"
```

Expected: "OK"

- [ ] **Step 4: 最终提交**

```bash
git add -A reqflow-npm/
git commit -m "feat: complete @reqflow/cli npm package"
```
