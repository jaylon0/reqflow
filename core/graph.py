"""Graph data structures for workflow orchestration."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Literal


@dataclass
class Node:
    """A node in the workflow graph."""
    id: str
    type: Literal["agent", "tool", "decision", "human_gate", "subgraph"]
    handler: Callable  # function or agent reference
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """A directed edge between two nodes, optionally conditional."""
    source: str  # node id
    target: str  # node id
    condition: Callable[[dict[str, Any]], bool] | None = None  # None = unconditional


@dataclass
class Graph:
    """A directed graph of workflow nodes."""
    nodes: dict[str, Node]
    edges: list[Edge]
    entry: str  # entry node id
    exit: list[str]  # terminal node ids

    def get_neighbors(
        self, node_id: str, state: dict[str, Any] | None = None
    ) -> list[str]:
        """Get target node IDs reachable from node_id.

        For unconditional edges the target is always included.
        For conditional edges the target is included only when
        the condition evaluates to True against the provided state.
        """
        neighbors: list[str] = []
        for edge in self.edges:
            if edge.source != node_id:
                continue
            if edge.condition is None:
                neighbors.append(edge.target)
            elif state is not None and edge.condition(state):
                neighbors.append(edge.target)
        return neighbors


class LoopSubgraph:
    """A subgraph that repeats until a condition is met or max_rounds is reached."""

    def __init__(self, graph: Graph, max_rounds: int = 3):
        self.graph = graph
        self.max_rounds = max_rounds

    def _should_continue(self, state: dict[str, Any]) -> bool:
        """Check if any exit node has a back-edge whose condition is True."""
        for exit_id in self.graph.exit:
            for edge in self.graph.edges:
                if edge.source == exit_id and edge.condition is not None:
                    if edge.condition(state):
                        return True
        return False

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the loop subgraph."""
        for round_num in range(self.max_rounds):
            state["_loop_round"] = round_num
            engine = GraphEngine(self.graph, state=state)
            state = await engine.run()

            if not self._should_continue(state):
                break

            # Clean up for next round
            state.pop("_paused_at", None)
            state.pop("_status", None)

        state["_loop_completed"] = True
        state.pop("_loop_round", None)
        state.pop("_paused_at", None)
        state["_status"] = "completed"
        return state


class GraphEngine:
    """Executes a workflow graph from entry to exit."""

    def __init__(self, graph: Graph, state: dict[str, Any] | None = None):
        self.graph = graph
        self.state: dict[str, Any] = state if state is not None else {}
        self._visited: set[str] = set()

    async def run(self) -> dict[str, Any]:
        """Execute graph from entry node to exit nodes."""
        return await self.run_from(self.graph.entry)

    async def run_from(self, node_id: str) -> dict[str, Any]:
        """Resume execution from a specific node."""
        self._visited.clear()
        # Clear any previous pause markers before resuming
        self.state.pop("_paused_at", None)
        self.state.pop("_status", None)
        await self._execute_node(node_id, skip_gate_for=node_id)
        if "_status" not in self.state:
            self.state["_status"] = "completed"
        return self.state

    async def _execute_node(
        self, node_id: str, skip_gate_for: str | None = None
    ) -> None:
        """Recursively execute a node and its successors."""
        if node_id in self._visited:
            return
        self._visited.add(node_id)

        node = self.graph.nodes[node_id]

        # Execute node handler
        if inspect.iscoroutinefunction(node.handler):
            self.state = await node.handler(self.state)
        else:
            self.state = node.handler(self.state)

        # Human gate: pause execution (unless this is the resume point)
        if node.type == "human_gate" and node_id != skip_gate_for:
            self.state["_paused_at"] = node_id
            self.state["_status"] = "paused"
            return

        # Find and execute neighbors
        neighbors = self.graph.get_neighbors(node_id, state=self.state)

        if not neighbors:
            return

        # Fan-out: execute neighbors in parallel
        if len(neighbors) > 1:
            await asyncio.gather(
                *[self._execute_node(n) for n in neighbors]
            )
        else:
            await self._execute_node(neighbors[0])
