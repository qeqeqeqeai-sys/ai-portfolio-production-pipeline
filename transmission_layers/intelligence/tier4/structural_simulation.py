"""Tier 4A deterministic structural stress simulation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SCORING_VERSION = "4A.v1"
MAX_PROPAGATION_DEPTH = 4
MAX_AMPLIFICATION_FACTOR = 1.0
MIN_DECAY_FACTOR = 0.15
DEFAULT_DECAY_COEFFICIENT = 0.82

# Transition ordering: healthy -> stressed -> degraded -> suppressed -> failed.
CORRIDOR_STATES_ORDER = ["healthy", "stressed", "degraded", "suppressed", "failed"]
VALID_CORRIDOR_TRANSITIONS = {
    "healthy": {"healthy", "stressed"},
    "stressed": {"stressed", "degraded"},
    "degraded": {"degraded", "suppressed"},
    "suppressed": {"suppressed", "failed"},
    "failed": {"failed"},
}


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def clamp_normalized_score(value: float) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def _stable_string_list(values: Iterable[str]) -> List[str]:
    return sorted({str(v) for v in values if str(v).strip()})


def _deterministic_replay_checksum(payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _corridor_state_from_failure_index(edge: Dict[str, Any], failure_index: float) -> str:
    if failure_index >= 0.82:
        return "failed"
    if bool(edge.get("suppressed_for_propagation", False)) or failure_index >= 0.66:
        return "suppressed"
    if failure_index >= 0.45:
        return "degraded"
    if failure_index >= 0.28:
        return "stressed"
    return "healthy"


def _resolve_corridor_transition(previous_state: str, candidate_state: str) -> Tuple[str, bool]:
    if candidate_state in VALID_CORRIDOR_TRANSITIONS.get(previous_state, set()):
        return candidate_state, False
    prev_index = CORRIDOR_STATES_ORDER.index(previous_state)
    cand_index = CORRIDOR_STATES_ORDER.index(candidate_state)
    if cand_index <= prev_index:
        return previous_state, True
    return CORRIDOR_STATES_ORDER[prev_index + 1], True


def load_simulation_inputs() -> Dict[str, Any]:
    return {"quality_scored_edges": [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.92, "suppressed_for_propagation": False}, {"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.87, "suppressed_for_propagation": False}, {"source_node_id": "A", "target_node_id": "D", "edge_quality_score": 0.56, "suppressed_for_propagation": False}, {"source_node_id": "D", "target_node_id": "E", "edge_quality_score": 0.42, "suppressed_for_propagation": True}], "structural_influence_nodes": [{"node_id": "A", "influence_score": 0.88, "contagion_score": 0.81, "chokepoint_score": 0.62, "fragmentation_score": 0.33, "regime_fragility_score": 0.49, "resilience_score": 0.52, "traffic_score": 0.76, "centrality_score": 0.89}, {"node_id": "B", "influence_score": 0.74, "contagion_score": 0.68, "chokepoint_score": 0.79, "fragmentation_score": 0.28, "regime_fragility_score": 0.55, "resilience_score": 0.44, "traffic_score": 0.82, "centrality_score": 0.84}, {"node_id": "C", "influence_score": 0.55, "contagion_score": 0.57, "chokepoint_score": 0.41, "fragmentation_score": 0.25, "regime_fragility_score": 0.35, "resilience_score": 0.65, "traffic_score": 0.51, "centrality_score": 0.63}, {"node_id": "D", "influence_score": 0.42, "contagion_score": 0.49, "chokepoint_score": 0.60, "fragmentation_score": 0.71, "regime_fragility_score": 0.66, "resilience_score": 0.36, "traffic_score": 0.71, "centrality_score": 0.58}, {"node_id": "E", "influence_score": 0.33, "contagion_score": 0.45, "chokepoint_score": 0.29, "fragmentation_score": 0.62, "regime_fragility_score": 0.59, "resilience_score": 0.39, "traffic_score": 0.47, "centrality_score": 0.45}]}


def inject_structural_stress(nodes: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    injected = {}
    for node in sorted(nodes, key=lambda n: str(n.get("node_id", ""))):
        nid = str(node.get("node_id", ""))
        score = 0.32 * _to_float(node.get("influence_score")) + 0.24 * _to_float(node.get("contagion_score")) + 0.19 * _to_float(node.get("chokepoint_score")) + 0.13 * _to_float(node.get("fragmentation_score")) + 0.12 * _to_float(node.get("regime_fragility_score"))
        injected[nid] = clamp_normalized_score(score)
    return injected


def compute_amplification_effects(nodes: Iterable[Dict[str, Any]]) -> float:
    vals = []
    for node in nodes:
        vals.append(clamp_normalized_score(0.35 * _to_float(node.get("influence_score")) + 0.35 * _to_float(node.get("contagion_score")) + 0.20 * _to_float(node.get("regime_fragility_score")) + 0.10 * (1.0 - _to_float(node.get("resilience_score"), 0.5))))
    return clamp_normalized_score(sum(vals) / len(vals) if vals else 0.0)


def propagate_stress(edges: Iterable[Dict[str, Any]], injected: Dict[str, float], amplification: float) -> Tuple[Dict[str, float], float, Dict[str, int]]:
    by_depth = dict(injected)
    result = dict(injected)
    diagnostics = {"amplification_cap_hits": 0, "decay_floor_hits": 0, "propagation_depth_reached": 0}
    bounded_amp = clamp_normalized_score(min(MAX_AMPLIFICATION_FACTOR, amplification))
    if amplification > MAX_AMPLIFICATION_FACTOR:
        diagnostics["amplification_cap_hits"] += 1
    for depth in range(1, MAX_PROPAGATION_DEPTH + 1):
        diagnostics["propagation_depth_reached"] = depth
        decay_raw = DEFAULT_DECAY_COEFFICIENT ** depth
        decay = max(MIN_DECAY_FACTOR, decay_raw)
        if decay == MIN_DECAY_FACTOR and decay_raw < MIN_DECAY_FACTOR:
            diagnostics["decay_floor_hits"] += 1
        nxt = {}
        for edge in sorted(edges, key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", "")))):
            if bool(edge.get("suppressed_for_propagation", False)):
                continue
            src = str(edge.get("source_node_id", ""))
            dst = str(edge.get("target_node_id", ""))
            prop = _to_float(by_depth.get(src, 0.0)) * clamp_normalized_score(_to_float(edge.get("edge_quality_score"), 0.0)) * decay * (1.0 + 0.5 * bounded_amp)
            nxt[dst] = max(nxt.get(dst, 0.0), clamp_normalized_score(prop))
        for k, v in nxt.items():
            result[k] = max(result.get(k, 0.0), v)
        by_depth = nxt
        if not by_depth:
            break
    return result, clamp_normalized_score(sum(result.values()) / len(result) if result else 0.0), diagnostics


def compute_chokepoint_overload(nodes: Iterable[Dict[str, Any]], node_stress: Dict[str, float]) -> Tuple[List[str], float]:
    overloaded = []
    sev = []
    for node in sorted(nodes, key=lambda n: str(n.get("node_id", ""))):
        nid = str(node.get("node_id", ""))
        stress = _to_float(node_stress.get(nid, 0.0))
        score = clamp_normalized_score(0.40 * stress + 0.30 * _to_float(node.get("chokepoint_score")) + 0.20 * _to_float(node.get("traffic_score")) + 0.10 * _to_float(node.get("centrality_score")))
        sev.append(score)
        if score >= 0.67:
            overloaded.append(nid)
    return overloaded, clamp_normalized_score(sum(sev) / len(sev) if sev else 0.0)


def compute_suppression_cascades(edges: Iterable[Dict[str, Any]], overload_score: float, avg_stress: float) -> float:
    es = list(edges)
    sr = sum(1 for e in es if bool(e.get("suppressed_for_propagation", False))) / len(es) if es else 0.0
    return clamp_normalized_score(0.45 * sr + 0.30 * overload_score + 0.25 * avg_stress)


def classify_corridor_health(edges: Iterable[Dict[str, Any]], node_stress: Dict[str, float], suppression: float, resilience_deg: float) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    out = {"resilient_corridors": [], "degraded_corridors": [], "suppressed_corridors": [], "failed_corridors": []}
    transition_diag = {"illegal_transition_prevented": 0, "resolved_transitions": []}
    for edge in sorted(edges, key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", "")))):
        cid = f"{edge.get('source_node_id', '')}->{edge.get('target_node_id', '')}"
        q = clamp_normalized_score(_to_float(edge.get("edge_quality_score"), 0.0))
        s = max(_to_float(node_stress.get(str(edge.get("source_node_id", "")), 0.0)), _to_float(node_stress.get(str(edge.get("target_node_id", "")), 0.0)))
        fi = clamp_normalized_score(0.55 * s + 0.20 * suppression + 0.15 * resilience_deg + 0.10 * (1.0 - q))
        candidate_state = _corridor_state_from_failure_index(edge, fi)
        resolved_state, prevented = _resolve_corridor_transition("healthy", candidate_state)
        if prevented:
            transition_diag["illegal_transition_prevented"] += 1
        transition_diag["resolved_transitions"].append(f"{cid}:healthy->{resolved_state}")
        if resolved_state == "failed":
            out["failed_corridors"].append(cid)
        elif resolved_state == "suppressed":
            out["suppressed_corridors"].append(cid)
        elif resolved_state == "degraded":
            out["degraded_corridors"].append(cid)
        else:
            out["resilient_corridors"].append(cid)
    transition_diag["resolved_transitions"] = _stable_string_list(transition_diag["resolved_transitions"])
    return out, transition_diag


def classify_simulation_health_state(overload: float, contagion: float, suppression: float, resilience_deg: float, stressed_nodes: int) -> str:
    # Deterministic precedence order: cascading_failure > fragile > overloaded > stressed > contained > resilient > mixed.
    if overload >= 0.75 and contagion >= 0.72 and suppression >= 0.68 and resilience_deg >= 0.72:
        return "cascading_failure"
    if overload >= 0.58 and resilience_deg >= 0.55:
        return "fragile"
    if overload >= 0.62:
        return "overloaded"
    if contagion >= 0.50 or suppression >= 0.45:
        return "stressed"
    if stressed_nodes <= 2 and max(overload, contagion, suppression) < 0.45:
        return "contained"
    if overload < 0.35 and resilience_deg < 0.40 and contagion < 0.40 and suppression < 0.40:
        return "resilient"
    return "mixed"


def validate_simulation_invariants(result: Dict[str, Any]) -> Dict[str, Any]:
    tracked = [
        "propagated_stress_score",
        "amplification_effect_score",
        "suppression_cascade_score",
        "chokepoint_overload_score",
        "resilience_degradation_score",
        "contagion_escalation_score",
        "propagation_decay_score",
        "corridor_deterioration_score",
    ]
    failed = [k for k in tracked if not (0.0 <= _to_float(result.get(k, 0.0)) <= 1.0)]
    return {"all_invariants_valid": len(failed) == 0, "failed_invariants": failed}


def build_explainability_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "amplification_explanations": ["Amplification is bounded and deterministic from influence, contagion, fragility, and resilience."],
        "chokepoint_explanations": [f"{len(result['overloaded_nodes'])} nodes exceeded overload threshold >= 0.67."],
        "corridor_failure_explanations": [f"Failed corridors: {', '.join(result['failed_corridors']) or 'none'}."],
        "dominant_simulation_drivers": ["chokepoint_pressure", "contagion_hubs", "suppression_overlap"],
        "propagation_explanations": ["Propagation follows sorted unsuppressed edges with bounded depth and deterministic decay."],
        "resilience_explanations": ["Resilience degradation rises deterministically with suppression, overload, and propagated stress."],
        "simulation_rationale_strings": [
            f"Initial stress average: {result['initial_stress_score']:.3f}.",
            f"Propagated stress after bounded attenuation: {result['propagated_stress_score']:.3f}.",
        ],
        "suppression_explanations": ["Suppression blends suppressed-edge ratio, overload severity, and stress density."],
        "warnings": ["Structural failure warning active." if result["structural_failure_warning"] else "No structural failure warning."],
    }
    return {k: _stable_string_list(v) for k, v in payload.items()}


def run_structural_simulation(inputs: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = inputs or load_simulation_inputs()
    nodes = p.get("structural_influence_nodes", [])
    edges = p.get("quality_scored_edges", [])
    injected = inject_structural_stress(nodes)
    initial = clamp_normalized_score(sum(injected.values()) / len(injected) if injected else 0.0)
    amp = compute_amplification_effects(nodes)
    node_stress, prop, propagation_diag = propagate_stress(edges, injected, amp)
    overloaded, overload = compute_chokepoint_overload(nodes, node_stress)
    suppression = compute_suppression_cascades(edges, overload, prop)
    resilience = clamp_normalized_score(0.35 * suppression + 0.35 * overload + 0.30 * prop)
    corridors, corridor_diag = classify_corridor_health(edges, node_stress, suppression, resilience)
    stressed = sorted([n for n, s in node_stress.items() if s >= 0.45])
    contagion = clamp_normalized_score(0.60 * amp + 0.40 * prop)
    corridor_deterioration = clamp_normalized_score((len(corridors["degraded_corridors"]) + len(corridors["suppressed_corridors"]) + len(corridors["failed_corridors"])) / len(edges) if edges else 0.0)
    health = classify_simulation_health_state(overload, contagion, suppression, resilience, len(stressed))
    result = {"simulation_run_id": "tier4a_deterministic_run", "simulation_steps": ["inject", "propagate", "amplify", "suppress", "overload", "degrade", "classify"], "initial_stress_score": initial, "propagated_stress_score": prop, "amplification_effect_score": amp, "suppression_cascade_score": suppression, "chokepoint_overload_score": overload, "resilience_degradation_score": resilience, "contagion_escalation_score": contagion, "propagation_decay_score": clamp_normalized_score(1.0 - DEFAULT_DECAY_COEFFICIENT), "corridor_deterioration_score": corridor_deterioration, "stressed_nodes": stressed, "overloaded_nodes": overloaded, "degraded_corridors": corridors["degraded_corridors"], "resilient_corridors": corridors["resilient_corridors"], "suppressed_corridors": corridors["suppressed_corridors"], "failed_corridors": corridors["failed_corridors"], "simulation_health_state": health, "structural_failure_warning": health in {"fragile", "cascading_failure", "overloaded"} or bool(corridors["failed_corridors"]), "scoring_version": SCORING_VERSION}
    result["explainability_payload"] = build_explainability_payload(result)
    result["invariant_validation"] = validate_simulation_invariants(result)
    result["operational_diagnostics"] = {
        "amplification_cap_hits": propagation_diag["amplification_cap_hits"],
        "decay_floor_hits": propagation_diag["decay_floor_hits"],
        "propagation_depth_reached": propagation_diag["propagation_depth_reached"],
        "corridor_transition_diagnostics": corridor_diag,
    }
    checksum_payload = {
        k: result[k]
        for k in sorted(result.keys())
        if k not in {"deterministic_replay_checksum"}
    }
    result["deterministic_replay_checksum"] = _deterministic_replay_checksum(checksum_payload)
    return result


def _write_cli_summary(result: Dict[str, Any]) -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)
    summary = {"tier": "4", "phase": "4A", "scoring_version": result["scoring_version"], "simulation_health_state": result["simulation_health_state"], "initial_stress_score": result["initial_stress_score"], "propagated_stress_score": result["propagated_stress_score"], "amplification_effect_score": result["amplification_effect_score"], "suppression_cascade_score": result["suppression_cascade_score"], "chokepoint_overload_score": result["chokepoint_overload_score"], "resilience_degradation_score": result["resilience_degradation_score"], "contagion_escalation_score": result["contagion_escalation_score"], "propagation_decay_score": result["propagation_decay_score"], "structural_failure_warning": result["structural_failure_warning"], "stressed_nodes": result["stressed_nodes"], "overloaded_nodes": result["overloaded_nodes"], "degraded_corridors": result["degraded_corridors"], "failed_corridors": result["failed_corridors"], "status": "success"}
    Path("logs/tier4_structural_simulation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    r = run_structural_simulation()
    _write_cli_summary(r)
    print(f"[tier4] simulation_health_state={r['simulation_health_state']} propagated_stress={r['propagated_stress_score']:.4f} overload={r['chokepoint_overload_score']:.4f} resilience={r['resilience_degradation_score']:.4f} status=success")
