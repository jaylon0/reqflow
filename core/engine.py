"""ReqFlow orchestration engine - wires all components to execute workflows."""

from __future__ import annotations

import asyncio
import os

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .runtime_config import RuntimeConfig
from .registry import RuntimeRegistry
from .adapters.base import ModelAdapter, ModelResponse, TokenUsage
from .adapters.claude_code import ClaudeCodeAdapter
from .adapters.api import APIAdapter
from .adapters.manual import ManualAdapter
from .tool_bridge import ToolBridge
from .context_adapter import ContextAdapter
from .state_manager import StateManager, RunState
from .tracer import Tracer, TokenUsage as TracerTokenUsage
from .guardrails import Guardrails, Constraint, Violation, Severity
from .workflow_loader import WorkflowLoader


@dataclass
class StepResult:
    name: str
    status: str  # success | failure | skipped | aborted
    response: ModelResponse | None = None
    violations: list[Violation] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class Engine:
    """ReqFlow orchestration engine - wires all components to execute workflows."""

    def __init__(self, config: RuntimeConfig, run_dir: str | None = None, workflows_dir: str | None = None):
        self.config = config
        if run_dir:
            self.run_dir = run_dir
        else:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.run_dir = os.path.join(config.paths.run_dir, f"run-{timestamp}")
        self.run_id = Path(self.run_dir).name

        self.tool_bridge = ToolBridge(config)
        self.context_adapter = ContextAdapter(config)
        self.state_manager = StateManager(self.run_dir)
        self.tracer = Tracer(self.run_id, output_dir=os.path.join(self.run_dir, "traces"))
        self.guardrails = Guardrails()
        self.workflow_loader = WorkflowLoader(workflows_dir)

        self._adapter: ModelAdapter | None = None
        self._step_results: dict[str, StepResult] = {}

    # --- Adapter selection ---

    def select_adapter(self) -> ModelAdapter:
        """Select adapter based on RuntimeConfig name. Falls back to ManualAdapter."""
        if self._adapter is not None:
            return self._adapter

        name = self.config.name.lower()

        if name == "claude":
            self._adapter = ClaudeCodeAdapter()
        elif name in ("gpt", "gemini", "deepseek"):
            self._adapter = APIAdapter.from_config(self.config)
        elif name in ("host", "host-codex", "host-claude-code", "host-cursor", "host-copilot"):
            from .adapters.host import HostAgentAdapter
            self._adapter = HostAgentAdapter(run_dir=self.run_dir)
        elif name == "manual":
            self._adapter = ManualAdapter()
        else:
            self._adapter = ManualAdapter()

        return self._adapter

    # --- Parallel dispatch ---

    async def dispatch_parallel(
        self, agents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Dispatch multiple agents in parallel using asyncio.gather.

        Each agent dict must have:
            name: str
            handler: async callable(prompt, **kwargs) -> dict
            prompt: str
            kwargs: optional extra args

        Returns list of results in the same order as input.
        Each result dict includes the agent's 'name' key.
        """
        max_concurrent = getattr(self, "_max_concurrent_agents", 3)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _run_one(agent: dict[str, Any]) -> dict[str, Any]:
            name = agent.get("name", "unnamed")
            async with semaphore:
                try:
                    handler = agent["handler"]
                    prompt = agent["prompt"]
                except KeyError as e:
                    return {"name": name, "status": "error", "error": f"Missing required key {e} in agent '{name}'"}
                kwargs = agent.get("kwargs", {})
                try:
                    result = await handler(prompt, **kwargs)
                    if isinstance(result, dict):
                        result.setdefault("name", name)
                        return result
                    return {"name": name, "status": "success", "result": result}
                except Exception as e:
                    return {"name": name, "status": "error", "error": str(e)}

        return await asyncio.gather(*[_run_one(a) for a in agents])

    # --- Workflow execution ---

    async def run_workflow(
        self, workflow_steps: list[dict[str, Any]], requirement: str
    ) -> dict[str, Any]:
        """Execute a list of workflow steps sequentially.

        Each step dict:
            name: str
            prompt: str
            tools: list[str] (optional)
            constraints: list[dict] (optional)
            checkpoint: bool (optional)
            loop: dict (optional) - {condition, max_iterations}
        """
        adapter = self.select_adapter()
        self.state_manager.update_stage("workflow_start")
        self.state_manager.save_state()

        workflow_span = self.tracer.start_span(
            "workflow", input_data={"requirement": requirement, "steps": len(workflow_steps)}
        )

        completed_steps: list[dict[str, Any]] = []
        final_result: dict[str, Any] = {"steps": [], "status": "completed"}

        try:
            for step in workflow_steps:
                step_result = await self._execute_step_with_loop(
                    step, adapter, requirement, completed_steps
                )
                self._step_results[step["name"]] = step_result
                completed_steps.append({
                    "name": step["name"],
                    "status": step_result.status,
                    "content": step_result.response.content if step_result.response else "",
                })
                self.state_manager.state.stage_records.append({
                    "name": step["name"],
                    "status": step_result.status,
                    "duration_ms": step_result.duration_ms,
                    "error": step_result.error,
                    "content": step_result.response.content[:2000] if step_result.response else "",
                })
                self.state_manager.state.agent_execution_log.append({
                    "type": "step",
                    "step_name": step["name"],
                    "status": step_result.status,
                    "duration_ms": step_result.duration_ms,
                    "error": step_result.error,
                    "content_preview": step_result.response.content[:500] if step_result.response else "",
                    "timestamp": datetime.now().isoformat(),
                })
                final_result["steps"].append({
                    "name": step["name"],
                    "status": step_result.status,
                })

                if step_result.status == "aborted":
                    final_result["status"] = "aborted"
                    final_result["abort_reason"] = step_result.error
                    break

                if step_result.status == "failure":
                    final_result["status"] = "failed"
                    final_result["error"] = step_result.error
                    final_result["failed_at"] = step["name"]
                    break

                self.state_manager.complete_module(step["name"])

            if final_result["status"] not in ("failed", "aborted"):
                final_result["status"] = "completed"
        except Exception as e:
            final_result["status"] = "error"
            final_result["error"] = str(e)
        finally:
            self.tracer.end_span(
                workflow_span.span_id,
                output=final_result["status"],
                status="success" if final_result["status"] == "completed" else "failure",
            )
            self.tracer.export()

        self.state_manager.state.agent_execution_log.append({
            "workflow": "run_workflow",
            "requirement": requirement,
            "result": final_result["status"],
            "timestamp": datetime.now().isoformat(),
        })
        self.state_manager.save_state()

        return final_result

    async def run_workflow_by_name(
        self,
        workflow_name: str,
        requirement: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a named workflow loaded from YAML.

        Uses WorkflowLoader to load the workflow definition, extracts stages,
        and delegates to the existing run_workflow().

        Args:
            workflow_name: Name of the workflow YAML file (without extension).
            requirement: The requirement text driving this workflow.
            context: Optional additional context passed to all steps.

        Returns:
            Workflow execution result dict.
        """
        stages = self.workflow_loader.get_stages(workflow_name)

        # Inject caller context into each step if provided
        if context:
            for stage in stages:
                existing_ctx = stage.get("context", {})
                merged = {**context, **existing_ctx}
                stage["context"] = merged

        # Apply gate_calls constraints from the full definition
        definition = self.workflow_loader.load(workflow_name)
        yaml_stages = definition.get("stages", [])
        for yaml_stage, engine_stage in zip(yaml_stages, stages):
            gate_constraints = self.workflow_loader.get_stage_gates(yaml_stage)
            if gate_constraints:
                existing = engine_stage.get("constraints", [])
                engine_stage["constraints"] = existing + gate_constraints

        # Store loop_engine config so _execute_step_with_loop can resolve it
        self._current_loop_engine = definition.get("loop_engine")

        try:
            return await self.run_workflow(stages, requirement)
        finally:
            self._current_loop_engine = None

    async def run_graph(self, graph: "Graph") -> dict[str, Any]:
        """Execute a workflow graph.

        Args:
            graph: Graph instance to execute.

        Returns:
            Final state dict with _status key.
        """
        from .graph import GraphEngine

        self.state_manager.update_stage("graph_start")
        self.state_manager.save_state()

        state: dict[str, Any] = {"requirement": ""}
        graph_engine = GraphEngine(graph, state=state)
        result = await graph_engine.run()

        self.state_manager.state.agent_execution_log.append({
            "workflow": "run_graph",
            "result": result.get("_status", "unknown"),
            "timestamp": datetime.now().isoformat(),
        })
        self.state_manager.save_state()

        return result

    async def _apply_gate_calls(
        self, stage: dict[str, Any], context: dict[str, Any]
    ) -> list[Violation]:
        """Check gate_calls constraints for a stage.

        Extracts gate_calls from a YAML stage definition and runs them
        through the guardrails system.

        Args:
            stage: A stage dict that may contain 'gate_calls'.
            context: The execution context to check against.

        Returns:
            List of violations found. Empty if all gates pass.
        """
        gate_calls = stage.get("gate_calls", [])
        if not gate_calls:
            return []

        constraints = self.workflow_loader.get_stage_gates(stage)
        return await self._check_guardrails(constraints, context)

    async def _execute_step_with_loop(
        self,
        step: dict[str, Any],
        adapter: ModelAdapter,
        requirement: str,
        previous_steps: list[dict[str, Any]],
    ) -> StepResult:
        """Execute a step, respecting loop conditions if present.

        Loop config resolution order:
        1. step["loop"] - inline loop config from the step itself
        2. Workflow-level loop_engine config (from YAML) that matches this step name
        """
        loop_config = step.get("loop")

        # Fall back to workflow-level loop_engine if step has no inline loop
        if not loop_config:
            loop_config = self._resolve_loop_engine_for_step(step["name"])

        if not loop_config:
            return await self.run_step(step, context={"requirement": requirement, "previous_steps": previous_steps})

        max_iterations = loop_config.get("max_iterations", 3)
        condition = loop_config.get("condition", "")

        last_result: StepResult | None = None
        for i in range(max_iterations):
            iteration_context = {
                "requirement": requirement,
                "previous_steps": previous_steps,
                "loop_iteration": i,
                "loop_condition": condition,
            }
            last_result = await self.run_step(step, context=iteration_context)

            if last_result.status == "aborted":
                return last_result

            if last_result.response and not self._should_continue_loop(
                last_result.response.content, condition
            ):
                break

        return last_result or StepResult(name=step["name"], status="failure", error="Loop produced no result")

    def _resolve_loop_engine_for_step(self, step_name: str) -> dict[str, Any] | None:
        """Look up loop_engine config for a step from the current workflow definition.

        The loop_engine YAML structure defines states; each state may have a
        'loop' key with {condition, max_iterations}. If the step_name matches
        a state name that has a loop, return that config.

        Returns None if no loop_engine is loaded or no matching state exists.
        """
        loop_engine = getattr(self, "_current_loop_engine", None)
        if not loop_engine:
            return None

        states = loop_engine.get("states", {})
        state_config = states.get(step_name)
        if state_config and "loop" in state_config:
            return state_config["loop"]
        return None

    @staticmethod
    def _should_continue_loop(content: str, condition: str) -> bool:
        """Simple heuristic: continue loop if content indicates work remains."""
        lower = content.lower()
        if "needs_revision" in lower or "retry" in lower or "not_complete" in lower:
            return True
        if condition and condition.lower() in lower:
            return True
        return False

    # --- Single step execution ---

    async def run_step(
        self, step: dict[str, Any], context: dict[str, Any] | None = None
    ) -> StepResult:
        """Execute a single workflow step.

        1. start_span
        2. format context
        3. check guardrails (constraints from step)
        4. adapter.call(prompt, tools, context)
        5. end_span
        6. create checkpoint if requested
        7. return step result
        """
        step_name = step.get("name", "unnamed")
        prompt = step.get("prompt", "")
        tools = step.get("tools")
        constraints = step.get("constraints", [])
        want_checkpoint = step.get("checkpoint", False)

        span = self.tracer.start_span(
            f"step:{step_name}", input_data={"prompt": prompt, "tools": tools}
        )
        start_time = datetime.now()

        try:
            # Format context
            formatted_context = self.format_step_context(step, context)

            # Check guardrails
            violations = await self._check_guardrails(constraints, context or {})
            if violations and self.guardrails.is_fatal(violations):
                duration = int((datetime.now() - start_time).total_seconds() * 1000)
                self.tracer.end_span(span.span_id, output="aborted", status="failure")
                return StepResult(
                    name=step_name,
                    status="aborted",
                    violations=violations,
                    error=f"Fatal guardrail violation: {self.guardrails.format_violations(violations)}",
                    duration_ms=duration,
                )

            # Call adapter
            adapter = self.select_adapter()
            system_prompt = self.context_adapter.format_system_prompt(step_name)
            response = adapter.call(
                prompt=prompt,
                tools=tools,
                context=formatted_context,
                system_prompt=system_prompt,
            )

            # Record trace
            tokens = TracerTokenUsage(
                input_tokens=response.tokens.input_tokens,
                output_tokens=response.tokens.output_tokens,
            )
            self.tracer.end_span(
                span.span_id,
                output={"content_length": len(response.content)},
                status="success",
                tokens=tokens,
            )

            # Checkpoint
            if want_checkpoint:
                self.state_manager.create_checkpoint(
                    stage=step_name,
                    context={"step": step_name, "response": response.content[:2000]},
                )

            # Log to memory
            self.state_manager.state.memory.add_short_term(
                key=f"step:{step_name}",
                value=response.content[:500],
            )
            self.state_manager.save_state()

            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            return StepResult(
                name=step_name,
                status="success",
                response=response,
                violations=violations,
                duration_ms=duration,
            )

        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            self.tracer.end_span(span.span_id, output=str(e), status="error")
            return StepResult(
                name=step_name,
                status="failure",
                error=str(e),
                duration_ms=duration,
            )

    async def _check_guardrails(
        self, constraints: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[Violation]:
        """Build Constraint objects from step config and run guardrail checks."""
        if not constraints:
            return []

        for c in constraints:
            severity = Severity(c.get("severity", "error"))
            self.guardrails.add_constraint(Constraint(
                name=c.get("name", "unnamed"),
                description=c.get("description", ""),
                severity=severity,
                check_fn=c.get("check_fn"),
            ))

        return await self.guardrails.check(context)

    # --- Context formatting ---

    def format_step_context(
        self, step: dict[str, Any], context: dict[str, Any] | None = None
    ) -> str:
        """Format context for the current step including state, memory, and prior results."""
        context_pack: dict[str, Any] = {}

        # State info
        state = self.state_manager.state
        context_pack["current_stage"] = state.current_stage
        context_pack["completed_modules"] = state.completed_modules

        # Short-term memory
        if state.memory.short_term:
            context_pack["recent_memory"] = state.memory.short_term[-10:]

        # Caller-provided context (requirement, previous steps, etc.)
        if context:
            if "requirement" in context:
                context_pack["requirement"] = context["requirement"]
            if "previous_steps" in context:
                context_pack["previous_steps"] = context["previous_steps"]
            for key, value in context.items():
                if key not in ("requirement", "previous_steps"):
                    context_pack[key] = value

        # Step-level context overrides
        if "context" in step:
            context_pack.update(step["context"])

        return self.context_adapter.truncate_to_fit(
            self.context_adapter.format_context(context_pack)
        )

    # --- Runtime detection ---

    def detect_runtime(self) -> RuntimeConfig:
        """Auto-detect runtime: try Claude Code, then env vars, then default to manual."""
        # Check if running inside Claude Code
        if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDECODE"):
            try:
                registry = RuntimeRegistry()
                return registry.get("claude")
            except (ValueError, FileNotFoundError):
                pass

        # Check env var for explicit runtime name
        runtime_name = os.environ.get("REQFLOW_RUNTIME", "").lower()
        if runtime_name:
            try:
                registry = RuntimeRegistry()
                return registry.get(runtime_name)
            except (ValueError, FileNotFoundError):
                pass

        # Check for API keys as hints
        for provider in ("openai", "anthropic", "gemini", "deepseek"):
            env_key = f"{provider.upper()}_API_KEY"
            if os.environ.get(env_key):
                return RuntimeConfig(
                    name=provider,
                    display_name=provider.title(),
                )

        # Fallback to manual
        return RuntimeConfig(name="manual", display_name="Manual")

    # --- Status ---

    def get_status(self) -> dict[str, Any]:
        """Return engine status summary."""
        state = self.state_manager.state
        return {
            "run_id": self.run_id,
            "config": self.config.name,
            "adapter": self._adapter.name if self._adapter else "not_selected",
            "current_stage": state.current_stage,
            "completed_modules": state.completed_modules,
            "steps_executed": len(self._step_results),
            "step_statuses": {name: r.status for name, r in self._step_results.items()},
            "checkpoints": len(state.checkpoints),
            "memory_entries": len(state.memory.short_term),
            "trace_summary": self.tracer.get_summary(),
        }
