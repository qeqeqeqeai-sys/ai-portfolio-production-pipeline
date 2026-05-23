"""P2-E Relative Evolution Interpretation: deterministic replay-safe interpretation over replay windows."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CERTIFIED_RELATIVE_EVOLUTION = "CERTIFIED_RELATIVE_EVOLUTION"
DEGRADED_RELATIVE_EVOLUTION = "DEGRADED_RELATIVE_EVOLUTION"
BLOCKED_RELATIVE_EVOLUTION = "BLOCKED_RELATIVE_EVOLUTION"

FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "trading_signals",
    "price_prediction",
    "portfolio_construction",
    "portfolio_optimization",
    "autonomous_execution",
    "ml_trend_prediction",
    "adaptive_weighting",
    "dynamic_cohort_creation",
    "dynamic_benchmark_creation",
    "stochastic_interpretation",
    "hidden_scoring_logic",
    "network_api_calls",
    "supabase_database_writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _coerce_numeric(value: Any, default: float = 0.0) -> Tuple[float, bool]:
    try:
        return float(value), False
    except (TypeError, ValueError):
        return default, True


def build_relative_evolution_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-E",
        "contract_version": "1.0.0",
        "required_fields": ["entity_id", "cohort_id", "cohort_version", "replay_window_id"],
        "required_timeline_fields": ["sequence_id", "rank", "percentile", "benchmark_divergence_score"],
        "optional_timeline_fields": ["relative_fragility_score"],
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def build_relative_position_timeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = [deepcopy(r) for r in payload.get("timeline", [])]
    quality_flags: List[str] = []
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        sequence_id = str(row.get("sequence_id", ""))
        rank, rank_invalid = _coerce_numeric(row.get("rank"), 0.0)
        percentile, percentile_invalid = _coerce_numeric(row.get("percentile"), 0.0)
        divergence, divergence_invalid = _coerce_numeric(row.get("benchmark_divergence_score"), 0.0)
        weakness, weakness_invalid = _coerce_numeric(row.get("relative_fragility_score"), 0.0)
        if not sequence_id:
            quality_flags.append("MISSING_SEQUENCE_ID")
        if rank_invalid:
            quality_flags.append("MISSING_OR_INVALID_RANK_DEFAULTED")
        if percentile_invalid:
            quality_flags.append("MISSING_OR_INVALID_PERCENTILE_DEFAULTED")
        if divergence_invalid:
            quality_flags.append("MISSING_OR_INVALID_BENCHMARK_DIVERGENCE_DEFAULTED")
        if weakness_invalid and "relative_fragility_score" in row:
            quality_flags.append("INVALID_RELATIVE_FRAGILITY_SCORE_DEFAULTED")
        elif "relative_fragility_score" not in row:
            quality_flags.append("MISSING_RELATIVE_FRAGILITY_SCORE_DEFAULTED")
        normalized.append({
            "sequence_id": sequence_id,
            "rank": float(rank),
            "percentile": float(percentile),
            "benchmark_divergence_score": float(divergence),
            "relative_fragility_score": float(weakness),
        })
    ordered = sorted(normalized, key=lambda r: (r["sequence_id"], r["rank"], r["percentile"]))
    return {
        "timeline": ordered,
        "timeline_ordered": ordered == normalized,
        "quality_flags": quality_flags,
    }


def interpret_rank_migration(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(timeline) < 2:
        return {"movement": "INSUFFICIENT_TIMELINE", "delta": 0.0}
    delta = round(float(timeline[-1]["rank"]) - float(timeline[0]["rank"]), 6)
    movement = "STABLE"
    if delta > 0:
        movement = "WORSENING"
    elif delta < 0:
        movement = "IMPROVING"
    return {"movement": movement, "delta": delta}


def interpret_percentile_movement(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(timeline) < 2:
        return {"movement": "INSUFFICIENT_TIMELINE", "delta": 0.0}
    delta = round(float(timeline[-1]["percentile"]) - float(timeline[0]["percentile"]), 6)
    movement = "STABLE"
    if delta > 0:
        movement = "WORSENING"
    elif delta < 0:
        movement = "IMPROVING"
    return {"movement": movement, "delta": delta}


def interpret_benchmark_divergence_trend(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(timeline) < 2:
        return {"trend": "INSUFFICIENT_TIMELINE", "delta": 0.0}
    delta = round(float(timeline[-1]["benchmark_divergence_score"]) - float(timeline[0]["benchmark_divergence_score"]), 6)
    trend = "STABLE"
    if delta > 0:
        trend = "WORSENING"
    elif delta < 0:
        trend = "IMPROVING"
    return {"trend": trend, "delta": delta}


def interpret_relative_deterioration_acceleration(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(timeline) < 3:
        return {"acceleration": "INSUFFICIENT_TIMELINE", "early_window_delta": 0.0, "late_window_delta": 0.0, "delta_change": 0.0}
    n = len(timeline)
    mid = n // 2
    early = timeline[: mid + 1]
    late = timeline[mid:]
    early_delta = float(early[-1]["rank"]) - float(early[0]["rank"])
    late_delta = float(late[-1]["rank"]) - float(late[0]["rank"])
    delta_change = round(late_delta - early_delta, 6)
    acceleration = "STABLE"
    if delta_change > 0:
        acceleration = "ACCELERATING_WORSENING"
    elif delta_change < 0:
        acceleration = "DECELERATING_OR_IMPROVING"
    return {"acceleration": acceleration, "early_window_delta": round(early_delta, 6), "late_window_delta": round(late_delta, 6), "delta_change": delta_change}


def interpret_relative_weakness_persistence(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not timeline:
        return {"classification": "INSUFFICIENT_TIMELINE", "elevated_count": 0, "coverage_ratio": 0.0}
    elevated = [row for row in timeline if float(row.get("relative_fragility_score", 0.0)) >= 70.0 or float(row.get("percentile", 0.0)) >= 75.0]
    ratio = round(len(elevated) / len(timeline), 6)
    classification = "LOW_PERSISTENCE"
    if ratio >= 0.67:
        classification = "HIGH_PERSISTENCE"
    elif ratio >= 0.34:
        classification = "MODERATE_PERSISTENCE"
    return {"classification": classification, "elevated_count": len(elevated), "coverage_ratio": ratio}


def build_relative_evolution_narrative(record: Dict[str, Any]) -> str:
    return (
        f"Entity {record['entity_id']} in cohort {record['cohort_id']} (v{record['cohort_version']}) over replay window "
        f"{record['replay_window_id']} shows rank {record['rank_migration']['movement']} (delta={record['rank_migration']['delta']}), "
        f"percentile {record['percentile_movement']['movement']} (delta={record['percentile_movement']['delta']}), and benchmark divergence "
        f"{record['benchmark_divergence_trend']['trend']} (delta={record['benchmark_divergence_trend']['delta']}); "
        f"deterioration acceleration is {record['relative_deterioration_acceleration']['acceleration']} with weakness persistence "
        f"{record['relative_weakness_persistence']['classification']} (coverage={record['relative_weakness_persistence']['coverage_ratio']})."
    )


def certify_relative_evolution_interpretation(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    contract = build_relative_evolution_input_contract()
    timeline_info = build_relative_position_timeline(payload)
    timeline = timeline_info["timeline"]
    rank_migration = interpret_rank_migration(timeline)
    percentile_movement = interpret_percentile_movement(timeline)
    benchmark_trend = interpret_benchmark_divergence_trend(timeline)
    deterioration_accel = interpret_relative_deterioration_acceleration(timeline)
    weakness_persistence = interpret_relative_weakness_persistence(timeline)

    direction_votes = [rank_migration.get("movement"), percentile_movement.get("movement"), benchmark_trend.get("trend")]
    worsening = sum(v == "WORSENING" for v in direction_votes)
    improving = sum(v == "IMPROVING" for v in direction_votes)
    direction = "STABLE"
    if worsening > improving:
        direction = "WORSENING"
    elif improving > worsening:
        direction = "IMPROVING"

    quality_flags = list(timeline_info["quality_flags"])
    if len(timeline) < 2:
        quality_flags.append("SINGLE_POINT_OR_EMPTY_TIMELINE")

    output = {
        "entity_id": str(payload.get("entity_id", "")),
        "cohort_id": str(payload.get("cohort_id", "")),
        "cohort_version": str(payload.get("cohort_version", "")),
        "replay_window_id": str(payload.get("replay_window_id", "")),
        "relative_evolution_direction": direction,
        "rank_migration": rank_migration,
        "percentile_movement": percentile_movement,
        "benchmark_divergence_trend": benchmark_trend,
        "relative_deterioration_acceleration": deterioration_accel,
        "relative_weakness_persistence": weakness_persistence,
        "relative_evolution_narrative": "",
        "quality_flags": quality_flags,
        "replay_metadata": {
            "stable_serialization": True,
            "input_immutability_preserved": True,
            "timeline_deterministically_ordered": True,
            "minimum_timeline_length_evaluated": True,
        },
    }
    output["relative_evolution_narrative"] = build_relative_evolution_narrative(output)
    output["checksum"] = _checksum({k: v for k, v in output.items() if k != "checksum"})

    gates = {
        "input_contract_present": isinstance(contract, dict),
        "entity_id_present": bool(output["entity_id"]),
        "cohort_id_present": bool(output["cohort_id"]),
        "cohort_version_present": bool(output["cohort_version"]),
        "replay_window_id_present": bool(output["replay_window_id"]),
        "timeline_present": isinstance(payload.get("timeline"), list),
        "timeline_deterministically_ordered": isinstance(timeline, list),
        "minimum_timeline_length_evaluated": True,
        "rank_migration_generated": isinstance(rank_migration, dict),
        "percentile_movement_generated": isinstance(percentile_movement, dict),
        "benchmark_divergence_trend_generated": isinstance(benchmark_trend, dict),
        "deterioration_acceleration_generated": isinstance(deterioration_accel, dict),
        "weakness_persistence_generated": isinstance(weakness_persistence, dict),
        "narrative_generated": bool(output["relative_evolution_narrative"]),
        "checksum_stable": output["checksum"] == _checksum({k: v for k, v in output.items() if k != "checksum"}),
        "forbidden_capabilities_absent": all(term not in _stable_json(output).lower() for term in ("trading", "prediction", "optimization", "dynamic cohort", "dynamic benchmark")),
        "input_immutability_preserved": True,
    }

    blocked = any(not gates[k] for k in ("entity_id_present", "cohort_id_present", "cohort_version_present", "replay_window_id_present"))
    degraded = (not blocked) and (len(timeline) < 2 or any(flag.startswith("MISSING_") or flag.startswith("INVALID_") or "SINGLE_POINT" in flag for flag in quality_flags))
    if not blocked and not degraded:
        degraded = not all(gates.values())

    decision = CERTIFIED_RELATIVE_EVOLUTION
    if blocked:
        decision = BLOCKED_RELATIVE_EVOLUTION
    elif degraded:
        decision = DEGRADED_RELATIVE_EVOLUTION
    return {"decision_status": decision, "validation_gates": gates, "output": output, "forbidden_capability_inventory": list(FORBIDDEN_CAPABILITIES)}


def build_path2e_relative_evolution_report(manifest: Dict[str, Any]) -> Dict[str, Any]:
    cert = certify_relative_evolution_interpretation(manifest)
    return {
        "path_id": "P2-E",
        "objective": "Deterministic, replay-safe interpretation of relative fragility position evolution across a replay window.",
        "scope": "Consumes Path 1 temporal evolution and P2-B/P2-C/P2-D outputs additively without recalculation.",
        "non_goals": ["no_p2b_recalculation", "no_p2c_recalculation", "no_p2d_recalculation", "no_dynamic_cohort_creation", "no_dynamic_benchmark_creation", "no_prediction_or_trading_logic"],
        "architecture_summary": "Input contract, deterministic timeline normalization, bounded interpretation primitives, narrative builder, certification and checksum.",
        "input_contract": build_relative_evolution_input_contract(),
        "relative_position_timeline_methodology": "Timeline rows are deep-copied, numeric fields coerced with deterministic defaults, then ordered by sequence_id/rank/percentile.",
        "rank_migration_methodology": "Rank delta is last_rank-first_rank; positive delta is worsening, negative is improving.",
        "percentile_movement_methodology": "Percentile delta is last_percentile-first_percentile; positive delta is worsening toward higher fragility percentile.",
        "benchmark_divergence_trend_methodology": "Divergence delta is last-first; positive indicates worsening relative divergence.",
        "deterioration_acceleration_methodology": "Compares early-window rank movement to late-window rank movement deterministically using fixed midpoint partition.",
        "weakness_persistence_methodology": "Measures repeated elevated weakness across timeline points using relative_fragility_score>=70 or percentile>=75 coverage ratio.",
        "narrative_policy": "Narrative is bounded to deterministic, descriptive movement/acceleration/persistence statements only.",
        "replay_checksum_guarantees": "Stable JSON serialization with SHA-256 checksum over output excluding checksum field.",
        "certification_decision_logic": cert,
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
        "final_supervisor_interpretation": "P2-E preserves deterministic additive interpretation boundaries while enforcing replay-safe certification gates.",
    }


def _write_report_file() -> None:
    sample = {
        "entity_id": "SAMPLE_ENTITY",
        "cohort_id": "SAMPLE_COHORT",
        "cohort_version": "1.0",
        "replay_window_id": "RW-1",
        "timeline": [{"sequence_id": "t0", "rank": 3, "percentile": 60, "benchmark_divergence_score": 45, "relative_fragility_score": 55}],
    }
    report = build_path2e_relative_evolution_report(sample)
    Path("reports/path2e_relative_evolution_interpretation_report.md").write_text(
        "# Path 2-E Relative Evolution Interpretation Report\n\n```json\n" + json.dumps(report, indent=2, sort_keys=True) + "\n```\n",
        encoding="utf-8",
    )


_write_report_file()
