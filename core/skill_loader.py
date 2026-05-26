"""SkillLoader -- loads SKILL.md content with caching."""

from __future__ import annotations

from .skill_registry import SkillRegistry


class SkillNotFoundError(Exception):
    """Raised when a skill is not found in the registry."""

    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        super().__init__(f"Skill not found: {skill_name}")


class SkillLoader:
    """Loads skill content from the registry with caching."""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self._cache: dict[str, str] = {}

    def load(self, skill_name: str) -> str:
        """Load a single skill's content."""
        if skill_name in self._cache:
            return self._cache[skill_name]

        meta = self.registry.get(skill_name)
        if not meta:
            raise SkillNotFoundError(skill_name)

        self._cache[skill_name] = meta.content
        return meta.content

    def load_for_stage(
        self,
        stage_id: str,
        required: list[str],
        methodology: list[str],
    ) -> str:
        """Load all skills needed for a stage."""
        sections: list[str] = []

        for skill_name in required:
            try:
                content = self.load(skill_name)
                sections.append(f"## Required Skill: {skill_name}\n{content}")
            except SkillNotFoundError:
                pass

        for skill_name in methodology:
            try:
                content = self.load(skill_name)
                sections.append(f"## Methodology: {skill_name}\n{content}")
            except SkillNotFoundError:
                pass

        return "\n\n---\n\n".join(sections)
