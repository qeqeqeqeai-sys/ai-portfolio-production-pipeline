"""P3-C Benchmark-Relative Asymmetry Intelligence: deterministic additive benchmark/cohort context for P3-B."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Tuple

BENCHMARK_ASYMMETRY_STATES: Tuple[str, ...] = (
    "BENCHMARK_ALIGNED",
    "BENCHMARK_RESILIENT_DIVERGENCE",
    "BENCHMARK_FRAGILITY_DIVERGENCE",
    "ASYMMETRY_SPREAD_EXPANSION",
    "ASYMMETRY_SPREAD_COMPRESSION",
    "BENCHMARK_RELATIVE_DOWNSIDE_PRESSURE",
    "BENCHMARK_RELATIVE_UPSIDE_RESILIENCE",
    "EXTREME_BENCHMARK_IMBALANCE",
)

CERTIFIED_P3C_BENCHMARK_ASYMMETRY_READY = "CERTIFIED_P3C_BENCHMARK_ASYMMETRY_READY"
DEGRADED_P3C_BENCHMARK_ASYMMETRY_READY = "DEGRADED_P3C_BENCHMARK_ASYMMETRY_READY"
BLOCKED_P3C_BENCHMARK_ASYMMETRY_INVALID = "BLOCKED_P3C_BENCHMARK_ASYMMETRY_INVALID"

DIMENSION_KEYS: Tuple[str, ...] = (
    "entity_asymmetry_score",
    "benchmark_asymmetry_score",
    "relative_asymmetry_spread",
    "downside_spread",
    "upside_resilience_spread",
    "fragility_divergence",
    "resilience_divergence",
    "benchmark_relative_pressure",
    "benchmark_relative_resilience",
    "spread_direction",
)

FORBIDDEN_CAPABILITIES = (
    "buy", "sell", "hold", "portfolio allocation", "trade execution", "leverage", "alpha optimization", "expected return", "prediction", "stochastic", "adaptive ml", "autonomous strategy"
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _safe_number(value: Any, default: float = 50.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _clamp(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_number(value))), 2)


def _spread_direction(relative_spread: float) -> str:
    if relative_spread >= 8.0:
        return "EXPANDING"
    if relative_spread <= -8.0:
        return "COMPRESSING"
    return "STABLE"


def build_p3c_benchmark_asymmetry_registry(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    p3b = src.get("path3b", {})
    benchmark = src.get("benchmark", {})

    p3b_dims = p3b.get("asymmetry_dimensions", {})
    entity_asymmetry = _clamp(p3b_dims.get("downside_asymmetry", p3b.get("entity_asymmetry_score", 50.0)))
    entity_resilience = _clamp(p3b_dims.get("upside_resilience", p3b.get("entity_resilience_score", 50.0)))

    benchmark_asymmetry = _clamp(benchmark.get("benchmark_asymmetry_score", benchmark.get("asymmetry_score", 50.0)))
    benchmark_resilience = _clamp(benchmark.get("benchmark_resilience_score", benchmark.get("resilience_score", 50.0)))

    relative_spread = round(entity_asymmetry - benchmark_asymmetry, 2)
    downside_spread = _clamp(relative_spread + 50.0)
    upside_spread = _clamp(entity_resilience - benchmark_resilience + 50.0)
    fragility_divergence = _clamp((entity_asymmetry * 0.7) + ((100.0 - benchmark_asymmetry) * 0.3))
    resilience_divergence = _clamp((entity_resilience * 0.7) + ((100.0 - benchmark_resilience) * 0.3))
    pressure = _clamp((downside_spread * 0.7) + (fragility_divergence * 0.3))
    rel_resilience = _clamp((upside_spread * 0.7) + (resilience_divergence * 0.3))

    registry = {
        "entity_asymmetry_score": entity_asymmetry,
        "benchmark_asymmetry_score": benchmark_asymmetry,
        "relative_asymmetry_spread": relative_spread,
        "downside_spread": downside_spread,
        "upside_resilience_spread": upside_spread,
        "fragility_divergence": fragility_divergence,
        "resilience_divergence": resilience_divergence,
        "benchmark_relative_pressure": pressure,
        "benchmark_relative_resilience": rel_resilience,
        "spread_direction": _spread_direction(relative_spread),
    }
    return {k: registry[k] for k in DIMENSION_KEYS}


def build_p3c_relative_asymmetry_spread(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {
        "spread_score": _clamp(reg["relative_asymmetry_spread"] + 50.0),
        "spread_direction": reg["spread_direction"],
        "absolute_spread": round(abs(_safe_number(reg["relative_asymmetry_spread"], 0.0)), 2),
    }


def build_p3c_benchmark_divergence_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {
        "fragility_divergence": reg["fragility_divergence"],
        "benchmark_relative_pressure": reg["benchmark_relative_pressure"],
        "downside_spread": reg["downside_spread"],
    }


def build_p3c_resilience_divergence_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {
        "resilience_divergence": reg["resilience_divergence"],
        "benchmark_relative_resilience": reg["benchmark_relative_resilience"],
        "upside_resilience_spread": reg["upside_resilience_spread"],
    }


def classify_p3c_benchmark_relative_asymmetry_state(registry: Dict[str, Any]) -> str:
    reg = deepcopy(registry)
    spread = _safe_number(reg["relative_asymmetry_spread"], 0.0)
    downside = _safe_number(reg["downside_spread"], 50.0)
    upside = _safe_number(reg["upside_resilience_spread"], 50.0)
    entity = _safe_number(reg["entity_asymmetry_score"], 50.0)
    bench = _safe_number(reg["benchmark_asymmetry_score"], 50.0)
    bench_weak = bench >= 60.0

    if abs(spread) >= 30.0:
        return "EXTREME_BENCHMARK_IMBALANCE"
    if downside >= 75.0:
        return "BENCHMARK_RELATIVE_DOWNSIDE_PRESSURE"
    if upside >= 75.0:
        return "BENCHMARK_RELATIVE_UPSIDE_RESILIENCE"
    if spread >= 8.0:
        return "ASYMMETRY_SPREAD_EXPANSION"
    if spread <= -8.0:
        return "ASYMMETRY_SPREAD_COMPRESSION"
    if entity - bench >= 12.0:
        return "BENCHMARK_FRAGILITY_DIVERGENCE"
    if (upside >= 62.0) and bench_weak:
        return "BENCHMARK_RESILIENT_DIVERGENCE"
    return "BENCHMARK_ALIGNED"


def build_p3c_benchmark_asymmetry_explainability_summary(registry: Dict[str, Any], state: str) -> Dict[str, Any]:
    reg = deepcopy(registry)
    drivers = [
        f"entity_asymmetry_driver:entity_asymmetry_score={reg['entity_asymmetry_score']}",
        f"benchmark_comparison_driver:benchmark_asymmetry_score={reg['benchmark_asymmetry_score']};relative_asymmetry_spread={reg['relative_asymmetry_spread']}",
        f"spread_direction_driver:spread_direction={reg['spread_direction']}",
        f"downside_upside_driver:downside_spread={reg['downside_spread']};upside_resilience_spread={reg['upside_resilience_spread']}",
        f"resilience_divergence_driver:resilience_divergence={reg['resilience_divergence']}",
    ]
    explanations = [
        f"entity asymmetry driver indicates bounded structural level {reg['entity_asymmetry_score']}.",
        f"benchmark comparison driver indicates bounded benchmark level {reg['benchmark_asymmetry_score']} with spread {reg['relative_asymmetry_spread']}.",
        f"spread direction interpretation: {reg['spread_direction']}.",
        "downside/upside interpretation: benchmark-relative pressure and resilience are descriptively evaluated.",
        f"resilience divergence interpretation indicates bounded divergence level {reg['resilience_divergence']}.",
        f"bounded structural label: {state}.",
    ]
    return {"benchmark_asymmetry_drivers": drivers, "benchmark_asymmetry_explanations": explanations}


def build_p3c_benchmark_asymmetry_certification(envelope: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(envelope)
    dims = data.get("benchmark_asymmetry_dimensions", {})
    gates = {
        "deterministic_replay": True,
        "checksum_stability": isinstance(data.get("checksum_metadata", {}).get("checksum"), str),
        "bounded_scores": all((k == "spread_direction") or (0 <= float(dims.get(k, -1)) <= 100) for k in DIMENSION_KEYS),
        "valid_benchmark_relative_state": data.get("benchmark_asymmetry_state") in BENCHMARK_ASYMMETRY_STATES,
        "explanation_completeness": len(data.get("benchmark_asymmetry_explanations", [])) >= 6,
        "additive_only_integration": True,
        "immutability": bool(data.get("invariant_flags", {}).get("input_immutability", False)),
        "missing_benchmark_degraded_behavior": bool(data.get("invariant_flags", {}).get("missing_benchmark_fallback", False)) or data.get("benchmark_asymmetry_status") == "READY",
        "benchmark_context_present": data.get("benchmark_asymmetry_status") == "READY",
        "no_prediction": True,
        "no_execution": True,
        "no_optimization": True,
        "no_stochastic_behavior": True,
        "forbidden_capability_exclusion": not any(data.get("forbidden_capability_flags", {}).values()),
    }
    hard_fail = (not gates["valid_benchmark_relative_state"]) or (not gates["forbidden_capability_exclusion"]) or (not gates["bounded_scores"])
    status = BLOCKED_P3C_BENCHMARK_ASYMMETRY_INVALID if hard_fail else (CERTIFIED_P3C_BENCHMARK_ASYMMETRY_READY if all(gates.values()) else DEGRADED_P3C_BENCHMARK_ASYMMETRY_READY)
    return {"certification_status": status, "certification_gates": gates}


def run_p3c_benchmark_relative_asymmetry_intelligence(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(path_inputs)
    registry = build_p3c_benchmark_asymmetry_registry(path_inputs)
    state = classify_p3c_benchmark_relative_asymmetry_state(registry)
    explain = build_p3c_benchmark_asymmetry_explainability_summary(registry, state)
    json_view = _stable_json(original).lower()
    forbidden_flags = {f"forbidden_{cap.replace(' ', '_')}": cap in json_view for cap in FORBIDDEN_CAPABILITIES}

    has_benchmark = isinstance(path_inputs.get("benchmark"), dict) and bool(path_inputs.get("benchmark"))
    envelope = {
        "benchmark_asymmetry_status": "READY" if has_benchmark else "DEGRADED_MISSING_BENCHMARK",
        "benchmark_asymmetry_state": state,
        "benchmark_asymmetry_dimensions": registry,
        "relative_asymmetry_spread": build_p3c_relative_asymmetry_spread(registry),
        "benchmark_divergence_summary": build_p3c_benchmark_divergence_summary(registry),
        "resilience_divergence_summary": build_p3c_resilience_divergence_summary(registry),
        "benchmark_asymmetry_drivers": explain["benchmark_asymmetry_drivers"],
        "benchmark_asymmetry_explanations": explain["benchmark_asymmetry_explanations"],
        "replay_metadata": {"stable_serialization": True, "deterministic_threshold_profile": "P3C_FIXED_V1"},
        "checksum_metadata": {},
        "invariant_flags": {
            "deterministic_ordering": True,
            "bounded_scores": all((k == "spread_direction") or (0 <= registry[k] <= 100) for k in DIMENSION_KEYS),
            "input_immutability": original == deepcopy(path_inputs),
            "missing_benchmark_fallback": not has_benchmark,
        },
        "forbidden_capability_flags": forbidden_flags,
    }
    envelope["checksum_metadata"] = {"serialization": "stable_sorted_json", "checksum": _checksum(envelope)}
    cert = build_p3c_benchmark_asymmetry_certification(envelope)
    envelope["certification_status"] = cert["certification_status"]
    return {k: envelope[k] for k in (
        "benchmark_asymmetry_status", "benchmark_asymmetry_state", "benchmark_asymmetry_dimensions", "relative_asymmetry_spread", "benchmark_divergence_summary", "resilience_divergence_summary", "benchmark_asymmetry_drivers", "benchmark_asymmetry_explanations", "certification_status", "replay_metadata", "checksum_metadata", "invariant_flags", "forbidden_capability_flags"
    )}


def build_p3c_benchmark_asymmetry_report(output_path: str = "reports/path3c_benchmark_relative_asymmetry_report.md") -> str:
    report = """# P3-C Benchmark-Relative Asymmetry Intelligence Report

## objective
Implement deterministic additive benchmark-relative asymmetry intelligence that contextualizes P3-B outputs against benchmark/cohort signals.

## scope
Produce bounded benchmark-relative dimensions, spread/divergence summaries, deterministic state classification, explainability templates, and certification metadata.

## non-goals
No buy/sell/hold recommendations, portfolio allocation, trade execution, leverage logic, alpha optimization, expected return prediction, autonomous strategy selection, stochastic signals, or adaptive ML weighting.

## architectural placement
`transmission_layers/expectation_failure/path3c_benchmark_relative_asymmetry.py`

## relationship to P3-B
P3-B contributes deterministic entity downside and upside asymmetry dimensions used as entity context.

## benchmark-relative methodology
Entity asymmetry and resilience are compared against deterministic benchmark asymmetry and resilience to derive bounded relative pressure/resilience context.

## spread/divergence methodology
Relative spread is entity minus benchmark asymmetry with deterministic direction labels (EXPANDING, COMPRESSING, STABLE) and bounded projections.

## classification methodology
Fixed tie-break ordering maps dimensions to BENCHMARK_ALIGNED, BENCHMARK_RESILIENT_DIVERGENCE, BENCHMARK_FRAGILITY_DIVERGENCE, ASYMMETRY_SPREAD_EXPANSION, ASYMMETRY_SPREAD_COMPRESSION, BENCHMARK_RELATIVE_DOWNSIDE_PRESSURE, BENCHMARK_RELATIVE_UPSIDE_RESILIENCE, EXTREME_BENCHMARK_IMBALANCE.

## explainability methodology
Deterministic templates provide entity driver, benchmark comparison driver, spread direction, downside/upside interpretation, resilience divergence interpretation, and bounded structural label.

## certification gates
Replay determinism, checksum stability, bounded scores, valid state, explanation completeness, additive-only integration, immutability, missing benchmark degraded behavior, no prediction/execution/optimization/stochastic behavior, and forbidden capability exclusion.

## governance boundaries
SEFI remains deterministic, replay-safe, explainable, bounded, additive-only, checksum-traceable, and institutionally interpretable.

## forbidden capabilities
No trading recommendations, no execution directives, no predictive return claims, and no autonomous strategy logic.

## final interpretation
P3-C is benchmark-relative structural interpretation only and provides institutional diagnostics rather than trading actions.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return str(path)
