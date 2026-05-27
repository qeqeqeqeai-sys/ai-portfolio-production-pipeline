"""OBS300-3B deterministic ecosystem rotation, recovery bridges & pressure absorption intelligence."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

_MAX_LIST_ITEMS = 8
_MAX_SUMMARY_CHARS = 240


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))


def _band(score: int) -> str:
    if score < 20:
        return "low"
    if score < 40:
        return "mild"
    if score < 60:
        return "elevated"
    if score < 80:
        return "high"
    return "severe"


def _f(payload: Dict[str, object], key: str, default: float = 50.0) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        return max(0.0, min(100.0, float(value)))
    return default


def _bounded_list(payload: Dict[str, object], key: str, default: List[str]) -> List[str]:
    raw = payload.get(key)
    if isinstance(raw, list):
        values = [str(x)[:80] for x in raw]
        return values[:_MAX_LIST_ITEMS] if values else default
    return default[:_MAX_LIST_ITEMS]


def _bounded_summary(summary: str) -> str:
    return summary[:_MAX_SUMMARY_CHARS]


def build_obs300_3b_ecosystem_rotation_recovery_absorption_intelligence(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    leadership_rotation_score = _clamp((_f(payload, "ai_leadership_decay", 50.0) * 0.45) + (_f(payload, "defensive_stabilization_emergence", 50.0) * 0.35) + (_f(payload, "propagation_migration_intensity", 50.0) * 0.20))
    thematic_rotation_score = _clamp((_f(payload, "liquidity_sensitive_fragmentation_rotation", 50.0) * 0.50) + (_f(payload, "cyclical_decomposition_shift", 50.0) * 0.50))
    topology_leadership_decay_score = _clamp((_f(payload, "topology_leadership_decay", 50.0) * 0.60) + (_f(payload, "propagation_continuity_loss", 50.0) * 0.40))

    recovery_bridge_score = _clamp((_f(payload, "duration_stabilization", 50.0) * 0.30) + (_f(payload, "energy_normalization", 50.0) * 0.30) + (_f(payload, "liquidity_recovery", 50.0) * 0.40))
    stabilization_propagation_score = _clamp((_f(payload, "stabilization_pathway_strength", 50.0) * 0.55) + (_f(payload, "normalization_transmission_clarity", 50.0) * 0.45))
    recovery_continuity_score = _clamp((_f(payload, "recovery_continuity", 50.0) * 0.60) + ((100.0 - _f(payload, "decompression_disruption", 50.0)) * 0.40))

    pressure_absorber_score = _clamp((_f(payload, "defensive_absorption", 50.0) * 0.35) + (_f(payload, "quality_balance_sheet_stabilization", 50.0) * 0.35) + (_f(payload, "utilities_normalization", 50.0) * 0.30))
    resilience_cluster_score = _clamp((pressure_absorber_score * 0.55) + (stabilization_propagation_score * 0.45))
    ecosystem_resilience_score = _clamp((recovery_bridge_score * 0.40) + (pressure_absorber_score * 0.35) + (recovery_continuity_score * 0.25))

    strongest_recovery_bridges = _bounded_list(payload, "strongest_recovery_bridges", [
        "falling_yields->duration_stabilization",
        "energy_normalization->industrials_decompression",
        "liquidity_recovery->credit_stabilization",
    ])
    resilience_clusters = _bounded_list(payload, "resilience_clusters", [
        "defensive_sectors_volatility_absorption",
        "quality_balance_sheet_cluster",
        "utilities_infrastructure_normalization",
    ])
    stabilization_pathways = _bounded_list(payload, "stabilization_pathways", [
        "duration->quality_growth_stabilization",
        "liquidity->credit->cyclical_normalization",
    ])

    governance_certification = {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    ecosystem_resilience_summary = {
        "strongest_recovery_bridges": strongest_recovery_bridges,
        "highest_resilience_clusters": resilience_clusters,
        "stabilization_propagation_summary": _bounded_summary(f"stabilization_score={stabilization_propagation_score};recovery_continuity_band={_band(recovery_continuity_score)}"),
        "ecosystem_normalization_observations": _bounded_summary(f"normalization_band={_band(_clamp(_f(payload, 'normalization_transmission_clarity', 50.0)))};resilience_band={_band(ecosystem_resilience_score)}"),
        "pressure_absorption_hotspots": resilience_clusters,
        "rotation_topology_summary": _bounded_summary(f"leadership_rotation_score={leadership_rotation_score};thematic_rotation_score={thematic_rotation_score};topology_decay_band={_band(topology_leadership_decay_score)}"),
    }

    visualization_payloads = {
        "ecosystem_rotation_dashboards": {
            "leadership_rotation_score": leadership_rotation_score,
            "thematic_rotation_score": thematic_rotation_score,
            "rotation_continuity_band": _band(_clamp((100 + leadership_rotation_score - topology_leadership_decay_score) / 2)),
        },
        "recovery_bridge_maps": {
            "recovery_bridge_score": recovery_bridge_score,
            "strongest_recovery_bridges": strongest_recovery_bridges,
        },
        "resilience_cluster_panels": {
            "resilience_cluster_score": resilience_cluster_score,
            "highest_resilience_clusters": resilience_clusters,
        },
        "stabilization_pathway_summaries": {
            "stabilization_propagation_score": stabilization_propagation_score,
            "stabilization_pathways": stabilization_pathways,
        },
        "normalization_topology_views": {
            "recovery_continuity_score": recovery_continuity_score,
            "ecosystem_resilience_score": ecosystem_resilience_score,
            "normalization_transmission_band": _band(_clamp(_f(payload, "normalization_transmission_clarity", 50.0))),
        },
    }

    return {
        "module": "OBS300-3B",
        "status": "deterministic_ecosystem_rotation_recovery_absorption_intelligence_complete",
        "ecosystem_rotation_observation": {
            "leadership_rotation_score": leadership_rotation_score,
            "thematic_rotation_score": thematic_rotation_score,
            "propagation_migration_band": _band(_clamp(_f(payload, "propagation_migration_intensity", 50.0))),
            "topology_leadership_decay_score": topology_leadership_decay_score,
            "rotation_continuity_summary": _bounded_summary(f"leadership={leadership_rotation_score};thematic={thematic_rotation_score};decay={topology_leadership_decay_score}"),
        },
        "recovery_bridge_intelligence": {
            "recovery_bridge_score": recovery_bridge_score,
            "stabilization_propagation_score": stabilization_propagation_score,
            "recovery_continuity_score": recovery_continuity_score,
            "decompression_bridge_summary": _bounded_summary(f"bridge_score={recovery_bridge_score};continuity_band={_band(recovery_continuity_score)}"),
            "normalization_transmission_pathways": stabilization_pathways,
        },
        "pressure_absorption_observation": {
            "pressure_absorber_score": pressure_absorber_score,
            "stabilization_node_observation": _bounded_summary(f"absorber_band={_band(pressure_absorber_score)};stabilization_band={_band(stabilization_propagation_score)}"),
            "resilience_cluster_summaries": resilience_clusters,
            "pressure_dampening_observation": _bounded_summary(f"dampening_band={_band(_clamp((pressure_absorber_score + recovery_continuity_score)/2))}"),
            "ecosystem_resilience_pathways": stabilization_pathways,
        },
        "ecosystem_resilience_intelligence": ecosystem_resilience_summary,
        "operator_facing_visualization_payloads": visualization_payloads,
        "recovery_bridge_architecture_summary": {
            "payload_only_contracts": True,
            "graph_execution_engine_required": False,
            "topology_activation_required": False,
            "autonomous_replay_required": False,
            "orchestration_complexity": "lightweight",
        },
        "governance_certification": governance_certification,
        "operational_report": {
            "implementation": "deterministic_observational_rotation_recovery_absorption_intelligence",
            "deterministic": True,
            "bounded": True,
            "autonomous_logic": False,
            "sql_writes_enabled": False,
            "prediction_or_trading_execution": False,
        },
    }
