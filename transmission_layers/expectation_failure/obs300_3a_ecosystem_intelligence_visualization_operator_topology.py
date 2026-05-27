"""OBS300-3A deterministic ecosystem intelligence visualization & operator topology payload layer."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

_MAX_LIST_ITEMS = 8
_MAX_SUMMARY_CHARS = 240


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))


def _f(payload: Dict[str, object], key: str, default: float = 50.0) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        return max(0.0, min(100.0, float(value)))
    return default


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


def _bounded_list(payload: Dict[str, object], key: str, default: List[str]) -> List[str]:
    raw = payload.get(key)
    if isinstance(raw, list):
        values = [str(x)[:80] for x in raw]
        return values[:_MAX_LIST_ITEMS] if values else default
    return default


def _bounded_summary(summary: str) -> str:
    return summary[:_MAX_SUMMARY_CHARS]


def build_obs300_3a_ecosystem_visualization_payloads(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    topology_visibility_score = _clamp(
        (_f(payload, "ecosystem_topology_signal", 50.0) * 0.35)
        + (_f(payload, "propagation_adjacency_clarity", 50.0) * 0.35)
        + (_f(payload, "operator_surface_coverage", 50.0) * 0.30)
    )
    pressure_bridge_intensity_score = _clamp(
        (_f(payload, "pressure_bridge_strength", 50.0) * 0.40)
        + (_f(payload, "instability_transmission_intensity", 50.0) * 0.35)
        + (_f(payload, "bridge_concentration", 50.0) * 0.25)
    )
    fragmentation_heat_score = _clamp(
        (_f(payload, "fragmentation_signal", 50.0) * 0.30)
        + (_f(payload, "topology_decomposition", 50.0) * 0.35)
        + (_f(payload, "cohesion_weakening", 50.0) * 0.35)
    )
    contradiction_concentration_score = _clamp(
        (_f(payload, "contradiction_pressure", 50.0) * 0.55)
        + (_f(payload, "contradiction_recurrence", 50.0) * 0.45)
    )
    persistence_continuity_score = _clamp(
        (_f(payload, "temporal_persistence", 50.0) * 0.35)
        + (_f(payload, "propagation_continuity", 50.0) * 0.35)
        + ((100.0 - _f(payload, "propagation_decay", 50.0)) * 0.30)
    )

    ecosystem_cohesion_score = _clamp(
        100.0 - ((fragmentation_heat_score * 0.45) + (contradiction_concentration_score * 0.30) + ((100 - persistence_continuity_score) * 0.25))
    )

    strongest_pressure_bridges = _bounded_list(
        payload,
        "strongest_pressure_bridges",
        [
            "ai_infrastructure->utilities_capacity_pressure",
            "credit_tightening->regional_banks->consumer_demand_fragility",
            "energy_shock->industrials_margin_pressure",
        ],
    )
    strongest_instability_pathways = _bounded_list(
        payload,
        "strongest_instability_pathways",
        [
            "duration_stress->funding_costs->consumption_contraction",
            "capex_saturation->semis_inventory_pressure",
        ],
    )
    contradiction_pressure_zones = _bounded_list(
        payload,
        "contradiction_pressure_zones",
        ["ai_capex_chain", "regional_credit_cycle", "energy_sensitive_industrials"],
    )

    topology_visualization_payloads = {
        "ecosystem_topology_summary": {
            "topology_visibility_score": topology_visibility_score,
            "topology_visibility_band": _band(topology_visibility_score),
        },
        "pressure_bridge_map": {
            "pressure_bridge_intensity_score": pressure_bridge_intensity_score,
            "bridge_concentration_band": _band(_clamp(_f(payload, "bridge_concentration", 50.0))),
            "strongest_pressure_bridges": strongest_pressure_bridges,
        },
        "propagation_pathway_view": {
            "strongest_instability_pathways": strongest_instability_pathways,
            "propagation_continuity_band": _band(_clamp(_f(payload, "propagation_continuity", 50.0))),
        },
        "fragmentation_topology_summary": {
            "fragmentation_heat_score": fragmentation_heat_score,
            "fragmentation_band": _band(fragmentation_heat_score),
        },
        "contradiction_concentration_view": {
            "contradiction_concentration_score": contradiction_concentration_score,
            "contradiction_pressure_zones": contradiction_pressure_zones,
        },
        "ecosystem_cohesion_summary": {
            "ecosystem_cohesion_score": ecosystem_cohesion_score,
            "cohesion_band": _band(ecosystem_cohesion_score),
        },
    }

    temporal_persistence_visualization = {
        "persistence_topology_summary": _bounded_summary(
            f"persistence_continuity_score={persistence_continuity_score};topology_visibility_band={_band(topology_visibility_score)}"
        ),
        "contradiction_recurrence_panel": _bounded_summary(
            f"contradiction_recurrence_band={_band(_clamp(_f(payload, 'contradiction_recurrence', 50.0)))};"
            f"concentration_band={_band(contradiction_concentration_score)}"
        ),
        "escalation_stabilization_summary": _bounded_summary(
            f"instability_band={_band(pressure_bridge_intensity_score)};cohesion_band={_band(ecosystem_cohesion_score)}"
        ),
        "propagation_continuity_summary": _bounded_summary(
            f"continuity_band={_band(_clamp(_f(payload, 'propagation_continuity', 50.0)))};"
            f"decay_band={_band(_clamp(_f(payload, 'propagation_decay', 50.0)))}"
        ),
        "propagation_decay_dashboard": {
            "propagation_decay_score": _clamp(_f(payload, "propagation_decay", 50.0)),
            "decay_band": _band(_clamp(_f(payload, "propagation_decay", 50.0))),
        },
    }

    operator_intelligence_panels = {
        "ecosystem_stress_overview": _bounded_summary(
            f"pressure_bridge_intensity_score={pressure_bridge_intensity_score};fragmentation_heat_score={fragmentation_heat_score};"
            f"cohesion_score={ecosystem_cohesion_score}"
        ),
        "highest_contradiction_pressure_zones": contradiction_pressure_zones,
        "strongest_instability_pathways": strongest_instability_pathways,
        "propagation_exhaustion_summary": _bounded_summary(
            f"propagation_decay_band={_band(_clamp(_f(payload, 'propagation_decay', 50.0)))};"
            f"persistence_continuity_band={_band(persistence_continuity_score)}"
        ),
        "ecosystem_recovery_observations": _bounded_summary(
            f"cohesion_band={_band(ecosystem_cohesion_score)};"
            f"stabilization_signal_band={_band(_clamp(100 - pressure_bridge_intensity_score))}"
        ),
        "decomposition_risk_summary": _bounded_summary(
            f"topology_decomposition_band={_band(_clamp(_f(payload, 'topology_decomposition', 50.0)))};"
            f"fragmentation_band={_band(fragmentation_heat_score)}"
        ),
    }

    governance_certification = {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    return {
        "module": "OBS300-3A",
        "status": "deterministic_ecosystem_intelligence_visualization_operator_topology_complete",
        "visualization_payloads": topology_visualization_payloads,
        "pressure_bridge_visualization": {
            "strongest_pressure_bridge_payloads": strongest_pressure_bridges,
            "instability_transmission_visualization_summary": _bounded_summary(
                f"intensity_band={_band(pressure_bridge_intensity_score)};"
                f"continuity_band={_band(_clamp(_f(payload, 'propagation_continuity', 50.0)))}"
            ),
            "bridge_concentration_map": _band(_clamp(_f(payload, "bridge_concentration", 50.0))),
            "bridge_persistence_summary": _bounded_summary(
                f"bridge_persistence_band={_band(_clamp(_f(payload, 'temporal_persistence', 50.0)))}"
            ),
        },
        "fragmentation_cohesion_visualization": {
            "fragmentation_heatmap": _band(fragmentation_heat_score),
            "cohesion_weakening_summary": _band(_clamp(_f(payload, "cohesion_weakening", 50.0))),
            "topology_decomposition_visualization_payload": _band(_clamp(_f(payload, "topology_decomposition", 50.0))),
            "fragmentation_persistence_summary": _bounded_summary(
                f"fragmentation_band={_band(fragmentation_heat_score)};persistence_band={_band(persistence_continuity_score)}"
            ),
        },
        "temporal_persistence_visualization": temporal_persistence_visualization,
        "operator_intelligence_panels": operator_intelligence_panels,
        "topology_dashboard_architecture_summary": {
            "payload_only_contracts": True,
            "frontend_framework_required": False,
            "graph_engine_required": False,
            "rendering_engine_implemented": False,
            "orchestration_complexity": "lightweight",
            "power_bi_dashboard_friendly": True,
        },
        "visualization_payload_summary": {
            "deterministic": True,
            "bounded": True,
            "lightweight": True,
            "surface_count": 6,
        },
        "operational_report": {
            "implementation": "deterministic_operator_facing_ecosystem_intelligence_payloads",
            "autonomous_logic": False,
            "sql_writes_enabled": False,
            "prediction_or_trading_execution": False,
        },
        "governance_certification": governance_certification,
    }
