#!/usr/bin/env python3
"""Regression checks for the local Java context engine provider."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def create_project(root: Path) -> None:
    write(
        root / "src/main/java/com/example/order/OrderController.java",
        """
        package com.example.order;

        import org.springframework.web.bind.annotation.GetMapping;
        import org.springframework.web.bind.annotation.RequestMapping;
        import org.springframework.web.bind.annotation.RestController;

        @RestController
        @RequestMapping("/orders")
        public class OrderController {
            private final OrderService orderService = new OrderService();

            @GetMapping("/list")
            public OrderVO list(OrderDTO dto) {
                return orderService.listOrders(dto);
            }
        }
        """,
    )
    write(
        root / "src/main/java/com/example/order/OrderService.java",
        """
        package com.example.order;

        public class OrderService {
            private final OrderMapper orderMapper = new OrderMapper();

            public OrderVO listOrders(OrderDTO dto) {
                int total = orderMapper.countOrders(dto);
                return orderMapper.listOrders(dto, total);
            }
        }
        """,
    )
    write(
        root / "src/main/java/com/example/order/OrderMapper.java",
        """
        package com.example.order;

        public class OrderMapper {
            public int countOrders(OrderDTO dto) {
                return 1;
            }

            public OrderVO listOrders(OrderDTO dto, int total) {
                return new OrderVO(total);
            }
        }
        """,
    )
    write(
        root / "src/main/java/com/example/order/OrderDTO.java",
        """
        package com.example.order;

        public class OrderDTO {
            private String status;
        }
        """,
    )
    write(
        root / "src/main/java/com/example/order/OrderVO.java",
        """
        package com.example.order;

        public class OrderVO {
            private final int total;

            public OrderVO(int total) {
                this.total = total;
            }
        }
        """,
    )


def run_provider(project_root: Path, run_dir: Path, requirement: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "scripts/java_context_engine.py"),
            "analyze",
            "--project-root",
            str(project_root),
            "--run-dir",
            str(run_dir),
            "--requirement",
            requirement,
            "--top-k",
            "5",
        ],
        cwd=PLUGIN_ROOT,
        check=True,
    )


def assert_main_outputs(run_dir: Path) -> None:
    expected = [
        "graph/java-code-graph.response.json",
        "rag/java-semantic-index.response.json",
        "graph/java-impact-analysis.response.json",
        "agent/context-packs/java-context.md",
        "04_context_discovery.md",
    ]
    for rel in expected:
        assert_true((run_dir / rel).exists(), f"missing artifact {rel}")

    graph = load_json(run_dir / "graph/java-code-graph.response.json")
    semantic = load_json(run_dir / "rag/java-semantic-index.response.json")
    impact = load_json(run_dir / "graph/java-impact-analysis.response.json")

    entrypoints = json.dumps(graph.get("entrypoints", []), ensure_ascii=False)
    assert_true("OrderController" in entrypoints, "controller entrypoint not found")
    assert_true("/orders" in entrypoints and "/list" in entrypoints, "route path not found")

    chain_with_three_layers = False
    for chain in graph.get("call_chains", []):
        chain_text = json.dumps(chain, ensure_ascii=False)
        if all(symbol in chain_text for symbol in ["OrderController", "OrderService", "OrderMapper"]):
            chain_with_three_layers = True
            break
    assert_true(
        chain_with_three_layers,
        "no call chain contained controller, service, and mapper together",
    )

    matches = json.dumps(semantic.get("matches", []), ensure_ascii=False)
    assert_true(
        "OrderController" in matches or "OrderService" in matches,
        "semantic matches did not include controller or service",
    )

    risks = json.dumps(impact.get("risk_signals", []), ensure_ascii=False)
    assert_true("list" in risks.lower() and "count" in risks.lower(), "list/count risk missing")
    assert_true(
        any(term in risks for term in ["DTO", "VO", "Mapper"]),
        "DTO/VO/Mapper risk missing",
    )


def assert_low_confidence_outputs(project_root: Path, run_dir: Path) -> None:
    run_provider(project_root, run_dir, "完全无关的天文观测需求")
    semantic = load_json(run_dir / "rag/java-semantic-index.response.json")
    impact = load_json(run_dir / "graph/java-impact-analysis.response.json")
    assert_true(semantic.get("missing_context"), "semantic missing_context should be non-empty")
    assert_true(impact.get("missing_context"), "impact missing_context should be non-empty")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        project_root = tmp_path / "project"
        run_dir = tmp_path / "run"
        low_confidence_run = tmp_path / "low-confidence-run"
        create_project(project_root)

        run_provider(project_root, run_dir, "新增订单列表筛选并同步 list count 查询")
        assert_main_outputs(run_dir)
        assert_low_confidence_outputs(project_root, low_confidence_run)

    print("java_context_engine_regression: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
