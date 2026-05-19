"""ReqFlow Multi Repo — 多仓库支持。

从 AUTO_GIT 或目录结构推断仓库，支持跨仓库调用链路追踪。
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RepoInfo:
    name: str
    path: str
    branch: str = ""
    remote: str = ""

    def __post_init__(self):
        if not self.branch:
            self.branch = self._detect_branch()
        if not self.remote:
            self.remote = self._detect_remote()

    def _detect_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.path, capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    def _detect_remote(self) -> str:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.path, capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""


class MultiRepo:
    """多仓库支持。"""

    def __init__(self):
        self._repos: dict[str, RepoInfo] = {}

    def detect_repos(self, root: str = ".") -> list[RepoInfo]:
        """从目录结构推断仓库。"""
        repos = []
        root_path = Path(root).resolve()

        # 检查根目录本身是否是 git 仓库
        if (root_path / ".git").exists():
            repo = RepoInfo(name=root_path.name, path=str(root_path))
            repos.append(repo)
            self._repos[repo.name] = repo

        # 检查子目录
        for subdir in root_path.iterdir():
            if subdir.is_dir() and (subdir / ".git").exists():
                repo = RepoInfo(name=subdir.name, path=str(subdir))
                repos.append(repo)
                self._repos[repo.name] = repo

        logger.info("检测到 %d 个仓库", len(repos))
        return repos

    def add_repo(self, name: str, path: str) -> RepoInfo:
        """手动添加仓库。"""
        repo = RepoInfo(name=name, path=path)
        self._repos[name] = repo
        return repo

    def switch_repo(self, repo_name: str) -> RepoInfo | None:
        """切换到指定仓库。"""
        repo = self._repos.get(repo_name)
        if repo:
            os.chdir(repo.path)
            logger.info("切换到仓库: %s (%s)", repo_name, repo.path)
        return repo

    def get_current_repo(self) -> RepoInfo | None:
        """获取当前目录对应的仓库。"""
        cwd = os.getcwd()
        for repo in self._repos.values():
            if cwd.startswith(repo.path):
                return repo
        return None

    def get_repo(self, name: str) -> RepoInfo | None:
        """获取指定仓库。"""
        return self._repos.get(name)

    def list_repos(self) -> list[RepoInfo]:
        """列出所有仓库。"""
        return list(self._repos.values())

    def cross_repo_trace(self, entry_file: str) -> list[RepoInfo]:
        """跨仓库调用链路追踪（简化版）。"""
        related_repos = []
        for repo in self._repos.values():
            if os.path.exists(os.path.join(repo.path, entry_file)):
                related_repos.append(repo)
        return related_repos

    def to_list(self) -> list[dict[str, Any]]:
        """导出为字典列表。"""
        return [{"name": r.name, "path": r.path, "branch": r.branch, "remote": r.remote}
                for r in self._repos.values()]

    def load_from_list(self, data: list[dict[str, Any]]) -> None:
        """从字典列表加载。"""
        for item in data:
            repo = RepoInfo(name=item["name"], path=item["path"],
                           branch=item.get("branch", ""), remote=item.get("remote", ""))
            self._repos[repo.name] = repo
