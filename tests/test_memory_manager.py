import tempfile
from pathlib import Path
from reqflow.core.memory_manager import MemoryManager, MemoryEntry


def test_save_and_load():
    mm = MemoryManager()
    entry = mm.save("decision", "Use HMAC signature for auth", stage="design")
    assert isinstance(entry, MemoryEntry)
    assert entry.category == "decision"
    assert entry.content == "Use HMAC signature for auth"
    assert entry.stage == "design"


def test_get_by_category():
    mm = MemoryManager()
    mm.save("decision", "key1", stage="s1")
    mm.save("decision", "key2", stage="s2")
    mm.save("constraint", "key3")
    decisions = mm.get_by_category("decision")
    assert len(decisions) == 2
    constraints = mm.get_by_category("constraint")
    assert len(constraints) == 1


def test_export_markdown():
    mm = MemoryManager()
    mm.save("decision", "Use HMAC auth", stage="design")
    mm.save("constraint", "No direct commits to main")
    md = mm.export_markdown()
    assert "长期记忆" in md
    assert "关键决策" in md
    assert "HMAC auth" in md
    assert "No direct commits" in md


def test_save_and_load_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = str(Path(tmpdir) / "memory.md")
        mm = MemoryManager(md_path)
        mm.save("decision", "Test decision", stage="test")
        mm.save_to_file()

        mm2 = MemoryManager(md_path)
        mm2.load_from_file()
        decisions = mm2.get_decisions()
        assert len(decisions) == 1
        assert "Test decision" in decisions[0].content


def test_export_empty():
    mm = MemoryManager()
    md = mm.export_markdown()
    assert "空" in md


def test_to_list_and_load_from_list():
    mm = MemoryManager()
    mm.save("decision", "d1", stage="s1")
    mm.save("pattern", "p1")
    data = mm.to_list()
    assert len(data) == 2

    mm2 = MemoryManager()
    mm2.load_from_list(data)
    assert len(mm2.load()) == 2
