#!/usr/bin/env python3
"""Local V1 Java context evidence provider.

This provider scans source text only. It does not produce bytecode, graph
database, or vector-index evidence.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from runtime_support import ARTIFACT_PATHS


GRAPH_VERSION = "local-source-scan-v1"
INDEX_VERSION = "local-lexical-semantic-v1"


CLASS_RE = re.compile(r"\b(?:public\s+)?(?:class|interface|enum)\s+([A-Z][A-Za-z0-9_]*)")
PACKAGE_RE = re.compile(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;", re.MULTILINE)
METHOD_RE = re.compile(
    r"(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?"
    r"([A-Za-z0-9_<>, ?\[\]]+)\s+([a-zA-Z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*\{",
    re.MULTILINE,
)
FIELD_RE = re.compile(r"\b(?:private|protected|public)\s+(?:final\s+)?([A-Z][A-Za-z0-9_]*)\s+([a-z][A-Za-z0-9_]*)\b")
ANNOTATION_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_]*)(?:\(([^)]*)\))?")
CALL_RE = re.compile(r"\b([a-z][A-Za-z0-9_]*)\.([a-zA-Z_][A-Za-z0-9_]*)\s*\(")
CLASS_REF_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*|[\u4e00-\u9fff]{2,}")
COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


@dataclass
class JavaMethod:
    name: str
    return_type: str
    params: str
    annotations: list[str]
    body: str
    line: int


@dataclass
class JavaFile:
    path: Path
    rel_path: str
    package: str
    class_name: str
    annotations: list[str]
    fields: dict[str, str]
    methods: list[JavaMethod] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    text: str = ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def annotation_value(raw: str | None) -> str:
    if not raw:
        return ""
    values = re.findall(r'"([^"]+)"', raw)
    return " ".join(values)


def route_part(annotations: list[str]) -> str:
    parts: list[str] = []
    for item in annotations:
        name, _, value = item.partition(":")
        if name.endswith("Mapping") and value:
            parts.append(value)
    return "/".join(part.strip("/") for part in parts if part).replace("//", "/")


def extract_method_body(text: str, open_brace: int) -> str:
    depth = 0
    for index in range(open_brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace + 1 : index]
    return text[open_brace + 1 :]


def preceding_annotations(text: str, start: int) -> list[str]:
    prefix = text[:start].splitlines()
    annotations: list[str] = []
    for line in reversed(prefix[-8:]):
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("@"):
            if annotations:
                break
            continue
        match = ANNOTATION_RE.match(stripped)
        if match:
            name, raw = match.groups()
            value = annotation_value(raw)
            annotations.append(f"{name}:{value}" if value else name)
    return list(reversed(annotations))


def parse_java_file(path: Path, project_root: Path) -> JavaFile | None:
    text = read_text(path)
    class_match = CLASS_RE.search(text)
    if not class_match:
        return None
    package_match = PACKAGE_RE.search(text)
    rel_path = path.relative_to(project_root).as_posix()
    class_name = class_match.group(1)
    class_annotations = preceding_annotations(text, class_match.start())
    fields = {name: type_name for type_name, name in FIELD_RE.findall(text)}
    comments = [match.group(0) for match in COMMENT_RE.finditer(text)]

    methods: list[JavaMethod] = []
    for match in METHOD_RE.finditer(text):
        open_brace = text.find("{", match.end() - 1)
        methods.append(
            JavaMethod(
                name=match.group(2),
                return_type=match.group(1).strip(),
                params=match.group(3).strip(),
                annotations=preceding_annotations(text, match.start()),
                body=extract_method_body(text, open_brace),
                line=line_number(text, match.start()),
            )
        )

    return JavaFile(
        path=path,
        rel_path=rel_path,
        package=package_match.group(1) if package_match else "",
        class_name=class_name,
        annotations=class_annotations,
        fields=fields,
        methods=methods,
        comments=comments,
        text=text,
    )


def iter_java_files(project_root: Path, scope_paths: list[Path]) -> list[Path]:
    if scope_paths:
        roots = [path if path.is_absolute() else project_root / path for path in scope_paths]
    else:
        roots = [project_root]

    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".java":
            files.append(root)
        elif root.exists():
            files.extend(root.rglob("*.java"))
    return sorted({path.resolve() for path in files})


def split_identifier(value: str) -> list[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return [part.lower() for part in TOKEN_RE.findall(spaced)]


def tokens_from_text(value: str) -> set[str]:
    tokens: set[str] = set()
    for raw in TOKEN_RE.findall(value):
        tokens.update(split_identifier(raw))
        tokens.add(raw.lower())
    return {token for token in tokens if len(token) > 1}


def method_symbol(java_file: JavaFile, method: JavaMethod) -> str:
    return f"{java_file.class_name}.{method.name}"


def build_graph(files: list[JavaFile]) -> dict:
    method_index = {
        (java_file.class_name, method.name): method_symbol(java_file, method)
        for java_file in files
        for method in java_file.methods
    }
    entrypoints: list[dict] = []
    call_chains: list[dict] = []
    affected_nodes: list[dict] = []
    evidence: list[dict] = []
    risk_signals: set[str] = set()
    direct_calls: dict[str, list[dict]] = {}

    for java_file in files:
        class_route = route_part(java_file.annotations)
        for method in java_file.methods:
            symbol = method_symbol(java_file, method)
            method_route = route_part(method.annotations)
            route = "/" + "/".join(part.strip("/") for part in [class_route, method_route] if part).strip("/")
            if any("Mapping" in annotation for annotation in java_file.annotations + method.annotations):
                entrypoints.append(
                    {
                        "type": "http",
                        "pattern": route if route != "/" else "",
                        "symbol": symbol,
                        "file": java_file.rel_path,
                        "line": method.line,
                        "evidence": f"{java_file.rel_path}:{method.line}",
                    }
                )

            calls: list[dict] = []
            for variable, called_method in CALL_RE.findall(method.body):
                target_class = java_file.fields.get(variable)
                target_symbol = method_index.get((target_class, called_method)) if target_class else None
                if target_symbol:
                    calls.append(
                        {
                            "from": symbol,
                            "to": target_symbol,
                            "via": variable,
                            "evidence": f"{java_file.rel_path}:{method.line}",
                        }
                    )
            if calls:
                call_chains.append({"source": symbol, "calls": calls})
                direct_calls[symbol] = calls

            refs = sorted(set(CLASS_REF_RE.findall(method.params + " " + method.return_type + " " + method.body)))
            affected_nodes.append(
                {
                    "symbol": symbol,
                    "file": java_file.rel_path,
                    "line": method.line,
                    "references": refs,
                }
            )
            evidence.append(
                {
                    "file": java_file.rel_path,
                    "symbol": symbol,
                    "line": method.line,
                    "source": "local-source-scan",
                }
            )

    all_text = " ".join(file.text for file in files).lower()
    if "list" in all_text and "count" in all_text:
        risk_signals.add("list query and count query may need synchronized filtering")
    if any(term in all_text for term in ["dto", "vo", "mapper"]):
        risk_signals.add("DTO/VO/Mapper ownership and mapping drift require review")

    call_chains.extend(expand_call_chains(entrypoints, direct_calls))

    return {
        "status": "success",
        "provider": GRAPH_VERSION,
        "graph_version": GRAPH_VERSION,
        "entrypoints": entrypoints,
        "call_chains": call_chains,
        "affected_nodes": affected_nodes,
        "risk_signals": sorted(risk_signals),
        "evidence": evidence,
        "limitations": [
            "Source heuristic only; not ASM bytecode analysis",
            "No graph database was built or queried",
        ],
    }


def expand_call_chains(entrypoints: list[dict], direct_calls: dict[str, list[dict]]) -> list[dict]:
    expanded: list[dict] = []
    for entrypoint in entrypoints:
        source = entrypoint.get("symbol", "")
        if not source:
            continue
        stack: list[tuple[str, list[str], list[str]]] = [(source, [source], [entrypoint.get("evidence", "")])]
        while stack:
            current, path, evidence = stack.pop()
            next_calls = direct_calls.get(current, [])
            if not next_calls and len(path) > 1:
                expanded.append(
                    {
                        "source": source,
                        "path": path,
                        "evidence": [item for item in evidence if item],
                    }
                )
                continue
            for call in next_calls:
                target = call.get("to", "")
                if not target or target in path:
                    continue
                stack.append((target, path + [target], evidence + [call.get("evidence", "")]))
    return expanded


def semantic_candidates(files: list[JavaFile], requirement: str, top_k: int) -> dict:
    requirement_tokens = tokens_from_text(requirement)
    matches: list[dict] = []
    for java_file in files:
        base_tokens = tokens_from_text(java_file.rel_path + " " + java_file.class_name)
        base_tokens.update(tokens_from_text(" ".join(java_file.annotations)))
        base_tokens.update(tokens_from_text(" ".join(java_file.comments)))
        for method in java_file.methods:
            candidate_tokens = set(base_tokens)
            candidate_tokens.update(tokens_from_text(method.name))
            candidate_tokens.update(tokens_from_text(method.params))
            candidate_tokens.update(tokens_from_text(method.return_type))
            candidate_tokens.update(tokens_from_text(" ".join(method.annotations)))
            overlap = sorted(requirement_tokens & candidate_tokens)
            score = round(len(overlap) / max(len(requirement_tokens), 1), 4)
            if score > 0:
                matches.append(
                    {
                        "file": java_file.rel_path,
                        "symbol": method_symbol(java_file, method),
                        "score": score,
                        "reason": "matched tokens: " + ", ".join(overlap),
                        "snippet_ref": f"{java_file.rel_path}:{method.line}",
                        "source": "local-lexical-semantic",
                    }
                )

    matches.sort(key=lambda item: (-item["score"], item["file"], item["symbol"]))
    selected = matches[:top_k]
    missing_context = []
    if not selected or selected[0]["score"] < 0.15:
        missing_context.append("No high-confidence local semantic match for requirement")

    return {
        "status": "success",
        "provider": INDEX_VERSION,
        "index_version": INDEX_VERSION,
        "matches": selected,
        "missing_context": missing_context,
        "limitations": [
            "Local lexical matching only; no vector database or embedding model was used",
        ],
    }


def build_impact(graph: dict, semantic: dict) -> dict:
    candidate_files = sorted({match["file"] for match in semantic.get("matches", [])})
    candidate_symbols = sorted({match["symbol"] for match in semantic.get("matches", [])})
    candidate_modules = sorted({Path(path).parts[0] for path in candidate_files if Path(path).parts})
    risk_signals = set(graph.get("risk_signals", []))
    missing_context = list(semantic.get("missing_context", []))
    entrypoints = graph.get("entrypoints", [])

    if not entrypoints:
        missing_context.append("No HTTP entrypoint discovered by local source scan")
    if not candidate_files:
        missing_context.append("No candidate files selected by local semantic scan")

    if candidate_files and entrypoints and not missing_context:
        confidence = "high"
    elif candidate_files or entrypoints:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "status": "success",
        "provider": "local-impact-merge-v1",
        "entrypoint_confidence": confidence,
        "candidate_change_scope": {
            "modules": candidate_modules,
            "files": candidate_files,
            "symbols": candidate_symbols,
        },
        "required_followups": [
            "Confirm whether list and count query filters must remain synchronized",
            "Confirm DTO, VO, and Mapper ownership before changing contracts",
        ]
        if risk_signals
        else [],
        "risk_signals": sorted(risk_signals),
        "missing_context": missing_context,
        "evidence_refs": [
            "graph/java-code-graph.response.json",
            "rag/java-semantic-index.response.json",
        ],
        "limitations": [
            "Impact is merged from local heuristic graph and lexical semantic evidence",
        ],
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(run_dir: Path, graph: dict, semantic: dict, impact: dict) -> None:
    context_pack = run_dir / "agent/context-packs/java-context.md"
    context_pack.parent.mkdir(parents=True, exist_ok=True)
    top_matches = semantic.get("matches", [])[:5]
    context_pack.write_text(
        "\n".join(
            [
                "# Java Context Pack",
                "",
                "## Evidence Artifacts",
                "- `graph/java-code-graph.response.json`",
                "- `rag/java-semantic-index.response.json`",
                "- `graph/java-impact-analysis.response.json`",
                "",
                "## Entrypoints",
                *[
                    f"- `{item.get('symbol')}` `{item.get('pattern')}` ({item.get('evidence')})"
                    for item in graph.get("entrypoints", [])
                ],
                "",
                "## Top Semantic Matches",
                *[
                    f"- `{item.get('symbol')}` score={item.get('score')} ({item.get('snippet_ref')})"
                    for item in top_matches
                ],
                "",
                "## Risk Signals",
                *[f"- {item}" for item in impact.get("risk_signals", [])],
                "",
                "## Missing Context",
                *[f"- {item}" for item in impact.get("missing_context", [])],
                "",
            ]
        ),
        encoding="utf-8",
    )

    discovery = run_dir / ARTIFACT_PATHS["context_discovery"]
    discovery.write_text(
        "\n".join(
            [
                "# 04 Context Discovery",
                "",
                "## Java Code Graph",
                f"- Status: {graph.get('status')}",
                f"- Provider: {graph.get('provider')}",
                "- Result artifact: `graph/java-code-graph.response.json`",
                "",
                "## Semantic Index",
                f"- Status: {semantic.get('status')}",
                f"- Provider: {semantic.get('provider')}",
                "- Result artifact: `rag/java-semantic-index.response.json`",
                "",
                "## Impact Analysis",
                f"- Entrypoint confidence: {impact.get('entrypoint_confidence')}",
                "- Result artifact: `graph/java-impact-analysis.response.json`",
                "",
                "## Candidate Change Scope",
                *[f"- `{path}`" for path in impact.get("candidate_change_scope", {}).get("files", [])],
                "",
                "## Risk Signals",
                *[f"- {item}" for item in impact.get("risk_signals", [])],
                "",
                "## Missing Context",
                *[f"- {item}" for item in impact.get("missing_context", [])],
                "",
                "## BLOCKER",
                "- None" if not impact.get("missing_context") else "- Missing context requires manual review",
                "",
            ]
        ),
        encoding="utf-8",
    )


def analyze(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    run_dir = Path(args.run_dir).resolve()
    scope_paths = [Path(item) for item in args.scope_path]
    java_files = [parse_java_file(path, project_root) for path in iter_java_files(project_root, scope_paths)]
    parsed_files = [item for item in java_files if item is not None]

    graph = build_graph(parsed_files)
    semantic = semantic_candidates(parsed_files, args.requirement, args.top_k)
    impact = build_impact(graph, semantic)

    write_json(run_dir / "graph/java-code-graph.response.json", graph)
    write_json(run_dir / "rag/java-semantic-index.response.json", semantic)
    write_json(run_dir / "graph/java-impact-analysis.response.json", impact)
    write_markdown(run_dir, graph, semantic, impact)

    print(
        json.dumps(
            {
                "status": "success",
                "artifacts": [
                    "graph/java-code-graph.response.json",
                    "rag/java-semantic-index.response.json",
                    "graph/java-impact-analysis.response.json",
                    "agent/context-packs/java-context.md",
                    "04_context_discovery.md",
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Java context engine provider")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--project-root", required=True)
    analyze_parser.add_argument("--run-dir", required=True)
    analyze_parser.add_argument("--requirement", required=True)
    analyze_parser.add_argument("--scope-path", action="append", default=[])
    analyze_parser.add_argument("--top-k", type=int, default=20)
    analyze_parser.set_defaults(func=analyze)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
