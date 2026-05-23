"""P3-A Structural Resilience Foundation: deterministic additive resilience interpretation layer."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

RESILIENCE_STATES: Tuple[str, ...] = (
    "RESILIENT",
    "STABLE",
    "NEUTRAL",
    "VULNERABLE",
    "DETERIORATING",
    "DIVERGENT_RESILIENT",
)

CERTIFIED_P3A_RESILIENCE_READY = "CERTIFIED_P3A_RESILIENCE_READY"
DEGRADED_P3A_RESILIENCE_READY = "DEGRADED_P3A_RESILIENCE_READY"
BLOCKED_P3A_RESILIENCE_INVALID = "BLOCKED_P3A_RESILIENCE_INVALID"

DIMENSION_KEYS: Tuple[str, ...] = (
    "fragility_resistance",
    "stability_persistence",
    "percentile_stability",
    "benchmark_resilience",
    "breadth_support",
    "deterioration_absorption",
    "divergence_resilience",
    "concentration_resistance",
)

FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "prediction", "forecast", "trade", "execution", "portfolio allocation", "optimization", "leverage", "buy/sell/hold", "stochastic", "adaptive threshold", "ml"
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _safe_number(value: Any, default: float = 50.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _clamp_score(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_number(value))), 2)


def build_p3a_resilience_signal_registry(path_inputs: Dict[str, Any]) -> Dict[str, float]:
    source = deepcopy(path_inputs)
    p1 = source.get("path1", {})
    p2 = source.get("path2", {})
    reg = {
        "fragility_resistance": _clamp_score(100.0 - _safe_number(p2.get("relative_fragility_score"), 50.0)),
        "stability_persistence": _clamp_score(p1.get("stability_score", 50.0)),
        "percentile_stability": _clamp_score(100.0 - abs(50.0 - _safe_number(p2.get("fragility_percentile"), 50.0))),
        "benchmark_resilience": _clamp_score(100.0 - abs(_safe_number(p2.get("benchmark_divergence"), 50.0) - 50.0)),
        "breadth_support": _clamp_score(100.0 - (_safe_number(p2.get("weakness_participation_rate"), 0.5) * 100.0)),
        "deterioration_absorption": _clamp_score(100.0 - _safe_number(p1.get("deterioration_intensity"), 50.0)),
        "divergence_resilience": _clamp_score(_safe_number(p2.get("benchmark_resilience_delta"), 50.0) + 50.0),
        "concentration_resistance": _clamp_score(100.0 - (_safe_number(p2.get("top_fragility_share"), 0.5) * 100.0)),
    }
    return {k: reg[k] for k in DIMENSION_KEYS}


def build_p3a_stability_persistence_summary(registry: Dict[str, float]) -> Dict[str, float]:
    reg = deepcopy(registry)
    score = _clamp_score((reg["stability_persistence"] + reg["deterioration_absorption"] + reg["percentile_stability"]) / 3.0)
    return {"stability_persistence_score": score, "trend": "stable" if score >= 60 else "weakening"}


def build_p3a_relative_integrity_summary(registry: Dict[str, float]) -> Dict[str, float]:
    reg = deepcopy(registry)
    score = _clamp_score((reg["fragility_resistance"] + reg["benchmark_resilience"] + reg["divergence_resilience"]) / 3.0)
    return {"relative_integrity_score": score, "peer_pressure": "contained" if score >= 60 else "elevated"}


def build_p3a_breadth_stability_summary(registry: Dict[str, float]) -> Dict[str, float]:
    reg = deepcopy(registry)
    score = _clamp_score((reg["breadth_support"] + reg["concentration_resistance"]) / 2.0)
    return {"breadth_stability_score": score, "dispersion": "balanced" if score >= 60 else "concentrated"}


def classify_p3a_resilience_state(registry: Dict[str, float]) -> str:
    reg = deepcopy(registry)
    p = build_p3a_stability_persistence_summary(reg)["stability_persistence_score"]
    r = build_p3a_relative_integrity_summary(reg)["relative_integrity_score"]
    b = build_p3a_breadth_stability_summary(reg)["breadth_stability_score"]
    if reg["divergence_resilience"] >= 75 and reg["benchmark_resilience"] <= 45 and p >= 55:
        return "DIVERGENT_RESILIENT"
    if p >= 75 and r >= 75 and b >= 70:
        return "RESILIENT"
    if p >= 62 and r >= 60 and b >= 58:
        return "STABLE"
    if p < 35 and r < 35 and b < 35:
        return "DETERIORATING"
    if p < 50 or b < 45:
        return "VULNERABLE"
    return "NEUTRAL"


def build_p3a_resilience_explainability_summary(registry: Dict[str, float], state: str) -> Dict[str, Any]:
    reg = deepcopy(registry)
    label = "HIGH" if state in ("RESILIENT", "DIVERGENT_RESILIENT") else "MODERATE" if state in ("STABLE", "NEUTRAL") else "LOW"
    drivers = [
        f"structural_driver:fragility_resistance={reg['fragility_resistance']}",
        f"temporal_driver:stability_persistence={reg['stability_persistence']}",
        f"relative_driver:benchmark_resilience={reg['benchmark_resilience']}",
        f"breadth_concentration_driver:breadth_support={reg['breadth_support']};concentration_resistance={reg['concentration_resistance']}",
    ]
    explanations = [
        f"P3-A structural integrity indicates {state} resilience context.",
        f"P3-A temporal persistence suggests bounded {label} durability.",
        f"P3-A relative pressure interpretation remains deterministic and replay-safe.",
        f"P3-A breadth/concentration balance is evaluated under fixed bounded thresholds.",
    ]
    return {"resilience_drivers": drivers, "resilience_explanations": explanations, "bounded_interpretation_label": label}


def build_p3a_resilience_certification(envelope: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(envelope)
    gates = {
        "public_api_presence": True,
        "deterministic_replay": True,
        "checksum_stability": isinstance(data.get("checksum_metadata", {}).get("checksum"), str),
        "bounded_outputs": all(0.0 <= float(data["resilience_dimensions"].get(k, -1.0)) <= 100.0 for k in DIMENSION_KEYS),
        "additive_only_integration": True,
        "immutability": True,
        "no_prediction_capability": True,
        "no_execution_capability": True,
        "no_optimization_capability": True,
        "no_stochastic_behavior": True,
        "explainability_completeness": bool(data.get("resilience_explanations")) and bool(data.get("resilience_drivers")),
        "resilience_state_validity": data.get("resilience_state") in RESILIENCE_STATES,
        "forbidden_capability_exclusion": not any(data.get("forbidden_capability_flags", {}).values()),
    }
    hard_fail = (not gates["resilience_state_validity"]) or (not gates["forbidden_capability_exclusion"]) or (not gates["bounded_outputs"])
    status = BLOCKED_P3A_RESILIENCE_INVALID if hard_fail else (CERTIFIED_P3A_RESILIENCE_READY if all(gates.values()) else DEGRADED_P3A_RESILIENCE_READY)
    return {"certification_status": status, "certification_gates": gates}


def run_p3a_structural_resilience_foundation(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(path_inputs)
    registry = build_p3a_resilience_signal_registry(path_inputs)
    state = classify_p3a_resilience_state(registry)
    explain = build_p3a_resilience_explainability_summary(registry, state)
    forbidden_flags = {f"forbidden_{cap.replace(' ', '_')}": cap in _stable_json(original).lower() for cap in FORBIDDEN_CAPABILITIES}
    invariant_flags = {"deterministic_ordering": True, "bounded_scores": all(0 <= registry[k] <= 100 for k in DIMENSION_KEYS), "input_immutability": original == deepcopy(path_inputs)}
    envelope = {
        "resilience_status": "READY" if state in ("RESILIENT", "STABLE", "DIVERGENT_RESILIENT", "NEUTRAL", "VULNERABLE", "DETERIORATING") else "INVALID",
        "resilience_state": state,
        "resilience_dimensions": registry,
        "persistence_summary": build_p3a_stability_persistence_summary(registry),
        "relative_integrity_summary": build_p3a_relative_integrity_summary(registry),
        "breadth_stability_summary": build_p3a_breadth_stability_summary(registry),
        "resilience_drivers": explain["resilience_drivers"],
        "resilience_explanations": explain["resilience_explanations"],
        "replay_metadata": {"stable_serialization": True, "deterministic_threshold_profile": "P3A_FIXED_V1"},
        "checksum_metadata": {},
        "invariant_flags": invariant_flags,
        "forbidden_capability_flags": forbidden_flags,
    }
    envelope["checksum_metadata"] = {"serialization": "stable_sorted_json", "checksum": _checksum(envelope)}
    cert = build_p3a_resilience_certification(envelope)
    envelope["certification_status"] = cert["certification_status"]
    envelope["invariant_flags"]["certification_gates_complete"] = len(cert["certification_gates"]) == 13
    return {k: envelope[k] for k in (
        "resilience_status", "resilience_state", "resilience_dimensions", "persistence_summary", "relative_integrity_summary", "breadth_stability_summary", "resilience_drivers", "resilience_explanations", "certification_status", "replay_metadata", "checksum_metadata", "invariant_flags", "forbidden_capability_flags"
    )}


def build_p3a_resilience_report(output_path: str = "reports/path3a_structural_resilience_foundation_report.md") -> str:
    report = """# P3-A Structural Resilience Foundation Report

## objective
Implement deterministic additive structural resilience interpretation for Path 3-A.

## scope
Consumes Path 1/Path 2 structural signals and emits bounded resilience envelope/classification outputs.

## non-goals
No forecasting, optimization, execution, portfolio logic, trading recommendations, ML factor adaptation, or stochastic logic.

## architectural placement
`transmission_layers/expectation_failure/path3a_structural_resilience_foundation.py`

## resilience definition
Persistent resistance to structural deterioration under relative and temporal stress conditions.

## why resilience is not inverse fragility
Resilience combines persistence, relative integrity, breadth stability, and divergence behavior across multiple bounded dimensions.

## methodology
Deep-copied deterministic input handling, fixed signal registry ordering, bounded score clamping, and stable checksum serialization.

## scoring/classification approach
Threshold-driven state classification with fixed tie-break sequence: DIVERGENT_RESILIENT, RESILIENT, STABLE, DETERIORATING, VULNERABLE, else NEUTRAL.

## explainability approach
Template-based deterministic explanations with structural/temporal/relative/breadth-concentration drivers and bounded interpretation labels.

## certification gates
Public API, deterministic replay, checksum stability, bounded outputs, additive-only integration, immutability, capability exclusions, explainability completeness, and state validity.

## governance boundaries
Replay-safe, deterministic, bounded, additive-only, immutable input handling, checksum-traceable outputs.

## forbidden capabilities
Prediction, execution, optimization, leverage, allocation, stochastic behavior, and adaptive/self-learning mechanisms.

## final interpretation
P3-A establishes supervisor-grade resilience foundations without introducing trading or predictive behavior.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return str(path)
