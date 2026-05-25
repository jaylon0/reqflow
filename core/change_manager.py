"""ReqFlow Change Manager — OpenSpec 风格目录结构管理。

管理 changes/ 目录下的变更生命周期：创建、归档、查询。
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 变更目录下的标准子目录
_CHANGE_SUBDIRS = [
    "runs",
]

# 变更目录下的标准文件
_CHANGE_FILES = [
    "proposal.md",
    "spec.md",
    "design.md",
    "plan.md",
    "tasks.md",
    "blockers.md",
    "acceptance.md",
    "conversation.md",
]


@dataclass
class ChangeInfo:
    """变更信息。"""
    name: str
    path: str
    description: str = ""
    status: str = "active"  # active | archived
    created_at: str = ""


class ChangeManager:
    """OpenSpec 风格变更管理器。"""

    def __init__(self, base_dir: str):
        """base_dir 是 .reqflow 目录路径。"""
        self.base_dir = Path(base_dir)
        self.changes_dir = self.base_dir / "changes"
        self.archive_dir = self.base_dir / "changes" / "archive"
        self.library_dir = self.base_dir / "library"

    def create_change(self, name: str, description: str = "") -> ChangeInfo:
        """创建新变更目录，包含标准子目录和空文件。"""
        change_dir = self.changes_dir / name
        if change_dir.exists():
            raise ValueError(f"变更已存在: {name}")

        change_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        for subdir in _CHANGE_SUBDIRS:
            (change_dir / subdir).mkdir(exist_ok=True)

        # 创建空文件
        for fname in _CHANGE_FILES:
            (change_dir / fname).touch()

        info = ChangeInfo(
            name=name,
            path=str(change_dir),
            description=description,
            status="active",
            created_at=datetime.now().isoformat(),
        )

        # 写入 config.yaml
        config = {
            "name": name,
            "description": description,
            "status": "active",
            "created_at": info.created_at,
        }
        config_path = change_dir / "config.yaml"
        try:
            import yaml
            config_path.write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")
        except ImportError:
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info("创建变更: %s at %s", name, change_dir)
        return info

    def get_change(self, name: str) -> ChangeInfo | None:
        """获取变更信息。"""
        change_dir = self.changes_dir / name
        if not change_dir.exists():
            return None
        return ChangeInfo(
            name=name,
            path=str(change_dir),
            status="active",
        )

    def list_changes(self, status: str = "active") -> list[ChangeInfo]:
        """列出变更。"""
        if not self.changes_dir.exists():
            return []
        result = []
        for child in sorted(self.changes_dir.iterdir()):
            if child.is_dir() and child.name != "archive":
                result.append(ChangeInfo(
                    name=child.name,
                    path=str(child),
                    status="active",
                ))
        return result

    def archive_change(self, name: str) -> str:
        """归档变更到 changes/archive/<date>-<name>。"""
        change_dir = self.changes_dir / name
        if not change_dir.exists():
            raise ValueError(f"变更不存在: {name}")

        date_prefix = datetime.now().strftime("%Y%m%d")
        archive_name = f"{date_prefix}-{name}"
        archive_path = self.archive_dir / archive_name

        self.archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(change_dir), str(archive_path))
        logger.info("归档变更: %s -> %s", name, archive_path)
        return str(archive_path)

    def create_run(self, change_name: str, run_id: str) -> str:
        """为变更创建运行目录。"""
        change_dir = self.changes_dir / change_name
        if not change_dir.exists():
            raise ValueError(f"变更不存在: {change_name}")

        run_dir = change_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 state.json
        state = {
            "run_id": run_id,
            "change_name": change_name,
            "status": "running",
            "current_stage": "startup",
            "created_at": datetime.now().isoformat(),
        }
        state_path = run_dir / "state.json"
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("创建运行: %s/%s", change_name, run_id)
        return str(run_dir)

    def get_artifact_path(self, change_name: str, artifact: str) -> str:
        """获取变更产物的路径。"""
        change_dir = self.changes_dir / change_name
        return str(change_dir / artifact)
