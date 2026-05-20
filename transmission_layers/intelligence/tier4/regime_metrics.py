from __future__ import annotations

from typing import Any, Dict


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def round_score(value: float) -> float:
    return round(_to_float(value), 6)


def safe_ratio(numerator: float, denominator: float) -> float:
    if _to_float(denominator) <= 0.0:
        return 0.0
    return clamp_score(_to_float(numerator) / _to_float(denominator))


def _base_metrics(snapshot: Dict[str, Any]) -> Dict[str, float]:
    return {
        "propagated": clamp_score(snapshot.get("propagated_stress_score", 0.0)),
        "overload": clamp_score(snapshot.get("chokepoint_overload_score", 0.0)),
        "suppression": clamp_score(snapshot.get("suppression_cascade_score", 0.0)),
        "resilience_deg": clamp_score(snapshot.get("resilience_degradation_score", 0.0)),
        "corridor_det": clamp_score(snapshot.get("corridor_deterioration_score", 0.0)),
        "contagion": clamp_score(snapshot.get("contagion_escalation_score", 0.0)),
    }


def compute_regime_metrics(snapshot: Dict[str, Any]) -> Dict[str, float]:
    m = _base_metrics(snapshot)
    fragmentation = clamp_score(0.55 * m["corridor_det"] + 0.45 * m["resilience_deg"])
    cascade = clamp_score(0.45 * m["propagated"] + 0.30 * m["overload"] + 0.25 * m["suppression"])
    recovery = clamp_score((1.0 - m["overload"]) * 0.45 + (1.0 - m["corridor_det"]) * 0.35 + (1.0 - m["suppression"]) * 0.20)
    coherence = clamp_score((1.0 - m["corridor_det"]) * 0.5 + (1.0 - m["resilience_deg"]) * 0.5)
    structural = clamp_score(0.25 * m["propagated"] + 0.2 * m["overload"] + 0.2 * m["suppression"] + 0.2 * m["resilience_deg"] + 0.15 * m["corridor_det"])
    return {
        "structural_regime_score": structural,
        "fragmentation_regime_score": fragmentation,
        "overload_regime_score": m["overload"],
        "recovery_regime_score": recovery,
        "suppression_regime_score": m["suppression"],
        "cascade_regime_score": cascade,
        "regime_coherence_score": coherence,
        "regime_transition_intensity_score": clamp_score(abs(m["overload"] - m["suppression"]) * 0.4 + abs(m["propagated"] - m["corridor_det"]) * 0.6),
    }
