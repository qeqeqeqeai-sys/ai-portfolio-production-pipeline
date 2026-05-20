from __future__ import annotations

from typing import Any, Dict, List

from .regime_metrics import clamp_score
from .structural_regimes import classify_structural_regime


def compute_regime_continuity(snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    if len(snapshots) <= 1: return {"continuity_score": 1.0, "transition_frequency_score": 0.0, "regime_volatility_score": 0.0}
    ordered = sorted(snapshots, key=lambda s: str(s.get("run_date", "")))
    names = [classify_structural_regime(s)["regime_name"] for s in ordered]
    transitions = sum(1 for i in range(1, len(names)) if names[i] != names[i-1])
    freq = clamp_score(transitions / (len(names)-1))
    return {"continuity_score": clamp_score(1.0 - freq), "transition_frequency_score": freq, "regime_volatility_score": freq}


def compute_regime_stability(snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    c = compute_regime_continuity(snapshots)
    return {"persistence_score": c["continuity_score"], **c}


def compute_regime_persistence(snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    s = compute_regime_stability(snapshots)
    names = [classify_structural_regime(x)["regime_name"] for x in sorted(snapshots, key=lambda y: str(y.get("run_date", "")))]
    n = max(1, len(names))
    s.update({
        "fragmentation_persistence": clamp_score(names.count("fragmented") / n),
        "cascade_persistence": clamp_score(names.count("cascading_failure") / n),
        "suppression_persistence": clamp_score(names.count("suppressed") / n),
    })
    return s
