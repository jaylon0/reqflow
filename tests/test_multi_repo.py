import os
import pytest
from pathlib import Path
from core.multi_repo import MultiRepo


@pytest.fixture
def mr():
    return MultiRepo()


def test_add_repo(mr):
    """add_repo creates and returns a RepoInfo."""
    repo = mr.add_repo("frontend", "/app/frontend")
    assert repo.name == "frontend"
    assert repo.path == "/app/frontend"
    assert repo.is_primary is False


def test_get_primary(mr):
    """add_repo with is_primary=True, get_primary returns it."""
    mr.add_repo("backend", "/app/backend", is_primary=True)
    primary = mr.get_primary()
    assert primary is not None
    assert primary.name == "backend"
    assert primary.is_primary is True


def test_get_primary_none(mr):
    """no repos, get_primary returns None."""
    assert mr.get_primary() is None


def test_add_repo_switches_primary(mr):
    """adding a new primary clears old primary."""
    mr.add_repo("a", "/a", is_primary=True)
    mr.add_repo("b", "/b", is_primary=True)
    assert mr.get_primary().name == "b"
    assert mr.get_by_name("a").is_primary is False


def test_get_by_name(mr):
    """get_by_name returns correct repo."""
    mr.add_repo("svc", "/svc")
    repo = mr.get_by_name("svc")
    assert repo is not None
    assert repo.path == "/svc"


def test_get_by_name_missing(mr):
    """get_by_name returns None for unknown name."""
    assert mr.get_by_name("nope") is None


def test_list_repos(mr):
    """list_repos returns dicts with expected keys."""
    mr.add_repo("x", "/x", is_primary=True)
    mr.add_repo("y", "/y")
    repos = mr.list_repos()
    assert len(repos) == 2
    assert repos[0]["name"] == "x"
    assert repos[0]["is_primary"] is True
    assert repos[1]["name"] == "y"
    assert repos[1]["is_primary"] is False


def test_detect_repos_with_git_dir(tmp_path):
    """detect_repos finds a directory with .git."""
    repo_dir = tmp_path / "myproject"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    mr = MultiRepo()
    detected = mr.detect_repos(str(tmp_path))
    assert len(detected) == 1
    assert detected[0].name == "myproject"
    assert detected[0].is_primary is True


def test_detect_repos_base_is_repo(tmp_path):
    """detect_repos detects base_dir itself as a repo."""
    (tmp_path / ".git").mkdir()

    mr = MultiRepo()
    detected = mr.detect_repos(str(tmp_path))
    assert len(detected) == 1
    assert detected[0].name == tmp_path.name


def test_detect_repos_no_git(tmp_path):
    """detect_repos returns empty for dir with no .git."""
    (tmp_path / "notarepo").mkdir()

    mr = MultiRepo()
    detected = mr.detect_repos(str(tmp_path))
    assert len(detected) == 0


def test_detect_repos_nonexistent_dir(mr):
    """detect_repos returns empty for nonexistent dir."""
    detected = mr.detect_repos("/nonexistent/path")
    assert len(detected) == 0
