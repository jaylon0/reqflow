"""ReqFlow Multi Repo — 多仓库支持。

从 AUTO_GIT 或目录结构推断仓库，支持跨仓库调用链路追踪。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RepoInfo:
    name: str
    path: str
    branch: str = ""
    is_primary: bool = False


class MultiRepo:
    """多仓库支持。"""

    def __init__(self):
        """No args."""
        self._repos: dict[str, RepoInfo] = {}

    def add_repo(self, name: str, path: str, is_primary: bool = False) -> RepoInfo:
        """Add a repo with name, path, and optional is_primary flag."""
        if is_primary:
            for repo in self._repos.values():
                repo.is_primary = False
        repo = RepoInfo(name=name, path=path, is_primary=is_primary)
        self._repos[name] = repo
        logger.info("添加仓库: %s (%s)", name, path)
        return repo

    def get_primary(self) -> RepoInfo | None:
        """Get the primary repo."""
        for repo in self._repos.values():
            if repo.is_primary:
                return repo
        return None

    def get_by_name(self, name: str) -> RepoInfo | None:
        """Get repo by name."""
        return self._repos.get(name)

    def list_repos(self) -> list[dict[str, Any]]:
        """List all repos as dicts."""
        return [
            {"name": r.name, "path": r.path, "branch": r.branch, "is_primary": r.is_primary}
            for r in self._repos.values()
        ]
