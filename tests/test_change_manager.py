"""Tests for core.change_manager — OpenSpec 风格变更管理。"""

import json
import tempfile
from pathlib import Path

from core.change_manager import ChangeInfo, ChangeManager, _CHANGE_FILES, _CHANGE_SUBDIRS


def test_create_change():
    """创建变更，验证名称和路径。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        info = mgr.create_change("feat-login", description="添加登录功能")

        assert info.name == "feat-login"
        assert "feat-login" in info.path
        assert info.status == "active"
        assert info.created_at  # 非空


def test_change_directory_structure():
    """验证变更目录包含所有标准子目录和文件。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        mgr.create_change("test-change")

        change_dir = Path(tmpdir) / "changes" / "test-change"

        # 检查子目录
        for subdir in _CHANGE_SUBDIRS:
            assert (change_dir / subdir).is_dir(), f"缺少子目录: {subdir}"

        # 检查文件
        for fname in _CHANGE_FILES:
            assert (change_dir / fname).is_file(), f"缺少文件: {fname}"

        # 检查 config.yaml
        assert (change_dir / "config.yaml").is_file()


def test_create_run():
    """创建运行目录，验证 state.json 存在且内容正确。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        mgr.create_change("feat-auth")

        run_dir = mgr.create_run("feat-auth", "run-001")

        assert Path(run_dir).is_dir()
        state_path = Path(run_dir) / "state.json"
        assert state_path.is_file()

        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["run_id"] == "run-001"
        assert state["change_name"] == "feat-auth"
        assert state["status"] == "running"
        assert state["current_stage"] == "startup"
        assert state["created_at"]


def test_archive_change():
    """归档变更，验证移动到 archive 目录。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        mgr.create_change("old-feature")

        archive_path = mgr.archive_change("old-feature")

        # 原目录不存在
        assert not (Path(tmpdir) / "changes" / "old-feature").exists()

        # 归档目录存在
        archive = Path(archive_path)
        assert archive.exists()
        assert archive.parent.name == "archive"
        assert "old-feature" in archive.name


def test_list_changes():
    """列出活跃变更。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        mgr.create_change("alpha")
        mgr.create_change("beta")
        mgr.create_change("gamma")

        changes = mgr.list_changes()
        names = [c.name for c in changes]
        assert names == ["alpha", "beta", "gamma"]


def test_get_change():
    """获取变更信息。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        mgr.create_change("my-feature")

        info = mgr.get_change("my-feature")
        assert info is not None
        assert info.name == "my-feature"
        assert info.status == "active"


def test_get_change_missing():
    """查询不存在的变更，返回 None。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ChangeManager(tmpdir)
        info = mgr.get_change("nonexistent")
        assert info is None
