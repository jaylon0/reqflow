"""ReqFlow Git Workflow — Git 工作流检查。

提供 Git 仓库状态检查能力。
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAIN_BRANCHES = {"master", "main"}


@dataclass
class GitStatus:
    branch: str = ""
    is_clean: bool = True
    modified_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    last_commit: str = ""
    is_main_branch: bool = False


class GitWorkflow:
    """Git 工作流检查。"""

    def __init__(self, repo_dir: str = "."):
        """Takes repo_dir string."""
        self.repo_dir = repo_dir

    def _run_git(self, *args: str) -> tuple[int, str]:
        """执行 git 命令。"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout.strip()
        except Exception as e:
            return -1, str(e)

    def check_status(self) -> GitStatus:
        """Check git status and return GitStatus object."""
        _, branch = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        _, porcelain = self._run_git("status", "--porcelain")
        _, last_commit = self._run_git("log", "-1", "--format=%s")

        modified_files = []
        untracked_files = []
        for line in porcelain.split("\n"):
            line = line.strip()
            if not line:
                continue
            status_code = line[:2]
            filepath = line[3:]
            if status_code.strip() == "??":
                untracked_files.append(filepath)
            else:
                modified_files.append(filepath)

        is_clean = len(modified_files) == 0 and len(untracked_files) == 0
        is_main_branch = branch in MAIN_BRANCHES

        return GitStatus(
            branch=branch,
            is_clean=is_clean,
            modified_files=modified_files,
            untracked_files=untracked_files,
            last_commit=last_commit,
            is_main_branch=is_main_branch,
        )
