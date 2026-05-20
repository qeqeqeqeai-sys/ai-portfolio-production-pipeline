from __future__ import annotations

from typing import Any, Dict

from .scenario_semantics import clamp_score, round_score


KEYS = [
    "propagated_stress_score",
    "chokepoint_overload_score",
    "resilience_degradation_score",
    "corridor_deterioration_score",
    "suppression_cascade_score",
    "contagion_escalation_score",
]


def _g(snapshot: Dict[str, Any], key: str) -> float:
    return clamp_score(snapshot.get(key, 0.0))


def compute_scenario_delta_metrics(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, float]:
    stress = round_score(_g(candidate, "propagated_stress_score") - _g(baseline, "propagated_stress_score"))
    overload = round_score(_g(candidate, "chokepoint_overload_score") - _g(baseline, "chokepoint_overload_score"))
    resilience = round_score(_g(candidate, "resilience_degradation_score") - _g(baseline, "resilience_degradation_score"))
    fragment = round_score(_g(candidate, "corridor_deterioration_score") - _g(baseline, "corridor_deterioration_score"))
    suppression = round_score(_g(candidate, "suppression_cascade_score") - _g(baseline, "suppression_cascade_score"))
    cascade = round_score(_g(candidate, "contagion_escalation_score") - _g(baseline, "contagion_escalation_score"))
    return {
        "stress_delta_signed": max(-1.0, min(1.0, stress)),
        "overload_delta_signed": max(-1.0, min(1.0, overload)),
        "resilience_delta_signed": max(-1.0, min(1.0, resilience)),
        "fragmentation_delta_signed": max(-1.0, min(1.0, fragment)),
        "corridor_deterioration_delta_signed": max(-1.0, min(1.0, fragment)),
        "suppression_delta_signed": max(-1.0, min(1.0, suppression)),
        "cascade_delta_signed": max(-1.0, min(1.0, cascade)),
    }


def compute_scenario_response_metrics(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, float]:
    d = compute_scenario_delta_metrics(baseline, candidate)
    mag = {k.replace("_signed", ""): clamp_score(abs(v)) for k, v in d.items()}
    regime_shift = clamp_score(0.5 * mag["overload_delta"] + 0.5 * mag["fragmentation_delta"])
    sensitivity = clamp_score((mag["stress_delta"] + mag["overload_delta"] + mag["fragmentation_delta"]) / 3.0)
    impact = clamp_score(sum(mag.values()) / len(mag))
    coherence = clamp_score(1.0 - max(mag.values() or [0.0]))
    return {**mag, "regime_shift_intensity": regime_shift, "sensitivity_score": sensitivity, "scenario_impact_score": impact, "response_coherence_score": coherence}


def summarize_scenario_response(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    m = compute_scenario_response_metrics(baseline, candidate)
    dom = sorted([(k, v) for k, v in m.items() if k.endswith("_delta")], key=lambda kv: (-kv[1], kv[0]))[:3]
    return {"scenario_impact_score": m["scenario_impact_score"], "regime_shift_intensity": m["regime_shift_intensity"], "dominant_response_factors": [k for k, _ in dom]}
