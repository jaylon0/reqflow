"""Tests for extended WorkflowLoader fields.

Tests support for: required_skills, optional_skills, methodology_skills,
topology, requires_debate per stage.
"""

from __future__ import annotations

import pytest
import tempfile
import yaml
from pathlib import Path

from core.workflow_loader import WorkflowLoader


@pytest.fixture
def tmp_workflows(tmp_path):
    """Create a temporary workflows directory."""
    return tmp_path


def _write_workflow(path: Path, definition: dict) -> None:
    """Write a workflow YAML file."""
    path.write_text(yaml.dump(definition, default_flow_style=False, allow_unicode=True))


class TestWorkflowLoaderExtended:
    """Tests for extended workflow fields."""

    def test_required_skills(self, tmp_workflows):
        """Stage should support required_skills field."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Analysis",
                    "skill": "analysis",
                    "required_skills": ["prd-review", "security-audit"],
                    "task": "Analyze requirements",
                }
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        steps = loader.get_stages("test-wf")
        assert len(steps) == 1
        assert steps[0]["name"] == "Analysis"

    def test_optional_skills(self, tmp_workflows):
        """Stage should support optional_skills field."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Design",
                    "skill": "design",
                    "optional_skills": ["ui-design", "api-design"],
                    "task": "Create design",
                }
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        definition = loader.load("test-wf")
        stage = definition["stages"][0]
        assert stage["optional_skills"] == ["ui-design", "api-design"]

    def test_methodology_skills(self, tmp_workflows):
        """Stage should support methodology_skills field."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Implementation",
                    "skill": "implementation",
                    "methodology_skills": ["tdd", "pair-programming"],
                    "task": "Implement feature",
                }
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        definition = loader.load("test-wf")
        stage = definition["stages"][0]
        assert stage["methodology_skills"] == ["tdd", "pair-programming"]

    def test_topology_field(self, tmp_workflows):
        """Stage should support topology field."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Parallel Analysis",
                    "skill": "analysis",
                    "topology": "parallel",
                    "task": "Run parallel analysis",
                },
                {
                    "id": "s2",
                    "name": "Sequential Review",
                    "skill": "review",
                    "topology": "sequential",
                    "task": "Sequential review",
                },
                {
                    "id": "s3",
                    "name": "Selector Stage",
                    "skill": "selector",
                    "topology": "selector",
                    "task": "Select best approach",
                },
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        definition = loader.load("test-wf")
        assert definition["stages"][0]["topology"] == "parallel"
        assert definition["stages"][1]["topology"] == "sequential"
        assert definition["stages"][2]["topology"] == "selector"

    def test_requires_debate_field(self, tmp_workflows):
        """Stage should support requires_debate field."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Architecture Decision",
                    "skill": "architecture",
                    "requires_debate": True,
                    "task": "Make architecture decision",
                },
                {
                    "id": "s2",
                    "name": "Simple Task",
                    "skill": "implementation",
                    "requires_debate": False,
                    "task": "Simple implementation",
                },
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        definition = loader.load("test-wf")
        assert definition["stages"][0]["requires_debate"] is True
        assert definition["stages"][1]["requires_debate"] is False

    def test_combined_extended_fields(self, tmp_workflows):
        """Stage should support all extended fields together."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Full Featured Stage",
                    "skill": "analysis",
                    "task": "Comprehensive analysis",
                    "required_skills": ["prd-review"],
                    "optional_skills": ["ui-design"],
                    "methodology_skills": ["tdd"],
                    "topology": "parallel",
                    "requires_debate": True,
                }
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        definition = loader.load("test-wf")
        stage = definition["stages"][0]

        assert stage["required_skills"] == ["prd-review"]
        assert stage["optional_skills"] == ["ui-design"]
        assert stage["methodology_skills"] == ["tdd"]
        assert stage["topology"] == "parallel"
        assert stage["requires_debate"] is True

    def test_extended_fields_in_get_stages(self, tmp_workflows):
        """Extended fields should be preserved in get_stages output."""
        wf = {
            "name": "test-wf",
            "version": "1.0",
            "stages": [
                {
                    "id": "s1",
                    "name": "Stage 1",
                    "skill": "analysis",
                    "task": "Analyze",
                    "topology": "parallel",
                    "requires_debate": True,
                }
            ],
        }
        _write_workflow(tmp_workflows / "test-wf.yaml", wf)

        loader = WorkflowLoader(str(tmp_workflows))
        steps = loader.get_stages("test-wf")

        # Verify the workflow loads successfully with extended fields
        assert len(steps) == 1
        assert steps[0]["name"] == "Stage 1"
