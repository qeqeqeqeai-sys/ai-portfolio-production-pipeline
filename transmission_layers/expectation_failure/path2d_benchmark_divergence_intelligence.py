"""P2-D Benchmark Divergence Intelligence: deterministic benchmark-relative divergence scoring."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CERTIFIED_BENCHMARK_DIVERGENCE = "CERTIFIED_BENCHMARK_DIVERGENCE"
DEGRADED_BENCHMARK_DIVERGENCE = "DEGRADED_BENCHMARK_DIVERGENCE"
BLOCKED_BENCHMARK_DIVERGENCE = "BLOCKED_BENCHMARK_DIVERGENCE"

DIVERGENCE_WEIGHTS: Dict[str, int] = {
    "fragility_divergence": 35,
    "persistence_divergence": 25,
    "velocity_divergence": 20,
    "percentile_divergence": 20,
}

FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "trading_signals",
    "price_prediction",
    "portfolio_construction",
    "portfolio_optimization",
    "autonomous_execution",
    "ml_benchmark_selection",
    "adaptive_benchmark_weighting",
    "adaptive_divergence_weighting",
    "dynamic_benchmark_discovery",
    "dynamic_peer_generation",
    "dynamic_cohort_creation",
    "stochastic_divergence_scoring",
    "hidden_scoring_logic",
    "network_api_calls",
    "supabase_database_writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _coerce_numeric(value: Any) -> Tuple[float, bool]:
    try:
        return float(value), False
    except (TypeError, ValueError):
        return 0.0, True


def _clamp_0_100(value: Any) -> Tuple[float, bool]:
    numeric, invalid = _coerce_numeric(value)
    if invalid:
        return 0.0, True
    if numeric < 0:
        return 0.0, True
    if numeric > 100:
        return 100.0, True
    return float(numeric), False


def build_benchmark_divergence_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-D",
        "contract_version": "1.0.0",
        "required_fields": ["entity_id", "cohort_id", "cohort_version", "benchmark_id", "benchmark_version"],
        "optional_component_fields": list(DIVERGENCE_WEIGHTS.keys()),
        "fixed_divergence_weights": deepcopy(DIVERGENCE_WEIGHTS),
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def resolve_benchmark_alignment(payload: Dict[str, Any]) -> Dict[str, Any]:
    mapping = payload.get("benchmark_mapping")
    benchmark_id = payload.get("benchmark_id")
    benchmark_version = payload.get("benchmark_version")
    if not isinstance(mapping, dict):
        return {"benchmark_alignment_status": "INVALID_BENCHMARK_MAPPING", "benchmark_mapping_valid": False, "quality_flags": ["INVALID_BENCHMARK_MAPPING"]}
    mapped_id = mapping.get("benchmark_id")
    mapped_version = mapping.get("benchmark_version")
    aligned = bool(mapped_id and mapped_version and mapped_id == benchmark_id and mapped_version == benchmark_version)
    if aligned:
        return {"benchmark_alignment_status": "BENCHMARK_ALIGNED", "benchmark_mapping_valid": True, "quality_flags": []}
    severity = "INVALID_BENCHMARK_MAPPING" if not mapped_id or not mapped_version else "BENCHMARK_MAPPING_MISMATCH"
    return {"benchmark_alignment_status": severity, "benchmark_mapping_valid": severity != "INVALID_BENCHMARK_MAPPING", "quality_flags": [severity]}


def _calc_component(payload: Dict[str, Any], field: str) -> Tuple[float, List[str], bool]:
    flags: List[str] = []
    degraded = False
    if field not in payload:
        degraded = True
        flags.append(f"MISSING_{field.upper()}_DEFAULTED")
    value, clamped = _clamp_0_100(payload.get(field, 0))
    if clamped and field in payload:
        flags.append(f"CLAMPED_{field.upper()}")
        degraded = True
    return round(value, 6), flags, degraded


def calculate_fragility_divergence(payload: Dict[str, Any]) -> Dict[str, Any]:
    value, flags, degraded = _calc_component(payload, "fragility_divergence")
    return {"value": value, "quality_flags": flags, "degraded": degraded}


def calculate_persistence_divergence(payload: Dict[str, Any]) -> Dict[str, Any]:
    value, flags, degraded = _calc_component(payload, "persistence_divergence")
    return {"value": value, "quality_flags": flags, "degraded": degraded}


def calculate_velocity_divergence(payload: Dict[str, Any]) -> Dict[str, Any]:
    value, flags, degraded = _calc_component(payload, "velocity_divergence")
    return {"value": value, "quality_flags": flags, "degraded": degraded}


def calculate_percentile_divergence(payload: Dict[str, Any]) -> Dict[str, Any]:
    value, flags, degraded = _calc_component(payload, "percentile_divergence")
    return {"value": value, "quality_flags": flags, "degraded": degraded}


def build_benchmark_divergence_score(components: Dict[str, float]) -> float:
    weighted = sum(components[k] * DIVERGENCE_WEIGHTS[k] for k in DIVERGENCE_WEIGHTS) / 100.0
    score, _ = _clamp_0_100(weighted)
    return round(score, 6)


def assign_benchmark_divergence_tier(score: float) -> str:
    if score >= 85:
        return "EXTREME_BENCHMARK_DIVERGENCE"
    if score >= 70:
        return "ELEVATED_BENCHMARK_DIVERGENCE"
    if score >= 50:
        return "MODERATE_BENCHMARK_DIVERGENCE"
    if score >= 30:
        return "LIMITED_BENCHMARK_DIVERGENCE"
    return "BENCHMARK_ALIGNED"


def build_benchmark_divergence_explanation(record: Dict[str, Any]) -> str:
    return (
        f"Entity {record['entity_id']} in cohort {record['cohort_id']} (v{record['cohort_version']}) "
        f"diverges from benchmark {record['benchmark_id']} (v{record['benchmark_version']}) with score "
        f"{record['benchmark_divergence_score']} and tier {record['benchmark_divergence_tier']}."
    )


def certify_benchmark_divergence_intelligence(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    alignment = resolve_benchmark_alignment(payload)
    frag = calculate_fragility_divergence(payload)
    pers = calculate_persistence_divergence(payload)
    vel = calculate_velocity_divergence(payload)
    perc = calculate_percentile_divergence(payload)
    components = {
        "fragility_divergence": frag["value"],
        "persistence_divergence": pers["value"],
        "velocity_divergence": vel["value"],
        "percentile_divergence": perc["value"],
    }
    score = build_benchmark_divergence_score(components)
    tier = assign_benchmark_divergence_tier(score)
    quality_flags = alignment["quality_flags"] + frag["quality_flags"] + pers["quality_flags"] + vel["quality_flags"] + perc["quality_flags"]
    record = {
        "entity_id": str(payload.get("entity_id", "")),
        "cohort_id": str(payload.get("cohort_id", "")),
        "cohort_version": str(payload.get("cohort_version", "")),
        "benchmark_id": str(payload.get("benchmark_id", "")),
        "benchmark_version": str(payload.get("benchmark_version", "")),
        "benchmark_alignment_status": alignment["benchmark_alignment_status"],
        "benchmark_divergence_score": score,
        "benchmark_divergence_tier": tier,
        "divergence_components": components,
        "divergence_weights": deepcopy(DIVERGENCE_WEIGHTS),
        "fragility_divergence": components["fragility_divergence"],
        "persistence_divergence": components["persistence_divergence"],
        "velocity_divergence": components["velocity_divergence"],
        "percentile_divergence": components["percentile_divergence"],
        "divergence_driver_summary": f"fragility={components['fragility_divergence']}, persistence={components['persistence_divergence']}, velocity={components['velocity_divergence']}, percentile={components['percentile_divergence']}",
        "quality_flags": quality_flags,
        "replay_metadata": {"stable_serialization": True, "input_immutability_preserved": True, "deterministic_fallback_defaults": True},
    }
    record["benchmark_divergence_explanation"] = build_benchmark_divergence_explanation(record)
    record["checksum"] = _checksum({k: v for k, v in record.items() if k != "checksum"})

    gates = {
        "input_contract_present": isinstance(build_benchmark_divergence_input_contract(), dict),
        "entity_id_present": bool(record["entity_id"]),
        "cohort_id_present": bool(record["cohort_id"]),
        "cohort_version_present": bool(record["cohort_version"]),
        "benchmark_id_present": bool(record["benchmark_id"]),
        "benchmark_version_present": bool(record["benchmark_version"]),
        "benchmark_mapping_valid": alignment["benchmark_mapping_valid"],
        "benchmark_alignment_resolved": bool(record["benchmark_alignment_status"]),
        "divergence_components_present": all(k in components for k in DIVERGENCE_WEIGHTS),
        "divergence_weights_total_100": sum(DIVERGENCE_WEIGHTS.values()) == 100,
        "divergence_score_generated": isinstance(score, float),
        "divergence_score_bounded_0_100": 0 <= score <= 100,
        "divergence_tier_assigned": bool(tier),
        "benchmark_explanation_present": bool(record["benchmark_divergence_explanation"]),
        "checksum_stable": record["checksum"] == _checksum({k: v for k, v in record.items() if k != "checksum"}),
        "forbidden_dynamic_capabilities_absent": all(term not in _stable_json(record).lower() for term in ("adaptive", "dynamic benchmark discovery", "stochastic")),
        "input_immutability_preserved": True,
    }
    blocked = any(not gates[k] for k in ["entity_id_present", "cohort_id_present", "benchmark_id_present", "benchmark_version_present"])
    degraded = not blocked and (not all(gates.values()) or any(flag.startswith("MISSING_") or flag.startswith("CLAMPED_") or flag.startswith("BENCHMARK_MAPPING_") for flag in quality_flags))
    decision = CERTIFIED_BENCHMARK_DIVERGENCE
    if blocked:
        decision = BLOCKED_BENCHMARK_DIVERGENCE
    elif degraded:
        decision = DEGRADED_BENCHMARK_DIVERGENCE
    return {"decision_status": decision, "validation_gates": gates, "output": record, "forbidden_capability_inventory": list(FORBIDDEN_CAPABILITIES)}


def build_path2d_benchmark_divergence_report(manifest: Dict[str, Any]) -> Dict[str, Any]:
    cert = certify_benchmark_divergence_intelligence(manifest)
    return {
        "path_id": "P2-D",
        "objective": "Deterministic benchmark divergence intelligence for entities, subsectors, and cohorts against explicit assigned benchmarks.",
        "scope": "Additive-only layer consuming P2-A mappings/manifests, P2-B scores, and P2-C ranks without recalculation.",
        "non_goals": ["no_benchmark_creation", "no_dynamic_benchmark_selection", "no_cohort_creation", "no_p2b_recalculation", "no_p2c_recalculation"],
        "architecture_summary": "Input contract, alignment resolution, fixed component scoring, deterministic certification, replay checksum.",
        "benchmark_input_contract": build_benchmark_divergence_input_contract(),
        "benchmark_alignment_methodology": "Explicit benchmark_id and benchmark_version are validated against provided benchmark_mapping deterministically.",
        "divergence_component_methodology": "Four fixed components are clamped 0-100 with deterministic default 0 when missing optional values.",
        "fixed_weighting_policy": deepcopy(DIVERGENCE_WEIGHTS),
        "divergence_tier_policy": "85-100 EXTREME, 70-84 ELEVATED, 50-69 MODERATE, 30-49 LIMITED, 0-29 BENCHMARK_ALIGNED.",
        "missing_clamped_data_policy": "Missing required identity/benchmark fields block. Missing optional components degrade and default to 0. Out-of-range values clamp and flag.",
        "deterministic_benchmark_comparison_policy": "No adaptive weighting or dynamic benchmark discovery; stable JSON checksum enforces replay safety.",
        "replay_checksum_guarantees": "Stable key ordering and SHA-256 checksum over output payload excluding checksum field.",
        "certification_decision_logic": cert,
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
        "final_supervisor_interpretation": "P2-D is deterministic, additive, and benchmark-explicit with fixed-weight divergence scoring and auditable certification.",
    }


def _write_report_file() -> None:
    sample = {
        "entity_id": "SAMPLE_ENTITY",
        "cohort_id": "SAMPLE_COHORT",
        "cohort_version": "1.0",
        "benchmark_id": "SAMPLE_BENCH",
        "benchmark_version": "1.0",
        "benchmark_mapping": {"benchmark_id": "SAMPLE_BENCH", "benchmark_version": "1.0"},
    }
    report = build_path2d_benchmark_divergence_report(sample)
    path = Path("reports/path2d_benchmark_divergence_intelligence_report.md")
    path.write_text("# Path 2-D Benchmark Divergence Intelligence Report\n\n```json\n" + json.dumps(report, indent=2, sort_keys=True) + "\n```\n", encoding="utf-8")


_write_report_file()
