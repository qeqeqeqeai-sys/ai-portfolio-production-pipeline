"""OBS300-2B deterministic temporal persistence & fragility persistence observation."""

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


def _classify(score: int) -> str:
    if score < 25:
        return "transient"
    if score < 50:
        return "recurring"
    if score < 75:
        return "persistent"
    return "entrenched"


def _f(payload: Dict[str, object], key: str, default: float = 50.0) -> float:
    v = payload.get(key)
    if isinstance(v, bool) or v is None:
        return default
    if isinstance(v, (int, float)):
        return max(0.0, min(100.0, float(v)))
    return default


def _list(payload: Dict[str, object], key: str, default: List[str]) -> List[str]:
    raw = payload.get(key)
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return default


def score_obs300_2b_temporal_persistence(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    temporal_window_count = int(max(1, _f(payload, "temporal_window_count", 6)))

    propagation_persistence_score = _clamp((_f(payload, "propagation_continuity", 50.0) * 0.7) + (_f(payload, "propagation_pathway_reuse", 50.0) * 0.3))
    contradiction_persistence_score = _clamp((_f(payload, "contradiction_pressure_score", 50.0) * 0.6) + (_f(payload, "contradiction_carryover_score", 50.0) * 0.4))
    fragility_persistence_score = _clamp((_f(payload, "narrative_fragility_score", 50.0) * 0.6) + (_f(payload, "fragility_carryover_score", 50.0) * 0.4))
    congestion_persistence_score = _clamp((_f(payload, "propagation_congestion", 50.0) * 0.65) + (_f(payload, "congestion_carryover_score", 50.0) * 0.35))
    instability_persistence_score = _clamp((contradiction_persistence_score * 0.35) + (fragility_persistence_score * 0.35) + (congestion_persistence_score * 0.30))

    propagation_acceleration_score = _clamp(_f(payload, "propagation_acceleration_delta", 0.0) + 50.0)
    contradiction_escalation_score = _clamp(_f(payload, "contradiction_escalation_delta", 0.0) + 50.0)
    instability_escalation_score = _clamp((propagation_acceleration_score * 0.25) + (contradiction_escalation_score * 0.35) + (instability_persistence_score * 0.40))
    narrative_cooling_score = _clamp((_f(payload, "narrative_cooling_signal", 50.0) * 0.7) + ((100 - fragility_persistence_score) * 0.3))
    stabilization_observation_score = _clamp((narrative_cooling_score * 0.45) + ((100 - instability_escalation_score) * 0.55))
    entropy_recovery_score = _clamp((_f(payload, "entropy_recovery_signal", 50.0) * 0.6) + (stabilization_observation_score * 0.4))

    contradiction_recurrence_score = _clamp((contradiction_persistence_score * 0.65) + (_f(payload, "contradiction_recurrence_density", 50.0) * 0.35))

    escalation_posture = "escalating" if instability_escalation_score >= 60 else "stabilizing" if stabilization_observation_score >= 60 else "mixed"
    ecosystem_posture = "fragmenting" if contradiction_recurrence_score >= 70 and instability_persistence_score >= 65 else "recovering" if entropy_recovery_score >= 60 else "transitional"

    persistence_classifications = {
        "propagation": _classify(propagation_persistence_score),
        "contradiction": _classify(contradiction_persistence_score),
        "fragility": _classify(fragility_persistence_score),
        "instability": _classify(instability_persistence_score),
        "recurrence": _classify(contradiction_recurrence_score),
    }

    most_persistent_contradiction_domains = _list(payload, "contradiction_domains", ["macro-liquidity-tension", "capex-vs-margin-compression"])
    most_persistent_fragility_clusters = _list(payload, "fragility_clusters", ["semiconductor-capacity-chain", "consumer-credit-sensitivity"])
    strongest_propagation_continuity_pathways = _list(payload, "propagation_continuity_pathways", ["ai_compute->power_infrastructure", "rates_sensitivity->duration_equities"])

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
        "module": "OBS300-2B",
        "status": "deterministic_temporal_persistence_observation_complete",
        "temporal_window_count": temporal_window_count,
        "propagation_persistence_score": propagation_persistence_score,
        "contradiction_persistence_score": contradiction_persistence_score,
        "fragility_persistence_score": fragility_persistence_score,
        "congestion_persistence_score": congestion_persistence_score,
        "instability_persistence_score": instability_persistence_score,
        "contradiction_recurrence_score": contradiction_recurrence_score,
        "propagation_acceleration_score": propagation_acceleration_score,
        "contradiction_escalation_score": contradiction_escalation_score,
        "instability_escalation_score": instability_escalation_score,
        "narrative_cooling_score": narrative_cooling_score,
        "stabilization_observation_score": stabilization_observation_score,
        "entropy_recovery_score": entropy_recovery_score,
        "persistence_classifications": persistence_classifications,
        "contradiction_persistence_clusters": {
            "most_persistent_contradiction_domains": most_persistent_contradiction_domains,
            "contradiction_cluster_band": _band(contradiction_persistence_score),
            "repeated_instability_pattern_observation": f"{_band(contradiction_recurrence_score)} recurrence with {ecosystem_posture} posture",
            "structural_recurrence_summary": f"{persistence_classifications['contradiction']} contradiction persistence across {temporal_window_count} windows",
        },
        "temporal_ecosystem_intelligence": {
            "most_persistent_contradiction_domains": most_persistent_contradiction_domains,
            "most_persistent_fragility_clusters": most_persistent_fragility_clusters,
            "strongest_propagation_continuity_pathways": strongest_propagation_continuity_pathways,
            "stabilization_recovery_observations": [
                f"stabilization_observation_score={stabilization_observation_score}",
                f"entropy_recovery_score={entropy_recovery_score}",
            ],
            "escalation_pressure_summary": f"{escalation_posture}:{_band(instability_escalation_score)}",
            "temporal_topology_summary": f"continuity={_band(propagation_persistence_score)} congestion={_band(congestion_persistence_score)}",
        },
        "operator_facing_summary": {
            "temporal_window_count": temporal_window_count,
            "propagation_persistence_score": propagation_persistence_score,
            "contradiction_persistence_score": contradiction_persistence_score,
            "fragility_persistence_score": fragility_persistence_score,
            "instability_persistence_score": instability_persistence_score,
            "contradiction_recurrence_score": contradiction_recurrence_score,
            "escalation_pressure_summary": f"instability_escalation_score={instability_escalation_score};posture={escalation_posture}",
            "stabilization_recovery_summary": f"stabilization_observation_score={stabilization_observation_score};entropy_recovery_score={entropy_recovery_score};ecosystem_posture={ecosystem_posture}",
            "most_persistent_contradiction_domains": most_persistent_contradiction_domains,
            "most_persistent_fragility_clusters": most_persistent_fragility_clusters,
            "governance_certification": governance_certification,
        },
        "operational_report": {
            "implementation": "metadata_driven_deterministic_temporal_observation",
            "deterministic": True,
            "bounded": True,
            "lightweight": True,
            "autonomous_logic": False,
        },
        "governance_certification": governance_certification,
    }
