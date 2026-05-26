"""ContextManager -- structured context passing between stages."""

from __future__ import annotations

from .models import RunState, Stage


class ContextManager:
    """Builds context for stages from structured artifacts.

    Instead of passing raw conversation history, stages receive
    conclusions and artifacts from previous stages.
    """

    def build_stage_context(self, stage: Stage, state: RunState) -> str:
        """Build context for a stage from previous stage outputs."""
        sections: list[str] = []

        # 1. Requirement (always included)
        sections.append(f"## 需求\n{state.requirement}")

        # 2. Previous stage conclusions
        for prev in state.completed_stages:
            if prev.output and prev.output.analysis:
                sections.append(
                    f"## {prev.stage_id} 结论\n"
                    f"{prev.output.analysis.summary}"
                )

        # 3. Previous stage findings
        for prev in state.completed_stages:
            if prev.output and prev.output.analysis and prev.output.analysis.findings:
                findings_text = "\n".join(
                    f"- {f}" for f in prev.output.analysis.findings
                )
                sections.append(f"## {prev.stage_id} 发现\n{findings_text}")

        # 4. Previous stage artifacts
        for prev in state.completed_stages:
            if prev.output and prev.output.artifacts:
                for artifact in prev.output.artifacts:
                    sections.append(
                        f"## {prev.stage_id} 产物: {artifact.name}\n"
                        f"路径: {artifact.path}\n"
                        f"类型: {artifact.type}\n"
                        f"描述: {artifact.description}"
                    )

        return "\n\n---\n\n".join(sections)


class ContextCompressor:
    """Compresses context to avoid token overflow."""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def compress(self, context: str) -> str:
        """Compress context if it exceeds the token limit."""
        if self._estimate_tokens(context) <= self.max_tokens:
            return context

        # Strategy 1: Keep only recent stages
        context = self._keep_recent_summaries(context, max_stages=3)

        # Strategy 2: Truncate sections based on remaining budget
        sections = context.split("\n\n---\n\n")
        max_chars = self.max_tokens * 4  # convert tokens to chars
        per_section = max_chars // max(1, len(sections))
        context = self._truncate_sections(context, max_per_section=per_section)

        return context

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimation (4 chars per token)."""
        return len(text) // 4

    @staticmethod
    def _truncate_sections(context: str, max_per_section: int) -> str:
        """Truncate each section to max_per_section characters."""
        sections = context.split("\n\n---\n\n")
        truncated = []
        for section in sections:
            if len(section) > max_per_section:
                section = section[:max_per_section] + "\n...(截断)"
            truncated.append(section)
        return "\n\n---\n\n".join(truncated)

    @staticmethod
    def _keep_recent_summaries(context: str, max_stages: int) -> str:
        """Keep only the most recent stage summaries."""
        sections = context.split("\n\n---\n\n")

        # Always keep the requirement section
        requirement_sections = [s for s in sections if s.startswith("## 需求")]
        conclusion_sections = [s for s in sections if "结论" in s]
        other_sections = [
            s for s in sections
            if not s.startswith("## 需求") and "结论" not in s
        ]

        # Keep only recent conclusions
        recent_conclusions = conclusion_sections[-max_stages:]

        return "\n\n---\n\n".join(
            requirement_sections + recent_conclusions + other_sections
        )
