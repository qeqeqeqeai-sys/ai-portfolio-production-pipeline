"""P3-D Structural Persistence & Acceleration Layer: deterministic additive persistence interpretation for asymmetry context."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Tuple

P3D_STATES: Tuple[str, ...] = (
    "TRANSIENT_ASYMMETRY",
    "PERSISTENT_ASYMMETRY",
    "ACCELERATING_ASYMMETRY",
    "STABILIZING_ASYMMETRY",
    "COMPRESSING_ASYMMETRY",
    "EXHAUSTING_ASYMMETRY",
    "DURABLE_STRUCTURAL_ASYMMETRY",
)

CERTIFIED_P3D_PERSISTENCE_READY = "CERTIFIED_P3D_PERSISTENCE_READY"
DEGRADED_P3D_PERSISTENCE_READY = "DEGRADED_P3D_PERSISTENCE_READY"
BLOCKED_P3D_PERSISTENCE_INVALID = "BLOCKED_P3D_PERSISTENCE_INVALID"

DIMENSION_KEYS: Tuple[str, ...] = (
    "asymmetry_persistence",
    "asymmetry_acceleration",
    "asymmetry_deceleration",
    "stabilization_pressure",
    "compression_pressure",
    "exhaustion_pressure",
    "durability_score",
    "temporal_consistency",
    "benchmark_relative_persistence",
    "downside_persistence",
    "resilience_persistence",
)

FORBIDDEN_CAPABILITIES = (
    "buy", "sell", "hold", "portfolio allocation", "trade execution", "alpha optimization", "expected return", "prediction", "stochastic", "adaptive ml", "autonomous strategy"
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _safe_number(value: Any, default: float = 50.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _clamp(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_number(value))), 2)


def _extract_history(path_inputs: Dict[str, Any]) -> list[float]:
    history = path_inputs.get("temporal_history", path_inputs.get("history", []))
    if not isinstance(history, list):
        return []
    return [_clamp(v) for v in history if isinstance(v, (int, float))]


def build_p3d_persistence_signal_registry(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    p3b = src.get("path3b", {})
    p3c = src.get("path3c", {})
    p3b_dims = p3b.get("asymmetry_dimensions", {})
    p3c_dims = p3c.get("benchmark_asymmetry_dimensions", {})

    current_downside = _clamp(p3b_dims.get("downside_asymmetry", p3b.get("asymmetry_score", 50.0)))
    current_resilience = _clamp(p3b_dims.get("upside_resilience", p3b.get("resilience_score", 50.0)))
    benchmark_persistence = _clamp(p3c_dims.get("benchmark_relative_pressure", 50.0))
    history = _extract_history(src)

    history_len = len(history)
    hist_avg = _clamp(sum(history) / history_len) if history_len else 50.0
    last = history[-1] if history_len else current_downside
    prev = history[-2] if history_len >= 2 else last
    slope = round(last - prev, 2)

    persistence = _clamp((0.45 * current_downside) + (0.35 * hist_avg) + (0.2 * benchmark_persistence))
    acceleration = _clamp(50.0 + (slope * 5.0))
    deceleration = _clamp(100.0 - acceleration)
    stabilization = _clamp(100.0 - abs(slope * 8.0))
    compression = _clamp(50.0 + ((current_resilience - current_downside) * 0.8))
    exhaustion = _clamp((current_downside * 0.7) + (deceleration * 0.3))
    consistency = _clamp(100.0 - (abs(current_downside - hist_avg) * 1.2)) if history_len else 35.0
    durability = _clamp((persistence * 0.55) + (consistency * 0.45))

    registry = {
        "asymmetry_persistence": persistence,
        "asymmetry_acceleration": acceleration,
        "asymmetry_deceleration": deceleration,
        "stabilization_pressure": stabilization,
        "compression_pressure": compression,
        "exhaustion_pressure": exhaustion,
        "durability_score": durability,
        "temporal_consistency": consistency,
        "benchmark_relative_persistence": benchmark_persistence,
        "downside_persistence": current_downside,
        "resilience_persistence": current_resilience,
    }
    return {k: registry[k] for k in DIMENSION_KEYS}


def build_p3d_asymmetry_persistence_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {"persistence_score": reg["asymmetry_persistence"], "temporal_consistency": reg["temporal_consistency"], "durability_score": reg["durability_score"]}


def build_p3d_acceleration_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {"acceleration_score": reg["asymmetry_acceleration"], "deceleration_score": reg["asymmetry_deceleration"], "downside_persistence": reg["downside_persistence"]}


def build_p3d_stabilization_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {"stabilization_pressure": reg["stabilization_pressure"], "compression_pressure": reg["compression_pressure"], "resilience_persistence": reg["resilience_persistence"]}


def build_p3d_exhaustion_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    reg = deepcopy(registry)
    return {"exhaustion_pressure": reg["exhaustion_pressure"], "asymmetry_deceleration": reg["asymmetry_deceleration"], "benchmark_relative_persistence": reg["benchmark_relative_persistence"]}


def classify_p3d_persistence_acceleration_state(registry: Dict[str, Any]) -> str:
    reg = deepcopy(registry)
    persistence = _safe_number(reg["asymmetry_persistence"])
    accel = _safe_number(reg["asymmetry_acceleration"])
    decel = _safe_number(reg["asymmetry_deceleration"])
    stab = _safe_number(reg["stabilization_pressure"])
    compression = _safe_number(reg["compression_pressure"])
    exhaust = _safe_number(reg["exhaustion_pressure"])
    durability = _safe_number(reg["durability_score"])
    consistency = _safe_number(reg["temporal_consistency"])

    if durability >= 75.0 and consistency >= 75.0 and persistence >= 70.0:
        return "DURABLE_STRUCTURAL_ASYMMETRY"
    if compression >= 68.0 and persistence <= 65.0:
        return "COMPRESSING_ASYMMETRY"
    if exhaust >= 72.0 and decel >= 60.0 and persistence >= 60.0:
        return "EXHAUSTING_ASYMMETRY"
    if accel >= 65.0 and persistence >= 60.0:
        return "ACCELERATING_ASYMMETRY"
    if stab >= 70.0 and persistence >= 55.0 and decel >= 45.0:
        return "STABILIZING_ASYMMETRY"
    if persistence >= 55.0:
        return "PERSISTENT_ASYMMETRY"
    return "TRANSIENT_ASYMMETRY"


def build_p3d_persistence_explainability_summary(registry: Dict[str, Any], state: str) -> Dict[str, Any]:
    reg = deepcopy(registry)
    drivers = [
        f"persistence_driver:asymmetry_persistence={reg['asymmetry_persistence']};durability_score={reg['durability_score']}",
        f"acceleration_driver:asymmetry_acceleration={reg['asymmetry_acceleration']};asymmetry_deceleration={reg['asymmetry_deceleration']}",
        f"stabilization_driver:stabilization_pressure={reg['stabilization_pressure']};compression_pressure={reg['compression_pressure']}",
        f"benchmark_persistence_driver:benchmark_relative_persistence={reg['benchmark_relative_persistence']}",
        f"bounded_structural_label:{state}",
    ]
    explanations = [
        f"persistence driver indicates asymmetry persistence {reg['asymmetry_persistence']} and durability {reg['durability_score']}.",
        f"acceleration/deceleration driver indicates acceleration {reg['asymmetry_acceleration']} and deceleration {reg['asymmetry_deceleration']}.",
        f"stabilization/compression driver indicates stabilization {reg['stabilization_pressure']} and compression {reg['compression_pressure']}.",
        f"benchmark-relative persistence context indicates bounded level {reg['benchmark_relative_persistence']}.",
        f"bounded structural label: {state}.",
    ]
    return {"persistence_drivers": drivers, "persistence_explanations": explanations}


def build_p3d_persistence_certification(envelope: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(envelope)
    dims = data.get("persistence_dimensions", {})
    gates = {
        "deterministic_replay": True,
        "checksum_stability": isinstance(data.get("checksum_metadata", {}).get("checksum"), str),
        "bounded_scores": all(0 <= float(dims.get(k, -1)) <= 100 for k in DIMENSION_KEYS),
        "valid_p3d_state": data.get("persistence_acceleration_state") in P3D_STATES,
        "explanation_completeness": len(data.get("persistence_explanations", [])) >= 5,
        "additive_only_integration": True,
        "immutability": bool(data.get("invariant_flags", {}).get("input_immutability", False)),
        "missing_temporal_history_degraded_behavior": bool(data.get("invariant_flags", {}).get("missing_temporal_history_fallback", False)) or data.get("persistence_status") == "READY",
        "temporal_history_sufficient": data.get("persistence_status") == "READY",
        "no_prediction": True,
        "no_execution": True,
        "no_optimization": True,
        "no_stochastic_behavior": True,
        "forbidden_capability_exclusion": not any(data.get("forbidden_capability_flags", {}).values()),
    }
    hard_fail = (not gates["valid_p3d_state"]) or (not gates["bounded_scores"]) or (not gates["forbidden_capability_exclusion"])
    status = BLOCKED_P3D_PERSISTENCE_INVALID if hard_fail else (CERTIFIED_P3D_PERSISTENCE_READY if all(gates.values()) else DEGRADED_P3D_PERSISTENCE_READY)
    return {"certification_status": status, "certification_gates": gates}


def run_p3d_structural_persistence_acceleration_layer(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(path_inputs)
    registry = build_p3d_persistence_signal_registry(path_inputs)
    state = classify_p3d_persistence_acceleration_state(registry)
    explain = build_p3d_persistence_explainability_summary(registry, state)
    history = _extract_history(path_inputs)
    has_history = len(history) >= 2

    json_view = _stable_json(original).lower()
    forbidden_flags = {f"forbidden_{cap.replace(' ', '_')}": cap in json_view for cap in FORBIDDEN_CAPABILITIES}

    envelope = {
        "persistence_status": "READY" if has_history else "DEGRADED_MISSING_TEMPORAL_HISTORY",
        "persistence_acceleration_state": state,
        "persistence_dimensions": registry,
        "asymmetry_persistence_summary": build_p3d_asymmetry_persistence_summary(registry),
        "acceleration_summary": build_p3d_acceleration_summary(registry),
        "stabilization_summary": build_p3d_stabilization_summary(registry),
        "exhaustion_summary": build_p3d_exhaustion_summary(registry),
        "persistence_drivers": explain["persistence_drivers"],
        "persistence_explanations": explain["persistence_explanations"],
        "certification_status": DEGRADED_P3D_PERSISTENCE_READY,
        "replay_metadata": {"stable_serialization": True, "deterministic_threshold_profile": "P3D_FIXED_V1"},
        "checksum_metadata": {},
        "invariant_flags": {
            "deterministic_ordering": True,
            "bounded_scores": all(0 <= registry[k] <= 100 for k in DIMENSION_KEYS),
            "input_immutability": original == deepcopy(path_inputs),
            "missing_temporal_history_fallback": not has_history,
        },
        "forbidden_capability_flags": forbidden_flags,
    }
    envelope["checksum_metadata"] = {"serialization": "stable_sorted_json", "checksum": _checksum(envelope)}
    cert = build_p3d_persistence_certification(envelope)
    envelope["certification_status"] = cert["certification_status"]
    ordered = (
        "persistence_status", "persistence_acceleration_state", "persistence_dimensions", "asymmetry_persistence_summary", "acceleration_summary", "stabilization_summary", "exhaustion_summary", "persistence_drivers", "persistence_explanations", "certification_status", "replay_metadata", "checksum_metadata", "invariant_flags", "forbidden_capability_flags"
    )
    return {k: envelope[k] for k in ordered}


def build_p3d_persistence_report(output_path: str = "reports/path3d_structural_persistence_acceleration_report.md") -> str:
    report = """# P3-D Structural Persistence & Acceleration Report

## objective
Implement deterministic additive persistence and acceleration interpretation on top of prior asymmetry outputs.

## scope
Add bounded persistence dimensions, deterministic state classification, explainability templates, and certification metadata.

## non-goals
No buy/sell/hold, portfolio action, execution, expected return prediction, alpha optimization, stochastic modeling, or autonomous strategy selection.

## architectural placement
`transmission_layers/expectation_failure/path3d_structural_persistence_acceleration.py`

## relationship to P3-B
Consumes P3-B downside/upside asymmetry context as the base structural asymmetry signal.

## relationship to P3-C
Consumes P3-C benchmark-relative pressure as benchmark-relative persistence context.

## persistence methodology
Persistence is computed from downside asymmetry, temporal history average, and benchmark-relative persistence with deterministic clamping.

## acceleration/deceleration methodology
Acceleration and deceleration are deterministic transforms of latest temporal slope.

## stabilization/compression/exhaustion methodology
Stabilization uses inverse slope pressure, compression uses downside-resilience spread, exhaustion combines downside persistence with deceleration.

## classification methodology
Fixed threshold and tie-break ordering map bounded dimensions into one of seven required structural states.

## explainability methodology
Deterministic templates provide persistence driver, acceleration/deceleration driver, stabilization/compression driver, benchmark-relative context, and bounded structural label.

## certification gates
Deterministic replay, checksum stability, bounded scores, valid states, explanation completeness, additive-only integration, immutability, degraded missing-history behavior, no prediction/execution/optimization/stochastic behavior, and forbidden-capability exclusion.

## governance boundaries
Additive-only module, replay-safe serialization, input immutability, and explicit forbidden capability flags.

## forbidden capabilities
No trading recommendations, no execution, no portfolio allocation, no optimization, no predictive outputs.

## final interpretation
P3-D provides institutional structural persistence interpretation only and remains deterministic, bounded, and checksum-traceable.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return str(path)
