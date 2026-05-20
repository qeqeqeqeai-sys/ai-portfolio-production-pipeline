from __future__ import annotations

import hashlib, json
from typing import Any, Dict, List

from .regime_metrics import clamp_score
from .structural_regimes import classify_structural_regime


def _checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def detect_regime_transition(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    p = classify_structural_regime(previous)
    c = classify_structural_regime(current)
    causes: List[str] = []
    if current.get("propagated_stress_score", 0.0) > previous.get("propagated_stress_score", 0.0): causes.append("propagated_stress_increase")
    if current.get("corridor_deterioration_score", 0.0) > previous.get("corridor_deterioration_score", 0.0): causes.append("corridor_deterioration")
    if current.get("resilience_degradation_score", 0.0) > previous.get("resilience_degradation_score", 0.0): causes.append("resilience_degradation")
    if current.get("suppression_cascade_score", 0.0) > previous.get("suppression_cascade_score", 0.0): causes.append("suppression_dominance")
    if current.get("chokepoint_overload_score", 0.0) < previous.get("chokepoint_overload_score", 0.0): causes.append("overload_reduction")
    out = {"previous_regime": p["regime_name"], "current_regime": c["regime_name"], "transition_detected": p["regime_name"] != c["regime_name"], "transition_causes": sorted(set(causes)), "dominant_influence_shift": sorted(set(c["dominant_structural_factors"]) - set(p["dominant_structural_factors"]))}
    out["transition_checksum"] = _checksum(out)
    return out


def replay_regime_transitions(snapshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered = sorted(snapshots, key=lambda s: str(s.get("run_date", "")))
    return [detect_regime_transition(ordered[i-1], ordered[i]) for i in range(1, len(ordered))]


def summarize_regime_transition(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    t = detect_regime_transition(previous, current)
    return {"transition_detected": t["transition_detected"], "summary": f"transition to {t['current_regime']} regime caused by {', '.join(t['transition_causes']) or 'no material shift'}."[:220], "transition_intensity": clamp_score(len(t["transition_causes"]) / 5.0)}
