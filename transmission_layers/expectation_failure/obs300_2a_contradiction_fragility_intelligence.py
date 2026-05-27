"""OBS300-2A deterministic contradiction pressure & narrative fragility intelligence."""

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
    v = payload.get(key)
    if isinstance(v, bool) or v is None:
        return default
    if isinstance(v, (int, float)):
        return max(0.0, min(100.0, float(v)))
    return default


def build_obs300_2a_weights() -> Dict[str, Dict[str, float]]:
    return {
        "contradiction_pressure": {
            "thematic_saturation": 0.20,
            "propagation_congestion": 0.20,
            "regime_transition_overlap": 0.15,
            "contradiction_exposure_density": 0.15,
            "bridge_role_concentration": 0.15,
            "cross_sector_instability_exposure": 0.15,
        },
        "narrative_fragility": {
            "thematic_overextension_score": 0.25,
            "contradiction_concentration_score": 0.25,
            "propagation_instability_score": 0.25,
            "ecosystem_instability_score": 0.25,
        },
        "interaction": {
            "saturation_fragility": 0.5,
            "congestion_fragility": 0.5,
        },
    }


def score_obs300_2a_contradiction_fragility(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)
    weights = build_obs300_2a_weights()

    cp_sub = {
        "thematic_saturation": _f(payload, "thematic_saturation"),
        "propagation_congestion": _f(payload, "propagation_congestion"),
        "regime_transition_overlap": _f(payload, "regime_transition_overlap"),
        "contradiction_exposure_density": _f(payload, "contradiction_exposure_density"),
        "bridge_role_concentration": _f(payload, "bridge_role_concentration"),
        "cross_sector_instability_exposure": _f(payload, "cross_sector_instability_exposure"),
    }
    contradiction_pressure_score = _clamp(sum(cp_sub[k] * w for k, w in weights["contradiction_pressure"].items()))

    thematic_overextension_score = _clamp((cp_sub["thematic_saturation"] * 0.6) + (cp_sub["cross_sector_instability_exposure"] * 0.4))
    contradiction_concentration_score = _clamp((cp_sub["contradiction_exposure_density"] * 0.65) + (cp_sub["bridge_role_concentration"] * 0.35))
    propagation_instability_score = _clamp((cp_sub["propagation_congestion"] * 0.7) + (cp_sub["regime_transition_overlap"] * 0.3))
    ecosystem_instability_score = _clamp((cp_sub["cross_sector_instability_exposure"] * 0.5) + (cp_sub["propagation_congestion"] * 0.3) + (cp_sub["bridge_role_concentration"] * 0.2))

    frag_sub = {
        "thematic_overextension_score": thematic_overextension_score,
        "contradiction_concentration_score": contradiction_concentration_score,
        "propagation_instability_score": propagation_instability_score,
        "ecosystem_instability_score": ecosystem_instability_score,
    }
    narrative_fragility_score = _clamp(sum(frag_sub[k] * w for k, w in weights["narrative_fragility"].items()))

    saturation_fragility_interaction_score = _clamp((cp_sub["thematic_saturation"] + narrative_fragility_score) / 2)
    congestion_fragility_interaction_score = _clamp((cp_sub["propagation_congestion"] + narrative_fragility_score) / 2)

    contradiction_cluster_summary = {
        "cluster_id": payload.get("cluster_id", "UNKNOWN_CLUSTER"),
        "domain": payload.get("domain", "unknown"),
        "contradiction_examples": list(payload.get("contradiction_examples") or [
            "ai_optimism_vs_infrastructure_bottlenecks",
            "growth_optimism_vs_liquidity_tightening",
            "consumer_resilience_vs_credit_deterioration",
            "capex_expansion_vs_margin_pressure",
        ]),
        "contradiction_bridge_entities": list(payload.get("contradiction_bridge_entities") or []),
        "contradiction_concentration_map": {
            "core": _band(contradiction_concentration_score),
            "diffusion_candidates": list(payload.get("contradiction_diffusion_candidates") or []),
        },
        "structural_instability_summary": f"{_band(ecosystem_instability_score)} ecosystem instability with {_band(propagation_instability_score)} propagation instability",
    }

    operator_summary = {
        "highest_contradiction_pressure_domains": list(payload.get("highest_contradiction_pressure_domains") or [payload.get("domain", "unknown")]),
        "most_fragile_narrative_clusters": list(payload.get("most_fragile_narrative_clusters") or [payload.get("cluster_id", "UNKNOWN_CLUSTER")]),
        "ecosystem_instability_observations": [f"ecosystem_instability_score={ecosystem_instability_score}", f"propagation_instability_score={propagation_instability_score}"],
        "contradiction_bridge_summaries": contradiction_cluster_summary["contradiction_bridge_entities"],
        "saturation_risk_warnings": [f"saturation_fragility_interaction_score={saturation_fragility_interaction_score}"],
        "topology_instability_summaries": [contradiction_cluster_summary["structural_instability_summary"]],
        "dominance_risk_summary": f"dominance_risk={_band(max(saturation_fragility_interaction_score, congestion_fragility_interaction_score))}",
        "monoculture_instability_indicator": _band(_clamp((saturation_fragility_interaction_score * 0.6) + (contradiction_concentration_score * 0.4))),
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
        "module": "OBS300-2A",
        "status": "deterministic_observational_intelligence_complete",
        "contradiction_pressure_score": contradiction_pressure_score,
        "contradiction_pressure_band": _band(contradiction_pressure_score),
        "contradiction_pressure_subcomponents": cp_sub,
        "narrative_fragility_score": narrative_fragility_score,
        "narrative_fragility_band": _band(narrative_fragility_score),
        "narrative_fragility_subcomponents": frag_sub,
        "ecosystem_instability_score": ecosystem_instability_score,
        "thematic_overextension_score": thematic_overextension_score,
        "contradiction_concentration_score": contradiction_concentration_score,
        "propagation_instability_score": propagation_instability_score,
        "saturation_fragility_interaction_score": saturation_fragility_interaction_score,
        "congestion_fragility_interaction_score": congestion_fragility_interaction_score,
        "contradiction_cluster_summary": contradiction_cluster_summary,
        "operator_intelligence_summary": operator_summary,
        "governance_certification": governance_certification,
        "operational_report": {
            "implementation": "metadata_driven_deterministic_scoring",
            "deterministic": True,
            "bounded": True,
            "lightweight": True,
            "autonomous_logic": False,
        },
    }
