from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHASE = "tier3h5_phase2c"
PHASE_PERSISTENCE = "tier3h5_phase2c1"
LOG_DIR = Path("logs")

LINEAGE_PATH = LOG_DIR / "tier3h5_registry_snapshot_lineage.json"
INGESTION_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_foundation_summary.json"

DRIFT_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_drift_summary.json"
GOVERNANCE_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_replay_governance_summary.json"
COMPARISON_PATH = LOG_DIR / "tier3h5_registry_snapshot_comparison.json"
METRICS_PATH = LOG_DIR / "tier3h5_registry_replay_metrics.json"
PHASE_SUMMARY_PATH = LOG_DIR / "tier3h5_phase2c_replay_governance_summary.json"

REPLAY_BASELINE_MANIFEST_PATH = LOG_DIR / "tier3h5_replay_baseline_manifest.json"
REPLAY_HISTORY_SUMMARY_PATH = LOG_DIR / "tier3h5_replay_history_summary.json"
REPLAY_CONTINUITY_LINEAGE_PATH = LOG_DIR / "tier3h5_replay_continuity_lineage.json"
REPLAY_CHAIN_METRICS_PATH = LOG_DIR / "tier3h5_replay_chain_metrics.json"
PHASE2C1_SUMMARY_PATH = LOG_DIR / "tier3h5_phase2c1_replay_persistence_summary.json"
REPLAY_BASELINE_STORE_PATH = LOG_DIR / "tier3h5_registry_replay_baseline_history.json"


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "registry_snapshot_id": row.get("registry_snapshot_id"),
        "source_name": row.get("source_name") or "unknown_source",
        "source_dataset_version": row.get("source_dataset_version"),
        "ingestion_run_id": row.get("ingestion_run_id"),
        "normalization_version": row.get("normalization_version"),
        "records_seen": _safe_int(row.get("records_seen", row.get("source_record_count"))),
        "records_accepted": _safe_int(row.get("records_accepted", row.get("accepted_record_count"))),
        "records_rejected": _safe_int(row.get("records_rejected", row.get("rejected_record_count"))),
        "duplicates": _safe_int(row.get("duplicates", row.get("duplicate_record_count"))),
        "conflicts": _safe_int(row.get("conflicts", row.get("conflict_record_count"))),
        "normalization_failures": _safe_int(row.get("normalization_failures")),
        "deterministic_id_collisions": _safe_int(row.get("deterministic_id_collisions")),
    }


def _row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("registry_snapshot_id") or ""), str(row.get("source_name") or "unknown_source"))


def _density(value: int, seen: int) -> float:
    return round(value / seen, 6) if seen > 0 else 0.0


def _snapshot_id(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    snapshot_id = rows[0].get("registry_snapshot_id")
    return str(snapshot_id) if snapshot_id is not None else None


def _comparison_baseline_id(rows: list[dict[str, Any]]) -> str | None:
    snapshot_id = _snapshot_id(rows)
    return f"baseline::{snapshot_id}" if snapshot_id is not None else None


def _load_replay_history() -> list[dict[str, Any]]:
    payload = _load_json(REPLAY_BASELINE_STORE_PATH)
    entries = payload.get("history")
    if not isinstance(entries, list):
        return []
    normalized = [e for e in entries if isinstance(e, dict)]
    return sorted(normalized, key=lambda e: (str(e.get("replay_timestamp_sgt") or ""), str(e.get("registry_snapshot_id") or ""), str(e.get("ingestion_run_id") or "")))


def _select_prior_baseline(history: list[dict[str, Any]], current_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not history:
        return None
    current_sources = sorted({_normalize_row(r).get("source_name") for r in current_rows})
    source_matched = [h for h in history if sorted(h.get("source_names", [])) == current_sources]
    ordered = source_matched if source_matched else history
    return ordered[-1] if ordered else None


def classify_replay_governance(diffs: dict[str, Any], baseline_available: bool) -> str:
    if not baseline_available:
        return "replay_baseline_unavailable"
    if diffs["replay_difference_count"] == 0:
        return "stable_replay"
    if diffs["replay_normalization_difference_count"] > 0:
        return "normalization_drift"
    if diffs["replay_provenance_difference_count"] > 0 and diffs["replay_structural_difference_count"] == 0:
        return "metadata_drift"
    if diffs["replay_provenance_difference_count"] > 0:
        return "provenance_drift"
    if diffs["replay_structural_difference_count"] > 0:
        if diffs.get("record_count_drift", 0) > 0 and diffs.get("governance_anomaly_count", 0) == 0:
            return "expected_growth"
        return "structural_drift"
    return "unresolved_replay_difference"


def compare_registry_snapshots(current_rows: list[dict[str, Any]], prior_rows: list[dict[str, Any]] | None) -> dict[str, Any]:
    cur = {_row_key(_normalize_row(r)): _normalize_row(r) for r in current_rows}
    prv_rows = [_normalize_row(r) for r in (prior_rows or [])]
    prv = {_row_key(r): r for r in prv_rows}
    if not prv:
        return {"baseline_available": False, "status": "insufficient_replay_history", "differences": [], "source_additions": sorted({k[1] for k in cur.keys()}), "source_removals": []}

    differences: list[dict[str, Any]] = []
    source_additions = sorted({k[1] for k in cur.keys() - prv.keys()})
    source_removals = sorted({k[1] for k in prv.keys() - cur.keys()})

    for key in sorted(cur.keys() & prv.keys()):
        c = cur[key]
        p = prv[key]
        change: dict[str, Any] = {"key": {"registry_snapshot_id": key[0], "source_name": key[1]}}
        numeric_fields = ["records_seen", "records_accepted", "records_rejected", "duplicates", "conflicts", "normalization_failures", "deterministic_id_collisions"]
        metadata_fields = ["source_dataset_version", "ingestion_run_id", "registry_snapshot_id"]
        version_fields = ["normalization_version"]

        for f in numeric_fields + metadata_fields + version_fields:
            if c.get(f) != p.get(f):
                change[f] = {"prior": p.get(f), "current": c.get(f)}

        c_seen = _safe_int(c.get("records_seen"))
        p_seen = _safe_int(p.get("records_seen"))
        for drift_field, base_field in [("duplicate_density_drift", "duplicates"), ("conflict_density_drift", "conflicts"), ("unresolved_density_drift", "records_rejected"), ("normalization_failure_drift", "normalization_failures")]:
            drift = round(_density(_safe_int(c.get(base_field)), c_seen) - _density(_safe_int(p.get(base_field)), p_seen), 6)
            if drift != 0.0:
                change[drift_field] = drift

        if len(change) > 1:
            differences.append(change)

    return {"baseline_available": True, "status": "success", "differences": differences, "source_additions": source_additions, "source_removals": source_removals}


def compute_replay_metrics(comparison: dict[str, Any]) -> dict[str, Any]:
    differences = comparison.get("differences", [])
    struct = meta = norm = prov = unresolved = 0
    for d in differences:
        keys = set(d.keys())
        if keys & {"records_seen", "records_accepted", "records_rejected", "duplicates", "conflicts", "deterministic_id_collisions", "record_count_drift", "duplicate_density_drift", "conflict_density_drift", "unresolved_density_drift"}:
            struct += 1
        if keys & {"source_dataset_version", "ingestion_run_id", "registry_snapshot_id"}:
            meta += 1
            prov += 1
        if keys & {"normalization_version", "normalization_failure_drift", "normalization_failures"}:
            norm += 1
        if keys == {"key"}:
            unresolved += 1
    diff_count = len(differences) + len(comparison.get("source_additions", [])) + len(comparison.get("source_removals", []))
    ratio = round(max(0.0, 1.0 - (diff_count / max(1, diff_count + 1))), 6)
    return {"replay_difference_count": diff_count, "replay_structural_difference_count": struct, "replay_metadata_difference_count": meta, "replay_normalization_difference_count": norm, "replay_provenance_difference_count": prov, "replay_unresolved_difference_count": unresolved, "replay_consistency_ratio": ratio, "replay_exact_match": diff_count == 0, "normalization_replay_stable": norm == 0, "provenance_replay_stable": prov == 0, "governance_replay_stable": struct == 0 and norm == 0 and prov == 0}


def run_phase2c_replay_governance(current_rows: list[dict[str, Any]] | None = None, prior_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    lineage_payload = _load_json(LINEAGE_PATH)
    lineage_rows = lineage_payload.get("lineage") if isinstance(lineage_payload.get("lineage"), list) else []
    current = [_normalize_row(r) for r in (current_rows or lineage_rows)]
    if not current:
        ingestion = _load_json(INGESTION_SUMMARY_PATH)
        if ingestion:
            current = [_normalize_row(ingestion)]

    history = _load_replay_history()
    baseline_entry = _select_prior_baseline(history, current) if current else None

    prior = [_normalize_row(r) for r in (prior_rows or [])]
    if not prior and baseline_entry:
        prior = [_normalize_row(r) for r in baseline_entry.get("comparison_rows", [])]
    if not prior and len(lineage_rows) > 1:
        prior = [_normalize_row(r) for r in lineage_rows[:-1]]

    comparison = compare_registry_snapshots(current, prior)
    metrics = compute_replay_metrics(comparison)
    combined = {**metrics, "record_count_drift": sum(1 for d in comparison.get("differences", []) if "records_seen" in d), "governance_anomaly_count": sum(1 for d in comparison.get("differences", []) if "conflicts" in d or "duplicates" in d)}
    base_status = classify_replay_governance(combined, baseline_available=comparison.get("baseline_available", False))

    replay_history_available = len(history) > 0
    replay_chain_length = len(history) + 1
    comparable_history = [e for e in history if bool(e.get("replay_baseline_available", False))]
    replay_stable_chain_length = 0 if base_status != "stable_replay" else 1
    replay_drift_chain_length = 1 if base_status != "stable_replay" and comparison.get("baseline_available", False) else 0
    if comparable_history and comparison.get("baseline_available", False):
        for e in reversed(comparable_history):
            prior_status = str(e.get("replay_governance_status") or "")
            if prior_status == "stable_replay" and base_status == "stable_replay":
                replay_stable_chain_length += 1
            elif prior_status != "stable_replay" and base_status != "stable_replay":
                replay_drift_chain_length += 1
            else:
                break

    status_tags = []
    if not replay_history_available:
        status_tags.extend(["first_snapshot_only", "replay_history_initializing", "replay_history_unavailable"])
    else:
        status_tags.append("replay_history_established")
    if comparison.get("baseline_available") and base_status == "stable_replay":
        status_tags.append("stable_replay_chain")
    if comparison.get("baseline_available") and base_status != "stable_replay":
        if history and any(str(e.get("replay_governance_status")) == base_status for e in history[-2:]):
            mapping = {"metadata_drift": "persistent_metadata_drift", "normalization_drift": "persistent_normalization_drift", "structural_drift": "persistent_structural_drift"}
            status_tags.append(mapping.get(base_status, "persistent_drift_detected"))
        else:
            status_tags.append("transient_replay_difference")

    replay_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    replay_comparison_baseline_id = _comparison_baseline_id(prior) if prior else None
    lineage = {
        "phase": PHASE,
        "status": comparison.get("status"),
        "replay_baseline_available": comparison.get("baseline_available", False),
        "prior_replay_snapshot_id": _snapshot_id(prior) if prior else None,
        "replay_comparison_baseline_id": replay_comparison_baseline_id,
        "replay_baseline_timestamp_sgt": baseline_entry.get("replay_timestamp_sgt") if baseline_entry else None,
        "replay_lineage_depth": replay_chain_length,
        "replay_history_available": replay_history_available,
        "compared_registry_snapshot_id": _snapshot_id(current),
        "replay_comparison_run_id": f"replay-{(current[0].get('ingestion_run_id') if current else 'none')}",
        "replay_governance_status": base_status,
        "replay_status_tags": sorted(set(status_tags)),
        "replay_difference_summary": {"difference_count": metrics["replay_difference_count"], "source_additions": comparison.get("source_additions", []), "source_removals": comparison.get("source_removals", [])},
        "replay_timestamp_sgt": replay_timestamp,
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }

    drift_diag = {
        "first_observed_drift": base_status != "stable_replay" and replay_chain_length == 1,
        "persistent_drift_detected": base_status != "stable_replay" and replay_drift_chain_length > 1,
        "transient_drift_detected": base_status != "stable_replay" and replay_drift_chain_length == 1,
        "normalization_drift_persistence": base_status == "normalization_drift" and replay_drift_chain_length > 1,
        "provenance_drift_persistence": base_status in {"provenance_drift", "metadata_drift"} and replay_drift_chain_length > 1,
        "replay_stability_trend": "stable" if base_status == "stable_replay" else ("degraded" if replay_drift_chain_length > 1 else "volatile"),
    }

    drift_counter = Counter([base_status])
    drift_summary = {"phase": PHASE, "status": comparison.get("status"), "replay_governance_status": base_status, "drift_status_counts": dict(drift_counter), "drift_continuity_diagnostics": drift_diag, "source_additions": comparison.get("source_additions", []), "source_removals": comparison.get("source_removals", []), "difference_rows": comparison.get("differences", []), "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}
    governance_summary = {"phase": PHASE, "status": comparison.get("status"), "replay_governance_status": base_status, "replay_status_tags": sorted(set(status_tags)), **metrics, "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}
    phase_summary = {"phase": PHASE, "status": comparison.get("status"), "replay_governance_status": base_status, "replay_status_tags": sorted(set(status_tags)), "replay_exact_match": metrics["replay_exact_match"], "replay_consistency_ratio": metrics["replay_consistency_ratio"], "replay_difference_count": metrics["replay_difference_count"], "drift_status_counts": dict(drift_counter), "normalization_replay_stable": metrics["normalization_replay_stable"], "provenance_replay_stable": metrics["provenance_replay_stable"], "governance_replay_stable": metrics["governance_replay_stable"], "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}

    _write_json(COMPARISON_PATH, {"phase": PHASE, "status": comparison.get("status"), **comparison, "enforcement_enabled": False, "canonical_override_enabled": False})
    _write_json(METRICS_PATH, {"phase": PHASE, "status": comparison.get("status"), **metrics, "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"})
    _write_json(DRIFT_SUMMARY_PATH, drift_summary)
    _write_json(GOVERNANCE_SUMMARY_PATH, governance_summary)
    _write_json(PHASE_SUMMARY_PATH, phase_summary)

    baseline_entry_new = {
        "phase": PHASE_PERSISTENCE,
        "registry_snapshot_id": _snapshot_id(current),
        "ingestion_run_id": current[0].get("ingestion_run_id") if current else None,
        "source_names": sorted({r.get("source_name") for r in current}),
        "comparison_rows": current,
        "replay_governance_status": base_status,
        "replay_timestamp_sgt": replay_timestamp,
        "replay_exact_match": metrics["replay_exact_match"],
        "replay_consistency_ratio": metrics["replay_consistency_ratio"],
        "replay_difference_count": metrics["replay_difference_count"],
        "replay_baseline_available": comparison.get("baseline_available", False),
    }
    updated_history = history + [baseline_entry_new]
    _write_json(REPLAY_BASELINE_STORE_PATH, {"phase": PHASE_PERSISTENCE, "history": updated_history, "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"})

    chain_metrics = {"phase": PHASE_PERSISTENCE, "replay_chain_length": replay_chain_length, "replay_stable_chain_length": replay_stable_chain_length, "replay_drift_chain_length": replay_drift_chain_length, "replay_lineage_depth": replay_chain_length, "replay_history_available": replay_history_available, "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}
    baseline_manifest = {"phase": PHASE_PERSISTENCE, "replay_baseline_available": comparison.get("baseline_available", False), "prior_replay_snapshot_id": _snapshot_id(prior) if prior else None, "replay_comparison_baseline_id": replay_comparison_baseline_id, "replay_baseline_timestamp_sgt": baseline_entry.get("replay_timestamp_sgt") if baseline_entry else None, "replay_history_available": replay_history_available, "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}
    history_summary = {"phase": PHASE_PERSISTENCE, "replay_history_available": replay_history_available, "replay_history_count": len(updated_history), "latest_replay_snapshot_id": _snapshot_id(current), "replay_status_tags": sorted(set(status_tags)), "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}
    continuity_summary = {"phase": PHASE_PERSISTENCE, **lineage, "drift_continuity_diagnostics": drift_diag, "replay_chain_length": replay_chain_length, "replay_stable_chain_length": replay_stable_chain_length, "replay_drift_chain_length": replay_drift_chain_length, "replay_history_available": replay_history_available, "enforcement_enabled": False, "canonical_override_enabled": False, "replay_mode": "advisory_only"}
    persistence_summary = {"phase": PHASE_PERSISTENCE, "replay_baseline_available": comparison.get("baseline_available", False), "replay_history_available": replay_history_available, "replay_chain_length": replay_chain_length, "replay_governance_status": base_status, "replay_exact_match": metrics["replay_exact_match"], "replay_consistency_ratio": metrics["replay_consistency_ratio"], "replay_difference_count": metrics["replay_difference_count"], "replay_lineage_depth": replay_chain_length, "replay_mode": "advisory_only", "enforcement_enabled": False, "canonical_override_enabled": False}

    _write_json(REPLAY_BASELINE_MANIFEST_PATH, baseline_manifest)
    _write_json(REPLAY_HISTORY_SUMMARY_PATH, history_summary)
    _write_json(REPLAY_CONTINUITY_LINEAGE_PATH, continuity_summary)
    _write_json(REPLAY_CHAIN_METRICS_PATH, chain_metrics)
    _write_json(PHASE2C1_SUMMARY_PATH, persistence_summary)

    return {"comparison": comparison, "metrics": metrics, "lineage": lineage, "summary": phase_summary}


if __name__ == "__main__":
    run_phase2c_replay_governance()
