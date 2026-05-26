"""SkillRegistry -- unified management of all available Skills."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillMeta:
    """Skill metadata."""
    name: str
    description: str
    category: str  # "stage" | "methodology" | "utility" | "external"
    tools: list[str] = field(default_factory=list)
    content: str = ""
    auto_load: bool = False
    applicable_stages: list[str] = field(default_factory=list)


class SkillRegistry:
    """Skill registry -- scans and manages all available skills."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._skills: dict[str, SkillMeta] = {}
        if skills_dir.exists():
            self._scan_skills()

    def _scan_skills(self) -> None:
        """Scan skills directory and register all skills."""
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                meta = self._parse_skill_meta(skill_md)
                if meta:
                    self._skills[meta.name] = meta

    def _parse_skill_meta(self, path: Path) -> SkillMeta | None:
        """Parse SKILL.md frontmatter and body."""
        try:
            content = path.read_text(encoding="utf-8")
            # Parse YAML frontmatter
            match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
            if not match:
                return None

            frontmatter = match.group(1)
            body = match.group(2)

            name = self._extract_field(frontmatter, "name") or path.parent.name
            desc = self._extract_field(frontmatter, "description") or ""

            return SkillMeta(
                name=name,
                description=desc.strip(),
                category="stage",
                content=body.strip(),
            )
        except Exception:
            return None

    @staticmethod
    def _extract_field(text: str, field_name: str) -> str | None:
        """Extract a YAML field value from frontmatter text."""
        match = re.search(rf"^{field_name}:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else None

    def get(self, name: str) -> SkillMeta | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_all(self) -> list[SkillMeta]:
        """List all registered skills."""
        return list(self._skills.values())

    def list_by_category(self, category: str) -> list[SkillMeta]:
        """List skills filtered by category."""
        return [s for s in self._skills.values() if s.category == category]
