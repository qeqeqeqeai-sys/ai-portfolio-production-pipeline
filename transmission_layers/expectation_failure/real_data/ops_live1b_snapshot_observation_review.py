from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

MAX_REVIEW_SNAPSHOTS = 30
REVIEW_GOVERNANCE_FLAGS = {
    "observational_only": True,
    "no_recursive_replay_operationalization": True,
    "no_autonomous_replay": True,
    "no_topology_activation": True,
    "no_self_modifying_pathways": True,
    "no_prediction_or_trading_execution": True,
    "no_graph_execution_engines": True,
    "no_high_frequency_streaming": True,
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_snapshot_record(payload: dict[str, Any], source_file: str) -> dict[str, Any]:
    live = payload.get("ops_live1b_payload", {})
    canonical = live.get("canonical_tables", {})
    streamlit = live.get("streamlit_payloads", {})
    diagnostics = live.get("diagnostics", {})
    metadata_rows = canonical.get("snapshot_metadata_rows", [])
    meta = metadata_rows[0] if metadata_rows else {}
    posture = (streamlit.get("streamlit_summary_cards") or [{}])[0]
    return {
        "source_file": source_file,
        "snapshot_ts": live.get("snapshot_ts") or meta.get("snapshot_ts") or "",
        "snapshot_id": live.get("snapshot_id") or meta.get("snapshot_id") or "",
        "status": payload.get("status", "unknown"),
        "universe_checksum": meta.get("universe_checksum", ""),
        "universe_size": meta.get("universe_size", 0),
        "observation_mode": live.get("observation_mode", ""),
        "governance_boundaries": live.get("governance_boundaries", payload.get("governance_boundaries", {})),
        "canonical_keys": sorted(canonical.keys()),
        "streamlit_keys": sorted(streamlit.keys()),
        "symbol_rows": len(canonical.get("symbol_snapshot_rows", [])),
        "compression_ratio": float(diagnostics.get("compression_ratio", 0.0)),
        "summary_items": int((canonical.get("pressure_rows") and len(canonical.get("pressure_rows", []))) or 0),
        "normalization_completeness_percentage": float(diagnostics.get("normalization_completeness_percentage", 0.0)),
        "data_completeness_summary": float(diagnostics.get("data_completeness_summary", 0.0)),
        "symbols_successfully_normalized": int(diagnostics.get("symbols_successfully_normalized", 0)),
        "symbols_failed_closed": int(diagnostics.get("symbols_failed_closed", 0)),
        "invalid_values": int(diagnostics.get("invalid_values", 0)),
        "missing_fields": int(diagnostics.get("missing_fields", 0)),
        "null_fields": int(diagnostics.get("null_fields", 0)),
        "fallback_usage_percentage": float(diagnostics.get("fallback_usage_percentage", 0.0)),
        "sector_distribution": tuple((x.get("sector", ""), x.get("count", 0)) for x in diagnostics.get("sector_distribution", [])),
        "posture": posture.get("value", "unknown"),
        "pressure": tuple((x.get("symbol", ""), x.get("structural_pressure_score", 0)) for x in canonical.get("pressure_rows", [])),
        "resilience": tuple((x.get("symbol", ""), x.get("profitability_structure", 0)) for x in canonical.get("resilience_rows", [])),
        "fragmentation": tuple((x.get("symbol", ""), x.get("breadth_dispersion_structure", 0)) for x in canonical.get("fragmentation_rows", [])),
    }


def load_ops_live1b_snapshots(input_dir: str = "reports/ops_live1b_runs", max_snapshots: int = MAX_REVIEW_SNAPSHOTS) -> list[dict[str, Any]]:
    files = sorted(Path(input_dir).glob("*.json"), key=lambda p: p.name)
    rows = [_extract_snapshot_record(_load_json(p), p.name) for p in files]
    rows = sorted(rows, key=lambda r: (r.get("snapshot_ts", ""), r.get("source_file", "")))
    return rows[-max_snapshots:]


def _stable(values: list[Any]) -> bool:
    return len(set(values)) <= 1


def build_ops_live1b_snapshot_observation_review(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("No snapshots provided for observation review")
    checks = {
        "status_consistent_ok": all(s["status"] == "ok" for s in snapshots),
        "snapshot_id_presence": all(bool(s["snapshot_id"]) for s in snapshots),
        "universe_checksum_stable": _stable([s["universe_checksum"] for s in snapshots]),
        "universe_size_stable": _stable([s["universe_size"] for s in snapshots]),
        "observation_mode_consistent": _stable([s["observation_mode"] for s in snapshots]),
        "governance_boundary_consistent": _stable([json.dumps(s["governance_boundaries"], sort_keys=True) for s in snapshots]),
        "payload_schema_stable": _stable([tuple(s["canonical_keys"]) for s in snapshots]),
        "streamlit_payload_stable": _stable([tuple(s["streamlit_keys"]) for s in snapshots]),
    }
    repeated_failed = sorted({s["snapshot_id"] for s in snapshots if s["symbols_failed_closed"] > 0})
    avg_norm = round(sum(s["normalization_completeness_percentage"] for s in snapshots) / len(snapshots), 6)
    posture_transitions = []
    for i in range(1, len(snapshots)):
        a, b = snapshots[i - 1], snapshots[i]
        posture_transitions.append({
            "from_snapshot_id": a["snapshot_id"], "to_snapshot_id": b["snapshot_id"],
            "posture_from": a["posture"], "posture_to": b["posture"], "changed": a["posture"] != b["posture"],
        })
    governance_ok = checks["governance_boundary_consistent"] and all(REVIEW_GOVERNANCE_FLAGS.values())
    ready = all([
        checks["status_consistent_ok"], checks["universe_checksum_stable"], checks["governance_boundary_consistent"],
        checks["payload_schema_stable"], checks["streamlit_payload_stable"], avg_norm >= 98.0, len(repeated_failed) == 0,
    ])
    readiness = "ready_for_controlled_300_symbol_probe" if ready else (
        "blocked_by_governance_issue" if not governance_ok else
        "blocked_by_payload_instability" if (not checks["payload_schema_stable"] or not checks["streamlit_payload_stable"]) else
        "blocked_by_data_quality" if (avg_norm < 98.0 or len(repeated_failed) > 0) else
        "needs_more_50_symbol_observation"
    )
    return {
        "status": "ok",
        "reviewed_snapshot_count": len(snapshots),
        "readiness_classification": readiness,
        "governance_flags": deepcopy(REVIEW_GOVERNANCE_FLAGS),
        "review_summary_cards": {"average_normalization_completeness": avg_norm, "readiness": readiness},
        "snapshot_timeline_table": snapshots,
        "data_quality_table": [{"snapshot_id": s["snapshot_id"], "normalization_completeness_percentage": s["normalization_completeness_percentage"], "symbols_failed_closed": s["symbols_failed_closed"], "invalid_values": s["invalid_values"]} for s in snapshots],
        "posture_drift_table": posture_transitions,
        "pressure_drift_table": [{"snapshot_id": s["snapshot_id"], "dominant_pressure": s["pressure"][:1]} for s in snapshots],
        "resilience_drift_table": [{"snapshot_id": s["snapshot_id"], "strongest_resilience": s["resilience"][:1]} for s in snapshots],
        "fragmentation_drift_table": [{"snapshot_id": s["snapshot_id"], "fragmentation_hotspot": s["fragmentation"][:1]} for s in snapshots],
        "readiness_panel": {"classification": readiness, "repeated_problematic_symbols": repeated_failed},
        "governance_panel": {"consistent": governance_ok, **deepcopy(REVIEW_GOVERNANCE_FLAGS)},
        "reviewed_snapshot_rows": snapshots,
        "stability_check_rows": [{"check": k, "value": v} for k, v in checks.items()],
        "data_quality_rows": [{"snapshot_id": s["snapshot_id"], "data_completeness_summary": s["data_completeness_summary"], "fallback_usage_percentage": s["fallback_usage_percentage"], "missing_fields": s["missing_fields"], "null_fields": s["null_fields"]} for s in snapshots],
        "posture_transition_rows": posture_transitions,
        "pressure_change_rows": [{"snapshot_id": s["snapshot_id"], "pressure": s["pressure"]} for s in snapshots],
        "resilience_change_rows": [{"snapshot_id": s["snapshot_id"], "resilience": s["resilience"]} for s in snapshots],
        "fragmentation_change_rows": [{"snapshot_id": s["snapshot_id"], "fragmentation": s["fragmentation"]} for s in snapshots],
        "readiness_rows": [{"classification": readiness, "average_normalization_completeness": avg_norm}],
        "governance_consistency_rows": [{"consistent": governance_ok, **deepcopy(REVIEW_GOVERNANCE_FLAGS)}],
    }


def render_ops_live1b_observation_review_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-LIVE-1B-OBS Snapshot Observation Review",
        "## Objective",
        "Deterministic, bounded observational review of saved OPS-LIVE-1B snapshots.",
        f"## Reviewed snapshot count\n{review['reviewed_snapshot_count']}",
        f"## Stability summary\nReadiness: {review['readiness_classification']}",
        f"## Data quality summary\nAverage normalization completeness: {review['review_summary_cards']['average_normalization_completeness']}",
        "## Posture drift summary",
        f"Posture transitions observed: {len(review['posture_transition_rows'])}",
        "## Pressure/resilience/fragmentation observations",
        "Descriptive drift only; no forecasts or trading implications.",
        "## Payload continuity summary",
        "Canonical and Streamlit payload section continuity is evaluated across snapshots.",
        "## Governance certification",
        "Observational-only controls remain active.",
        "## Readiness assessment for OPS-LIVE-1C",
        review["readiness_classification"],
        "## Explicit non-goals",
        "No ingestion, no Supabase writes, no scheduling/orchestration/streaming, no replay/topology/graph/prediction execution.",
    ])
