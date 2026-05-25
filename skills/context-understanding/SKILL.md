---
name: context-understanding
description: >
  上下文理解 — 脚本优先结构提取 + Agent 语义丰富 + 完备性检查。
  确保 Agent 在动手之前充分理解项目和需求。
---

# 上下文理解

## 核心原则

**先扫描，再理解，最后验证完备性。**

## 阶段 1: 脚本优先结构提取

快速、确定性地扫描项目结构：

```bash
# 使用 ReqFlow 内置扫描器
python -c "
from reqflow.core.context_scanner import scan_project, export_structure
import json
result = scan_project('.')
print(json.dumps({
    'languages': result.languages,
    'entry_points': result.entry_points,
    'config_files': result.config_files,
    'test_framework': result.test_framework,
    'build_system': result.build_system,
    'total_files': result.total_files,
}, indent=2, ensure_ascii=False))
"
```

产出信息：
- 项目类型和技术栈
- 目录结构
- 入口文件
- 配置文件
- 测试框架
- 构建系统

## 阶段 2: Agent 语义丰富

在脚本扫描结果基础上，添加语义理解：

### 2.1 模块依赖分析
- 识别主要模块及其依赖关系
- 绘制依赖图

### 2.2 调用链追踪
- 从入口文件开始追踪
- 入口层（Controller/Route）
- 服务层（Service/Manager）
- 数据层（DAO/Mapper/Repository）
- 外部层（RPC/Message/Cache/Search）

### 2.3 影响面分析
- 识别需求涉及的文件和模块
- 评估变更的影响范围

## 阶段 3: 完备性检查

验证上下文是否充分：

```
检查清单：
- [ ] 是否识别了所有相关模块？
- [ ] 是否追踪了完整调用链？
- [ ] 是否分析了影响面？
- [ ] 是否遗漏了关键依赖？
- [ ] 上下文置信度是否足够？
```

如果不完备：
1. 补充扫描遗漏的模块
2. 追踪更深层的调用链
3. 重新评估影响面

## 产出

上下文理解完成后，产出：
- 项目结构报告
- 语义索引
- 影响面分析
- 完备性报告

调用 `reqflow_report` 报告完成。
