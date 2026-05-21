from reqflow.core.git_workflow import GitWorkflow, BranchStatus, CommitResult, PROTECTED_BRANCHES


def test_check_branch_returns_status():
    gw = GitWorkflow(".")
    status = gw.check_branch()
    assert isinstance(status, BranchStatus)
    assert status.current_branch
    assert isinstance(status.is_protected, bool)
    assert isinstance(status.uncommitted_files, list)
    assert isinstance(status.last_commit, str)


def test_check_uncommitted():
    gw = GitWorkflow(".")
    files = gw.check_uncommitted()
    assert isinstance(files, list)


def test_is_on_protected_branch():
    gw = GitWorkflow(".")
    result = gw.is_on_protected_branch()
    assert isinstance(result, bool)


def test_protected_branches():
    assert "master" in PROTECTED_BRANCHES
    assert "main" in PROTECTED_BRANCHES


def test_to_dict():
    gw = GitWorkflow(".")
    d = gw.to_dict()
    assert "branch" in d
    assert "is_master" in d
    assert "uncommitted" in d
