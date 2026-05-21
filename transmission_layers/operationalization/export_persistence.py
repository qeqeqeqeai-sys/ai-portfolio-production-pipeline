"""Deterministic export envelope filesystem persistence (Operationalization O1F)."""

from __future__ import annotations

from pathlib import Path

from .export_envelope import build_manifest_export_envelope
from .manifests import manifest_checksum
from .serialization import stable_serialize


def build_export_filename(manifest: dict) -> str:
    """Return deterministic export filename for a manifest."""
    checksum = manifest_checksum(manifest)
    return f"manifest_export_{checksum}.json"


def persist_manifest_export_envelope(manifest: dict, export_dir: str | Path, *, overwrite: bool = False) -> dict:
    """Persist deterministic manifest export envelope to explicit filesystem boundary."""
    envelope = build_manifest_export_envelope(manifest)
    checksum = manifest_checksum(manifest)
    export_filename = build_export_filename(manifest)

    export_dir_path = Path(export_dir)
    export_path = export_dir_path / export_filename

    export_ready = bool(envelope.get("export_ready"))

    bytes_written = 0
    if not export_ready:
        persistence_status = "not_ready"
    elif export_path.exists() and not overwrite:
        persistence_status = "skipped_existing"
    else:
        export_dir_path.mkdir(parents=True, exist_ok=True)
        payload_text = stable_serialize(envelope)
        payload_bytes = payload_text.encode("utf-8")
        export_path.write_text(payload_text, encoding="utf-8")
        bytes_written = len(payload_bytes)
        persistence_status = "written"

    export_path_present = export_path.exists()

    return {
        "persistence_status": persistence_status,
        "export_path": str(export_path),
        "export_filename": export_filename,
        "export_ready": export_ready,
        "overwrite": overwrite,
        "bytes_written": bytes_written,
        "checksum": checksum,
        "integrity_check": {
            "checksum_matches_filename": checksum in export_filename,
            "file_written": persistence_status == "written",
            "export_path_present": export_path_present,
        },
        "export_summary": envelope["export_summary"],
    }
