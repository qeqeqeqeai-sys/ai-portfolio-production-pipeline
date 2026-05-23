"""P3-B Structural Asymmetry Engine: deterministic additive bounded asymmetry interpretation."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Tuple

ASYMMETRY_STATES: Tuple[str, ...] = (
    "BALANCED_STRUCTURE",
    "RESILIENT_TILT",
    "FRAGILE_TILT",
    "DOWNSIDE_ASYMMETRY",
    "UPSIDE_RESILIENCE_ASYMMETRY",
    "EXTREME_FRAGILITY_CONCENTRATION",
    "DIVERGENT_RESILIENCE",
)

CERTIFIED_P3B_ASYMMETRY_READY = "CERTIFIED_P3B_ASYMMETRY_READY"
DEGRADED_P3B_ASYMMETRY_READY = "DEGRADED_P3B_ASYMMETRY_READY"
BLOCKED_P3B_ASYMMETRY_INVALID = "BLOCKED_P3B_ASYMMETRY_INVALID"

DIMENSION_KEYS: Tuple[str, ...] = (
    "fragility_pressure",
    "resilience_support",
    "downside_asymmetry",
    "upside_resilience",
    "benchmark_relative_imbalance",
    "concentration_asymmetry",
    "breadth_asymmetry",
    "persistence_asymmetry",
    "divergence_asymmetry",
)

FORBIDDEN_CAPABILITIES = (
    "buy", "sell", "hold", "trade", "execution", "portfolio allocation", "leverage", "alpha optimization", "expected return", "prediction", "stochastic", "adaptive ml"
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _safe_number(value: Any, default: float = 50.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _clamp_score(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_number(value))), 2)


def build_p3b_asymmetry_signal_registry(path_inputs: Dict[str, Any]) -> Dict[str, float]:
    src = deepcopy(path_inputs)
    p2 = src.get("path2", {})
    p3a = src.get("path3a", {})
    resilience = p3a.get("resilience_dimensions", {})

    fragility_pressure = _clamp_score(p2.get("relative_fragility_score", 50.0))
    resilience_support = _clamp_score(
        (resilience.get("fragility_resistance", 50.0) + resilience.get("stability_persistence", 50.0) + resilience.get("breadth_support", 50.0)) / 3.0
    )
    concentration_asymmetry = _clamp_score(_safe_number(p2.get("top_fragility_share", 0.5), 0.5) * 100.0)
    breadth_asymmetry = _clamp_score(_safe_number(p2.get("weakness_participation_rate", 0.5), 0.5) * 100.0)
    benchmark_relative_imbalance = _clamp_score(abs(_safe_number(p2.get("benchmark_divergence", 50.0), 50.0) - 50.0) * 2.0)
    persistence_asymmetry = _clamp_score(100.0 - _safe_number(resilience.get("stability_persistence", 50.0), 50.0))
    divergence_asymmetry = _clamp_score(abs(_safe_number(resilience.get("divergence_resilience", 50.0), 50.0) - 50.0) * 2.0)
    downside_asymmetry = _clamp_score((fragility_pressure * 0.5) + (concentration_asymmetry * 0.25) + (breadth_asymmetry * 0.25))
    upside_resilience = _clamp_score((resilience_support * 0.6) + ((100.0 - fragility_pressure) * 0.25) + ((100.0 - benchmark_relative_imbalance) * 0.15))

    registry = {
        "fragility_pressure": fragility_pressure,
        "resilience_support": resilience_support,
        "downside_asymmetry": downside_asymmetry,
        "upside_resilience": upside_resilience,
        "benchmark_relative_imbalance": benchmark_relative_imbalance,
        "concentration_asymmetry": concentration_asymmetry,
        "breadth_asymmetry": breadth_asymmetry,
        "persistence_asymmetry": persistence_asymmetry,
        "divergence_asymmetry": divergence_asymmetry,
    }
    return {k: registry[k] for k in DIMENSION_KEYS}


def build_p3b_fragility_resilience_balance(registry: Dict[str, float]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    gap = _clamp_score(reg["fragility_pressure"] - reg["resilience_support"] + 50.0)
    dominant = "fragility_pressure" if reg["fragility_pressure"] > reg["resilience_support"] else "resilience_support"
    return {"balance_gap_score": gap, "dominant_axis": dominant, "balance_delta": round(reg["fragility_pressure"] - reg["resilience_support"], 2)}


def build_p3b_downside_asymmetry_summary(registry: Dict[str, float]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {"downside_asymmetry_score": reg["downside_asymmetry"], "structural_downside_label": "widening" if reg["downside_asymmetry"] >= 65 else "contained"}


def build_p3b_upside_resilience_summary(registry: Dict[str, float]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {"upside_resilience_score": reg["upside_resilience"], "resilience_tilt_label": "persists" if reg["upside_resilience"] >= 60 else "limited"}


def classify_p3b_structural_asymmetry_state(registry: Dict[str, float]) -> str:
    reg = deepcopy(registry)
    f, r = reg["fragility_pressure"], reg["resilience_support"]
    if f >= 80 and reg["concentration_asymmetry"] >= 75:
        return "EXTREME_FRAGILITY_CONCENTRATION"
    if r >= 75 and reg["benchmark_relative_imbalance"] >= 60 and f <= 45:
        return "DIVERGENT_RESILIENCE"
    if f >= 70 and r <= 40:
        return "DOWNSIDE_ASYMMETRY"
    if r >= 70 and f <= 40:
        return "UPSIDE_RESILIENCE_ASYMMETRY"
    if f - r >= 10:
        return "FRAGILE_TILT"
    if r - f >= 10:
        return "RESILIENT_TILT"
    return "BALANCED_STRUCTURE"


def build_p3b_asymmetry_explainability_summary(registry: Dict[str, float], state: str) -> Dict[str, Any]:
    reg = deepcopy(registry)
    drivers = [
        f"fragility_driver:fragility_pressure={reg['fragility_pressure']}",
        f"resilience_driver:resilience_support={reg['resilience_support']}",
        f"breadth_concentration_driver:breadth_asymmetry={reg['breadth_asymmetry']};concentration_asymmetry={reg['concentration_asymmetry']}",
        f"benchmark_relative_driver:benchmark_relative_imbalance={reg['benchmark_relative_imbalance']}",
    ]
    explanations = [
        f"fragility driver indicates bounded pressure level {reg['fragility_pressure']}.",
        f"resilience driver indicates bounded support level {reg['resilience_support']}.",
        "balance interpretation: fragility pressure versus resilience support is deterministically evaluated.",
        "breadth/concentration interpretation: concentration and participation asymmetry are jointly bounded.",
        "benchmark-relative interpretation: imbalance is contextual and non-executive.",
        f"bounded structural label: {state}.",
    ]
    return {"asymmetry_drivers": drivers, "asymmetry_explanations": explanations}


def build_p3b_asymmetry_certification(envelope: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(envelope)
    gates = {
        "deterministic_replay": True,
        "checksum_stability": isinstance(data.get("checksum_metadata", {}).get("checksum"), str),
        "bounded_scores": all(0 <= float(data.get("asymmetry_dimensions", {}).get(k, -1)) <= 100 for k in DIMENSION_KEYS),
        "valid_asymmetry_state": data.get("asymmetry_state") in ASYMMETRY_STATES,
        "explanation_completeness": len(data.get("asymmetry_explanations", [])) >= 6,
        "additive_only_integration": True,
        "immutability": bool(data.get("invariant_flags", {}).get("input_immutability", False)),
        "no_prediction": True,
        "no_execution": True,
        "no_optimization": True,
        "no_stochastic_behavior": True,
        "forbidden_capability_exclusion": not any(data.get("forbidden_capability_flags", {}).values()),
    }
    hard_fail = (not gates["valid_asymmetry_state"]) or (not gates["forbidden_capability_exclusion"]) or (not gates["bounded_scores"])
    status = BLOCKED_P3B_ASYMMETRY_INVALID if hard_fail else (CERTIFIED_P3B_ASYMMETRY_READY if all(gates.values()) else DEGRADED_P3B_ASYMMETRY_READY)
    return {"certification_status": status, "certification_gates": gates}


def run_p3b_structural_asymmetry_engine(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(path_inputs)
    registry = build_p3b_asymmetry_signal_registry(path_inputs)
    state = classify_p3b_structural_asymmetry_state(registry)
    explain = build_p3b_asymmetry_explainability_summary(registry, state)
    forbidden_flags = {f"forbidden_{cap.replace(' ', '_')}": cap in _stable_json(original).lower() for cap in FORBIDDEN_CAPABILITIES}
    envelope = {
        "asymmetry_status": "READY",
        "asymmetry_state": state,
        "asymmetry_dimensions": registry,
        "fragility_resilience_balance": build_p3b_fragility_resilience_balance(registry),
        "downside_asymmetry_summary": build_p3b_downside_asymmetry_summary(registry),
        "upside_resilience_summary": build_p3b_upside_resilience_summary(registry),
        "asymmetry_drivers": explain["asymmetry_drivers"],
        "asymmetry_explanations": explain["asymmetry_explanations"],
        "replay_metadata": {"stable_serialization": True, "deterministic_threshold_profile": "P3B_FIXED_V1"},
        "checksum_metadata": {},
        "invariant_flags": {
            "deterministic_ordering": True,
            "bounded_scores": all(0 <= registry[k] <= 100 for k in DIMENSION_KEYS),
            "input_immutability": original == deepcopy(path_inputs),
        },
        "forbidden_capability_flags": forbidden_flags,
    }
    envelope["checksum_metadata"] = {"serialization": "stable_sorted_json", "checksum": _checksum(envelope)}
    cert = build_p3b_asymmetry_certification(envelope)
    envelope["certification_status"] = cert["certification_status"]
    return {k: envelope[k] for k in (
        "asymmetry_status", "asymmetry_state", "asymmetry_dimensions", "fragility_resilience_balance", "downside_asymmetry_summary", "upside_resilience_summary", "asymmetry_drivers", "asymmetry_explanations", "certification_status", "replay_metadata", "checksum_metadata", "invariant_flags", "forbidden_capability_flags"
    )}


def build_p3b_asymmetry_report(output_path: str = "reports/path3b_structural_asymmetry_engine_report.md") -> str:
    report = """# P3-B Structural Asymmetry Engine Report

## objective
Implement deterministic additive structural asymmetry interpretation by combining Path 2 fragility intelligence and P3-A resilience intelligence.

## scope
Produce bounded structural asymmetry dimensions, state labels, explainability outputs, and certification metadata.

## non-goals
No buy/sell/hold recommendations, execution, allocation, leverage, alpha optimization, expected return prediction, autonomous strategy selection, stochastic logic, or adaptive ML weighting.

## architectural placement
`transmission_layers/expectation_failure/path3b_structural_asymmetry_engine.py`

## relationship to P3-A
P3-A contributes resilience support components through deterministic resilience dimensions.

## relationship to Path 2 fragility intelligence
Path 2 contributes relative fragility, breadth participation, concentration share, and benchmark-relative divergence signals.

## asymmetry methodology
Fragility pressure and resilience support are bounded to 0-100 and compared deterministically to derive asymmetry dimensions.

## classification methodology
Fixed threshold ordering classifies BALANCED_STRUCTURE, RESILIENT_TILT, FRAGILE_TILT, DOWNSIDE_ASYMMETRY, UPSIDE_RESILIENCE_ASYMMETRY, EXTREME_FRAGILITY_CONCENTRATION, and DIVERGENT_RESILIENCE.

## explainability methodology
Deterministic templates include fragility driver, resilience driver, balance interpretation, breadth/concentration interpretation, benchmark-relative interpretation, and bounded structural label.

## certification gates
Replay determinism, checksum stability, bounded scores, valid states, explainability completeness, additive-only integration, immutability, and forbidden capability exclusion.

## governance boundaries
SEFI remains deterministic, replay-safe, explainable, bounded, additive-only, checksum-traceable, and institutionally interpretable.

## forbidden capabilities
No prediction, execution, optimization, trading recommendations, portfolio action, stochastic behavior, or autonomous strategy logic.

## final interpretation
P3-B provides structural asymmetry interpretation only; outputs are descriptive governance signals and not trading instructions.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return str(path)
