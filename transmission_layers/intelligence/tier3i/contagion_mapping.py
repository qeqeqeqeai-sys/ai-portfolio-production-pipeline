"""Tier 3I Phase 3C deterministic structural contagion mapping."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCORING_VERSION = "3I.3C.v1"


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _path_sort_key(path: Dict[str, Any]) -> Tuple[str, str, str]:
    return (str(path.get("path_id", "")), str(path.get("source_node_id", "")), str(path.get("terminal_node_id", "")))


def _node_sort_key(node_id: str, score: float) -> Tuple[float, str]:
    return (-score, node_id)


def _classify_corridor_state(path_quality: float, suppressed: bool, contaminated: bool, reinforcement: float) -> str:
    if contaminated:
        return "contaminated_corridor"
    if suppressed:
        return "suppressed_corridor"
    if path_quality < 0.45:
        return "weak_corridor"
    if path_quality >= 0.70 and reinforcement >= 0.10:
        return "amplified_corridor"
    return "healthy_corridor"


def _classify_risk_state(metrics: Dict[str, float]) -> str:
    contamination = metrics["contamination_spread_score"]
    amplification = metrics["amplification_score"]
    suppression = metrics["suppression_bottleneck_score"]
    fragility = metrics["contagion_fragility_score"]
    pressure = metrics["contagion_pressure_score"]
    chokepoint = metrics["chokepoint_score"]

    if contamination >= 0.55:
        return "contaminated"
    if suppression >= 0.75 or (suppression >= 0.58 and chokepoint >= 0.50):
        return "bottlenecked"
    if fragility >= 0.62:
        return "fragile"
    if amplification >= 0.66:
        return "amplified"
    if pressure >= 0.52:
        return "spreading"
    if max(abs(pressure - 0.50), abs(amplification - 0.50), abs(chokepoint - 0.50)) < 0.08:
        return "mixed"
    return "contained"


def map_structural_contagion(
    quality_scored_edges: Iterable[Dict[str, Any]],
    structural_influence_nodes: Iterable[Dict[str, Any]],
    multi_hop_paths: Iterable[Dict[str, Any]],
    path_explanations: Iterable[Dict[str, Any]] | None = None,
    structural_regime_summary: Dict[str, Any] | None = None,
    regime_drift_summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    edges = [dict(edge) for edge in quality_scored_edges]
    nodes = [dict(node) for node in structural_influence_nodes]
    paths = [dict(path) for path in multi_hop_paths]
    _ = [dict(e) for e in (path_explanations or [])]
    regime = dict(structural_regime_summary or {})
    drift = dict(regime_drift_summary or {})

    node_influence = {str(n.get("node_id", "")): _clip01(_to_float(n.get("structural_influence_score"), 0.0)) for n in nodes}
    unique_nodes = set(node_influence.keys())
    for edge in edges:
        unique_nodes.add(str(edge.get("source_node_id", "")))
        unique_nodes.add(str(edge.get("target_node_id", "")))

    path_records: List[Dict[str, Any]] = []
    node_occurrence: Counter[str] = Counter()
    strong_node_occurrence: Counter[str] = Counter()
    weak_node_occurrence: Counter[str] = Counter()
    suppressed_node_occurrence: Counter[str] = Counter()
    contaminated_node_occurrence: Counter[str] = Counter()
    node_pressure_contrib: defaultdict[str, float] = defaultdict(float)

    high_quality_count = 0
    total_reinforcement = 0.0
    suppressed_count = 0
    contaminated_count = 0

    regime_state = str(regime.get("regime_state", "transitioning"))
    regime_multiplier = 1.0 + (0.20 if regime_state in {"overheated", "fragile", "transitioning"} else 0.0)
    drift_multiplier = 1.0 + (0.10 if str(drift.get("drift_direction", "stable")) in {"deteriorating", "mixed"} else 0.0)

    ordered_paths = sorted(paths, key=_path_sort_key)
    for path in ordered_paths:
        path_id = str(path.get("path_id", ""))
        nodes_in_path = [str(n) for n in _safe_list(path.get("path_nodes")) if str(n)]
        if not nodes_in_path:
            continue
        quality = _clip01(_to_float(path.get("path_quality_score"), 0.0))
        reinforcement = _clip01(_to_float(path.get("reinforcement_score"), 0.0) / 0.15 if _to_float(path.get("reinforcement_score"), 0.0) <= 0.15 else _to_float(path.get("reinforcement_score"), 0.0))
        suppressed = bool(path.get("suppressed_for_propagation", False))
        contaminated = bool(path.get("contamination_warning", False))

        avg_influence = sum(node_influence.get(n, 0.0) for n in nodes_in_path) / max(len(nodes_in_path), 1)
        structural_pressure = _clip01((0.45 * quality) + (0.30 * avg_influence) + (0.25 * reinforcement))
        path_pressure = _clip01(structural_pressure * regime_multiplier * drift_multiplier)

        corridor_state = _classify_corridor_state(quality, suppressed, contaminated, reinforcement)
        if quality >= 0.70 and not suppressed:
            high_quality_count += 1
        if suppressed:
            suppressed_count += 1
        if contaminated:
            contaminated_count += 1

        total_reinforcement += reinforcement
        for n in nodes_in_path:
            node_occurrence[n] += 1
            node_pressure_contrib[n] += path_pressure
            if quality >= 0.65:
                strong_node_occurrence[n] += 1
            if quality < 0.45 or suppressed:
                weak_node_occurrence[n] += 1
            if suppressed:
                suppressed_node_occurrence[n] += 1
            if contaminated:
                contaminated_node_occurrence[n] += 1

        path_records.append({
            "path_id": path_id,
            "path_nodes": nodes_in_path,
            "path_quality_score": round(quality, 6),
            "path_pressure_score": round(path_pressure, 6),
            "corridor_state": corridor_state,
            "suppressed_for_propagation": suppressed,
            "contamination_warning": contaminated,
        })

    total_paths = len(path_records)
    node_count = max(1, len([n for n in unique_nodes if n]))

    pressure_avg = (sum(p["path_pressure_score"] for p in path_records) / total_paths) if total_paths else 0.0
    propagation_density = _clip01(high_quality_count / node_count)
    contagion_pressure_score = _clip01((0.70 * pressure_avg) + (0.30 * propagation_density))

    top_pressure = sorted(node_pressure_contrib.items(), key=lambda kv: _node_sort_key(kv[0], kv[1]))
    total_node_pressure = sum(score for _, score in top_pressure)
    top3_pressure = sum(score for _, score in top_pressure[:3])
    hub_concentration_score = _clip01((top3_pressure / total_node_pressure) if total_node_pressure > 0 else 0.0)

    reinforcement_avg = (total_reinforcement / total_paths) if total_paths else 0.0
    dominant_share = (max(node_occurrence.values()) / total_paths) if node_occurrence and total_paths else 0.0
    amplification_score = _clip01((0.35 * reinforcement_avg) + (0.35 * hub_concentration_score) + (0.30 * dominant_share))

    chokepoint_vals = []
    for nid, count in node_occurrence.items():
        participation = count / max(total_paths, 1)
        bridge_mix = min(strong_node_occurrence[nid], weak_node_occurrence[nid]) / max(count, 1)
        resilience_penalty = 1.0 - node_influence.get(nid, 0.0)
        chokepoint_vals.append(_clip01((0.45 * participation) + (0.30 * bridge_mix) + (0.25 * resilience_penalty)))
    chokepoint_score = _clip01(sum(chokepoint_vals) / len(chokepoint_vals)) if chokepoint_vals else 0.0

    corridor_density_score = _clip01(high_quality_count / max(total_paths, 1))
    suppressed_ratio = (suppressed_count / max(total_paths, 1)) if total_paths else 0.0
    clustered_suppression = (max(suppressed_node_occurrence.values()) / max(suppressed_count, 1)) if suppressed_node_occurrence else 0.0
    suppression_bottleneck_score = _clip01((0.55 * suppressed_ratio) + (0.45 * clustered_suppression))

    contaminated_ratio = (contaminated_count / max(total_paths, 1)) if total_paths else 0.0
    contaminated_overlap = 0.0
    if contaminated_count:
        overlap_hits = 0
        for rec in path_records:
            if rec["contamination_warning"] and rec["path_quality_score"] >= 0.60:
                overlap_hits += 1
        contaminated_overlap = overlap_hits / contaminated_count
    contamination_cluster = (max(contaminated_node_occurrence.values()) / max(contaminated_count, 1)) if contaminated_node_occurrence else 0.0
    contamination_spread_score = _clip01((0.45 * contaminated_ratio) + (0.30 * contamination_cluster) + (0.25 * contaminated_overlap))

    contagion_resilience_score = _clip01(
        (0.35 * corridor_density_score)
        + (0.20 * (1.0 - suppression_bottleneck_score))
        + (0.20 * (1.0 - contamination_spread_score))
        + (0.15 * (1.0 - chokepoint_score))
        + (0.10 * (1.0 - abs(hub_concentration_score - 0.5) / 0.5))
    )
    contagion_fragility_score = _clip01(
        (0.28 * contagion_pressure_score)
        + (0.22 * suppression_bottleneck_score)
        + (0.20 * contamination_spread_score)
        + (0.20 * chokepoint_score)
        + (0.10 * (1.0 - contagion_resilience_score))
    )

    metrics = {
        "contagion_pressure_score": round(contagion_pressure_score, 6),
        "amplification_score": round(amplification_score, 6),
        "chokepoint_score": round(chokepoint_score, 6),
        "corridor_density_score": round(corridor_density_score, 6),
        "suppression_bottleneck_score": round(suppression_bottleneck_score, 6),
        "contamination_spread_score": round(contamination_spread_score, 6),
        "hub_concentration_score": round(hub_concentration_score, 6),
        "contagion_fragility_score": round(contagion_fragility_score, 6),
        "contagion_resilience_score": round(contagion_resilience_score, 6),
    }

    contagion_risk_state = _classify_risk_state(metrics)
    contagion_hubs = [n for n, _ in sorted(node_pressure_contrib.items(), key=lambda kv: _node_sort_key(kv[0], kv[1]))[:5]]
    amplification_hubs = [n for n, _ in sorted(strong_node_occurrence.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
    chokepoint_nodes = [n for n, _ in sorted(node_occurrence.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
    vulnerable_nodes = [n for n, _ in sorted(suppressed_node_occurrence.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]

    contagion_corridors = [p["path_id"] for p in sorted(path_records, key=lambda p: (-p["path_pressure_score"], p["path_id"]))[:5]]
    high_pressure_paths = [p["path_id"] for p in sorted(path_records, key=lambda p: (-p["path_pressure_score"], p["path_id"])) if p["path_pressure_score"] >= 0.60][:5]
    suppressed_corridors = [p["path_id"] for p in sorted(path_records, key=lambda p: p["path_id"]) if p["corridor_state"] == "suppressed_corridor"]
    contaminated_corridors = [p["path_id"] for p in sorted(path_records, key=lambda p: p["path_id"]) if p["corridor_state"] == "contaminated_corridor"]
    weak_contagion_links = [p["path_id"] for p in sorted(path_records, key=lambda p: p["path_id"]) if p["corridor_state"] == "weak_corridor"]

    return {
        "tier": "3I",
        "phase": "3C",
        "scoring_version": SCORING_VERSION,
        "contagion_risk_state": contagion_risk_state,
        **metrics,
        "contagion_hubs": contagion_hubs,
        "amplification_hubs": amplification_hubs,
        "chokepoint_nodes": chokepoint_nodes,
        "vulnerable_nodes": vulnerable_nodes,
        "contagion_corridors": contagion_corridors,
        "high_pressure_paths": high_pressure_paths,
        "suppressed_corridors": suppressed_corridors,
        "contaminated_corridors": contaminated_corridors,
        "weak_contagion_links": weak_contagion_links,
        "path_corridor_states": [{"path_id": p["path_id"], "corridor_state": p["corridor_state"]} for p in sorted(path_records, key=lambda p: p["path_id"])],
        "explainability_payload": {
            "contagion_rationale": [
                "Contagion pressure combines path quality, structural influence, reinforcement, and propagation density.",
                f"Risk state={contagion_risk_state} from deterministic bounded thresholding.",
            ],
            "key_contributing_metrics": metrics,
            "dominant_contagion_drivers": [k for k, _ in sorted(metrics.items(), key=lambda kv: (-kv[1], kv[0]))[:3]],
            "hub_explanations": [f"Node {nid} participates in {node_occurrence.get(nid, 0)} paths with pressure contribution {node_pressure_contrib.get(nid, 0.0):.3f}." for nid in contagion_hubs],
            "corridor_explanations": [f"Path {p['path_id']} classified as {p['corridor_state']} with pressure={p['path_pressure_score']:.3f}." for p in sorted(path_records, key=lambda p: (-p['path_pressure_score'], p['path_id']))[:5]],
            "chokepoint_explanations": [f"Node {nid} appears in {node_occurrence.get(nid, 0)} paths across strong={strong_node_occurrence.get(nid, 0)} and weak={weak_node_occurrence.get(nid, 0)} participation." for nid in chokepoint_nodes],
            "suppression_explanations": [f"Suppressed corridor count={suppressed_count}, clustered_suppression={clustered_suppression:.3f}."],
            "contamination_explanations": [f"Contaminated corridor count={contaminated_count}, contamination_cluster={contamination_cluster:.3f}, overlap={contaminated_overlap:.3f}."],
            "resilience_explanation": f"Resilience={contagion_resilience_score:.3f} rises with healthy corridors and low suppression/contamination/chokepoint dominance.",
            "warnings": sorted([
                w for w, cond in [
                    ("elevated_suppression_bottlenecks", suppression_bottleneck_score >= 0.55),
                    ("elevated_contamination_spread", contamination_spread_score >= 0.50),
                    ("high_hub_concentration", hub_concentration_score >= 0.70),
                    ("fragile_contagion_structure", contagion_fragility_score >= 0.62),
                ] if cond
            ]),
        },
        "status": "success",
    }


def _sample_inputs() -> Dict[str, Any]:
    return {
        "quality_scored_edges": [],
        "structural_influence_nodes": [
            {"node_id": "A", "structural_influence_score": 0.82},
            {"node_id": "B", "structural_influence_score": 0.70},
            {"node_id": "C", "structural_influence_score": 0.58},
            {"node_id": "D", "structural_influence_score": 0.40},
        ],
        "multi_hop_paths": [
            {"path_id": "path::A->B->C", "path_nodes": ["A", "B", "C"], "path_quality_score": 0.81, "reinforcement_score": 0.12, "suppressed_for_propagation": False, "contamination_warning": False},
            {"path_id": "path::A->B->D", "path_nodes": ["A", "B", "D"], "path_quality_score": 0.73, "reinforcement_score": 0.10, "suppressed_for_propagation": False, "contamination_warning": False},
            {"path_id": "path::C->D", "path_nodes": ["C", "D"], "path_quality_score": 0.38, "reinforcement_score": 0.02, "suppressed_for_propagation": True, "contamination_warning": True},
        ],
        "path_explanations": [],
        "structural_regime_summary": {"regime_state": "transitioning"},
        "regime_drift_summary": {"drift_direction": "mixed"},
    }


def main() -> None:
    logs = Path("logs")
    inputs_path = logs / "tier3i_contagion_mapping_inputs.json"
    if inputs_path.exists():
        payload = json.loads(inputs_path.read_text(encoding="utf-8"))
    else:
        payload = _sample_inputs()

    summary = map_structural_contagion(
        quality_scored_edges=payload.get("quality_scored_edges", []),
        structural_influence_nodes=payload.get("structural_influence_nodes", []),
        multi_hop_paths=payload.get("multi_hop_paths", []),
        path_explanations=payload.get("path_explanations", []),
        structural_regime_summary=payload.get("structural_regime_summary", {}),
        regime_drift_summary=payload.get("regime_drift_summary", {}),
    )

    out = logs / "tier3i_contagion_mapping_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        "[tier3i] "
        f"contagion_risk_state={summary['contagion_risk_state']} "
        f"pressure={summary['contagion_pressure_score']:.3f} "
        f"amplification={summary['amplification_score']:.3f} "
        f"chokepoints={len(summary['chokepoint_nodes'])} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
