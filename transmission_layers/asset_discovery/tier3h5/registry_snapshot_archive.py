from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHASE = "tier3h5_phase2d"
LOG_DIR = Path("logs")

LINEAGE_PATH = LOG_DIR / "tier3h5_registry_snapshot_lineage.json"
INGESTION_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_foundation_summary.json"
REPLAY_BASELINE_MANIFEST_PATH = LOG_DIR / "tier3h5_replay_baseline_manifest.json"
REPLAY_HISTORY_PATH = LOG_DIR / "tier3h5_registry_replay_baseline_history.json"

ARCHIVE_PATH = LOG_DIR / "tier3h5_canonical_registry_snapshot_archive.json"
MANIFEST_PATH = LOG_DIR / "tier3h5_snapshot_archive_manifest.json"
RETENTION_PATH = LOG_DIR / "tier3h5_snapshot_retention_governance.json"
PHASE_SUMMARY_PATH = LOG_DIR / "tier3h5_phase2d_snapshot_time_travel_summary.json"


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


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        normalized = [_canonicalize(v) for v in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"), default=str))
    return value


def _snapshot_hash(snapshot_payload: dict[str, Any]) -> str:
    hash_payload = dict(snapshot_payload)
    hash_payload.pop("archived_at_sgt", None)
    canonical = _canonicalize(hash_payload)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _extract_rows() -> list[dict[str, Any]]:
    lineage = _load_json(LINEAGE_PATH).get("lineage")
    if isinstance(lineage, list) and lineage:
        return [r for r in lineage if isinstance(r, dict)]
    fallback = _load_json(INGESTION_SUMMARY_PATH)
    return [fallback] if fallback else []


def run_phase2d_snapshot_archive() -> dict[str, Any]:
    rows = _extract_rows()
    replay_manifest = _load_json(REPLAY_BASELINE_MANIFEST_PATH)
    replay_history = _load_json(REPLAY_HISTORY_PATH).get("history")
    replay_history_rows = [r for r in replay_history if isinstance(r, dict)] if isinstance(replay_history, list) else []

    issuer_records = [{"source_name": r.get("source_name"), "registry_region": r.get("registry_region")} for r in rows]
    security_records = [
        {
            "source_name": r.get("source_name"),
            "records_seen": r.get("records_seen", r.get("source_record_count")),
            "records_accepted": r.get("records_accepted", r.get("accepted_record_count")),
            "records_rejected": r.get("records_rejected", r.get("rejected_record_count")),
            "duplicates": r.get("duplicates", r.get("duplicate_record_count")),
            "conflicts": r.get("conflicts", r.get("conflict_record_count")),
        }
        for r in rows
    ]
    provenance_records = [
        {
            "source_name": r.get("source_name"),
            "source_dataset_version": r.get("source_dataset_version"),
            "ingestion_run_id": r.get("ingestion_run_id"),
            "normalization_version": r.get("normalization_version"),
            "registry_snapshot_id": r.get("registry_snapshot_id"),
        }
        for r in rows
    ]

    snapshot_id = rows[0].get("registry_snapshot_id") if rows else None
    archive = {
        "phase": PHASE,
        "snapshot_archive_schema_version": "1.0",
        "registry_snapshot_id": snapshot_id,
        "ingestion_run_id": rows[0].get("ingestion_run_id") if rows else None,
        "source_name": rows[0].get("source_name") if rows else None,
        "source_dataset_version": rows[0].get("source_dataset_version") if rows else None,
        "registry_effective_date": rows[0].get("registry_effective_date") if rows else None,
        "registry_region": rows[0].get("registry_region") if rows else None,
        "normalization_version": rows[0].get("normalization_version") if rows else None,
        "archived_at_sgt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "issuer_records": _canonicalize(issuer_records),
        "security_records": _canonicalize(security_records),
        "provenance_records": _canonicalize(provenance_records),
        "governance_summary": {"records_seen": sum(int(r.get("records_seen", r.get("source_record_count", 0)) or 0) for r in rows)},
        "replay_baseline_reference": replay_manifest.get("replay_comparison_baseline_id"),
        "source_precedence_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    snapshot_hash = _snapshot_hash(archive)
    _write_json(ARCHIVE_PATH, archive)

    manifest = {
        "archive_manifest_schema_version": "1.0",
        "registry_snapshot_id": snapshot_id,
        "snapshot_hash": snapshot_hash,
        "archive_file": str(ARCHIVE_PATH),
        "source_name": archive["source_name"],
        "source_dataset_version": archive["source_dataset_version"],
        "normalization_version": archive["normalization_version"],
        "records_seen": sum(int(r.get("records_seen", r.get("source_record_count", 0)) or 0) for r in rows),
        "records_accepted": sum(int(r.get("records_accepted", r.get("accepted_record_count", 0)) or 0) for r in rows),
        "records_rejected": sum(int(r.get("records_rejected", r.get("rejected_record_count", 0)) or 0) for r in rows),
        "duplicates": sum(int(r.get("duplicates", r.get("duplicate_record_count", 0)) or 0) for r in rows),
        "conflicts": sum(int(r.get("conflicts", r.get("conflict_record_count", 0)) or 0) for r in rows),
        "normalization_failures": sum(int(r.get("normalization_failures", 0) or 0) for r in rows),
        "deterministic_id_collisions": sum(int(r.get("deterministic_id_collisions", 0) or 0) for r in rows),
        "snapshot_lineage_reference": str(LINEAGE_PATH),
        "replay_baseline_reference": replay_manifest.get("replay_comparison_baseline_id"),
        "archival_status": "archived" if rows else "archive_unavailable",
    }
    _write_json(MANIFEST_PATH, manifest)

    snap_ids = sorted(str(r.get("registry_snapshot_id")) for r in replay_history_rows if r.get("registry_snapshot_id") is not None)
    retention = {
        "retention_mode": "advisory_only",
        "retained_snapshot_count": len(snap_ids),
        "oldest_snapshot_id": snap_ids[0] if snap_ids else None,
        "newest_snapshot_id": snap_ids[-1] if snap_ids else None,
        "retention_policy_configured": False,
        "retention_policy_applied": False,
        "retention_warnings": ["insufficient_archive_history"] if len(snap_ids) <= 1 else [],
        "archival_enforcement_enabled": False,
    }
    _write_json(RETENTION_PATH, retention)

    summary = {
        "phase": PHASE,
        "status": "ok" if rows else "archive_unavailable",
        "archival_status": manifest["archival_status"],
        "registry_snapshot_id": snapshot_id,
        "snapshot_hash": snapshot_hash,
        "snapshot_hash_verified": None,
        "time_travel_reconstruction_status": "pending",
        "retained_snapshot_count": retention["retained_snapshot_count"],
        "deterministic_reconstruction_enabled": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    _write_json(PHASE_SUMMARY_PATH, summary)

    return {"archive": archive, "manifest": manifest, "retention": retention, "summary": summary}


if __name__ == "__main__":
    run_phase2d_snapshot_archive()
