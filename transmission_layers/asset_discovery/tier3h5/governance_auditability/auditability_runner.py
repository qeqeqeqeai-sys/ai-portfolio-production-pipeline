from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .artifact_provenance import build_artifact_provenance_summary
from .auditability_context import load_auditability_context, stable_json_dumps
from .evidence_lineage import build_evidence_inventory
from .governance_audit_summary import build_auditability_summary
from .lineage_manifest_builder import build_lineage_manifest
from .monitoring_lineage import build_monitoring_lineage_summary
from .release_audit_snapshot import build_release_audit_snapshot
from .reporting_lineage import build_reporting_lineage_summary


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stable_json_dumps(payload), encoding="utf-8")


def run_governance_auditability() -> dict:
    context = load_auditability_context()
    manifest = build_lineage_manifest(context)
    provenance = build_artifact_provenance_summary(manifest)
    monitoring = build_monitoring_lineage_summary(manifest)
    reporting = build_reporting_lineage_summary(manifest)
    snapshot = build_release_audit_snapshot(context, manifest, provenance)

    outputs = [
        "logs/tier3h5_auditability_context.json",
        "logs/tier3h5_governance_lineage_manifest.json",
        "logs/tier3h5_evidence_inventory.json",
        "logs/tier3h5_artifact_provenance_summary.json",
        "logs/tier3h5_monitoring_lineage_summary.json",
        "logs/tier3h5_reporting_lineage_summary.json",
        "logs/tier3h5_release_audit_snapshot.json",
        "logs/tier3h5_phase5e_auditability_summary.json",
    ]
    evidence = build_evidence_inventory(context, manifest, outputs)
    summary = build_auditability_summary(context, manifest, provenance, snapshot)

    _write(outputs[0], context)
    _write(outputs[1], manifest)
    _write(outputs[2], evidence)
    _write(outputs[3], provenance)
    _write(outputs[4], monitoring)
    _write(outputs[5], reporting)
    _write(outputs[6], snapshot)
    _write(outputs[7], summary)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_dir = Path("logs/history/tier3h5_auditability") / run_id
    _write(str(history_dir / "lineage_manifest.json"), manifest)
    _write(str(history_dir / "evidence_inventory.json"), evidence)
    _write(str(history_dir / "release_audit_snapshot.json"), snapshot)
    _write(str(history_dir / "auditability_summary.json"), summary)
    return summary
