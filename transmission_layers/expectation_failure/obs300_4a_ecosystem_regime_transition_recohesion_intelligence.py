"""OBS300-4A deterministic ecosystem regime transition & narrative re-cohesion intelligence."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

_MAX_LIST_ITEMS = 8
_MAX_SUMMARY_CHARS = 260


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
        values = [str(x)[:96] for x in raw]
        return values[:_MAX_LIST_ITEMS] if values else default
    return default[:_MAX_LIST_ITEMS]


def _bounded_summary(summary: str) -> str:
    return summary[:_MAX_SUMMARY_CHARS]


def build_obs300_4a_ecosystem_regime_transition_recohesion_intelligence(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    regime_transition_score = _clamp((_f(payload, "tightening_stabilization_signal", 50.0) * 0.28) + (_f(payload, "disinflation_normalization_signal", 50.0) * 0.24) + (_f(payload, "capex_margin_normalization_signal", 50.0) * 0.22) + (_f(payload, "fragmentation_recohesion_signal", 50.0) * 0.26))
    structural_transition_score = _clamp((_f(payload, "structural_transition_signal", 50.0) * 0.60) + (_f(payload, "cross_regime_topology_signal", 50.0) * 0.40))
    transition_continuity_score = _clamp((_f(payload, "transition_continuity_signal", 50.0) * 0.65) + ((100.0 - _f(payload, "transition_dislocation_signal", 50.0)) * 0.35))
    normalization_migration_score = _clamp((_f(payload, "normalization_migration_signal", 50.0) * 0.70) + (_f(payload, "normalization_transmission_signal", 50.0) * 0.30))

    recohesion_score = _clamp((_f(payload, "narrative_recohesion_signal", 50.0) * 0.45) + (_f(payload, "decomposition_reconnection_signal", 50.0) * 0.30) + (_f(payload, "topology_realignment_signal", 50.0) * 0.25))
    synchronization_recovery_score = _clamp((_f(payload, "synchronization_recovery_signal", 50.0) * 0.65) + ((100.0 - _f(payload, "synchronization_dispersion_signal", 50.0)) * 0.35))
    topology_realignment_score = _clamp((_f(payload, "topology_realignment_signal", 50.0) * 0.55) + (_f(payload, "cross_regime_topology_signal", 50.0) * 0.45))

    cross_regime_bridge_score = _clamp((_f(payload, "cross_regime_bridge_signal", 50.0) * 0.55) + (_f(payload, "normalization_transmission_signal", 50.0) * 0.20) + (_f(payload, "stabilization_bridge_persistence_signal", 50.0) * 0.25))
    bridge_continuity_score = _clamp((_f(payload, "transition_bridge_continuity_signal", 50.0) * 0.60) + (_f(payload, "stabilization_bridge_persistence_signal", 50.0) * 0.40))

    strongest_transition_bridges = _bounded_list(payload, "strongest_transition_bridges", [
        "tightening->stabilization_duration_repricing",
        "inflation_pressure->disinflation_normalization",
        "capex_expansion->margin_normalization",
    ])
    highest_recohesion_clusters = _bounded_list(payload, "highest_recohesion_clusters", [
        "defensive_quality_duration_recohesion",
        "credit_liquidity_synchronization_recovery",
        "cyclical_fragmentation_to_realignment",
    ])
    normalization_migration_observations = _bounded_list(payload, "normalization_migration_observations", [
        "energy_cost_normalization->input_margin_relief",
        "rate_volatility_compression->duration_balance",
    ])
    cross_regime_propagation_pathways = _bounded_list(payload, "cross_regime_propagation_pathways", [
        "policy_tightening->liquidity_rebalancing->stabilization",
        "fragmentation->bridge_reconnectors->recohesion",
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

    transition_intelligence_summary = {
        "strongest_transition_bridges": strongest_transition_bridges,
        "highest_recohesion_clusters": highest_recohesion_clusters,
        "normalization_migration_observations": normalization_migration_observations,
        "synchronization_recovery_summaries": _bounded_summary(f"sync_recovery_band={_band(synchronization_recovery_score)};topology_realignment_band={_band(topology_realignment_score)}"),
        "regime_continuity_observations": _bounded_summary(f"transition_continuity_band={_band(transition_continuity_score)};bridge_continuity_band={_band(bridge_continuity_score)}"),
        "ecosystem_transition_topology_summaries": _bounded_summary(f"regime_transition_score={regime_transition_score};cross_regime_bridge_score={cross_regime_bridge_score};normalization_migration_band={_band(normalization_migration_score)}"),
    }

    visualization_payloads = {
        "regime_transition_dashboards": {
            "regime_transition_score": regime_transition_score,
            "structural_transition_score": structural_transition_score,
            "transition_continuity_score": transition_continuity_score,
        },
        "recohesion_topology_maps": {
            "narrative_recohesion_score": recohesion_score,
            "topology_realignment_score": topology_realignment_score,
            "highest_recohesion_clusters": highest_recohesion_clusters,
        },
        "transition_bridge_panels": {
            "cross_regime_bridge_score": cross_regime_bridge_score,
            "transition_bridge_continuity_score": bridge_continuity_score,
            "strongest_transition_bridges": strongest_transition_bridges,
        },
        "synchronization_recovery_summaries": {
            "synchronization_recovery_score": synchronization_recovery_score,
            "decomposed_pathway_reconnection_band": _band(_clamp((_f(payload, "decomposition_reconnection_signal", 50.0) + synchronization_recovery_score) / 2)),
        },
        "normalization_migration_views": {
            "normalization_migration_score": normalization_migration_score,
            "cross_regime_propagation_pathways": cross_regime_propagation_pathways,
        },
    }

    return {
        "module": "OBS300-4A",
        "status": "deterministic_ecosystem_regime_transition_recohesion_intelligence_complete",
        "ecosystem_regime_transition_observation": {
            "regime_transition_score": regime_transition_score,
            "structural_transition_observation_score": structural_transition_score,
            "transition_continuity_score": transition_continuity_score,
            "normalization_migration_score": normalization_migration_score,
            "cross_regime_propagation_pathways": cross_regime_propagation_pathways,
        },
        "narrative_recohesion_observation": {
            "narrative_recohesion_score": recohesion_score,
            "synchronization_recovery_score": synchronization_recovery_score,
            "topology_realignment_score": topology_realignment_score,
            "decomposed_pathway_reconnection_observation": _bounded_summary(f"reconnection_band={_band(_clamp(_f(payload, 'decomposition_reconnection_signal', 50.0)))};sync_band={_band(synchronization_recovery_score)}"),
            "ecosystem_resynchronization_summary": _bounded_summary(f"recohesion_band={_band(recohesion_score)};realignment_band={_band(topology_realignment_score)}"),
        },
        "cross_regime_bridge_intelligence": {
            "cross_regime_bridge_score": cross_regime_bridge_score,
            "transition_bridge_continuity_observation_score": bridge_continuity_score,
            "normalization_transmission_pathways": cross_regime_propagation_pathways,
            "regime_migration_summary": _bounded_summary(f"normalization_migration_band={_band(normalization_migration_score)};bridge_band={_band(cross_regime_bridge_score)}"),
            "stabilization_bridge_persistence_band": _band(_clamp(_f(payload, "stabilization_bridge_persistence_signal", 50.0))),
        },
        "ecosystem_transition_intelligence_summary": transition_intelligence_summary,
        "operator_facing_visualization_payloads": visualization_payloads,
        "regime_transition_architecture_summary": {
            "payload_only_contracts": True,
            "graph_execution_engine_required": False,
            "topology_activation_required": False,
            "autonomous_replay_required": False,
            "orchestration_complexity": "lightweight",
            "deterministic_where_practical": True,
        },
        "governance_certification": governance_certification,
        "operational_report": {
            "implementation": "deterministic_observational_regime_transition_recohesion_intelligence",
            "deterministic": True,
            "bounded": True,
            "autonomous_logic": False,
            "sql_writes_enabled": False,
            "prediction_or_trading_execution": False,
        },
    }
