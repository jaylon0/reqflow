from core.git_workflow import GitWorkflow, GitStatus


def test_git_status_returns_object():
    """check_status returns GitStatus instance."""
    gw = GitWorkflow(".")
    status = gw.check_status()
    assert isinstance(status, GitStatus)
    assert isinstance(status.branch, str)
    assert isinstance(status.is_clean, bool)
    assert isinstance(status.modified_files, list)
    assert isinstance(status.untracked_files, list)
    assert isinstance(status.last_commit, str)


def test_git_status_branch_detection():
    """check_status returns valid is_main_branch bool."""
    gw = GitWorkflow(".")
    status = gw.check_status()
    assert isinstance(status.is_main_branch, bool)
    if status.branch in ("master", "main"):
        assert status.is_main_branch is True
    else:
        assert status.is_main_branch is False
