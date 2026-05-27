"""OBS300-4B deterministic ecosystem state compression & structural signal prioritization intelligence."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping

_MAX_LIST_ITEMS = 6
_MAX_SUMMARY_CHARS = 280


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))


def _f(payload: Mapping[str, object], key: str, default: float = 50.0) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        return max(0.0, min(100.0, float(value)))
    return default


def _bounded_summary(summary: str) -> str:
    return summary[:_MAX_SUMMARY_CHARS]


def _bounded_list(values: List[str]) -> List[str]:
    return [str(v)[:96] for v in values[:_MAX_LIST_ITEMS]]


def _band(score: int) -> str:
    if score < 25:
        return "low"
    if score < 45:
        return "mild"
    if score < 65:
        return "elevated"
    if score < 80:
        return "high"
    return "severe"


def _signal_row(payload: Mapping[str, object], name: str, *, persistence_key: str, propagation_key: str, bridge_key: str, impact_key: str, relevance_key: str) -> Dict[str, Any]:
    relevance = _clamp(_f(payload, relevance_key, 50.0))
    persistence = _clamp(_f(payload, persistence_key, 50.0))
    propagation = _clamp(_f(payload, propagation_key, 50.0))
    bridge = _clamp(_f(payload, bridge_key, 50.0))
    impact = _clamp(_f(payload, impact_key, 50.0))
    priority = _clamp((relevance * 0.30) + (persistence * 0.20) + (propagation * 0.20) + (bridge * 0.15) + (impact * 0.15))
    return {
        "signal": name,
        "relevance_score": relevance,
        "persistence_weight": persistence,
        "propagation_weight": propagation,
        "bridge_significance_weight": bridge,
        "ecosystem_impact_weight": impact,
        "structural_priority_score": priority,
    }


def _classify_posture(scores: Mapping[str, int]) -> str:
    stress = scores["stress"]
    normalization = scores["recovery"]
    transition = scores["transition"]
    frag = scores["fragmentation"]
    resilience = scores["resilience"]
    if frag >= 70 and resilience <= 45:
        return "fragmented"
    if stress >= 70 and normalization <= 45:
        return "stress_dominant"
    if normalization >= 70 and stress <= 50:
        return "normalization_dominant"
    if resilience >= 72 and frag <= 48:
        return "resilient"
    if transition >= 68 and abs(normalization - stress) <= 15:
        return "mixed_transition"
    if transition >= 62:
        return "transitioning"
    if normalization >= 58 and frag <= 58:
        return "stabilizing"
    return "decompression_emerging"


def build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    scores = {
        "stress": _clamp((_f(payload, "dominant_stress_signal", 50.0) * 0.65) + (_f(payload, "topology_pressure_signal", 50.0) * 0.35)),
        "recovery": _clamp((_f(payload, "dominant_recovery_signal", 50.0) * 0.6) + (_f(payload, "normalization_pathway_signal", 50.0) * 0.4)),
        "transition": _clamp((_f(payload, "dominant_transition_signal", 50.0) * 0.7) + (_f(payload, "transition_bridge_signal", 50.0) * 0.3)),
        "fragmentation": _clamp((_f(payload, "dominant_fragmentation_signal", 50.0) * 0.7) + (_f(payload, "semantic_congestion_signal", 50.0) * 0.3)),
        "resilience": _clamp((_f(payload, "dominant_resilience_signal", 50.0) * 0.7) + (_f(payload, "continuity_domain_signal", 50.0) * 0.3)),
    }

    rows = [
        _signal_row(payload, "stress_cluster", persistence_key="stress_persistence", propagation_key="stress_propagation", bridge_key="stress_bridge_significance", impact_key="stress_impact", relevance_key="stress_relevance"),
        _signal_row(payload, "recovery_cluster", persistence_key="recovery_persistence", propagation_key="recovery_propagation", bridge_key="recovery_bridge_significance", impact_key="recovery_impact", relevance_key="recovery_relevance"),
        _signal_row(payload, "transition_bridge_cluster", persistence_key="transition_persistence", propagation_key="transition_propagation", bridge_key="transition_bridge_significance", impact_key="transition_impact", relevance_key="transition_relevance"),
        _signal_row(payload, "resilience_cluster", persistence_key="resilience_persistence", propagation_key="resilience_propagation", bridge_key="resilience_bridge_significance", impact_key="resilience_impact", relevance_key="resilience_relevance"),
        _signal_row(payload, "fragmentation_cluster", persistence_key="fragmentation_persistence", propagation_key="fragmentation_propagation", bridge_key="fragmentation_bridge_significance", impact_key="fragmentation_impact", relevance_key="fragmentation_relevance"),
    ]
    ranked = sorted(rows, key=lambda r: (-r["structural_priority_score"], r["signal"]))

    posture = _classify_posture(scores)
    top_signals = [r["signal"] for r in ranked[:3]]

    noise_layer = {
        "topology_saturation_suppression": _clamp(100 - _f(payload, "topology_saturation_signal", 50.0)),
        "repetitive_signal_compression": _clamp(100 - _f(payload, "repetitive_signal_density", 50.0)),
        "redundant_pathway_suppression": _clamp(100 - _f(payload, "redundant_pathway_density", 50.0)),
        "monoculture_signal_suppression": _clamp(100 - _f(payload, "monoculture_signal_density", 50.0)),
        "semantic_congestion_reduction": _clamp(100 - _f(payload, "semantic_congestion_signal", 50.0)),
    }

    governance = {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    return {
        "module": "OBS300-4B",
        "status": "deterministic_ecosystem_state_compression_and_structural_signal_prioritization_complete",
        "ecosystem_state_compression_summary": {
            "dominant_stress_structure": _bounded_summary(f"score={scores['stress']};band={_band(scores['stress'])}"),
            "dominant_recovery_structure": _bounded_summary(f"score={scores['recovery']};band={_band(scores['recovery'])}"),
            "dominant_transition_structure": _bounded_summary(f"score={scores['transition']};band={_band(scores['transition'])}"),
            "dominant_fragmentation_structure": _bounded_summary(f"score={scores['fragmentation']};band={_band(scores['fragmentation'])}"),
            "dominant_resilience_structure": _bounded_summary(f"score={scores['resilience']};band={_band(scores['resilience'])}"),
            "ecosystem_posture_summary": _bounded_summary(f"posture={posture};priority_signals={','.join(top_signals)}"),
        },
        "structural_signal_prioritization": {"ranked_structural_signals": ranked, "prioritization_basis": "structural_importance_not_predictive_strength"},
        "ecosystem_attention_allocation": {
            "highest_priority_ecosystem_signals": _bounded_list(top_signals),
            "dominant_topology_pressures": _bounded_list(["stress_cluster", "fragmentation_cluster"] if scores["stress"] >= scores["fragmentation"] else ["fragmentation_cluster", "stress_cluster"]),
            "strongest_normalization_pathways": _bounded_list(["recovery_cluster", "transition_bridge_cluster"]),
            "critical_transition_bridges": _bounded_list(["transition_bridge_cluster"]),
            "highest_continuity_domains": _bounded_list(["resilience_cluster"]),
            "dominant_resilience_structures": _bounded_list(["resilience_cluster", "recovery_cluster"]),
        },
        "noise_suppression_layer": noise_layer,
        "ecosystem_posture_classification": {
            "posture": posture,
            "posture_band_context": _bounded_summary(f"stress={_band(scores['stress'])};recovery={_band(scores['recovery'])};transition={_band(scores['transition'])};fragmentation={_band(scores['fragmentation'])};resilience={_band(scores['resilience'])}"),
        },
        "operator_facing_visualization_payloads": {
            "compressed_ecosystem_dashboard": {"scores": scores, "posture": posture},
            "dominant_topology_summary": {"topology_pressure_band": _band(scores["stress"]), "fragmentation_band": _band(scores["fragmentation"])},
            "structural_priority_panel": {"top_ranked_signals": ranked[:3]},
            "ecosystem_posture_view": {"classification": posture, "context": scores},
            "signal_compression_summary": {"suppression_effectiveness": noise_layer},
        },
        "signal_prioritization_architecture_summary": {
            "payload_only_contracts": True,
            "deterministic_where_practical": True,
            "graph_execution_engine_required": False,
            "topology_activation_required": False,
            "autonomous_replay_required": False,
            "sql_write_required": False,
        },
        "governance_certification": governance,
        "operational_report": {
            "implementation": "deterministic_observational_ecosystem_state_compression_prioritization",
            "deterministic": True,
            "bounded": True,
            "autonomous_logic": False,
            "sql_writes_enabled": False,
            "prediction_or_trading_execution": False,
        },
    }
