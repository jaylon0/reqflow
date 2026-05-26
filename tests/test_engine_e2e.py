"""End-to-end integration test for the Engine workflow.

Tests: load workflow -> execute stages -> validate output -> save checkpoint -> query via MCPBridge.
"""

from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

from core.models import (
    AgentRole,
    Risk,
    RunState,
    Stage,
    StageOutput,
    StageState,
)
from core.output_validator import OutputValidator
from core.stage_executor import StageExecutor
from core.workflow_engine import WorkflowEngine, Workflow
from core.checkpoint_manager import CheckpointManager
from core.engine_mcp_bridge import EngineMCPBridge


def _mock_agent_handler(requirement: str = "Test requirement"):
    """Create a mock agent handler that returns valid structured JSON."""

    async def handler(prompt: str) -> str:
        # Generate a valid AgentReport JSON
        report = {
            "agent_role": "engineer",
            "task": "Execute stage task",
            "conclusion": "This is a detailed conclusion that meets the minimum length requirement. "
                         "The analysis covers all aspects of the requirement and provides clear recommendations.",
            "confidence": 0.85,
            "findings": [
                "Finding 1: The requirement is well-defined and actionable",
                "Finding 2: The architecture supports the required functionality",
                "Finding 3: Testing coverage is adequate for the scope",
            ],
            "recommendations": [
                "Recommendation 1: Proceed with implementation",
                "Recommendation 2: Add integration tests",
            ],
            "risks": [
                {"level": "low", "description": "Minor performance impact expected"},
            ],
            "skills_requested": [],
        }
        return json.dumps(report)

    return handler


def _create_test_stages(count: int = 3) -> list[Stage]:
    """Create test stages."""
    stages = []
    for i in range(count):
        stages.append(
            Stage(
                id=f"stage-{i + 1}",
                name=f"Stage {i + 1}",
                skill="analysis",
                task=f"Execute task {i + 1}",
                agents=[AgentRole(role="engineer", task=f"Task {i + 1}")],
                required_skills=[],
            )
        )
    return stages


class TestEngineE2E:
    """End-to-end engine tests."""

    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, tmp_path):
        """Test complete workflow: load -> execute -> validate -> checkpoint -> query."""
        # Setup
        checkpoint_dir = tmp_path / "checkpoints"
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        validator = OutputValidator()
        engine = WorkflowEngine(
            executor=executor,
            validator=validator,
            checkpoint_dir=checkpoint_dir,
        )

        # Create workflow
        stages = _create_test_stages(3)
        workflow = Workflow(name="test-workflow", version="1.0", stages=stages)

        # Execute
        result = await engine.run(
            requirement="Build a simple API endpoint",
            workflow=workflow,
            routing_level="L3",
        )

        # Verify execution completed
        assert result.status == "completed"
        assert result.error is None
        assert result.state.status == "completed"
        assert result.state.requirement == "Build a simple API endpoint"

        # Verify all stages completed
        for stage_state in result.state.stages:
            assert stage_state.status == "completed"
            assert stage_state.output is not None
            assert stage_state.output.status == "completed"

        # Verify checkpoints were saved
        assert checkpoint_dir.exists()
        checkpoints = list(checkpoint_dir.glob("*.json"))
        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_checkpoint_save_and_restore(self, tmp_path):
        """Test that checkpoints can be saved and restored."""
        checkpoint_dir = tmp_path / "checkpoints"
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(
            executor=executor,
            checkpoint_dir=checkpoint_dir,
        )

        stages = _create_test_stages(2)
        workflow = Workflow(name="test-wf", version="1.0", stages=stages)

        result = await engine.run("Test requirement", workflow)

        # Verify checkpoints exist
        checkpoint_manager = CheckpointManager(tmp_path)
        # Manually save a checkpoint for testing restore
        stage_output = result.state.stages[0].output
        checkpoint_manager.save("stage-1", stage_output, result.state)

        # Restore
        restored = checkpoint_manager.restore("stage-1")
        assert restored is not None
        output_dict, state_dict = restored
        assert output_dict["stage_id"] == "stage-1"
        assert output_dict["status"] == "completed"

    @pytest.mark.asyncio
    async def test_mcp_bridge_query(self, tmp_path):
        """Test querying run status via MCPBridge."""
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(executor=executor)

        stages = _create_test_stages(2)
        workflow = Workflow(name="test-wf", version="1.0", stages=stages)

        result = await engine.run("Test requirement", workflow)

        # Query via MCPBridge
        bridge = EngineMCPBridge(engine)
        run_id = result.state.run_id

        status = await bridge.handle_status(run_id)
        assert status["run_id"] == run_id
        assert status["status"] == "completed"
        assert "2/2" in status["progress"]

    @pytest.mark.asyncio
    async def test_mcp_bridge_accept_reject(self, tmp_path):
        """Test accept/reject via MCPBridge."""
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(executor=executor)

        stages = _create_test_stages(1)
        workflow = Workflow(name="test-wf", version="1.0", stages=stages)

        result = await engine.run("Test requirement", workflow)
        bridge = EngineMCPBridge(engine)
        run_id = result.state.run_id

        # Test accept
        accept_result = await bridge.handle_accept(run_id)
        assert accept_result["status"] == "accepted"

        # Verify state updated
        status = await bridge.handle_status(run_id)
        assert status["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_mcp_bridge_reject_with_reason(self, tmp_path):
        """Test rejection with reason via MCPBridge."""
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(executor=executor)

        stages = _create_test_stages(1)
        workflow = Workflow(name="test-wf", version="1.0", stages=stages)

        result = await engine.run("Test requirement", workflow)
        bridge = EngineMCPBridge(engine)
        run_id = result.state.run_id

        # Test reject
        reject_result = await bridge.handle_reject(run_id, "Missing feature X")
        assert reject_result["status"] == "rejected"
        assert reject_result["reason"] == "Missing feature X"

    @pytest.mark.asyncio
    async def test_mcp_bridge_nonexistent_run(self):
        """Test querying non-existent run."""
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(executor=executor)
        bridge = EngineMCPBridge(engine)

        status = await bridge.handle_status("nonexistent-run")
        assert "error" in status

    @pytest.mark.asyncio
    async def test_stage_output_serialization(self, tmp_path):
        """Test that StageOutput can be serialized and deserialized."""
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(executor=executor)

        stages = _create_test_stages(1)
        workflow = Workflow(name="test-wf", version="1.0", stages=stages)

        result = await engine.run("Test requirement", workflow)
        stage_state = result.state.stages[0]

        # Serialize
        output_dict = stage_state.output.to_dict()
        assert isinstance(output_dict, dict)
        assert output_dict["stage_id"] == "stage-1"

        # Deserialize
        restored = StageOutput.from_dict(output_dict)
        assert restored.stage_id == "stage-1"
        assert restored.status == "completed"
        assert len(restored.agent_reports) > 0
        assert len(restored.analysis.findings) > 0

    @pytest.mark.asyncio
    async def test_run_state_serialization(self, tmp_path):
        """Test that RunState can be serialized and deserialized."""
        handler = _mock_agent_handler()
        executor = StageExecutor(agent_handler=handler)
        engine = WorkflowEngine(executor=executor)

        stages = _create_test_stages(2)
        workflow = Workflow(name="test-wf", version="1.0", stages=stages)

        result = await engine.run("Test requirement", workflow)

        # Serialize
        state_dict = result.state.to_dict()
        assert isinstance(state_dict, dict)

        # Deserialize
        restored = RunState.from_dict(state_dict)
        assert restored.run_id == result.state.run_id
        assert restored.status == "completed"
        assert len(restored.stages) == 2
