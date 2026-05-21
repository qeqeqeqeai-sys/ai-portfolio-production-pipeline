from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, weighted_bounded_score
from .federation_degradation import federation_degradation_score
from .federation_diagnostic_readiness import federation_diagnostic_readiness
from .federation_health_alignment import federation_health_alignment
from .federation_health_classification import federation_health_classification
from .federation_health_explanations import fixed_federation_health_explanations
from .federation_health_signatures import federation_health_checksum


def _read_field(record: Any, field: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        return record.get(field, default)
    return getattr(record, field, default)


def _clamped_rounded_score(record: Any, field: str) -> float:
    raw_value = _read_field(record, field, 0.0)
    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        numeric_value = 0.0
    return round(clamp_score(numeric_value), 6)


def _stable_federation_sort_id(record: Any) -> str:
    for field in ("federation_health_id", "federation_observability_id", "federation_id", "system_id", "id"):
        value = _read_field(record, field, None)
        if value is not None and str(value) != "":
            return str(value)
    return ""


def build_federation_health_sort_key(record: Any) -> tuple[float, float, float, float, float, float, float, float, str]:
    return (
        -_clamped_rounded_score(record, "federation_structural_health_score"),
        -_clamped_rounded_score(record, "diagnostic_readiness_score"),
        _clamped_rounded_score(record, "health_degradation_score"),
        -_clamped_rounded_score(record, "observability_alignment_score"),
        -_clamped_rounded_score(record, "governance_alignment_score"),
        -_clamped_rounded_score(record, "replay_health_score"),
        -_clamped_rounded_score(record, "continuity_health_score"),
        -_clamped_rounded_score(record, "propagation_health_score"),
        _stable_federation_sort_id(record),
    )


def run_tier5f_federation_structural_health(*, federation_id: str, governance: dict[str, Any], persistence: dict[str, Any], temporal: dict[str, Any], observability: dict[str, Any]) -> dict[str, Any]:
    readiness = federation_diagnostic_readiness(governance, observability, persistence)
    alignment = federation_health_alignment(readiness)
    degradation = federation_degradation_score(readiness)
    structural_score = weighted_bounded_score([
        (readiness["diagnostic_readiness_score"], 0.40),
        (alignment["federation_health_alignment_score"], 0.20),
        (1.0 - degradation["health_degradation_score"], 0.20),
        (clamp_score(1.0 - temporal.get("federation_evolution_score", 0.0)), 0.20),
    ])
    factors = sorted([
        ("diagnostic_readiness_score", readiness["diagnostic_readiness_score"]),
        ("observability_alignment_score", readiness["observability_alignment_score"]),
        ("governance_alignment_score", readiness["governance_alignment_score"]),
        ("replay_health_score", readiness["replay_health_score"]),
        ("continuity_health_score", readiness["continuity_health_score"]),
        ("propagation_health_score", readiness["propagation_health_score"]),
        ("health_degradation_score", 1.0 - degradation["health_degradation_score"]),
    ], key=lambda x: (-x[1], x[0]))
    result = {
        "federation_health_id": federation_health_checksum({"federation_id": federation_id}, "fhid"),
        "federation_structural_health_score": structural_score,
        "bounded_federation_structural_health_score": clamp_score(structural_score),
        **readiness,
        **alignment,
        **degradation,
        "dominant_health_factor": factors[0][0] if factors else "none",
    }
    result["federation_health_classification"] = federation_health_classification(result["federation_structural_health_score"], result["health_degradation_score"], readiness)
    result["federation_structural_health_checksum"] = federation_health_checksum(result, "tier5f_structural")
    result["federation_diagnostic_readiness_checksum"] = federation_health_checksum(readiness, "tier5f_diagnostic")
    result["federation_health_alignment_checksum"] = federation_health_checksum(alignment, "tier5f_alignment")
    result["federation_degradation_checksum"] = federation_health_checksum(degradation, "tier5f_degradation")
    result["federation_health_signature_checksum"] = federation_health_checksum({"id": result["federation_health_id"], "score": structural_score}, "tier5f_signature")
    result["federation_health_checksum"] = federation_health_checksum({k: v for k, v in sorted(result.items()) if k != "federation_health_checksum"}, "tier5f_health")
    result.update(fixed_federation_health_explanations(result))
    return result
