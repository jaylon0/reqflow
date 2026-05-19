"""Tests for AgentCoordinator."""

import asyncio

from reqflow.core.agent_coordinator import AgentCoordinator, AgentResult, DispatchRule


# --- Fixtures ---

SAMPLE_CONFIG = {
    "mode": "supervised_agents",
    "dispatch": [
        {
            "type": "dev",
            "agent": "dev-agent",
            "model_selection": {
                "opus": "database schema changes",
                "sonnet": "standard API changes",
            },
        },
        {
            "type": "verify",
            "agent": "verify-agent",
            "parallel_with": "review",
        },
        {
            "type": "review",
            "agent": "review-agent",
            "parallel_with": "verify",
        },
    ],
    "repair": {
        "max_rounds": 3,
        "strategy": "resume_dev_agent",
    },
    "output_contracts": {
        "dev": "DEV_STATUS: success|failed\nFILES_CHANGED:\nSUMMARY:",
        "verify": "VERIFY_STATUS: pass|fail\nBUILD_RESULT: pass|fail\nTEST_RESULT: pass|fail",
        "review": "REVIEW_STATUS: pass|fail\nSPEC_COMPLIANCE: pass|fail\nCODE_QUALITY: pass|fail",
    },
}


def _make_coordinator() -> AgentCoordinator:
    return AgentCoordinator(SAMPLE_CONFIG)


# --- Tests ---


def test_coordinator_parses_dispatch_rules():
    """Verify rules parsed correctly from config."""
    coord = _make_coordinator()

    assert len(coord.dispatch_rules) == 3

    dev_rule = coord.dispatch_rules[0]
    assert isinstance(dev_rule, DispatchRule)
    assert dev_rule.type == "dev"
    assert dev_rule.agent == "dev-agent"
    assert dev_rule.parallel_with is None
    assert dev_rule.model_selection is not None

    verify_rule = coord.dispatch_rules[1]
    assert verify_rule.type == "verify"
    assert verify_rule.agent == "verify-agent"
    assert verify_rule.parallel_with == "review"

    review_rule = coord.dispatch_rules[2]
    assert review_rule.type == "review"
    assert review_rule.agent == "review-agent"
    assert review_rule.parallel_with == "verify"

    # Repair config
    assert coord.max_repair_rounds == 3
    assert coord.repair_strategy == "resume_dev_agent"

    # Output contracts
    assert "dev" in coord.output_contracts
    assert "verify" in coord.output_contracts
    assert "review" in coord.output_contracts


def test_coordinator_dispatches_dev_agent():
    """Verify dev agent is dispatched for implementation work items."""
    coord = _make_coordinator()

    dispatched = []

    async def mock_dispatch(agent_name, prompt, context):
        dispatched.append({"agent": agent_name, "prompt": prompt})
        return {"status": "success", "output": "Implementation done", "result": "Implementation done"}

    coord.set_dispatch_func(mock_dispatch)

    work_item = {
        "type": "dev",
        "name": "implement-login",
        "description": "Implement login endpoint",
    }

    async def _run():
        return await coord.execute_work_item(work_item, {"requirement": "Add login"})

    result = asyncio.run(_run())

    assert result.status == "success"
    assert result.agent == "dev-agent"
    assert "Implementation done" in result.output
    assert len(dispatched) == 1
    assert dispatched[0]["agent"] == "dev-agent"
    assert "implement-login" in dispatched[0]["prompt"]


def test_coordinator_runs_verify_and_review_parallel():
    """Verify verify+review run together via asyncio.gather."""
    coord = _make_coordinator()

    call_log = []

    async def mock_dispatch(agent_name, prompt, context):
        call_log.append({"agent": agent_name, "event": "start"})
        await asyncio.sleep(0.05)  # small delay to check parallelism
        call_log.append({"agent": agent_name, "event": "end"})
        return {"status": "success", "output": f"{agent_name} output"}

    coord.set_dispatch_func(mock_dispatch)

    work_item = {"type": "dev", "name": "test-item"}
    dev_result = AgentResult(agent="dev-agent", status="success", output="code written")

    async def _run():
        return await coord.run_verification(work_item, dev_result, {})

    verify_result, review_result = asyncio.run(_run())

    assert verify_result.agent == "verify-agent"
    assert review_result.agent == "review-agent"
    assert verify_result.status == "success"
    assert review_result.status == "success"

    # Both agents should have started before either ended (parallel)
    starts = [e for e in call_log if e["event"] == "start"]
    assert len(starts) == 2
    # Verify start order is verify then review (from gather order)
    assert starts[0]["agent"] == "verify-agent"
    assert starts[1]["agent"] == "review-agent"


def test_coordinator_repair_loop():
    """Verify retry logic when verify fails."""
    coord = _make_coordinator()

    call_count = {"dev": 0, "verify": 0, "review": 0}

    async def mock_dispatch(agent_name, prompt, context):
        if agent_name == "dev-agent":
            call_count["dev"] += 1
            # Succeed on third attempt
            if call_count["dev"] < 3:
                return {"status": "success", "output": f"attempt {call_count['dev']}"}
            return {"status": "success", "output": "final working code"}
        elif agent_name == "verify-agent":
            call_count["verify"] += 1
            # Fail verification first two times
            if call_count["verify"] < 3:
                return {"status": "failure", "output": "tests failed"}
            return {"status": "success", "output": "all tests pass"}
        elif agent_name == "review-agent":
            call_count["review"] += 1
            return {"status": "success", "output": "looks good"}
        return {"status": "error", "output": "unknown agent"}

    coord.set_dispatch_func(mock_dispatch)

    work_item = {"type": "dev", "name": "fix-bug"}

    async def _run():
        return await coord.execute_with_repair(work_item, {"requirement": "fix the bug"})

    result = asyncio.run(_run())

    # Should succeed after repair rounds
    assert result.status == "success"
    assert result.output == "final working code"
    # Dev called 3 times (2 failures + 1 success)
    assert call_count["dev"] == 3
    # Verify called 3 times (2 failures + 1 success)
    assert call_count["verify"] == 3
    # Review called 3 times (always passes, called with each verify)
    assert call_count["review"] == 3
