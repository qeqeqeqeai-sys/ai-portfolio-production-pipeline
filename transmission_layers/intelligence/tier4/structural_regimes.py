from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List

from .regime_metrics import clamp_score, compute_regime_metrics

TIE_PRIORITY = ["cascading_failure", "overloaded", "fragmented", "suppressed", "stressed", "recovering", "transitional", "stable"]


def _stable(items: Iterable[str]) -> List[str]:
    return sorted({str(x) for x in items if str(x).strip()})


def _checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def classify_structural_regime(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    metrics = compute_regime_metrics(snapshot)
    regime_scores = {
        "cascading_failure": clamp_score(0.5 * metrics["cascade_regime_score"] + 0.5 * metrics["suppression_regime_score"]),
        "overloaded": metrics["overload_regime_score"],
        "fragmented": metrics["fragmentation_regime_score"],
        "suppressed": metrics["suppression_regime_score"],
        "stressed": metrics["structural_regime_score"],
        "recovering": metrics["recovery_regime_score"],
        "transitional": metrics["regime_transition_intensity_score"],
        "stable": metrics["regime_coherence_score"],
    }
    best = sorted(regime_scores.items(), key=lambda kv: (-kv[1], TIE_PRIORITY.index(kv[0])))[0]
    factors = _stable([k for k, v in metrics.items() if v >= 0.55])[:3]
    chokepoints = sorted(snapshot.get("overloaded_nodes", []))[:5]
    corridors = _stable(snapshot.get("failed_corridors", []) + snapshot.get("suppressed_corridors", []) + snapshot.get("degraded_corridors", []))[:5]
    confidence = "low" if best[1] < 0.45 else "medium" if best[1] < 0.75 else "high"
    expl = f"system classified as {best[0]} due to {', '.join(factors) if factors else 'bounded structural conditions'}."
    out = {
        "regime_name": best[0],
        "regime_score": clamp_score(best[1]),
        "confidence_band": confidence,
        "dominant_structural_factors": factors,
        "dominant_chokepoints": chokepoints,
        "dominant_corridors": corridors,
        "regime_explanation": expl[:220],
    }
    out["regime_checksum"] = _checksum(out)
    return out


def summarize_regime(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    c = classify_structural_regime(snapshot)
    return {"structural_regime": c["regime_name"], "regime_score": c["regime_score"], "regime_checksum": c["regime_checksum"], "dominant_regime_factor": (c["dominant_structural_factors"][0] if c["dominant_structural_factors"] else "none")}


def compare_regime_states(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    p = classify_structural_regime(previous)
    c = classify_structural_regime(current)
    return {
        "previous_regime": p["regime_name"],
        "current_regime": c["regime_name"],
        "regime_score_delta": clamp_score(abs(c["regime_score"] - p["regime_score"])),
        "regime_changed": p["regime_name"] != c["regime_name"],
    }
