from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_auditability import run_governance_auditability


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_baseline() -> None:
    _write("logs/tier3h5_orchestration_summary.json", {"run": "ok"})
    _write("logs/tier3h5_monitoring_context.json", {"run": "ok"})
    _write("logs/tier3h5_governance_drift_diagnostics.json", {"drift_detected": False})
    _write("logs/tier3h5_governance_trend_analytics.json", {"trend": "stable"})
    _write("logs/tier3h5_operational_health_report.json", {"classification": "healthy"})
    _write("logs/tier3h5_release_confidence_summary.json", {"release_readiness": "ready"})
    _write("logs/tier3h5_phase5d_reporting_summary.json", {"reporting": "complete"})


def test_missing_optional_inputs_handled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_governance_auditability()
    assert out["auditability_run_status"] == "success"
    assert out["advisory_only_governance_verified"] is True


def test_deterministic_lineage_and_provenance(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_baseline()
    a = run_governance_auditability()
    b = run_governance_auditability()
    assert a == b
    assert a["provenance_relationships_generated"] >= 0
    assert a["exact_match_only_preserved"] is True


def test_append_only_history_and_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_baseline()
    run_governance_auditability()
    run_governance_auditability()
    history_root = Path("logs/history/tier3h5_auditability")
    runs = [p for p in history_root.iterdir() if p.is_dir()]
    assert len(runs) >= 1
    for path in [
        "logs/tier3h5_auditability_context.json",
        "logs/tier3h5_governance_lineage_manifest.json",
        "logs/tier3h5_evidence_inventory.json",
        "logs/tier3h5_artifact_provenance_summary.json",
        "logs/tier3h5_monitoring_lineage_summary.json",
        "logs/tier3h5_reporting_lineage_summary.json",
        "logs/tier3h5_release_audit_snapshot.json",
        "logs/tier3h5_phase5e_auditability_summary.json",
    ]:
        assert Path(path).exists()
