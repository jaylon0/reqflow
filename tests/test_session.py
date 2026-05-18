import json
from pathlib import Path
from reqflow.core.session import Session

def test_session_create(tmp_path):
    session = Session(session_id="test-1", storage_dir=str(tmp_path))
    assert session.session_id == "test-1"

def test_session_save_get_context(tmp_path):
    session = Session(session_id="test-2", storage_dir=str(tmp_path))
    session.save_context("project", "reqflow")
    session.save_context("requirement", "add auth")
    assert session.get_context("project") == "reqflow"
    assert session.get_context("requirement") == "add auth"
    assert session.get_context("nonexistent") is None

def test_session_persistence(tmp_path):
    session = Session(session_id="test-3", storage_dir=str(tmp_path))
    session.save_context("key", "value")
    session.save()
    session2 = Session(session_id="test-3", storage_dir=str(tmp_path))
    session2.load()
    assert session2.get_context("key") == "value"

def test_session_history(tmp_path):
    session = Session(session_id="test-4", storage_dir=str(tmp_path))
    session.add_history("step1", "analyzed requirement")
    session.add_history("step2", "wrote code")
    assert len(session.history) == 2
    assert session.history[0]["step"] == "step1"

def test_session_summarize(tmp_path):
    session = Session(session_id="test-5", storage_dir=str(tmp_path))
    session.add_history("step1", "a" * 500)
    session.add_history("step2", "b" * 500)
    summary = session.summarize(max_length=100)
    assert len(summary) <= 100

def test_session_list_sessions(tmp_path):
    Session(session_id="s1", storage_dir=str(tmp_path)).save()
    Session(session_id="s2", storage_dir=str(tmp_path)).save()
    sessions = Session.list_sessions(str(tmp_path))
    assert "s1" in sessions
    assert "s2" in sessions
