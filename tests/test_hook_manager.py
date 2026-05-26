"""Tests for core.hook_manager."""

from __future__ import annotations

import pytest

from core.hook_manager import Hook, HookManager


@pytest.fixture
def manager():
    return HookManager()


# ---------------------------------------------------------------------------
# Built-in hooks
# ---------------------------------------------------------------------------


class TestBuiltinHooks:
    def test_has_builtin_hooks(self, manager):
        hooks = manager.list_hooks()
        assert len(hooks) >= 4

    def test_structured_output_hook(self, manager):
        hooks = {h.name: h for h in manager.list_hooks()}
        assert "structured_output" in hooks
        assert "JSON" in hooks["structured_output"].constraint

    def test_no_json_display_hook(self, manager):
        hooks = {h.name: h for h in manager.list_hooks()}
        assert "no_json_display" in hooks

    def test_debate_required_hook(self, manager):
        hooks = {h.name: h for h in manager.list_hooks()}
        debate_hook = hooks["debate_required"]
        assert "PRD理解" in debate_hook.stages
        assert "技术方案" in debate_hook.stages

    def test_concrete_analysis_hook(self, manager):
        hooks = {h.name: h for h in manager.list_hooks()}
        assert "concrete_analysis" in hooks


# ---------------------------------------------------------------------------
# get_constraints
# ---------------------------------------------------------------------------


class TestGetConstraints:
    def test_returns_all_hooks_for_wildcard(self, manager):
        constraints = manager.get_constraints("claude-code", "analysis")
        assert "structured_output" in constraints
        assert "no_json_display" in constraints
        assert "concrete_analysis" in constraints

    def test_includes_debate_hook_for_matching_stage(self, manager):
        constraints = manager.get_constraints("claude-code", "PRD理解")
        assert "debate_required" in constraints

    def test_excludes_debate_hook_for_non_matching_stage(self, manager):
        constraints = manager.get_constraints("claude-code", "context_discovery")
        assert "debate_required" not in constraints

    def test_returns_empty_for_no_matching_hooks(self):
        manager = HookManager()
        # Add a hook that only applies to a specific platform
        manager.add_hook(Hook(
            name="specific",
            constraint="Only for codex",
            platforms=["codex"],
            stages=["analysis"],
        ))
        # claude-code should not get this hook
        constraints = manager.get_constraints("claude-code", "analysis")
        assert "specific" not in constraints


# ---------------------------------------------------------------------------
# Hook.applies_to
# ---------------------------------------------------------------------------


class TestHookAppliesTo:
    def test_wildcard_matches_all(self):
        hook = Hook(name="test", constraint="test")
        assert hook.applies_to("any-platform", "any-stage")

    def test_specific_platform_match(self):
        hook = Hook(name="test", constraint="test", platforms=["claude-code"])
        assert hook.applies_to("claude-code", "analysis")
        assert not hook.applies_to("codex", "analysis")

    def test_specific_stage_match(self):
        hook = Hook(name="test", constraint="test", stages=["PRD理解"])
        assert hook.applies_to("claude-code", "PRD理解")
        assert not hook.applies_to("claude-code", "analysis")

    def test_multiple_platforms(self):
        hook = Hook(name="test", constraint="test", platforms=["claude-code", "codex"])
        assert hook.applies_to("claude-code", "analysis")
        assert hook.applies_to("codex", "analysis")
        assert not hook.applies_to("cursor", "analysis")


# ---------------------------------------------------------------------------
# Hook.render
# ---------------------------------------------------------------------------


class TestHookRender:
    def test_render_format(self):
        hook = Hook(name="my_hook", constraint="Do something")
        assert hook.render() == "[my_hook] Do something"


# ---------------------------------------------------------------------------
# add_hook
# ---------------------------------------------------------------------------


class TestAddHook:
    def test_add_custom_hook(self, manager):
        initial_count = len(manager.list_hooks())
        manager.add_hook(Hook(name="custom", constraint="Custom constraint"))
        assert len(manager.list_hooks()) == initial_count + 1

    def test_custom_hook_appears_in_constraints(self, manager):
        manager.add_hook(Hook(
            name="custom",
            constraint="Custom constraint for analysis",
            stages=["analysis"],
        ))
        constraints = manager.get_constraints("claude-code", "analysis")
        assert "custom" in constraints
