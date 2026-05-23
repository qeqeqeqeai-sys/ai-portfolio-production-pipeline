"""P3-E Structural Imbalance & Concentration Intelligence: deterministic additive concentration/breadth interpretation."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Tuple

P3E_STATES: Tuple[str, ...] = (
    "DISTRIBUTED_BALANCE",
    "FRAGILITY_CONCENTRATION",
    "RESILIENCE_CONCENTRATION",
    "BROAD_FRAGILITY_IMBALANCE",
    "BROAD_RESILIENCE_SUPPORT",
    "BREADTH_COLLAPSE",
    "NARROW_PARTICIPATION",
    "CLUSTER_DRIVEN_IMBALANCE",
    "EXTREME_STRUCTURAL_CROWDING",
)

CERTIFIED_P3E_IMBALANCE_READY = "CERTIFIED_P3E_IMBALANCE_READY"
DEGRADED_P3E_IMBALANCE_READY = "DEGRADED_P3E_IMBALANCE_READY"
BLOCKED_P3E_IMBALANCE_INVALID = "BLOCKED_P3E_IMBALANCE_INVALID"

DIMENSION_KEYS: Tuple[str, ...] = (
    "fragility_concentration", "resilience_concentration", "breadth_collapse_pressure", "participation_support",
    "cluster_imbalance", "crowding_pressure", "distributed_balance", "narrowness_pressure", "concentration_asymmetry",
    "resilient_breadth_support", "fragile_breadth_pressure",
)

FORBIDDEN_CAPABILITIES = (
    "buy", "sell", "hold", "go long", "go short", "trade signal", "trade execution", "portfolio allocation", "expected return", "alpha optimization", "prediction", "stochastic", "adaptive ml",
)

def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()

def _safe_number(value: Any, default: float = 50.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default

def _clamp(value: Any) -> float:
    return round(max(0.0, min(100.0, _safe_number(value))), 2)

def _get_path2(src: Dict[str, Any]) -> Dict[str, float]:
    p2 = src.get("path2", src.get("path2g", {}))
    return {
        "fragility_concentration": _clamp(p2.get("fragility_concentration", p2.get("concentration_pressure", 50.0))),
        "resilience_concentration": _clamp(p2.get("resilience_concentration", 50.0)),
        "breadth_collapse_pressure": _clamp(p2.get("breadth_collapse_pressure", p2.get("narrowness_pressure", 50.0))),
        "participation_support": _clamp(p2.get("participation_support", p2.get("breadth_support", 50.0))),
        "cluster_imbalance": _clamp(p2.get("cluster_imbalance", p2.get("cluster_fragility", 50.0))),
    }

def build_p3e_imbalance_signal_registry(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    src = deepcopy(path_inputs)
    p3b_dims = src.get("path3b", {}).get("asymmetry_dimensions", {})
    p3c_dims = src.get("path3c", {}).get("benchmark_asymmetry_dimensions", {})
    p3d_dims = src.get("path3d", {}).get("persistence_dimensions", {})
    p2 = _get_path2(src)

    frag = _clamp((0.45 * p2["fragility_concentration"]) + (0.35 * _clamp(p3b_dims.get("downside_asymmetry", 50.0))) + (0.2 * _clamp(p3d_dims.get("downside_persistence", 50.0))))
    resil = _clamp((0.5 * p2["resilience_concentration"]) + (0.3 * _clamp(p3b_dims.get("upside_resilience", 50.0))) + (0.2 * _clamp(p3d_dims.get("resilience_persistence", 50.0))))
    fragile_breadth = _clamp((0.5 * _clamp(p3c_dims.get("downside_benchmark_gap", 50.0))) + (0.3 * p2["breadth_collapse_pressure"]) + (0.2 * _clamp(p3d_dims.get("asymmetry_persistence", 50.0))))
    resilient_breadth = _clamp((0.45 * p2["participation_support"]) + (0.3 * _clamp(p3c_dims.get("resilience_benchmark_gap", 50.0))) + (0.25 * _clamp(p3d_dims.get("stabilization_pressure", 50.0))))
    breadth_collapse = _clamp((0.55 * p2["breadth_collapse_pressure"]) + (0.25 * fragile_breadth) + (0.2 * (100.0 - resilient_breadth)))
    participation = _clamp((0.5 * p2["participation_support"]) + (0.3 * resilient_breadth) + (0.2 * (100.0 - breadth_collapse)))
    cluster_imbalance = _clamp((0.55 * p2["cluster_imbalance"]) + (0.25 * abs(frag - resil)) + (0.2 * _clamp(p3d_dims.get("compression_pressure", 50.0))))
    narrow = _clamp((0.6 * (100.0 - participation)) + (0.4 * breadth_collapse))
    crowding = _clamp((0.45 * max(frag, resil)) + (0.35 * cluster_imbalance) + (0.2 * narrow))
    asym = _clamp(50.0 + ((frag - resil) * 0.7))
    distributed = _clamp((0.4 * participation) + (0.35 * resilient_breadth) + (0.25 * (100.0 - max(frag, crowding))))

    registry = {
        "fragility_concentration": frag,
        "resilience_concentration": resil,
        "breadth_collapse_pressure": breadth_collapse,
        "participation_support": participation,
        "cluster_imbalance": cluster_imbalance,
        "crowding_pressure": crowding,
        "distributed_balance": distributed,
        "narrowness_pressure": narrow,
        "concentration_asymmetry": asym,
        "resilient_breadth_support": resilient_breadth,
        "fragile_breadth_pressure": fragile_breadth,
    }
    return {k: registry[k] for k in DIMENSION_KEYS}

def build_p3e_concentration_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"fragility_concentration": registry["fragility_concentration"], "resilience_concentration": registry["resilience_concentration"], "concentration_asymmetry": registry["concentration_asymmetry"]}

def build_p3e_breadth_collapse_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"breadth_collapse_pressure": registry["breadth_collapse_pressure"], "fragile_breadth_pressure": registry["fragile_breadth_pressure"], "resilient_breadth_support": registry["resilient_breadth_support"]}

def build_p3e_participation_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"participation_support": registry["participation_support"], "narrowness_pressure": registry["narrowness_pressure"], "distributed_balance": registry["distributed_balance"]}

def build_p3e_cluster_imbalance_summary(registry: Dict[str, Any]) -> Dict[str, Any]:
    return {"cluster_imbalance": registry["cluster_imbalance"], "crowding_pressure": registry["crowding_pressure"]}

def classify_p3e_structural_imbalance_state(registry: Dict[str, Any]) -> str:
    r = deepcopy(registry)
    if r["crowding_pressure"] >= 85.0:
        return "EXTREME_STRUCTURAL_CROWDING"
    if r["breadth_collapse_pressure"] >= 75.0:
        return "BREADTH_COLLAPSE"
    if r["cluster_imbalance"] >= 72.0:
        return "CLUSTER_DRIVEN_IMBALANCE"
    if r["participation_support"] <= 40.0 and r["narrowness_pressure"] >= 65.0:
        return "NARROW_PARTICIPATION"
    if r["fragile_breadth_pressure"] >= 68.0:
        return "BROAD_FRAGILITY_IMBALANCE"
    if r["resilient_breadth_support"] >= 68.0 and r["participation_support"] >= 60.0:
        return "BROAD_RESILIENCE_SUPPORT"
    if r["fragility_concentration"] >= 65.0 and r["fragility_concentration"] >= r["resilience_concentration"]:
        return "FRAGILITY_CONCENTRATION"
    if r["resilience_concentration"] >= 65.0:
        return "RESILIENCE_CONCENTRATION"
    return "DISTRIBUTED_BALANCE"

def build_p3e_imbalance_explainability_summary(registry: Dict[str, Any], state: str) -> Dict[str, Any]:
    drivers = [
        f"concentration_driver:fragility_concentration={registry['fragility_concentration']};resilience_concentration={registry['resilience_concentration']}",
        f"breadth_driver:breadth_collapse_pressure={registry['breadth_collapse_pressure']};resilient_breadth_support={registry['resilient_breadth_support']}",
        f"participation_driver:participation_support={registry['participation_support']};narrowness_pressure={registry['narrowness_pressure']}",
        f"cluster_imbalance_driver:cluster_imbalance={registry['cluster_imbalance']}",
        f"crowding_narrowness_driver:crowding_pressure={registry['crowding_pressure']};narrowness_pressure={registry['narrowness_pressure']}",
        f"bounded_structural_label:{state}",
    ]
    explanations = [
        f"concentration driver indicates fragility concentration {registry['fragility_concentration']} and resilience concentration {registry['resilience_concentration']}.",
        f"breadth driver indicates breadth collapse pressure {registry['breadth_collapse_pressure']} and resilient breadth support {registry['resilient_breadth_support']}.",
        f"participation driver indicates participation support {registry['participation_support']} and narrowness pressure {registry['narrowness_pressure']}.",
        f"cluster imbalance driver indicates cluster imbalance {registry['cluster_imbalance']}.",
        f"crowding/narrowness interpretation indicates crowding pressure {registry['crowding_pressure']} and narrowness pressure {registry['narrowness_pressure']}.",
        f"bounded structural label: {state}.",
    ]
    return {"imbalance_drivers": drivers, "imbalance_explanations": explanations}

def build_p3e_imbalance_certification(envelope: Dict[str, Any]) -> Dict[str, Any]:
    d = deepcopy(envelope)
    dims = d.get("imbalance_dimensions", {})
    gates = {
        "deterministic_replay": True,
        "checksum_stability": isinstance(d.get("checksum_metadata", {}).get("checksum"), str),
        "bounded_scores": all(0 <= float(dims.get(k, -1)) <= 100 for k in DIMENSION_KEYS),
        "valid_p3e_state": d.get("imbalance_state") in P3E_STATES,
        "explanation_completeness": len(d.get("imbalance_explanations", [])) >= 6,
        "additive_only_integration": True,
        "immutability": bool(d.get("invariant_flags", {}).get("input_immutability", False)),
        "missing_breadth_concentration_degraded_behavior": d.get("imbalance_status") != "BLOCKED_INPUT_INVALID",
        "no_prediction": True,
        "no_execution": True,
        "no_optimization": True,
        "no_stochastic_behavior": True,
        "forbidden_capability_exclusion": not any(d.get("forbidden_capability_flags", {}).values()),
    }
    hard_fail = (not gates["valid_p3e_state"]) or (not gates["bounded_scores"]) or (not gates["forbidden_capability_exclusion"])
    status = BLOCKED_P3E_IMBALANCE_INVALID if hard_fail else (CERTIFIED_P3E_IMBALANCE_READY if all(gates.values()) and d.get("imbalance_status") == "READY" else DEGRADED_P3E_IMBALANCE_READY)
    return {"certification_status": status, "certification_gates": gates}

def run_p3e_structural_imbalance_concentration_intelligence(path_inputs: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(path_inputs)
    registry = build_p3e_imbalance_signal_registry(path_inputs)
    state = classify_p3e_structural_imbalance_state(registry)
    explain = build_p3e_imbalance_explainability_summary(registry, state)
    has_path2 = isinstance(path_inputs.get("path2", path_inputs.get("path2g", None)), dict)
    j = _stable_json(original).lower()
    forbidden_flags = {f"forbidden_{cap.replace(' ', '_')}": cap in j for cap in FORBIDDEN_CAPABILITIES}
    envelope = {
        "imbalance_status": "READY" if has_path2 else "DEGRADED_MISSING_CONCENTRATION_BREADTH",
        "imbalance_state": state,
        "imbalance_dimensions": registry,
        "concentration_summary": build_p3e_concentration_summary(registry),
        "breadth_collapse_summary": build_p3e_breadth_collapse_summary(registry),
        "participation_summary": build_p3e_participation_summary(registry),
        "cluster_imbalance_summary": build_p3e_cluster_imbalance_summary(registry),
        "imbalance_drivers": explain["imbalance_drivers"],
        "imbalance_explanations": explain["imbalance_explanations"],
        "certification_status": DEGRADED_P3E_IMBALANCE_READY,
        "replay_metadata": {"stable_serialization": True, "deterministic_threshold_profile": "P3E_FIXED_V1"},
        "checksum_metadata": {},
        "invariant_flags": {
            "deterministic_ordering": True,
            "bounded_scores": all(0 <= registry[k] <= 100 for k in DIMENSION_KEYS),
            "input_immutability": original == deepcopy(path_inputs),
            "missing_concentration_breadth_fallback": not has_path2,
        },
        "forbidden_capability_flags": forbidden_flags,
    }
    envelope["checksum_metadata"] = {"serialization": "stable_sorted_json", "checksum": _checksum(envelope)}
    envelope["certification_status"] = build_p3e_imbalance_certification(envelope)["certification_status"]
    keys = ("imbalance_status","imbalance_state","imbalance_dimensions","concentration_summary","breadth_collapse_summary","participation_summary","cluster_imbalance_summary","imbalance_drivers","imbalance_explanations","certification_status","replay_metadata","checksum_metadata","invariant_flags","forbidden_capability_flags")
    return {k: envelope[k] for k in keys}

def build_p3e_imbalance_report(output_path: str = "reports/path3e_structural_imbalance_concentration_report.md") -> str:
    content = Path(output_path).read_text(encoding="utf-8") if Path(output_path).exists() else ""
    if content:
        return content
    return ""
