"""P5-A Structural Transmission Graph Layer: deterministic descriptive topology foundation."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

CERTIFIED_TRANSMISSION_GRAPH = "CERTIFIED_TRANSMISSION_GRAPH"
DEGRADED_TRANSMISSION_GRAPH = "DEGRADED_TRANSMISSION_GRAPH"
BLOCKED_TRANSMISSION_GRAPH = "BLOCKED_TRANSMISSION_GRAPH"

FORBIDDEN_SEMANTICS: Tuple[str, ...] = (
    "prediction", "predict", "forecast", "probabilistic", "expected return", "buy", "sell", "trade",
    "portfolio optimization", "recommendation", "signal", "stochastic", "graph ml", "llm", "alpha",
)

NODE_TYPES: Tuple[str, ...] = (
    "entity", "subsector", "sector", "benchmark", "theme", "regime", "structural_condition", "certified_interpretation",
)

EDGE_TYPES: Tuple[str, ...] = (
    "entity_to_subsector", "subsector_to_sector", "entity_to_benchmark", "entity_to_theme", "subsector_to_theme",
    "benchmark_relative_link", "regime_membership_link", "fragility_condition_link", "resilience_condition_link",
    "asymmetry_condition_link", "concentration_condition_link", "interpretation_lineage_link",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _clamp_0_100(value: Any, default: float = 50.0) -> float:
    n = float(value) if isinstance(value, (int, float)) else default
    return round(max(0.0, min(100.0, n)), 4)


def _stable_id(prefix: str, payload: Dict[str, Any]) -> str:
    return f"{prefix}_{_checksum(payload)[:20]}"


def build_path5a_node_taxonomy() -> Dict[str, Any]:
    node_defs = {
        "entity": "tradable or analyzable structural entity",
        "subsector": "industry subgroup structural bucket",
        "sector": "higher-order structural classification",
        "benchmark": "relative structural reference index",
        "theme": "cross-sectional thematic structural tag",
        "regime": "certified structural regime label",
        "structural_condition": "certified condition emitted by prior deterministic layers",
        "certified_interpretation": "bounded deterministic interpretation artifact",
    }
    return {"node_types": [{"node_type": k, "description": node_defs[k]} for k in NODE_TYPES], "taxonomy_version": "P5A_NODE_TAXONOMY_V1"}


def build_path5a_edge_taxonomy() -> Dict[str, Any]:
    return {"edge_types": [{"edge_type": et, "description": f"deterministic structural edge: {et}"} for et in EDGE_TYPES], "taxonomy_version": "P5A_EDGE_TAXONOMY_V1"}


def build_path5a_relationship_registry() -> Dict[str, Any]:
    relationships = [
        ("REL_ENTITY_SUBSECTOR_V1", "entity", "subsector", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_100"),
        ("REL_SUBSECTOR_SECTOR_V1", "subsector", "sector", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_100"),
        ("REL_ENTITY_BENCHMARK_V1", "entity", "benchmark", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_100"),
        ("REL_ENTITY_THEME_V1", "entity", "theme", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_80"),
        ("REL_SUBSECTOR_THEME_V1", "subsector", "theme", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_80"),
        ("REL_BENCHMARK_RELATIVE_V1", "benchmark", "benchmark", "UNDIRECTED", (0.0, 100.0), "fixed_input_or_default_50"),
        ("REL_REGIME_MEMBERSHIP_V1", "entity", "regime", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_70"),
        ("REL_FRAGILITY_CONDITION_V1", "entity", "structural_condition", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_60"),
        ("REL_RESILIENCE_CONDITION_V1", "entity", "structural_condition", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_60"),
        ("REL_ASYMMETRY_CONDITION_V1", "entity", "structural_condition", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_60"),
        ("REL_CONCENTRATION_CONDITION_V1", "entity", "structural_condition", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_60"),
        ("REL_INTERPRETATION_LINEAGE_V1", "certified_interpretation", "entity", "DIRECTED", (0.0, 100.0), "fixed_input_or_default_90"),
    ]
    edge_to_rel = dict(zip(EDGE_TYPES, [r[0] for r in relationships]))
    registry = []
    for rel_id, src, tgt, directionality, wrange, policy in relationships:
        registry.append({
            "relationship_id": rel_id,
            "source_node_type": src,
            "target_node_type": tgt,
            "directionality": directionality,
            "allowed_weight_range": {"min": wrange[0], "max": wrange[1]},
            "deterministic_weight_policy": policy,
            "governance_tags": ["deterministic", "descriptive_only", "additive_only", "replay_safe"],
            "description": f"Deterministic structural relation from {src} to {tgt}.",
        })
    return {"relationships": registry, "edge_type_to_relationship_id": edge_to_rel, "registry_version": "P5A_REL_REGISTRY_V1"}


def _normalize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    d = deepcopy(node)
    node_type = d.get("node_type", "entity")
    label = str(d.get("label", d.get("name", d.get("symbol", "UNKNOWN"))))
    key = {"node_type": node_type, "label": label, "external_id": str(d.get("external_id", ""))}
    node_id = d.get("node_id") or _stable_id("node", key)
    return {
        "node_id": node_id,
        "node_type": node_type,
        "label": label,
        "source_layer": str(d.get("source_layer", "path5a_structural_transmission_graph")),
        "source_field": str(d.get("source_field", "input.structural_nodes")),
        "input_checksum": str(d.get("input_checksum", _checksum(key))),
    }


def build_path5a_structural_nodes(structural_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    src = deepcopy(structural_input)
    raw_nodes = src.get("structural_nodes", [])
    normalized = [_normalize_node(n) for n in raw_nodes if isinstance(n, dict)]
    unique = {n["node_id"]: n for n in normalized if n["node_type"] in NODE_TYPES}
    return sorted(unique.values(), key=lambda x: (x["node_type"], x["label"], x["node_id"]))


def _relationship_for_edge_type(edge_type: str, registry: Dict[str, Any]) -> str:
    return registry.get("edge_type_to_relationship_id", {}).get(edge_type, "REL_UNKNOWN")


def _build_path5a_structural_edges_with_validation(
    structural_input: Dict[str, Any], nodes: Iterable[Dict[str, Any]] | None = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    src = deepcopy(structural_input)
    registry = build_path5a_relationship_registry()
    node_ids = {n["node_id"] for n in (list(nodes) if nodes is not None else build_path5a_structural_nodes(src))}
    edges: List[Dict[str, Any]] = []
    invalid_edges: List[Dict[str, Any]] = []
    for edge in src.get("structural_edges", []):
        if not isinstance(edge, dict):
            continue
        edge_type = edge.get("edge_type", "entity_to_theme")
        source_node_id = str(edge.get("source_node_id", ""))
        target_node_id = str(edge.get("target_node_id", ""))
        if (not source_node_id) or (not target_node_id):
            invalid_edges.append({"reason": "missing_or_empty_node_id", "edge": deepcopy(edge)})
            continue
        if edge_type not in EDGE_TYPES:
            invalid_edges.append({"reason": "invalid_edge_type", "edge": deepcopy(edge)})
            continue
        if source_node_id not in node_ids or target_node_id not in node_ids:
            invalid_edges.append({"reason": "nonexistent_node_reference", "edge": deepcopy(edge)})
            continue
        rel_id = _relationship_for_edge_type(edge_type, registry)
        weight = _clamp_0_100(edge.get("weight", 100.0))
        sig = {"edge_type": edge_type, "source_node_id": source_node_id, "target_node_id": target_node_id, "relationship_rule_id": rel_id}
        edge_id = edge.get("edge_id") or _stable_id("edge", sig)
        edges.append({
            "edge_id": edge_id,
            "edge_type": edge_type,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "directionality": edge.get("directionality", "DIRECTED"),
            "weight": weight,
            "relationship_rule_id": rel_id,
            "source_layer": str(edge.get("source_layer", "path5a_structural_transmission_graph")),
            "source_field": str(edge.get("source_field", "input.structural_edges")),
            "input_checksum": str(edge.get("input_checksum", _checksum(sig))),
        })
    unique = {e["edge_id"]: e for e in edges}
    return sorted(unique.values(), key=lambda x: (x["edge_type"], x["source_node_id"], x["target_node_id"], x["edge_id"])), invalid_edges


def build_path5a_structural_edges(structural_input: Dict[str, Any], nodes: Iterable[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    edges, _invalid_edges = _build_path5a_structural_edges_with_validation(structural_input, nodes=nodes)
    return edges


def build_path5a_transmission_graph(structural_input: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(structural_input)
    nodes = build_path5a_structural_nodes(src)
    edges, invalid_edges = _build_path5a_structural_edges_with_validation(src, nodes=nodes)
    graph = {
        "nodes": nodes,
        "edges": edges,
        "graph_version": "P5A_STRUCTURAL_TRANSMISSION_GRAPH_V1",
        "invalid_edge_count": len(invalid_edges),
        "invalid_edges": invalid_edges,
    }
    graph["graph_checksum"] = _checksum(graph)
    return graph


def build_path5a_topology_metrics(graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    graph = deepcopy(graph_payload)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = [n.get("node_id") for n in nodes]
    degree = {nid: 0 for nid in node_ids}
    adjacency = {nid: set() for nid in node_ids}
    for e in edges:
        s, t = e.get("source_node_id"), e.get("target_node_id")
        if s in degree and t in degree:
            degree[s] += 1
            degree[t] += 1
            adjacency[s].add(t)
            adjacency[t].add(s)
    node_count = len(nodes)
    edge_count = len(edges)
    max_edges = node_count * (node_count - 1) / 2 if node_count > 1 else 1
    density = _clamp_0_100((edge_count / max_edges) * 100.0 if max_edges else 0.0, default=0.0)
    max_degree = max(degree.values()) if degree else 0
    avg_degree = round((sum(degree.values()) / node_count), 4) if node_count else 0.0
    isolated = sum(1 for v in degree.values() if v == 0)

    seen, components = set(), 0
    for nid in node_ids:
        if nid in seen:
            continue
        components += 1
        stack = [nid]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(sorted(adjacency[cur] - seen))

    concentration = _clamp_0_100((max_degree / (sum(degree.values()) or 1)) * 100.0 if degree else 0.0, default=0.0)
    node_type_counts: Dict[str, int] = {}
    edge_type_counts: Dict[str, int] = {}
    for n in nodes:
        node_type_counts[n.get("node_type", "unknown")] = node_type_counts.get(n.get("node_type", "unknown"), 0) + 1
    for e in edges:
        edge_type_counts[e.get("edge_type", "unknown")] = edge_type_counts.get(e.get("edge_type", "unknown"), 0) + 1

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "edge_type_counts": dict(sorted(edge_type_counts.items())),
        "max_degree": max_degree,
        "average_degree": avg_degree,
        "connected_component_count": components,
        "isolated_node_count": isolated,
        "topology_density_score": density,
        "concentration_score": concentration,
    }


def build_path5a_graph_lineage(graph_payload: Dict[str, Any], topology_manifest_checksum: str = "") -> Dict[str, Any]:
    graph = deepcopy(graph_payload)
    graph_checksum = graph.get("graph_checksum", _checksum(graph))
    return {
        "graph_checksum": graph_checksum,
        "topology_manifest_checksum": topology_manifest_checksum,
        "node_lineage": [{"node_id": n["node_id"], "source_layer": n.get("source_layer", ""), "source_field": n.get("source_field", ""), "input_checksum": n.get("input_checksum", "")} for n in graph.get("nodes", [])],
        "edge_lineage": [{"edge_id": e["edge_id"], "relationship_rule_id": e.get("relationship_rule_id", ""), "source_layer": e.get("source_layer", ""), "source_field": e.get("source_field", ""), "input_checksum": e.get("input_checksum", "")} for e in graph.get("edges", [])],
    }


def build_path5a_topology_manifest(graph_payload: Dict[str, Any], metrics: Dict[str, Any], lineage: Dict[str, Any]) -> Dict[str, Any]:
    manifest = {
        "graph_checksum": graph_payload.get("graph_checksum", _checksum(graph_payload)),
        "metrics_checksum": _checksum(metrics),
        "lineage_checksum": _checksum(lineage),
        "serialization": "stable_sorted_json_sha256",
    }
    manifest["topology_manifest_checksum"] = _checksum(manifest)
    return manifest


def certify_path5a_transmission_graph(graph_bundle: Dict[str, Any]) -> Dict[str, Any]:
    b = deepcopy(graph_bundle)
    source_hits = b.get("source_payload_forbidden_semantics_hits", {})
    forbidden_hits = {term: bool(source_hits.get(term, False)) for term in FORBIDDEN_SEMANTICS}
    has_forbidden = any(forbidden_hits.values())
    taxonomy_ok = bool(build_path5a_node_taxonomy().get("node_types")) and bool(build_path5a_edge_taxonomy().get("edge_types"))
    registry_ok = bool(build_path5a_relationship_registry().get("relationships"))
    graph = b.get("graph", {})
    metrics = b.get("topology_metrics", {})
    lineage = b.get("graph_lineage", {})
    manifest = b.get("topology_manifest", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    checksum_stable = manifest.get("graph_checksum") == graph.get("graph_checksum")
    valid_edges = all(e.get("source_node_id") in {n.get("node_id") for n in nodes} and e.get("target_node_id") in {n.get("node_id") for n in nodes} for e in edges)
    deterministic_structures = isinstance(nodes, list) and isinstance(edges, list) and isinstance(metrics, dict) and isinstance(lineage, dict)
    degraded = (len(nodes) == 0 or len(edges) == 0)

    invalid_edge_count = int(graph.get("invalid_edge_count", 0))
    blocked = (not taxonomy_ok) or (not registry_ok) or (not deterministic_structures) or (not valid_edges) or (not checksum_stable) or has_forbidden or (invalid_edge_count > 0)
    status = BLOCKED_TRANSMISSION_GRAPH if blocked else (DEGRADED_TRANSMISSION_GRAPH if degraded else CERTIFIED_TRANSMISSION_GRAPH)
    return {
        "certification_status": status,
        "gates": {
            "valid_node_taxonomy": taxonomy_ok,
            "valid_edge_taxonomy": taxonomy_ok,
            "valid_relationship_registry": registry_ok,
            "deterministic_nodes_edges": deterministic_structures,
            "topology_metrics_generated": bool(metrics),
            "lineage_generated": bool(lineage),
            "checksums_stable": checksum_stable,
            "valid_edge_references": valid_edges,
            "invalid_edge_count_is_zero": invalid_edge_count == 0,
            "forbidden_semantics_excluded": not has_forbidden,
        },
        "forbidden_semantics_hits": forbidden_hits,
    }


def build_path5a_dashboard_graph_summary(graph_bundle: Dict[str, Any]) -> Dict[str, Any]:
    b = deepcopy(graph_bundle)
    g = b.get("graph", {})
    m = b.get("topology_metrics", {})
    c = b.get("certification", {})
    return {
        "certification_status": c.get("certification_status", DEGRADED_TRANSMISSION_GRAPH),
        "graph_checksum": g.get("graph_checksum", ""),
        "topology_manifest_checksum": b.get("topology_manifest", {}).get("topology_manifest_checksum", ""),
        "node_count": m.get("node_count", 0),
        "edge_count": m.get("edge_count", 0),
        "connected_component_count": m.get("connected_component_count", 0),
        "topology_density_score": m.get("topology_density_score", 0.0),
        "concentration_score": m.get("concentration_score", 0.0),
    }


def build_path5a_supervisor_report(graph_bundle: Dict[str, Any]) -> Dict[str, Any]:
    b = deepcopy(graph_bundle)
    return {
        "layer": "P5-A Structural Transmission Graph",
        "objective": "deterministic descriptive topology of structural connections",
        "what_is_connected": b.get("topology_metrics", {}).get("edge_type_counts", {}),
        "why_connected": "edge relationships mapped by deterministic registry and lineage rule IDs",
        "certification": b.get("certification", {}),
        "governance": {"descriptive_only": True, "prediction_excluded": True, "optimization_excluded": True},
    }


def build_path5a_report(output_path: str = "reports/path5a_structural_transmission_graph_report.md") -> str:
    p = Path(output_path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def run_path5a_structural_transmission_graph(structural_input: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(structural_input)
    source_payload_forbidden_hits = {term: (term in _stable_json(src).lower()) for term in FORBIDDEN_SEMANTICS}
    graph = build_path5a_transmission_graph(src)
    metrics = build_path5a_topology_metrics(graph)
    provisional_lineage = build_path5a_graph_lineage(graph)
    manifest = build_path5a_topology_manifest(graph, metrics, provisional_lineage)
    lineage = build_path5a_graph_lineage(graph, topology_manifest_checksum=manifest["topology_manifest_checksum"])
    bundle = {
        "node_taxonomy": build_path5a_node_taxonomy(),
        "edge_taxonomy": build_path5a_edge_taxonomy(),
        "relationship_registry": build_path5a_relationship_registry(),
        "graph": graph,
        "topology_metrics": metrics,
        "graph_lineage": lineage,
        "topology_manifest": manifest,
        "source_payload_checksum": _checksum(src),
        "source_payload_forbidden_semantics_hits": source_payload_forbidden_hits,
    }
    bundle["certification"] = certify_path5a_transmission_graph(bundle)
    bundle["dashboard_summary"] = build_path5a_dashboard_graph_summary(bundle)
    bundle["supervisor_report"] = build_path5a_supervisor_report(bundle)
    return bundle
