"""Tests for the LoopEngine state machine."""

import asyncio

from reqflow.core.loop_engine import LoopEngine


def test_loop_engine_state_machine():
    """Verify states are parsed correctly from the config string."""
    config = {
        "state_machine": "observe -> classify -> localize -> patch -> verify -> review -> decide",
    }
    engine = LoopEngine(config)
    assert engine.states == [
        "observe", "classify", "localize", "patch",
        "verify", "review", "decide",
    ]


def test_loop_engine_executes_state_handlers():
    """Register handlers for all states, run the engine, verify all executed."""
    config = {
        "state_machine": "a -> b -> c",
        "max_iterations": 1,
    }
    engine = LoopEngine(config)

    call_log = []

    def make_handler(name):
        def handler(ctx):
            call_log.append(name)
            return {}
        return handler

    engine.register_handler("a", make_handler("a"))
    engine.register_handler("b", make_handler("b"))
    engine.register_handler("c", make_handler("c"))

    result = asyncio.run(engine.run({}))
    assert call_log == ["a", "b", "c"]
    assert result["_loop_status"] == "max_iterations"


def test_loop_engine_stops_on_decide():
    """When decide returns {"action": "stop"}, the engine stops immediately."""
    config = {
        "state_machine": "patch -> verify -> decide",
        "max_iterations": 5,
    }
    engine = LoopEngine(config)

    engine.register_handler("patch", lambda ctx: {"patched": True})
    engine.register_handler("verify", lambda ctx: {"status": "fail"})
    engine.register_handler("decide", lambda ctx: {"action": "stop"})

    result = asyncio.run(engine.run({}))
    assert result["_loop_status"] == "stopped"
    assert result["patched"] is True
    assert result["_loop_iteration"] == 0


def test_loop_engine_retries_on_patch():
    """Verify fails twice then passes — engine should run 3 iterations."""
    config = {
        "state_machine": "patch -> verify -> decide",
        "max_iterations": 3,
    }
    engine = LoopEngine(config)

    iteration_count = {"value": 0}

    def patch_handler(ctx):
        iteration_count["value"] += 1
        return {}

    def verify_handler(ctx):
        # Fail on first two iterations, pass on third
        if ctx.get("_loop_iteration", 0) < 2:
            return {"status": "fail"}
        return {"status": "pass"}

    def decide_handler(ctx):
        # Only stop when verify passed
        if ctx.get("status") == "pass":
            return {"action": "stop"}
        return {}

    engine.register_handler("patch", patch_handler)
    engine.register_handler("verify", verify_handler)
    engine.register_handler("decide", decide_handler)

    result = asyncio.run(engine.run({}))
    # verify pass ends the loop directly
    assert result["_loop_status"] == "verified"
    assert iteration_count["value"] == 3
    assert result["_loop_iteration"] == 2


def test_loop_engine_risk_gate_stops():
    """When a risk gate triggers, the engine stops early."""
    config = {
        "state_machine": "patch -> verify",
        "max_iterations": 3,
        "risk_gates": ["max retry count reached"],
    }
    engine = LoopEngine(config)

    call_log = []

    def make_handler(name):
        def handler(ctx):
            call_log.append(name)
            return {}
        return handler

    engine.register_handler("patch", make_handler("patch"))
    engine.register_handler("verify", make_handler("verify"))

    # max_iterations=3, so "max retry count reached" triggers at iteration 2
    # (iteration goes 0, 1, 2; at 2 it equals max_iterations-1=2)
    result = asyncio.run(engine.run({}))
    assert result["_loop_status"] == "risk_gate_triggered"
    assert result["_risk_gate"] == "max retry count reached"


def test_loop_engine_max_iterations():
    """Engine returns max_iterations status when loop exhausts without stop."""
    config = {
        "state_machine": "do -> check",
        "max_iterations": 2,
    }
    engine = LoopEngine(config)

    engine.register_handler("do", lambda ctx: {})
    engine.register_handler("check", lambda ctx: {"status": "fail"})

    result = asyncio.run(engine.run({}))
    assert result["_loop_status"] == "max_iterations"
    assert result["_loop_iteration"] == 1


def test_loop_engine_async_handler():
    """Engine supports async handlers."""
    config = {
        "state_machine": "step1 -> step2",
        "max_iterations": 1,
    }
    engine = LoopEngine(config)

    async def step1(ctx):
        return {"step1_done": True}

    async def step2(ctx):
        return {"step2_done": True}

    engine.register_handler("step1", step1)
    engine.register_handler("step2", step2)

    result = asyncio.run(engine.run({}))
    assert result["step1_done"] is True
    assert result["step2_done"] is True


def test_loop_engine_verify_pass_ends_loop():
    """When verify returns status=pass, the loop ends (fix is verified)."""
    config = {
        "state_machine": "patch -> verify -> review -> decide",
        "max_iterations": 3,
    }
    engine = LoopEngine(config)

    call_log = []

    def make_handler(name):
        def handler(ctx):
            call_log.append(name)
            if name == "verify":
                return {"status": "pass"}
            if name == "decide":
                return {"action": "stop"}
            return {}
        return handler

    engine.register_handler("patch", make_handler("patch"))
    engine.register_handler("verify", make_handler("verify"))
    engine.register_handler("review", make_handler("review"))
    engine.register_handler("decide", make_handler("decide"))

    result = asyncio.run(engine.run({}))
    # verify -> pass ends the loop, so review and decide never run
    assert "review" not in call_log
    assert "decide" not in call_log
    assert result["_loop_status"] == "verified"
