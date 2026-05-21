"""ReqFlow Context Scanner — 脚本优先的上下文扫描器。

第一步：纯脚本扫描（快速、确定性）
第二步：Agent 语义丰富（智能、可选）
第三步：完备性检查
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProjectStructure:
    """项目结构扫描结果。"""
    root: str
    languages: dict[str, int] = field(default_factory=dict)  # 语言 -> 文件数
    entry_points: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    test_framework: str | None = None
    build_system: str | None = None
    directory_tree: dict[str, Any] = field(default_factory=dict)
    total_files: int = 0
    total_dirs: int = 0


@dataclass
class SemanticIndex:
    """语义索引（Agent 丰富后生成）。"""
    module_dependencies: dict[str, list[str]] = field(default_factory=dict)
    call_chains: list[list[str]] = field(default_factory=list)
    data_flows: list[dict[str, Any]] = field(default_factory=list)
    impact_analysis: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletenessReport:
    """完备性检查报告。"""
    coverage: float = 0.0
    missing_modules: list[str] = field(default_factory=list)
    missing_dependencies: list[str] = field(default_factory=list)
    confidence: float = 0.0
    suggestions: list[str] = field(default_factory=list)


# 语言映射
_LANG_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "React JSX",
    ".tsx": "React TSX",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".php": "PHP",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
}

# 入口文件模式
_ENTRY_PATTERNS = [
    "main.py", "app.py", "server.py", "manage.py", "__main__.py",
    "main.js", "index.js", "app.js", "server.js",
    "main.ts", "index.ts", "app.ts", "server.ts",
    "Main.java", "Application.java",
    "main.go", "main.rs",
    "Cargo.toml", "package.json", "pom.xml", "build.gradle",
]

# 配置文件模式
_CONFIG_PATTERNS = [
    "package.json", "tsconfig.json", "webpack.config.js", "vite.config.ts",
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile",
    "Cargo.toml", "go.mod", "go.sum",
    "pom.xml", "build.gradle", "build.gradle.kts",
    "Makefile", "CMakeLists.txt",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env", ".env.example", ".env.local",
    "jest.config.js", "vitest.config.ts", "pytest.ini", "conftest.py",
    ".eslintrc.js", ".prettierrc", "biome.json",
    "CLAUDE.md", "AGENTS.md", "GEMINI.md",
    ".gitignore", ".dockerignore",
]

# 测试框架检测
_TEST_FRAMEWORKS = {
    "pytest.ini": "pytest",
    "conftest.py": "pytest",
    "setup.cfg": "pytest",  # 可能包含 [tool:pytest]
    "jest.config.js": "jest",
    "jest.config.ts": "jest",
    "vitest.config.ts": "vitest",
    "vitest.config.js": "vitest",
    "phpunit.xml": "phpunit",
    "build.gradle": "junit",  # 可能包含 JUnit
}

# 构建系统检测
_BUILD_SYSTEMS = {
    "package.json": "npm/yarn/pnpm",
    "pyproject.toml": "pip/poetry",
    "setup.py": "pip/setuptools",
    "Cargo.toml": "cargo",
    "go.mod": "go",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "Makefile": "make",
    "CMakeLists.txt": "cmake",
}

# 忽略的目录
_IGNORE_DIRS = {
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    "venv", ".venv", "env", ".env",
    "dist", "build", "target", "out",
    ".idea", ".vscode", ".cursor",
    ".dev-workflow", ".reqflow",
    "vendor", "third_party", "third-party",
}


def scan_project(root: str, max_depth: int = 3) -> ProjectStructure:
    """纯脚本扫描项目结构，不依赖 Agent。

    Args:
        root: 项目根目录
        max_depth: 最大扫描深度

    Returns:
        ProjectStructure 包含项目结构信息
    """
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise ValueError(f"不是有效目录: {root}")

    structure = ProjectStructure(root=root)
    languages: dict[str, int] = {}
    entry_points: list[str] = []
    config_files: list[str] = []
    tree: dict[str, Any] = {}
    total_files = 0
    total_dirs = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # 计算当前深度
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1

        # 过滤忽略目录
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]

        if depth > max_depth:
            dirnames.clear()
            continue

        total_dirs += 1

        # 构建目录树
        current = tree
        if rel != ".":
            parts = rel.split(os.sep)
            for part in parts:
                current = current.setdefault(part, {})

        for filename in filenames:
            total_files += 1
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root)

            # 语言统计
            ext = os.path.splitext(filename)[1].lower()
            if ext in _LANG_MAP:
                lang = _LANG_MAP[ext]
                languages[lang] = languages.get(lang, 0) + 1

            # 入口文件
            if filename in _ENTRY_PATTERNS:
                entry_points.append(rel_path)

            # 配置文件
            if filename in _CONFIG_PATTERNS:
                config_files.append(rel_path)

            # 目录树中的文件（只记录前几层）
            if depth <= 2:
                current.setdefault("__files__", []).append(filename)

    structure.languages = languages
    structure.entry_points = entry_points
    structure.config_files = config_files
    structure.directory_tree = tree
    structure.total_files = total_files
    structure.total_dirs = total_dirs

    # 检测测试框架
    for config in config_files:
        basename = os.path.basename(config)
        if basename in _TEST_FRAMEWORKS:
            structure.test_framework = _TEST_FRAMEWORKS[basename]
            break

    # 检测构建系统
    for config in config_files:
        basename = os.path.basename(config)
        if basename in _BUILD_SYSTEMS:
            structure.build_system = _BUILD_SYSTEMS[basename]
            break

    return structure


def scan_for_requirement(
    root: str,
    requirement: str,
    max_depth: int = 3,
) -> dict[str, Any]:
    """扫描项目结构并关联需求。

    Args:
        root: 项目根目录
        requirement: 需求文本
        max_depth: 最大扫描深度

    Returns:
        包含结构信息和需求关联的字典
    """
    structure = scan_project(root, max_depth)

    # 提取需求中的关键词
    keywords = _extract_keywords(requirement)

    # 搜索相关文件
    related_files = _find_related_files(root, keywords, max_depth)

    return {
        "structure": structure,
        "keywords": keywords,
        "related_files": related_files,
    }


def _extract_keywords(text: str) -> list[str]:
    """从需求文本中提取关键词。"""
    import re
    # 提取英文单词和中文词
    words = re.findall(r'[a-zA-Z_]\w*|[一-鿿]+', text)
    # 过滤常见停用词
    stop_words = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
        "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "and", "but", "or", "not", "no", "nor",
        "so", "yet", "both", "either", "neither", "each", "every",
        "all", "any", "few", "more", "most", "other", "some", "such",
        "than", "too", "very", "just", "about", "up", "out", "if",
        "then", "that", "this", "these", "those", "it", "its",
    }
    return [w for w in words if w.lower() not in stop_words and len(w) > 1]


def _find_related_files(
    root: str,
    keywords: list[str],
    max_depth: int = 3,
) -> list[str]:
    """根据关键词搜索相关文件。"""
    related: list[str] = []
    keywords_lower = [k.lower() for k in keywords]

    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > max_depth:
            dirnames.clear()
            continue

        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]

        for filename in filenames:
            name_lower = filename.lower()
            rel_path = os.path.relpath(os.path.join(dirpath, filename), root)

            # 文件名匹配关键词
            for kw in keywords_lower:
                if kw in name_lower:
                    related.append(rel_path)
                    break

    return related[:50]  # 限制返回数量


def export_structure(structure: ProjectStructure, output_path: str) -> None:
    """导出项目结构到 JSON 文件。"""
    data = {
        "root": structure.root,
        "languages": structure.languages,
        "entry_points": structure.entry_points,
        "config_files": structure.config_files,
        "test_framework": structure.test_framework,
        "build_system": structure.build_system,
        "total_files": structure.total_files,
        "total_dirs": structure.total_dirs,
        "directory_tree": structure.directory_tree,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
