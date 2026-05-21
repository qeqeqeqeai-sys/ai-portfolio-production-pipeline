from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, weighted_bounded_score
from .federation_dependency_resilience import federation_dependency_resilience
from .federation_failure_containment import federation_failure_containment
from .federation_recoverability import federation_recoverability_assessment
from .federation_recovery import federation_recovery_readiness
from .federation_recovery_paths import federation_recovery_paths
from .federation_resilience_explanations import fixed_federation_resilience_explanations
from .federation_resilience_signatures import federation_resilience_checksum


def _record_get(record: Any, key: str, default: Any = 0.0) -> Any:
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


def _score(record: Any, key: str) -> float:
    return round(clamp_score(float(_record_get(record, key, 0.0))), 6)


def _stable_resilience_id(record: Any) -> str:
    for key in (
        "federation_resilience_id",
        "federation_health_id",
        "federation_observability_id",
        "federation_id",
        "system_id",
        "id",
    ):
        value = _record_get(record, key, None)
        if value is not None:
            return str(value)
    return ""


def build_federation_resilience_sort_key(record: Any) -> tuple[float, float, float, float, float, float, float, float, str]:
    rid = _stable_resilience_id(record)
    return (
        -_score(record, "federation_resilience_score"),
        -_score(record, "federation_recovery_readiness_score"),
        -_score(record, "federation_recoverability_score"),
        -_score(record, "federation_dependency_resilience_score"),
        -_score(record, "federation_failure_containment_score"),
        -_score(record, "federation_recovery_path_score"),
        _score(record, "federation_irreversibility_risk_score"),
        _score(record, "federation_recovery_gap_score"),
        rid,
    )


def run_tier5g_federation_resilience(*, federation_id: str, governance: dict[str, Any], persistence: dict[str, Any], temporal: dict[str, Any], observability: dict[str, Any], health: dict[str, Any], dependencies: list[dict[str, Any]], contagion_paths: list[dict[str, Any]], replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    recovery = federation_recovery_readiness(governance, persistence, observability)
    recoverability = federation_recoverability_assessment(recovery, temporal, health)
    dependency = federation_dependency_resilience(dependencies, governance)
    containment = federation_failure_containment(contagion_paths, governance, observability)
    paths = federation_recovery_paths(contagion_paths, replay_snapshots)
    resilience_score = weighted_bounded_score([
        (recovery["federation_recovery_readiness_score"], 0.24),
        (recoverability["federation_recoverability_score"], 0.24),
        (dependency["federation_dependency_resilience_score"], 0.16),
        (containment["federation_failure_containment_score"], 0.16),
        (paths["federation_recovery_path_score"], 0.10),
        (1.0 - recovery["federation_irreversibility_risk_score"], 0.10),
    ])
    factors = sorted([
        ("federation_recovery_readiness_score", recovery["federation_recovery_readiness_score"]),
        ("federation_recoverability_score", recoverability["federation_recoverability_score"]),
        ("federation_dependency_resilience_score", dependency["federation_dependency_resilience_score"]),
        ("federation_failure_containment_score", containment["federation_failure_containment_score"]),
        ("federation_recovery_path_score", paths["federation_recovery_path_score"]),
        ("federation_irreversibility_risk_score", 1.0 - recovery["federation_irreversibility_risk_score"]),
    ], key=lambda x: (-x[1], x[0]))
    result = {
        "federation_resilience_id": federation_resilience_checksum({"federation_id": federation_id}, "frid"),
        "federation_resilience_score": resilience_score,
        "bounded_federation_resilience_score": clamp_score(resilience_score),
        **recovery,
        **recoverability,
        **dependency,
        **containment,
        **paths,
        "dominant_resilience_factor": factors[0][0] if factors else "none",
    }
    if result["federation_irreversibility_risk_score"] >= 0.75:
        result["federation_resilience_classification"] = "irreversible_degradation_risk"
    elif result["federation_dependency_resilience_score"] < 0.35:
        result["federation_resilience_classification"] = "dependency_fragile"
    elif result["federation_failure_containment_score"] < 0.40:
        result["federation_resilience_classification"] = "containment_limited"
    elif result["federation_recovery_path_score"] < 0.40:
        result["federation_resilience_classification"] = "recovery_path_weak"
    elif result["federation_recovery_readiness_score"] < 0.40:
        result["federation_resilience_classification"] = "governance_recovery_constrained"
    elif result["federation_resilience_score"] >= 0.70:
        result["federation_resilience_classification"] = "resilient"
    elif result["federation_recoverability_score"] >= 0.55:
        result["federation_resilience_classification"] = "recoverable"
    else:
        result["federation_resilience_classification"] = "structurally_brittle"
    result["federation_resilience_signature_checksum"] = federation_resilience_checksum({"id": result["federation_resilience_id"], "score": result["federation_resilience_score"]}, "tier5g_signature")
    result["federation_resilience_checksum"] = federation_resilience_checksum({k: v for k, v in sorted(result.items()) if k != "federation_resilience_checksum"}, "tier5g_resilience")
    result.update(fixed_federation_resilience_explanations(result))
    return result
