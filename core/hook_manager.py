"""HookManager -- behavior constraint injection via system prompts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Hook:
    """A behavior constraint hook."""
    name: str
    constraint: str
    platforms: list[str] = field(default_factory=lambda: ["*"])
    stages: list[str] = field(default_factory=lambda: ["*"])

    def applies_to(self, platform: str, stage_id: str) -> bool:
        """Check if this hook applies to the given platform and stage."""
        platform_match = "*" in self.platforms or platform in self.platforms
        stage_match = "*" in self.stages or stage_id in self.stages
        return platform_match and stage_match

    def render(self) -> str:
        """Render the hook as a constraint string."""
        return f"[{self.name}] {self.constraint}"


class HookManager:
    """Manages behavior constraints injected into agent system prompts."""

    def __init__(self):
        self._hooks: list[Hook] = self._load_builtin_hooks()

    def get_constraints(self, platform: str, stage_id: str) -> str:
        """Get all applicable constraints for a platform and stage."""
        constraints = []
        for hook in self._hooks:
            if hook.applies_to(platform, stage_id):
                constraints.append(hook.render())
        return "\n".join(constraints)

    def add_hook(self, hook: Hook) -> None:
        """Add a custom hook."""
        self._hooks.append(hook)

    def list_hooks(self) -> list[Hook]:
        """List all registered hooks."""
        return list(self._hooks)

    @staticmethod
    def _load_builtin_hooks() -> list[Hook]:
        """Load built-in behavior constraints."""
        return [
            Hook(
                name="structured_output",
                constraint="必须返回 JSON 格式的结构化数据，不得返回自由文本",
            ),
            Hook(
                name="no_json_display",
                constraint="不得在对话中展示工具返回的原始 JSON，必须用自己的语言描述",
            ),
            Hook(
                name="debate_required",
                stages=["PRD理解", "技术方案", "代码审查", "交付验证"],
                constraint="必须进行至少 2 轮结构化辩论，每轮必须包含交叉评论",
            ),
            Hook(
                name="concrete_analysis",
                constraint="分析内容必须包含具体文件路径、代码引用或技术细节，不能是泛泛而谈",
            ),
        ]
