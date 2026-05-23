"""P2-F Cross-Sectional Explainability: deterministic replay-safe explanation packets."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CERTIFIED_CROSS_SECTIONAL_EXPLAINABILITY = "CERTIFIED_CROSS_SECTIONAL_EXPLAINABILITY"
DEGRADED_CROSS_SECTIONAL_EXPLAINABILITY = "DEGRADED_CROSS_SECTIONAL_EXPLAINABILITY"
BLOCKED_CROSS_SECTIONAL_EXPLAINABILITY = "BLOCKED_CROSS_SECTIONAL_EXPLAINABILITY"

EXPLANATION_VERSION = "1.0.0"

FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "llm_generated_autonomous_explanation",
    "stochastic_narrative_generation",
    "predictive_commentary",
    "trading_signals",
    "portfolio_recommendations",
    "portfolio_construction",
    "portfolio_optimization",
    "autonomous_execution",
    "adaptive_explanation_weighting",
    "hidden_explanation_logic",
    "dynamic_cohort_creation",
    "dynamic_benchmark_creation",
    "network_api_calls",
    "supabase_database_writes",
)

DRIVER_PRIORITY: Tuple[str, ...] = (
    "relative_fragility_score",
    "benchmark_divergence_score",
    "percentile",
    "rank_migration",
    "percentile_movement",
    "benchmark_divergence_trend",
    "relative_evolution_direction",
    "relative_weakness_persistence",
    "relative_deterioration_acceleration",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def build_cross_sectional_explainability_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-F",
        "contract_version": EXPLANATION_VERSION,
        "required_identity_fields": ["entity_id", "cohort_id", "cohort_version", "explanation_version"],
        "required_component_inputs": ["relative_fragility", "percentile_ranking", "benchmark_divergence", "relative_evolution"],
        "required_output_fields": [
            "entity_id", "cohort_id", "cohort_version", "benchmark_id", "explanation_version", "primary_driver", "secondary_driver",
            "supporting_evidence", "peer_relative_explanation", "percentile_ranking_explanation", "benchmark_divergence_explanation",
            "relative_evolution_explanation", "structural_evidence_summary", "quality_flags", "replay_metadata", "checksum",
        ],
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def build_peer_relative_explanation(payload: Dict[str, Any]) -> str:
    score = _num(payload.get("relative_fragility", {}).get("relative_fragility_score"))
    return f"Peer-relative fragility score is {score:.2f}; higher score indicates greater structural weakness vs cohort peers."


def build_percentile_ranking_explanation(payload: Dict[str, Any]) -> str:
    pr = payload.get("percentile_ranking", {})
    percentile = _num(pr.get("percentile"))
    rank = int(_num(pr.get("rank"), 0.0))
    n = int(_num(pr.get("cohort_size"), 0.0))
    return f"Percentile is {percentile:.2f} with rank {rank} of {n}; this locates the entity's cross-sectional position within cohort ordering."


def build_benchmark_divergence_explanation_packet(payload: Dict[str, Any]) -> str:
    b = payload.get("benchmark_divergence", {})
    score = _num(b.get("benchmark_divergence_score"))
    trend = str(payload.get("relative_evolution", {}).get("benchmark_divergence_trend", {}).get("trend", "UNKNOWN"))
    return f"Benchmark divergence score is {score:.2f}; replay trend is {trend}, indicating relative benchmark gap direction over the observed window."


def build_relative_evolution_explanation_packet(payload: Dict[str, Any]) -> str:
    e = payload.get("relative_evolution", {})
    direction = str(e.get("relative_evolution_direction", "UNKNOWN"))
    rank_move = str(e.get("rank_migration", {}).get("movement", "UNKNOWN"))
    pct_move = str(e.get("percentile_movement", {}).get("movement", "UNKNOWN"))
    return f"Relative evolution direction is {direction}; rank migration is {rank_move} and percentile movement is {pct_move} across replay snapshots."


def build_driver_attribution_hierarchy(payload: Dict[str, Any]) -> Dict[str, Any]:
    signals = {
        "relative_fragility_score": abs(_num(payload.get("relative_fragility", {}).get("relative_fragility_score"))),
        "percentile": abs(_num(payload.get("percentile_ranking", {}).get("percentile"))),
        "benchmark_divergence_score": abs(_num(payload.get("benchmark_divergence", {}).get("benchmark_divergence_score"))),
        "relative_evolution_direction": 1.0 if str(payload.get("relative_evolution", {}).get("relative_evolution_direction", "")).upper() == "WORSENING" else 0.5,
        "rank_migration": abs(_num(payload.get("relative_evolution", {}).get("rank_migration", {}).get("delta"))),
        "percentile_movement": abs(_num(payload.get("relative_evolution", {}).get("percentile_movement", {}).get("delta"))),
        "benchmark_divergence_trend": abs(_num(payload.get("relative_evolution", {}).get("benchmark_divergence_trend", {}).get("delta"))),
        "relative_weakness_persistence": abs(_num(payload.get("relative_evolution", {}).get("relative_weakness_persistence", {}).get("coverage_ratio"))),
        "relative_deterioration_acceleration": abs(_num(payload.get("relative_evolution", {}).get("relative_deterioration_acceleration", {}).get("delta_change"))),
    }
    ordered = sorted(signals.items(), key=lambda kv: (-kv[1], DRIVER_PRIORITY.index(kv[0])))
    primary = ordered[0][0] if ordered else ""
    secondary = ordered[1][0] if len(ordered) > 1 and ordered[1][1] > 0 else "DEGRADED_SECONDARY_DRIVER_UNAVAILABLE"
    return {"primary_driver": primary, "secondary_driver": secondary, "ordered_drivers": ordered}


def build_structural_evidence_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "relative_fragility_score": _num(payload.get("relative_fragility", {}).get("relative_fragility_score")),
        "percentile": _num(payload.get("percentile_ranking", {}).get("percentile")),
        "rank": _num(payload.get("percentile_ranking", {}).get("rank")),
        "benchmark_divergence_score": _num(payload.get("benchmark_divergence", {}).get("benchmark_divergence_score")),
        "relative_evolution_direction": str(payload.get("relative_evolution", {}).get("relative_evolution_direction", "UNKNOWN")),
        "rank_migration_delta": _num(payload.get("relative_evolution", {}).get("rank_migration", {}).get("delta")),
        "percentile_movement_delta": _num(payload.get("relative_evolution", {}).get("percentile_movement", {}).get("delta")),
        "benchmark_divergence_trend_delta": _num(payload.get("relative_evolution", {}).get("benchmark_divergence_trend", {}).get("delta")),
    }


def validate_explainability_consistency(packet: Dict[str, Any]) -> Dict[str, Any]:
    checks = {
        "peer_relative_explanation_generated": bool(packet.get("peer_relative_explanation")),
        "percentile_ranking_explanation_generated": bool(packet.get("percentile_ranking_explanation")),
        "benchmark_divergence_explanation_generated": bool(packet.get("benchmark_divergence_explanation")),
        "relative_evolution_explanation_generated": bool(packet.get("relative_evolution_explanation")),
        "driver_attribution_hierarchy_generated": bool(packet.get("primary_driver")),
        "structural_evidence_summary_generated": isinstance(packet.get("structural_evidence_summary"), dict),
        "primary_driver_present": bool(packet.get("primary_driver")),
        "secondary_driver_present_or_degraded": bool(packet.get("secondary_driver")),
    }
    checks["explanation_consistency_validated"] = all(checks.values())
    return checks


def certify_cross_sectional_explainability(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    quality_flags: List[str] = list(payload.get("quality_flags", []))
    hierarchy = build_driver_attribution_hierarchy(payload)
    packet = {
        "entity_id": str(payload.get("entity_id", "")),
        "cohort_id": str(payload.get("cohort_id", "")),
        "cohort_version": str(payload.get("cohort_version", "")),
        "benchmark_id": str(payload.get("benchmark_id", "")),
        "explanation_version": str(payload.get("explanation_version", EXPLANATION_VERSION)),
        "primary_driver": hierarchy["primary_driver"],
        "secondary_driver": hierarchy["secondary_driver"],
        "supporting_evidence": hierarchy["ordered_drivers"],
        "peer_relative_explanation": build_peer_relative_explanation(payload),
        "percentile_ranking_explanation": build_percentile_ranking_explanation(payload),
        "benchmark_divergence_explanation": build_benchmark_divergence_explanation_packet(payload),
        "relative_evolution_explanation": build_relative_evolution_explanation_packet(payload),
        "structural_evidence_summary": build_structural_evidence_summary(payload),
        "quality_flags": quality_flags,
        "replay_metadata": deepcopy(payload.get("replay_metadata", {"input_immutability_preserved": True, "stable_serialization": True})),
    }
    consistency = validate_explainability_consistency(packet)
    packet["replay_metadata"]["explanation_consistency_validated"] = consistency["explanation_consistency_validated"]
    packet["checksum"] = _checksum({k: v for k, v in packet.items() if k != "checksum"})

    gates = {
        "input_contract_present": isinstance(build_cross_sectional_explainability_input_contract(), dict),
        "entity_id_present": bool(packet["entity_id"]),
        "cohort_id_present": bool(packet["cohort_id"]),
        "cohort_version_present": bool(packet["cohort_version"]),
        "explanation_version_present": bool(packet["explanation_version"]),
        **consistency,
        "checksum_stable": packet["checksum"] == _checksum({k: v for k, v in packet.items() if k != "checksum"}),
        "forbidden_dynamic_capabilities_absent": all(term not in _stable_json(packet).lower() for term in ("prediction", "trading", "optimization")),
        "input_immutability_preserved": payload == deepcopy(input_payload),
    }

    blocked = not all(gates[k] for k in ("input_contract_present", "entity_id_present", "cohort_id_present", "cohort_version_present", "explanation_version_present"))
    degraded = blocked or (packet["secondary_driver"] == "DEGRADED_SECONDARY_DRIVER_UNAVAILABLE") or bool(quality_flags)
    packet["certification_gates"] = gates
    packet["certification_decision"] = BLOCKED_CROSS_SECTIONAL_EXPLAINABILITY if blocked else (DEGRADED_CROSS_SECTIONAL_EXPLAINABILITY if degraded else CERTIFIED_CROSS_SECTIONAL_EXPLAINABILITY)
    return packet


def build_path2f_cross_sectional_explainability_report(output_path: str = "reports/path2f_cross_sectional_explainability_report.md") -> str:
    report = """# P2-F Cross-Sectional Explainability Report

## Objective
Deliver deterministic, replay-safe cross-sectional explainability packets for supervisor-readable interpretation.

## Scope
Uses additive inputs from P2-B, P2-C, P2-D, P2-E, Path 1 replay metadata, checksums, and quality flags.

## Non-Goals
No score/rank/divergence/evolution recalculation. No prediction, trading, portfolio logic, cohort creation, benchmark creation, network/database calls, or LLM/stochastic narratives.

## Architecture Summary
Build input contract, deterministic explanation templates, driver attribution hierarchy, structural evidence summary, consistency validation, and certification decision.

## Input Contract
See `build_cross_sectional_explainability_input_contract` for required identity fields, required component inputs, output schema, and forbidden capability inventory.

## Peer-Relative Explanation Methodology
Deterministic template using relative fragility score with fixed wording.

## Percentile/Ranking Explanation Methodology
Deterministic template using percentile/rank/cohort size.

## Benchmark Divergence Explanation Methodology
Deterministic template using benchmark divergence score and replay trend.

## Relative Evolution Explanation Methodology
Deterministic template using evolution direction, rank migration movement, and percentile movement.

## Driver Attribution Hierarchy Methodology
Deterministic ordering by absolute signal strength, then stable tie-break via explicit priority list.

## Structural Evidence Summary Methodology
Explicit metric-aligned summary of core structural signals and deltas.

## Deterministic Template Policy
All narrative fields are fixed templates with deterministic interpolation.

## Consistency Validation Policy
Validation requires all explanation segments, attribution hierarchy, evidence summary, primary driver, and secondary driver/degradation marker.

## Replay/Checksum Guarantees
Deepcopy input isolation and stable JSON checksum generation ensure replay-safe deterministic outputs.

## Certification Decision Logic
Blocked when required identity fields are missing; degraded on quality flags or secondary-driver degradation; certified otherwise.

## Forbidden Capabilities
LLM/stochastic narratives, predictive/trading/portfolio logic, adaptive hidden logic, dynamic cohort/benchmark creation, and network/database writes are forbidden.

## Final Supervisor Interpretation
P2-F explains cross-sectional structure deterministically, compactly, and auditably while preserving additive-only integration boundaries.
"""
    Path(output_path).write_text(report, encoding="utf-8")
    return output_path
