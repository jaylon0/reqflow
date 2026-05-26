"""Tests for SkillRegistry and SkillLoader."""

from __future__ import annotations

import pytest
from pathlib import Path

from core.skill_registry import SkillRegistry, SkillMeta
from core.skill_loader import SkillLoader, SkillNotFoundError


@pytest.fixture
def skills_dir(tmp_path):
    """Create a temporary skills directory with a test skill."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
---

# Test Skill

This is test content.
""")
    return tmp_path


@pytest.fixture
def multi_skills_dir(tmp_path):
    """Create a skills directory with multiple skills."""
    for name, desc in [
        ("skill-a", "First skill"),
        ("skill-b", "Second skill"),
        ("skill-c", "Third skill"),
    ]:
        skill_dir = tmp_path / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"""---
name: {name}
description: {desc}
---

# {name}

Content for {name}.
""")
    return tmp_path


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------


class TestSkillRegistry:
    def test_scans_skills(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        assert "test-skill" in [s.name for s in registry.list_all()]

    def test_get_skill(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        meta = registry.get("test-skill")
        assert meta is not None
        assert meta.description == "A test skill"
        assert "Test Skill" in meta.content

    def test_get_nonexistent(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        assert registry.get("nonexistent") is None

    def test_list_all(self, multi_skills_dir):
        registry = SkillRegistry(multi_skills_dir)
        all_skills = registry.list_all()
        assert len(all_skills) == 3
        names = {s.name for s in all_skills}
        assert names == {"skill-a", "skill-b", "skill-c"}

    def test_list_by_category(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        # All skills default to "stage" category
        stage_skills = registry.list_by_category("stage")
        assert len(stage_skills) == 1

        utility_skills = registry.list_by_category("utility")
        assert len(utility_skills) == 0

    def test_empty_directory(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        registry = SkillRegistry(empty_dir)
        assert registry.list_all() == []

    def test_nonexistent_directory(self, tmp_path):
        registry = SkillRegistry(tmp_path / "nonexistent")
        assert registry.list_all() == []

    def test_ignores_non_skill_files(self, tmp_path):
        """Non-SKILL.md files should be ignored."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "README.md").write_text("# Not a skill")
        (skill_dir / "SKILL.md").write_text("""---
name: real-skill
description: Real
---

Content
""")
        registry = SkillRegistry(tmp_path)
        assert len(registry.list_all()) == 1
        assert registry.get("real-skill") is not None

    def test_ignores_files_at_root(self, tmp_path):
        """Files (not directories) in skills dir should be ignored."""
        (tmp_path / "random.md").write_text("# Not a skill")
        registry = SkillRegistry(tmp_path)
        assert registry.list_all() == []

    def test_fallback_name_from_directory(self, tmp_path):
        """If SKILL.md has no name field, use directory name."""
        skill_dir = tmp_path / "my-dir-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
description: No name field
---

Content
""")
        registry = SkillRegistry(tmp_path)
        meta = registry.get("my-dir-name")
        assert meta is not None


# ---------------------------------------------------------------------------
# SkillLoader
# ---------------------------------------------------------------------------


class TestSkillLoader:
    def test_loads_content(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        loader = SkillLoader(registry)
        content = loader.load("test-skill")
        assert "Test Skill" in content

    def test_caches_content(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        loader = SkillLoader(registry)
        content1 = loader.load("test-skill")
        content2 = loader.load("test-skill")
        assert content1 is content2  # same object reference

    def test_raises_on_missing(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        loader = SkillLoader(registry)
        with pytest.raises(SkillNotFoundError) as exc_info:
            loader.load("nonexistent")
        assert exc_info.value.skill_name == "nonexistent"

    def test_load_for_stage(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        loader = SkillLoader(registry)
        content = loader.load_for_stage("analysis", ["test-skill"], [])
        assert "Required Skill: test-skill" in content

    def test_load_for_stage_methodology(self, skills_dir):
        registry = SkillRegistry(skills_dir)
        loader = SkillLoader(registry)
        content = loader.load_for_stage("analysis", [], ["test-skill"])
        assert "Methodology: test-skill" in content

    def test_load_for_stage_missing_skill_skipped(self, skills_dir):
        """Missing skills in load_for_stage should be silently skipped."""
        registry = SkillRegistry(skills_dir)
        loader = SkillLoader(registry)
        content = loader.load_for_stage("analysis", ["nonexistent"], [])
        assert content == ""

    def test_load_for_stage_multiple(self, multi_skills_dir):
        registry = SkillRegistry(multi_skills_dir)
        loader = SkillLoader(registry)
        content = loader.load_for_stage(
            "analysis", ["skill-a", "skill-b"], ["skill-c"]
        )
        assert "Required Skill: skill-a" in content
        assert "Required Skill: skill-b" in content
        assert "Methodology: skill-c" in content
