"""Tests for ContextManager and ContextCompressor."""

from __future__ import annotations

import pytest

from core.context_manager import ContextCompressor, ContextManager
from core.models import (
    Artifact,
    RunState,
    Stage,
    StageAnalysis,
    StageOutput,
    StageState,
)


@pytest.fixture
def context_manager():
    return ContextManager()


@pytest.fixture
def compressor():
    return ContextCompressor(max_tokens=100)  # small limit for testing


def _make_stage() -> Stage:
    return Stage(id="planning", name="计划", task="制定计划")


def _make_state_with_history() -> RunState:
    return RunState(
        run_id="test-001",
        requirement="添加用户认证功能",
        routing_level="L3",
        stages=[
            StageState(
                stage_id="analysis",
                status="completed",
                output=StageOutput(
                    stage_id="analysis",
                    status="completed",
                    analysis=StageAnalysis(
                        summary="分析结果显示需要添加 JWT 认证",
                        findings=["现有系统无认证", "需要用户表", "需要登录接口"],
                    ),
                    artifacts=[
                        Artifact(
                            name="auth-spec.md",
                            path="/tmp/auth-spec.md",
                            type="file",
                            description="认证规范文档",
                        )
                    ],
                ),
            ),
            StageState(stage_id="planning", status="pending"),
        ],
    )


# ---------------------------------------------------------------------------
# ContextManager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_includes_requirement(self, context_manager):
        state = RunState(requirement="测试需求")
        stage = _make_stage()
        context = context_manager.build_stage_context(stage, state)
        assert "测试需求" in context

    def test_includes_previous_conclusions(self, context_manager):
        state = _make_state_with_history()
        stage = _make_stage()
        context = context_manager.build_stage_context(stage, state)
        assert "JWT 认证" in context

    def test_includes_previous_findings(self, context_manager):
        state = _make_state_with_history()
        stage = _make_stage()
        context = context_manager.build_stage_context(stage, state)
        assert "现有系统无认证" in context
        assert "需要用户表" in context

    def test_includes_previous_artifacts(self, context_manager):
        state = _make_state_with_history()
        stage = _make_stage()
        context = context_manager.build_stage_context(stage, state)
        assert "auth-spec.md" in context
        assert "/tmp/auth-spec.md" in context

    def test_empty_state(self, context_manager):
        state = RunState(requirement="需求")
        stage = _make_stage()
        context = context_manager.build_stage_context(stage, state)
        assert "需求" in context
        # Should not crash with empty stages
        assert isinstance(context, str)


# ---------------------------------------------------------------------------
# ContextCompressor
# ---------------------------------------------------------------------------


class TestContextCompressor:
    def test_short_context_unchanged(self, compressor):
        context = "Short context"
        assert compressor.compress(context) == context

    def test_long_context_compressed(self, compressor):
        # Create context with multiple sections that exceed token limit
        sections = ["## Section\n" + "B" * 600 for _ in range(3)]
        context = "\n\n---\n\n".join(sections)
        compressed = compressor.compress(context)
        assert len(compressed) < len(context)
        assert "截断" in compressed

    def test_preserves_structure(self, compressor):
        sections = ["Section 1 " * 200, "Section 2 " * 200]
        context = "\n\n---\n\n".join(sections)
        compressed = compressor.compress(context)
        # Should still have separator
        assert "---" in compressed

    def test_token_estimation(self):
        assert ContextCompressor._estimate_tokens("abcd") == 1
        assert ContextCompressor._estimate_tokens("a" * 400) == 100

    def test_keep_recent_summaries(self):
        compressor = ContextCompressor(max_tokens=10000)
        sections = [
            "## 需求\nTest",
            "## analysis 结论\nFirst conclusion",
            "## planning 结论\nSecond conclusion",
            "## design 结论\nThird conclusion",
            "## extra\nOther content",
        ]
        context = "\n\n---\n\n".join(sections)
        compressed = compressor._keep_recent_summaries(context, max_stages=2)
        # Should keep requirement + last 2 conclusions
        assert "需求" in compressed
        assert "Second conclusion" in compressed
        assert "Third conclusion" in compressed
        # First conclusion should be dropped
        assert "First conclusion" not in compressed
