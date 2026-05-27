"""OBS300-2C deterministic structural pressure bridges & fragmentation observation."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List


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


def _list(payload: Dict[str, object], key: str, default: List[str]) -> List[str]:
    raw = payload.get(key)
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return default


def score_obs300_2c_structural_pressure_bridges(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    pressure_bridge_score = _clamp(
        (_f(payload, "bridge_connectivity_pressure", 50.0) * 0.25)
        + (_f(payload, "instability_transmission_intensity", 50.0) * 0.25)
        + (_f(payload, "contradiction_bridge_escalation", 50.0) * 0.25)
        + (_f(payload, "bridge_stress_concentration", 50.0) * 0.25)
    )
    bridge_propagation_continuity_score = _clamp(
        (_f(payload, "bridge_pathway_reuse", 50.0) * 0.55)
        + (_f(payload, "adjacency_continuity", 50.0) * 0.45)
    )

    fragmentation_score = _clamp(
        (_f(payload, "cohesion_weakening_signal", 50.0) * 0.25)
        + (_f(payload, "propagation_fragmentation", 50.0) * 0.25)
        + (_f(payload, "narrative_divergence", 50.0) * 0.25)
        + (_f(payload, "topology_decomposition", 50.0) * 0.25)
    )
    ecosystem_cohesion_score = _clamp(
        100.0 - ((fragmentation_score * 0.65) + ((100 - bridge_propagation_continuity_score) * 0.35))
    )

    propagation_decay_score = _clamp(
        (_f(payload, "propagation_exhaustion", 50.0) * 0.30)
        + (_f(payload, "diffusion_decay", 50.0) * 0.20)
        + (_f(payload, "contradiction_dissipation", 50.0) * 0.20)
        + (_f(payload, "saturation_cooling", 50.0) * 0.15)
        + ((100 - bridge_propagation_continuity_score) * 0.15)
    )

    strongest_pressure_bridges = _list(
        payload,
        "strongest_pressure_bridges",
        [
            "ai_infrastructure->utilities_stress",
            "liquidity_tightening->banks->consumer_fragility",
            "capex_saturation->semis->margin_compression",
            "energy_shocks->industrial_cost_pressure",
        ],
    )
    highest_instability_transmission_pathways = _list(
        payload,
        "highest_instability_transmission_pathways",
        [
            "ai_compute_power_demand->grid_capacity_pressure",
            "duration_sensitivity->bank_funding_costs->consumer_credit_strain",
        ],
    )
    highest_fragmentation_domains = _list(
        payload,
        "highest_fragmentation_domains",
        ["semis_capex_chain", "regional_banks_credit", "industrial_energy_input_chain"],
    )

    propagation_exhaustion_summary = (
        f"propagation_decay_score={propagation_decay_score};"
        f"diffusion_decay_band={_band(_clamp(_f(payload, 'diffusion_decay', 50.0)))};"
        f"adjacency_continuity_band={_band(bridge_propagation_continuity_score)}"
    )
    decomposition_risk_summary = (
        f"fragmentation_score={fragmentation_score};"
        f"ecosystem_cohesion_score={ecosystem_cohesion_score};"
        f"topology_decomposition_band={_band(_clamp(_f(payload, 'topology_decomposition', 50.0)))}"
    )

    governance_certification = {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    operator_facing_summary = {
        "pressure_bridge_score": pressure_bridge_score,
        "fragmentation_score": fragmentation_score,
        "ecosystem_cohesion_score": ecosystem_cohesion_score,
        "propagation_decay_score": propagation_decay_score,
        "strongest_pressure_bridges": strongest_pressure_bridges,
        "highest_fragmentation_domains": highest_fragmentation_domains,
        "propagation_exhaustion_summary": propagation_exhaustion_summary,
        "decomposition_risk_summary": decomposition_risk_summary,
        "governance_certification": governance_certification,
    }

    structural_ecosystem_intelligence = {
        "strongest_pressure_bridges": strongest_pressure_bridges,
        "highest_instability_transmission_pathways": highest_instability_transmission_pathways,
        "fragmentation_hotspots": highest_fragmentation_domains,
        "propagation_decay_observations": [
            f"propagation_decay_score={propagation_decay_score}",
            f"contradiction_dissipation_band={_band(_clamp(_f(payload, 'contradiction_dissipation', 50.0)))}",
        ],
        "ecosystem_cohesion_summaries": [
            f"ecosystem_cohesion_score={ecosystem_cohesion_score}",
            f"fragmentation_band={_band(fragmentation_score)}",
        ],
        "decomposition_risk_observations": [decomposition_risk_summary],
    }

    return {
        "module": "OBS300-2C",
        "status": "deterministic_structural_pressure_bridges_fragmentation_observation_complete",
        "pressure_bridge_score": pressure_bridge_score,
        "bridge_propagation_continuity_score": bridge_propagation_continuity_score,
        "fragmentation_score": fragmentation_score,
        "ecosystem_cohesion_score": ecosystem_cohesion_score,
        "propagation_decay_score": propagation_decay_score,
        "strongest_pressure_bridges": strongest_pressure_bridges,
        "highest_instability_transmission_pathways": highest_instability_transmission_pathways,
        "highest_fragmentation_domains": highest_fragmentation_domains,
        "propagation_exhaustion_summary": propagation_exhaustion_summary,
        "decomposition_risk_summary": decomposition_risk_summary,
        "structural_ecosystem_intelligence": structural_ecosystem_intelligence,
        "operator_facing_summary": operator_facing_summary,
        "operational_report": {
            "implementation": "metadata_driven_deterministic_structural_fragmentation_observation",
            "deterministic": True,
            "bounded": True,
            "lightweight": True,
            "autonomous_logic": False,
        },
        "governance_certification": governance_certification,
    }
