"""ReqFlow Git Workflow — Git 工作流强制。

强制规则：
- master/main 上禁止直接开发
- 单次提交尽量小，不攒代码
- BLOCKER 修复后单独 commit
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BranchStatus:
    current_branch: str
    is_protected: bool
    uncommitted_files: list[str]
    last_commit: str


@dataclass
class CommitResult:
    success: bool
    hash: str = ""
    message: str = ""
    error: str = ""


PROTECTED_BRANCHES = {"master", "main", "develop", "release"}


class GitWorkflow:
    """Git 工作流强制。"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, *args: str) -> tuple[int, str]:
        """执行 git 命令。"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout.strip()
        except Exception as e:
            return -1, str(e)

    def check_branch(self) -> BranchStatus:
        """检查当前分支状态。"""
        _, branch = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        _, uncommitted = self._run_git("status", "--porcelain")
        _, last_commit = self._run_git("log", "-1", "--format=%s")

        uncommitted_files = [line.strip() for line in uncommitted.split("\n") if line.strip()]
        is_protected = branch in PROTECTED_BRANCHES

        return BranchStatus(
            current_branch=branch,
            is_protected=is_protected,
            uncommitted_files=uncommitted_files,
            last_commit=last_commit,
        )

    def enforce_branch(self, feature_name: str) -> str:
        """强制创建功能分支。如果在保护分支上，自动切换。"""
        status = self.check_branch()
        if not status.is_protected:
            return status.current_branch

        branch_name = f"feature/{feature_name}"
        code, _ = self._run_git("checkout", "-b", branch_name)
        if code == 0:
            logger.info("已创建功能分支: %s", branch_name)
            return branch_name
        else:
            logger.error("创建功能分支失败: %s", branch_name)
            return status.current_branch

    def commit(self, message: str) -> CommitResult:
        """标准化提交。"""
        code, _ = self._run_git("add", "-A")
        if code != 0:
            return CommitResult(success=False, error="git add 失败")

        code, output = self._run_git("commit", "-m", message)
        if code != 0:
            return CommitResult(success=False, error=f"git commit 失败: {output}")

        _, hash_val = self._run_git("rev-parse", "--short", "HEAD")
        return CommitResult(success=True, hash=hash_val, message=message)

    def check_uncommitted(self) -> list[str]:
        """检查未提交的文件。"""
        _, output = self._run_git("status", "--porcelain")
        return [line.strip() for line in output.split("\n") if line.strip()]

    def is_on_protected_branch(self) -> bool:
        """检查是否在保护分支上。"""
        status = self.check_branch()
        return status.is_protected

    def to_dict(self) -> dict[str, Any]:
        """导出为字典。"""
        status = self.check_branch()
        return {
            "branch": status.current_branch,
            "is_master": status.is_protected,
            "uncommitted": status.uncommitted_files,
        }
