from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry_snapshot_archive import ARCHIVE_PATH, MANIFEST_PATH, PHASE, PHASE_SUMMARY_PATH, _canonicalize, _snapshot_hash

SUMMARY_PATH = Path("logs") / "tier3h5_time_travel_reconstruction_summary.json"


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


def run_phase2d_time_travel_reconstruction(requested_registry_snapshot_id: str | None = None) -> dict[str, Any]:
    archive = _load_json(ARCHIVE_PATH)
    manifest = _load_json(MANIFEST_PATH)
    if not archive or not manifest:
        status = "archive_unavailable"
        summary = {
            "phase": PHASE,
            "requested_registry_snapshot_id": requested_registry_snapshot_id,
            "reconstructed_registry_snapshot_id": None,
            "reconstruction_status": status,
            "issuer_records_reconstructed": 0,
            "security_records_reconstructed": 0,
            "provenance_records_reconstructed": 0,
            "snapshot_hash": None,
            "recomputed_snapshot_hash": None,
            "snapshot_hash_verified": False,
            "hash_verification_status": "archive_unavailable",
            "deterministic_reconstruction": True,
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        }
    else:
        reconstructed_id = archive.get("registry_snapshot_id")
        expected_id = requested_registry_snapshot_id or reconstructed_id
        recomputed_hash = _snapshot_hash(_canonicalize(archive))
        snapshot_hash = manifest.get("snapshot_hash")
        hash_verified = recomputed_hash == snapshot_hash
        if expected_id != reconstructed_id:
            status = "snapshot_not_found"
        elif not hash_verified:
            status = "hash_mismatch_detected"
        else:
            status = "reconstructed"

        summary = {
            "phase": PHASE,
            "requested_registry_snapshot_id": expected_id,
            "reconstructed_registry_snapshot_id": reconstructed_id,
            "reconstruction_status": status,
            "issuer_records_reconstructed": len(archive.get("issuer_records", [])),
            "security_records_reconstructed": len(archive.get("security_records", [])),
            "provenance_records_reconstructed": len(archive.get("provenance_records", [])),
            "snapshot_hash": snapshot_hash,
            "recomputed_snapshot_hash": recomputed_hash,
            "snapshot_hash_verified": hash_verified,
            "hash_verification_status": "verified" if hash_verified else "hash_mismatch_detected",
            "deterministic_reconstruction": True,
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        }

    _write_json(SUMMARY_PATH, summary)

    phase_summary = _load_json(PHASE_SUMMARY_PATH)
    if phase_summary:
        phase_summary["time_travel_reconstruction_status"] = summary["reconstruction_status"]
        phase_summary["snapshot_hash_verified"] = summary["snapshot_hash_verified"]
        _write_json(PHASE_SUMMARY_PATH, phase_summary)

    return summary


if __name__ == "__main__":
    run_phase2d_time_travel_reconstruction()
