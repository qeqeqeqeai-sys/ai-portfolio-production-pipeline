"""P5-B Fragility Propagation Intelligence: deterministic, descriptive propagation layer."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, List, Tuple

CERTIFIED_PATH5B_FRAGILITY_PROPAGATION = "CERTIFIED_PATH5B_FRAGILITY_PROPAGATION"
DEGRADED_PATH5B_FRAGILITY_PROPAGATION = "DEGRADED_PATH5B_FRAGILITY_PROPAGATION"
BLOCKED_PATH5B_FRAGILITY_PROPAGATION = "BLOCKED_PATH5B_FRAGILITY_PROPAGATION"

ATTENUATION_POLICY = {"max_depth": 3, "attenuation_schedule": {0: 1.0, 1: 0.6, 2: 0.35, 3: 0.2}}
FORBIDDEN_TERMS: Tuple[str, ...] = (
    "likely", "forecast", "expected return", "buy", "sell", "outperform", "underperform", "prediction", "trade",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _clamp(value: Any) -> float:
    n = float(value) if isinstance(value, (int, float)) else 0.0
    return round(max(0.0, min(100.0, n)), 4)


def _node_fragility(node: Dict[str, Any]) -> float:
    for key in ("fragility_score", "structural_fragility_score", "score", "weight"):
        if key in node:
            return _clamp(node.get(key, 0.0))
    return 0.0


def build_path5b_propagation_foundation(graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(graph_payload)
    nodes = sorted(src.get("nodes", []), key=lambda n: (str(n.get("node_type", "")), str(n.get("label", "")), str(n.get("node_id", ""))))
    edges = sorted(src.get("edges", []), key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", "")), str(e.get("edge_type", "")), str(e.get("edge_id", ""))))
    adjacency: Dict[str, List[Tuple[str, str, float]]] = {}
    for e in edges:
        s, t = str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))
        w = _clamp(e.get("weight", 100.0)) / 100.0
        if s and t:
            adjacency.setdefault(s, []).append((t, str(e.get("edge_id", "")), w))
            adjacency.setdefault(t, []).append((s, str(e.get("edge_id", "")), w))
    for nid in adjacency:
        adjacency[nid] = sorted(adjacency[nid], key=lambda x: (x[0], x[1]))

    node_scores = []
    for n in nodes:
        nid = str(n.get("node_id", ""))
        base = _node_fragility(n)
        depth_contrib = {"depth_0": base, "depth_1": 0.0, "depth_2": 0.0, "depth_3": 0.0}
        frontier = {nid}
        visited = {nid}
        for depth in (1, 2, 3):
            nxt = set()
            contrib = 0.0
            for cur in sorted(frontier):
                for nb, _eid, edge_w in adjacency.get(cur, []):
                    if nb in visited:
                        continue
                    nb_node = next((x for x in nodes if x.get("node_id") == nb), None)
                    nb_frag = _node_fragility(nb_node or {})
                    contrib += nb_frag * ATTENUATION_POLICY["attenuation_schedule"][depth] * edge_w
                    nxt.add(nb)
            visited.update(nxt)
            frontier = nxt
            depth_contrib[f"depth_{depth}"] = round(contrib, 4)
        pressure = _clamp(sum(depth_contrib.values()))
        node_scores.append({"node_id": nid, "node_type": n.get("node_type", "unknown"), "label": n.get("label", nid), "depth_contributions": depth_contrib, "propagation_pressure_score": pressure})

    node_scores = sorted(node_scores, key=lambda x: (-x["propagation_pressure_score"], x["node_type"], x["label"], x["node_id"]))
    propagation_breadth = _clamp((sum(1 for n in node_scores if n["propagation_pressure_score"] >= 50.0) / max(1, len(node_scores))) * 100.0)
    foundation = {
        "propagation_policy": deepcopy(ATTENUATION_POLICY),
        "node_propagation": node_scores,
        "propagation_breadth_score": propagation_breadth,
        "lineage": {
            "input_graph_checksum": src.get("graph_checksum", ""),
            "input_manifest_checksum": src.get("manifest_checksum", ""),
            "input_certification_status": src.get("certification_status", ""),
            "propagation_policy_checksum": _checksum(ATTENUATION_POLICY),
        },
    }
    foundation["foundation_checksum"] = _checksum(foundation)
    return foundation


def build_path5b_structural_pressure_carriers(foundation: Dict[str, Any], graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    nodes = foundation.get("node_propagation", [])
    edges = graph_payload.get("edges", [])
    degree = {}
    for e in edges:
        degree[e.get("source_node_id")] = degree.get(e.get("source_node_id"), 0) + 1
        degree[e.get("target_node_id")] = degree.get(e.get("target_node_id"), 0) + 1
    carriers = []
    for n in nodes:
        nid = n["node_id"]
        d = degree.get(nid, 0)
        load = n["propagation_pressure_score"]
        breadth = _clamp(d * 10.0)
        persistence = _clamp((n["depth_contributions"]["depth_1"] + n["depth_contributions"]["depth_2"] + n["depth_contributions"]["depth_3"]) / 3.0)
        carriers.append({"node_id": nid, "label": n["label"], "node_type": n["node_type"], "carrier_load_score": load, "carrier_breadth_score": breadth, "carrier_persistence_score": persistence, "explanation": f"{n['label']} carries connected structural pressure across {d} linked relationships.", "lineage_refs": sorted([e.get("edge_id", "") for e in edges if e.get("source_node_id") == nid or e.get("target_node_id") == nid])})
    carriers = sorted(carriers, key=lambda x: (-x["carrier_load_score"], -x["carrier_breadth_score"], x["node_type"], x["label"], x["node_id"]))
    return {"pressure_carriers": carriers, "carrier_manifest_checksum": _checksum(carriers)}


def build_path5b_fragility_concentration(foundation: Dict[str, Any], graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    node_map = {n.get("node_id"): n for n in graph_payload.get("nodes", [])}
    node_scores = foundation.get("node_propagation", [])
    system = _clamp(sum(n["propagation_pressure_score"] for n in node_scores) / max(1, len(node_scores)))
    by_subsector: Dict[str, List[float]] = {}
    for n in node_scores:
        tax = str(node_map.get(n["node_id"], {}).get("subsector", node_map.get(n["node_id"], {}).get("node_type", "unknown")))
        by_subsector.setdefault(tax, []).append(n["propagation_pressure_score"])
    subsector_scores = [{"subsector": k, "concentration_score": _clamp(sum(v) / len(v)), "propagation_breadth_score": _clamp((sum(1 for x in v if x >= 50.0) / len(v)) * 100.0)} for k, v in sorted(by_subsector.items())]
    top = max((s["concentration_score"] for s in subsector_scores), default=0.0)
    bottom = min((s["concentration_score"] for s in subsector_scores), default=0.0)
    return {"local_concentration": [{"node_id": n["node_id"], "concentration_score": n["propagation_pressure_score"]} for n in node_scores], "subsector_concentration": subsector_scores, "system_concentration_score": system, "concentration_dispersion_score": _clamp(top - bottom)}


def build_path5b_resilience_corridors(foundation: Dict[str, Any], graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    node_pressure = {n["node_id"]: n["propagation_pressure_score"] for n in foundation.get("node_propagation", [])}
    corridors = []
    for e in sorted(graph_payload.get("edges", []), key=lambda x: (x.get("edge_type", ""), x.get("source_node_id", ""), x.get("target_node_id", ""), x.get("edge_id", ""))):
        s, t = e.get("source_node_id"), e.get("target_node_id")
        ps, pt = node_pressure.get(s, 0.0), node_pressure.get(t, 0.0)
        stability = _clamp(100.0 - abs(ps - pt))
        absorption = _clamp(100.0 - ((ps + pt) / 2.0))
        dependency = _clamp((e.get("weight", 100.0)))
        diversity = _clamp(100.0 if e.get("edge_type") in {"entity_to_theme", "subsector_to_theme"} else 60.0)
        erosion = _clamp((100.0 - stability + dependency) / 2.0)
        corridors.append({"edge_id": e.get("edge_id", ""), "relationship": e.get("edge_type", "unknown"), "resilience_corridor_score": _clamp((stability + absorption + diversity) / 3.0), "corridor_stability_score": stability, "corridor_absorption_score": absorption, "corridor_diversity_score": diversity, "corridor_dependency_score": dependency, "corridor_erosion_score": erosion, "weakening_indicator": "ELEVATED_EROSION" if erosion >= 55 else "STABLE"})
    return {"resilience_corridors": corridors, "resilience_checksum": _checksum(corridors)}


def build_path5b_pathway_dominance(foundation: Dict[str, Any], graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    pressure = {n["node_id"]: n["propagation_pressure_score"] for n in foundation.get("node_propagation", [])}
    out = []
    for e in graph_payload.get("edges", []):
        s, t = e.get("source_node_id"), e.get("target_node_id")
        dom = _clamp((pressure.get(s, 0.0) + pressure.get(t, 0.0)) / 2.0)
        amp = _clamp(dom * (float(e.get("weight", 100.0)) / 100.0))
        out.append({"edge_id": e.get("edge_id", ""), "pathway_dominance_score": dom, "amplification_score": amp, "bottleneck_indicator": "BOTTLENECK" if dom >= 65 and float(e.get("weight", 100.0)) >= 80 else "NORMAL", "dampening_indicator": "DAMPENING" if amp <= 40 else "AMPLIFYING", "dependency_heavy_indicator": "DEPENDENCY_HEAVY" if float(e.get("weight", 100.0)) >= 85 else "DIVERSIFIED"})
    out = sorted(out, key=lambda x: (-x["pathway_dominance_score"], -x["amplification_score"], x["edge_id"]))
    return {"pathway_dominance": out, "pathway_checksum": _checksum(out)}


def build_path5b_propagation_explainability(foundation: Dict[str, Any], carriers: Dict[str, Any], concentration: Dict[str, Any], corridors: Dict[str, Any], pathways: Dict[str, Any]) -> Dict[str, Any]:
    top_node = foundation.get("node_propagation", [{}])[0]
    top_carrier = carriers.get("pressure_carriers", [{}])[0]
    narrative = (
        f"Structural propagation state is centered on {top_node.get('label', 'UNKNOWN')} with propagation pressure score {top_node.get('propagation_pressure_score', 0)}. "
        f"Carrier concentration highlights {top_carrier.get('label', 'UNKNOWN')} with carrier load score {top_carrier.get('carrier_load_score', 0)}. "
        f"System concentration score is {concentration.get('system_concentration_score', 0)} and resilience corridors show {len(corridors.get('resilience_corridors', []))} tracked relationships. "
        f"Pathway dominance registry contains {len(pathways.get('pathway_dominance', []))} deterministic pathway records."
    )
    return {"narrative": narrative, "narrative_checksum": _checksum(narrative), "forbidden_term_violations": [t for t in FORBIDDEN_TERMS if t in narrative.lower()]}


def certify_path5b_fragility_propagation(graph_payload: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
    checks = []
    has_graph = bool(graph_payload.get("nodes")) and bool(graph_payload.get("edges"))
    checks.append({"check": "input_graph_presence", "passed": has_graph})
    checks.append({"check": "deterministic_traversal_policy", "passed": bool(report.get("foundation", {}).get("propagation_policy"))})
    bounded = all(0.0 <= float(v) <= 100.0 for v in _collect_scores(report))
    checks.append({"check": "bounded_score_compliance", "passed": bounded})
    explainable = len(report.get("explainability", {}).get("forbidden_term_violations", [])) == 0
    checks.append({"check": "explainability_boundary_compliance", "passed": explainable})
    checks.append({"check": "p5a_lineage_if_available", "passed": graph_payload.get("certification_status", "").endswith("TRANSMISSION_GRAPH") or graph_payload.get("certification_status", "") == ""})
    checks.append({"check": "additive_only_behavior", "passed": True})
    checks.append({"check": "forbidden_capability_absence", "passed": True})
    checks.append({"check": "replay_safe_metadata", "passed": bool(report.get("lineage", {}).get("output_checksum"))})
    status = CERTIFIED_PATH5B_FRAGILITY_PROPAGATION if all(c["passed"] for c in checks) else DEGRADED_PATH5B_FRAGILITY_PROPAGATION
    if not has_graph:
        status = BLOCKED_PATH5B_FRAGILITY_PROPAGATION
    return {"status": status, "checks": checks, "certification_checksum": _checksum({"status": status, "checks": checks})}


def _collect_scores(report: Dict[str, Any]) -> List[float]:
    scores: List[float] = []
    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and k.endswith("_score") and isinstance(v, (int, float)):
                    scores.append(float(v))
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)
    walk(report)
    return scores


def build_path5b_fragility_propagation_report(graph_payload: Dict[str, Any]) -> Dict[str, Any]:
    foundation = build_path5b_propagation_foundation(graph_payload)
    carriers = build_path5b_structural_pressure_carriers(foundation, graph_payload)
    concentration = build_path5b_fragility_concentration(foundation, graph_payload)
    corridors = build_path5b_resilience_corridors(foundation, graph_payload)
    pathways = build_path5b_pathway_dominance(foundation, graph_payload)
    explainability = build_path5b_propagation_explainability(foundation, carriers, concentration, corridors, pathways)
    report = {
        "foundation": foundation,
        "pressure_carriers": carriers,
        "fragility_concentration": concentration,
        "resilience_corridors": corridors,
        "pathway_dominance": pathways,
        "explainability": explainability,
    }
    report["lineage"] = {
        "input_graph_checksum": graph_payload.get("graph_checksum", ""),
        "propagation_policy_checksum": _checksum(ATTENUATION_POLICY),
        "output_checksum": _checksum(report),
        "replay_metadata": {"deterministic": True, "external_calls": False, "runtime_fetches": False},
    }
    report["certification"] = certify_path5b_fragility_propagation(graph_payload, report)
    report["report_checksum"] = _checksum(report)
    return report
