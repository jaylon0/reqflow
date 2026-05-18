"""Workflow loader - loads workflow definitions from YAML files."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any


# Tool name mapping: YAML shorthand -> canonical names used by ToolBridge
_TOOL_ALIASES: dict[str, str] = {
    "read_file": "read_file",
    "write_file": "write_file",
    "edit_file": "edit_file",
    "search": "search",
    "bash": "bash",
    "web_search": "web_search",
    "web_fetch": "web_fetch",
    "think": "think",
    "none": None,
}


class WorkflowLoader:
    """Loads and parses workflow YAML definitions."""

    def __init__(self, workflows_dir: str | None = None):
        if workflows_dir is None:
            workflows_dir = str(Path(__file__).parent.parent / "workflows")
        self.workflows_dir = Path(workflows_dir)

    def load(self, name: str) -> dict[str, Any]:
        """Load a workflow definition by name.

        Args:
            name: Workflow name (e.g., 'main-flow', 'flow')

        Returns:
            Full workflow definition dict

        Raises:
            FileNotFoundError: If the workflow YAML file does not exist.
        """
        path = self.workflows_dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            definition = yaml.safe_load(f)
        if not isinstance(definition, dict):
            raise ValueError(f"Workflow file must contain a YAML mapping, got {type(definition).__name__}")
        return definition

    def get_stages(self, name: str) -> list[dict[str, Any]]:
        """Get workflow stages as a list compatible with Engine.run_workflow.

        Converts each YAML stage definition into an Engine-executable step dict.
        Each step contains: name, prompt, tools, checkpoint, constraints, context.

        Args:
            name: Workflow name

        Returns:
            List of step dicts ready for Engine.run_workflow()
        """
        definition = self.load(name)
        stages = definition.get("stages", [])
        if not isinstance(stages, list):
            raise ValueError(f"'stages' must be a list, got {type(stages).__name__}")

        steps: list[dict[str, Any]] = []
        for stage in stages:
            step = self._convert_stage(stage)
            steps.append(step)
        return steps

    def get_stage_gates(self, stage: dict) -> list[dict]:
        """Extract gate calls from a stage definition.

        Args:
            stage: A single stage dict from the YAML definition.

        Returns:
            List of constraint dicts compatible with Guardrails.
        """
        gate_calls = stage.get("gate_calls", [])
        if not isinstance(gate_calls, list):
            return []

        constraints: list[dict] = []
        for gate in gate_calls:
            constraint: dict[str, Any] = {
                "name": gate.get("name", "unnamed_gate"),
                "description": gate.get("description", ""),
                "severity": gate.get("severity", "error"),
            }
            # If gate defines a check function reference, pass it through
            if "check_fn" in gate:
                constraint["check_fn"] = gate["check_fn"]
            # If gate defines required fields or patterns
            if "required_fields" in gate:
                constraint["required_fields"] = gate["required_fields"]
            if "pattern" in gate:
                constraint["pattern"] = gate["pattern"]
            constraints.append(constraint)
        return constraints

    def get_loop_config(self, name: str) -> dict | None:
        """Get loop engine configuration if defined.

        Args:
            name: Workflow name

        Returns:
            Loop engine state-machine definition, or None if not defined.
        """
        definition = self.load(name)
        return definition.get("loop_engine")

    def list_workflows(self) -> list[str]:
        """List available workflow names.

        Returns:
            Sorted list of workflow names (without .yaml extension).
        """
        if not self.workflows_dir.is_dir():
            return []
        return sorted(
            p.stem for p in self.workflows_dir.glob("*.yaml")
        )

    def load_graph(self, name: str) -> "Graph":
        """Load a workflow as a Graph.

        Supports two formats:
        1. Explicit 'graph' key with nodes/edges
        2. Legacy 'stages' key auto-converted to linear graph
        """
        from .graph import Node, Edge, Graph

        definition = self.load(name)

        if "graph" in definition:
            return self._parse_graph(definition["graph"])
        elif "stages" in definition:
            return self._stages_to_graph(definition["stages"])
        else:
            raise ValueError(f"Workflow '{name}' has neither 'graph' nor 'stages' key")

    def _parse_graph(self, graph_def: dict) -> "Graph":
        """Parse an explicit graph definition."""
        from .graph import Node, Edge, Graph

        nodes: dict[str, Node] = {}
        for node_def in graph_def.get("nodes", []):
            node = Node(
                id=node_def["id"],
                type=node_def.get("type", "agent"),
                handler=node_def.get("handler", lambda s: s),
                config={k: v for k, v in node_def.items() if k not in ("id", "type", "handler")},
            )
            nodes[node.id] = node

        edges: list[Edge] = []
        for edge_def in graph_def.get("edges", []):
            condition = None
            cond_str = edge_def.get("condition")
            if cond_str:
                def make_condition(expr):
                    def check(state):
                        try:
                            return eval(expr, {"state": state, "__builtins__": {}})
                        except Exception:
                            return False
                    check.__doc__ = expr
                    return check
                condition = make_condition(cond_str)

            edges.append(Edge(
                source=edge_def["source"],
                target=edge_def["target"],
                condition=condition,
            ))

        return Graph(
            nodes=nodes,
            edges=edges,
            entry=graph_def.get("entry", ""),
            exit=graph_def.get("exit", []),
        )

    def _stages_to_graph(self, stages: list[dict]) -> "Graph":
        """Convert linear stages list to a Graph."""
        from .graph import Node, Edge, Graph

        nodes: dict[str, Node] = {}
        edges: list[Edge] = []

        for i, stage in enumerate(stages):
            step = self._convert_stage(stage)
            node = Node(
                id=step["name"],
                type="agent",
                handler=step.get("handler", lambda s: s),
                config=step,
            )
            nodes[node.id] = node

            if i > 0:
                prev_name = self._convert_stage(stages[i - 1])["name"]
                edges.append(Edge(source=prev_name, target=node.id))

        entry = self._convert_stage(stages[0])["name"] if stages else ""
        exit_nodes = [self._convert_stage(stages[-1])["name"]] if stages else []

        return Graph(nodes=nodes, edges=edges, entry=entry, exit=exit_nodes)

    # --- internal helpers ---

    def _convert_stage(self, stage: dict) -> dict[str, Any]:
        """Convert a single YAML stage to an Engine step dict."""
        step: dict[str, Any] = {}

        # name (required)
        step["name"] = stage.get("name", "unnamed_stage")

        # prompt
        step["prompt"] = stage.get("prompt", "")

        # tools - map to canonical names
        raw_tools = stage.get("tools")
        if raw_tools is not None:
            step["tools"] = self._map_tools(raw_tools)

        # checkpoint
        checkpoint = stage.get("checkpoint")
        if checkpoint:
            step["checkpoint"] = True

        # gate_calls -> constraints
        constraints = self.get_stage_gates(stage)
        if constraints:
            step["constraints"] = constraints

        # knowledge_hooks -> merge into prompt as context hints
        knowledge_hooks = stage.get("knowledge_hooks")
        if knowledge_hooks:
            step["prompt"] = self._merge_knowledge_hooks(step["prompt"], knowledge_hooks)

        # context (pass through arbitrary context keys)
        if "context" in stage:
            step["context"] = stage["context"]

        # loop configuration
        if "loop" in stage:
            step["loop"] = stage["loop"]

        return step

    @staticmethod
    def _map_tools(raw_tools: Any) -> list[str]:
        """Map YAML tool names to canonical tool names."""
        if isinstance(raw_tools, str):
            raw_tools = [raw_tools]
        if not isinstance(raw_tools, list):
            return []

        mapped: list[str] = []
        for tool in raw_tools:
            canonical = _TOOL_ALIASES.get(tool, tool)
            if canonical is not None:
                mapped.append(canonical)
        return mapped

    @staticmethod
    def _merge_knowledge_hooks(prompt: str, hooks: Any) -> str:
        """Merge knowledge_hooks into the prompt as context hints."""
        if not hooks:
            return prompt

        if isinstance(hooks, str):
            hooks = [hooks]

        if not isinstance(hooks, list):
            return prompt

        hook_block = "\n".join(f"- {h}" for h in hooks)
        return f"{prompt}\n\n## Knowledge Hooks\n{hook_block}"
