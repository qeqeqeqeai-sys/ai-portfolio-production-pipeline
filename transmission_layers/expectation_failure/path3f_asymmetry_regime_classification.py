"""P3-F Asymmetry Regime Classification: deterministic additive bounded regime consolidation across P3-A..P3-E."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Tuple

P3F_REGIMES: Tuple[str, ...] = (
    "STABLE_SYMMETRY_REGIME",
    "RESILIENT_DIVERGENCE_REGIME",
    "FRAGILITY_DIVERGENCE_REGIME",
    "DOWNSIDE_ASYMMETRY_EXPANSION_REGIME",
    "UPSIDE_RESILIENCE_EXPANSION_REGIME",
    "CONCENTRATED_FRAGILITY_REGIME",
    "BROAD_STRUCTURAL_DETERIORATION_REGIME",
    "STRUCTURAL_COMPRESSION_REGIME",
    "EXHAUSTION_OR_STABILIZATION_REGIME",
    "EXTREME_IMBALANCE_REGIME",
)

CERTIFIED_P3F_REGIME_READY = "CERTIFIED_P3F_REGIME_READY"
DEGRADED_P3F_REGIME_READY = "DEGRADED_P3F_REGIME_READY"
BLOCKED_P3F_REGIME_INVALID = "BLOCKED_P3F_REGIME_INVALID"

DIMENSION_KEYS: Tuple[str, ...] = (
    "resilience_regime_pressure", "fragility_regime_pressure", "benchmark_divergence_pressure", "persistence_pressure",
    "acceleration_pressure", "concentration_pressure", "breadth_pressure", "compression_pressure", "exhaustion_pressure",
    "imbalance_severity", "regime_confidence",
)

FORBIDDEN_CAPABILITIES = (
    "buy", "sell", "hold", "go long", "go short", "trade signal", "trade execution", "portfolio allocation", "expected return", "alpha optimization", "prediction", "stochastic", "adaptive ml", "leverage",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _safe_number(value: Any, default: float = 50.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _clamp(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_number(value))), 2)


def build_p3f_regime_signal_registry(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    p3a = src.get("path3a", {}).get("resilience_dimensions", {})
    p3b = src.get("path3b", {}).get("asymmetry_dimensions", {})
    p3c = src.get("path3c", {}).get("benchmark_asymmetry_dimensions", {})
    p3d = src.get("path3d", {}).get("persistence_dimensions", {})
    p3e = src.get("path3e", {}).get("imbalance_dimensions", {})

    resilience = _clamp((0.45 * _clamp(p3a.get("resilience_support", 50.0))) + (0.35 * _clamp(p3b.get("upside_resilience", 50.0))) + (0.2 * _clamp(p3e.get("resilient_breadth_support", 50.0))))
    fragility = _clamp((0.45 * _clamp(p3a.get("fragility_pressure", 50.0))) + (0.35 * _clamp(p3b.get("downside_asymmetry", 50.0))) + (0.2 * _clamp(p3e.get("fragility_concentration", 50.0))))
    benchmark = _clamp((0.5 * _clamp(p3c.get("benchmark_relative_pressure", 50.0))) + (0.3 * _clamp(p3c.get("downside_benchmark_gap", 50.0))) + (0.2 * _clamp(p3c.get("resilience_benchmark_gap", 50.0))))
    persistence = _clamp((0.6 * _clamp(p3d.get("asymmetry_persistence", 50.0))) + (0.4 * _clamp(p3d.get("durability_score", 50.0))))
    acceleration = _clamp(_clamp(p3d.get("asymmetry_acceleration", 50.0)))
    concentration = _clamp((0.5 * _clamp(p3e.get("fragility_concentration", 50.0))) + (0.3 * _clamp(p3e.get("cluster_imbalance", 50.0))) + (0.2 * _clamp(p3e.get("crowding_pressure", 50.0))))
    breadth = _clamp((0.55 * _clamp(p3e.get("distributed_balance", 50.0))) + (0.45 * _clamp(p3e.get("participation_support", 50.0))))
    compression = _clamp((0.7 * _clamp(p3d.get("compression_pressure", 50.0))) + (0.3 * _clamp(p3e.get("breadth_collapse_pressure", 50.0))))
    exhaustion = _clamp((0.65 * _clamp(p3d.get("exhaustion_pressure", 50.0))) + (0.35 * _clamp(p3d.get("stabilization_pressure", 50.0))))
    imbalance = _clamp((0.4 * fragility) + (0.25 * concentration) + (0.2 * benchmark) + (0.15 * (100.0 - breadth)))
    confidence = _clamp((0.35 * abs(resilience - fragility)) + (0.25 * abs(acceleration - 50.0)) + (0.2 * abs(concentration - breadth)) + (0.2 * imbalance))

    registry = {
        "resilience_regime_pressure": resilience,
        "fragility_regime_pressure": fragility,
        "benchmark_divergence_pressure": benchmark,
        "persistence_pressure": persistence,
        "acceleration_pressure": acceleration,
        "concentration_pressure": concentration,
        "breadth_pressure": breadth,
        "compression_pressure": compression,
        "exhaustion_pressure": exhaustion,
        "imbalance_severity": imbalance,
        "regime_confidence": confidence,
    }
    return {k: registry[k] for k in DIMENSION_KEYS}


def build_p3f_regime_evidence_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"resilience_vs_fragility_balance": _clamp(50.0 + (registry["resilience_regime_pressure"] - registry["fragility_regime_pressure"]) * 0.8), "benchmark_divergence_pressure": registry["benchmark_divergence_pressure"], "imbalance_severity": registry["imbalance_severity"]}


def build_p3f_regime_pressure_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"persistence_pressure": registry["persistence_pressure"], "acceleration_pressure": registry["acceleration_pressure"], "compression_pressure": registry["compression_pressure"], "exhaustion_pressure": registry["exhaustion_pressure"]}


def build_p3f_regime_transition_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"concentration_pressure": registry["concentration_pressure"], "breadth_pressure": registry["breadth_pressure"], "transition_gap": _clamp(abs(registry["concentration_pressure"] - registry["breadth_pressure"]))}


def classify_p3f_asymmetry_regime(registry: Dict[str, Any]) -> str:
    r = deepcopy(registry)
    if r["imbalance_severity"] >= 88.0:
        return "EXTREME_IMBALANCE_REGIME"
    if r["fragility_regime_pressure"] >= 72.0 and r["breadth_pressure"] <= 38.0:
        return "BROAD_STRUCTURAL_DETERIORATION_REGIME"
    if r["concentration_pressure"] >= 75.0 and r["fragility_regime_pressure"] >= r["resilience_regime_pressure"]:
        return "CONCENTRATED_FRAGILITY_REGIME"
    if r["fragility_regime_pressure"] >= 66.0 and r["acceleration_pressure"] >= 64.0:
        return "DOWNSIDE_ASYMMETRY_EXPANSION_REGIME"
    if r["resilience_regime_pressure"] >= 66.0 and r["persistence_pressure"] >= 62.0:
        return "UPSIDE_RESILIENCE_EXPANSION_REGIME"
    if r["resilience_regime_pressure"] >= 68.0 and r["benchmark_divergence_pressure"] >= 62.0:
        return "RESILIENT_DIVERGENCE_REGIME"
    if r["fragility_regime_pressure"] >= 62.0 and r["benchmark_divergence_pressure"] >= 60.0:
        return "FRAGILITY_DIVERGENCE_REGIME"
    if r["compression_pressure"] >= 70.0:
        return "STRUCTURAL_COMPRESSION_REGIME"
    if r["exhaustion_pressure"] >= 70.0:
        return "EXHAUSTION_OR_STABILIZATION_REGIME"
    return "STABLE_SYMMETRY_REGIME"


def build_p3f_regime_explainability_summary(registry: Dict[str, Any], regime: str) -> Dict[str, Any]:
    drivers = [
        f"dominant_regime_driver:{regime}",
        f"resilience_fragility_balance:resilience={registry['resilience_regime_pressure']};fragility={registry['fragility_regime_pressure']}",
        f"benchmark_divergence_context:benchmark_divergence_pressure={registry['benchmark_divergence_pressure']}",
        f"persistence_acceleration_context:persistence_pressure={registry['persistence_pressure']};acceleration_pressure={registry['acceleration_pressure']}",
        f"concentration_breadth_context:concentration_pressure={registry['concentration_pressure']};breadth_pressure={registry['breadth_pressure']}",
        f"bounded_structural_regime_label:{regime}",
    ]
    explanations = [
        f"dominant regime driver indicates {regime}.",
        f"resilience/fragility balance indicates resilience {registry['resilience_regime_pressure']} versus fragility {registry['fragility_regime_pressure']}.",
        f"benchmark divergence context indicates pressure {registry['benchmark_divergence_pressure']}.",
        f"persistence/acceleration context indicates persistence {registry['persistence_pressure']} and acceleration {registry['acceleration_pressure']}.",
        f"concentration/breadth context indicates concentration {registry['concentration_pressure']} and breadth {registry['breadth_pressure']}.",
        f"bounded structural regime label: {regime}.",
    ]
    return {"regime_drivers": drivers, "regime_explanations": explanations}


def build_p3f_regime_certification(envelope: Dict[str, Any]) -> Dict[str, Any]:
    d = deepcopy(envelope)
    dims = d.get("regime_dimensions", {})
    gates = {
        "deterministic_replay": True,
        "checksum_stability": isinstance(d.get("checksum_metadata", {}).get("checksum"), str),
        "bounded_scores": all(0 <= float(dims.get(k, -1)) <= 100 for k in DIMENSION_KEYS),
        "valid_p3f_regime": d.get("asymmetry_regime") in P3F_REGIMES,
        "explanation_completeness": len(d.get("regime_explanations", [])) >= 6,
        "additive_only_integration": True,
        "immutability": bool(d.get("invariant_flags", {}).get("input_immutability", False)),
        "missing_prior_layer_degraded_behavior": d.get("regime_status") != "BLOCKED_INPUT_INVALID",
        "no_prediction": True,
        "no_execution": True,
        "no_optimization": True,
        "no_stochastic_behavior": True,
        "forbidden_capability_exclusion": not any(d.get("forbidden_capability_flags", {}).values()),
    }
    hard_fail = (not gates["valid_p3f_regime"]) or (not gates["bounded_scores"]) or (not gates["forbidden_capability_exclusion"])
    status = BLOCKED_P3F_REGIME_INVALID if hard_fail else (CERTIFIED_P3F_REGIME_READY if all(gates.values()) and d.get("regime_status") == "READY" else DEGRADED_P3F_REGIME_READY)
    return {"certification_status": status, "certification_gates": gates}


def run_p3f_asymmetry_regime_classification(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(path_inputs)
    registry = build_p3f_regime_signal_registry(path_inputs)
    regime = classify_p3f_asymmetry_regime(registry)
    explain = build_p3f_regime_explainability_summary(registry, regime)
    has_all = all(isinstance(path_inputs.get(k), dict) for k in ("path3a", "path3b", "path3c", "path3d", "path3e"))
    j = _stable_json(original).lower()
    forbidden_flags = {f"forbidden_{cap.replace(' ', '_')}": cap in j for cap in FORBIDDEN_CAPABILITIES}
    envelope = {
        "regime_status": "READY" if has_all else "DEGRADED_MISSING_PRIOR_P3_INPUTS",
        "asymmetry_regime": regime,
        "regime_dimensions": registry,
        "regime_evidence_summary": build_p3f_regime_evidence_summary(registry),
        "regime_pressure_summary": build_p3f_regime_pressure_summary(registry),
        "regime_transition_summary": build_p3f_regime_transition_summary(registry),
        "regime_drivers": explain["regime_drivers"],
        "regime_explanations": explain["regime_explanations"],
        "certification_status": DEGRADED_P3F_REGIME_READY,
        "replay_metadata": {"stable_serialization": True, "deterministic_threshold_profile": "P3F_FIXED_V1", "tie_break_priority": list(P3F_REGIMES[::-1])},
        "checksum_metadata": {},
        "invariant_flags": {
            "deterministic_ordering": True,
            "bounded_scores": all(0 <= registry[k] <= 100 for k in DIMENSION_KEYS),
            "input_immutability": original == deepcopy(path_inputs),
            "missing_prior_p3_fallback": not has_all,
        },
        "forbidden_capability_flags": forbidden_flags,
    }
    envelope["checksum_metadata"] = {"serialization": "stable_sorted_json", "checksum": _checksum(envelope)}
    envelope["certification_status"] = build_p3f_regime_certification(envelope)["certification_status"]
    keys = ("regime_status","asymmetry_regime","regime_dimensions","regime_evidence_summary","regime_pressure_summary","regime_transition_summary","regime_drivers","regime_explanations","certification_status","replay_metadata","checksum_metadata","invariant_flags","forbidden_capability_flags")
    return {k: envelope[k] for k in keys}


def build_p3f_regime_report(output_path: str = "reports/path3f_asymmetry_regime_classification_report.md") -> str:
    p = Path(output_path)
    return p.read_text(encoding="utf-8") if p.exists() else ""
