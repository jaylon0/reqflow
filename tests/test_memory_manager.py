import tempfile
from pathlib import Path
from core.memory_manager import MemoryManager


def test_save_and_load():
    """save with category/key/value, load and verify."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mm = MemoryManager(tmpdir)
        result = mm.save("decision", "auth_method", "Use HMAC signature for auth")
        assert result["category"] == "decision"
        assert result["key"] == "auth_method"
        assert result["value"] == "Use HMAC signature for auth"

        loaded = mm.load("decision", "auth_method")
        assert loaded["category"] == "decision"
        assert loaded["key"] == "auth_method"
        assert loaded["value"] == "Use HMAC signature for auth"


def test_load_category():
    """save multiple entries, load by category."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mm = MemoryManager(tmpdir)
        mm.save("decision", "key1", "value1")
        mm.save("decision", "key2", "value2")
        mm.save("constraint", "key3", "value3")

        decisions = mm.load("decision")
        assert decisions["category"] == "decision"
        assert len(decisions["entries"]) == 2
        assert decisions["entries"]["key1"] == "value1"
        assert decisions["entries"]["key2"] == "value2"


def test_load_all():
    """save entries in different categories, load all."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mm = MemoryManager(tmpdir)
        mm.save("decision", "key1", "value1")
        mm.save("constraint", "key2", "value2")

        all_memories = mm.load()
        assert "decision" in all_memories
        assert "constraint" in all_memories
        assert all_memories["decision"]["key1"] == "value1"
        assert all_memories["constraint"]["key2"] == "value2"


def test_markdown_generated():
    """save, verify memory.md exists with content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mm = MemoryManager(tmpdir)
        mm.save("decision", "auth", "Use HMAC")

        md_path = Path(tmpdir) / "memory.md"
        assert md_path.exists()
        content = md_path.read_text()
        assert "decision" in content
        assert "auth" in content
        assert "Use HMAC" in content
