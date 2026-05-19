from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_reporting import run_governance_operational_reporting


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_baseline() -> None:
    _write("logs/tier3h5_governance_drift_diagnostics.json", {"drift_detected": False})
    _write("logs/tier3h5_phase5b_monitoring_summary.json", {"drift_detected": False})
    _write("logs/tier3h5_readiness_drift_summary.json", {"readiness_drift_detected": False})
    _write("logs/tier3h5_governance_trend_analytics.json", {"trend": "stable"})
    _write("logs/tier3h5_phase5c_history_summary.json", {"monitoring_history_run_status": "success"})


def test_missing_optional_inputs_sparse_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_governance_operational_reporting()
    assert out["operational_classification"] == "insufficient_operational_history"
    assert out["release_readiness_classification"] == "insufficient_operational_history"


def test_healthy_baseline_reporting(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_baseline()
    out = run_governance_operational_reporting()
    assert out["operational_classification"] == "healthy_with_minor_variation"
    assert out["release_readiness_classification"] in {"operationally_ready", "operationally_ready_with_advisory_findings"}
    assert out["advisory_only_governance_verified"] is True
    assert out["exact_match_only_preserved"] is True
    assert out["tier3h4_freeze_boundary_preserved"] is True


def test_drift_operational_reporting_and_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_baseline()
    _write("logs/tier3h5_phase5b_monitoring_summary.json", {
        "drift_detected": True,
        "orchestration_drift_detected": True,
        "artifact_drift_detected": False,
        "validation_drift_detected": False,
        "readiness_drift_detected": True,
    })
    _write("logs/tier3h5_governance_drift_diagnostics.json", {"drift_detected": True})
    out = run_governance_operational_reporting()
    assert out["operational_classification"] == "operational_attention_recommended"
    assert out["release_readiness_classification"] == "operational_review_recommended"
    for path in [
        "logs/tier3h5_governance_reporting_context.json",
        "logs/tier3h5_operational_health_report.json",
        "logs/tier3h5_executive_readiness_summary.json",
        "logs/tier3h5_drift_operational_report.json",
        "logs/tier3h5_release_confidence_summary.json",
        "logs/tier3h5_dashboard_export_readiness.json",
        "logs/tier3h5_phase5d_reporting_summary.json",
    ]:
        assert Path(path).exists()


def test_deterministic_replay_safe_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_baseline()
    a = run_governance_operational_reporting()
    b = run_governance_operational_reporting()
    assert a == b
