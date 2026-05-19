from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_history import run_governance_monitoring_history


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_phase5b(drift: bool = False) -> None:
    _write("logs/tier3h5_monitoring_context.json", {"inputs": {"a": True}})
    _write("logs/tier3h5_governance_drift_diagnostics.json", {"drift_detected": drift})
    _write("logs/tier3h5_orchestration_drift_summary.json", {"orchestration_drift_detected": drift})
    _write("logs/tier3h5_artifact_drift_summary.json", {"artifact_drift_detected": drift, "optional_artifact_skip_drift_detected": drift})
    _write("logs/tier3h5_validation_drift_summary.json", {"validation_drift_detected": drift})
    _write("logs/tier3h5_readiness_drift_summary.json", {"readiness_drift_detected": drift})
    _write("logs/tier3h5_phase5b_monitoring_summary.json", {
        "drift_detected": drift,
        "orchestration_drift_detected": drift,
        "artifact_drift_detected": drift,
        "validation_drift_detected": drift,
        "readiness_drift_detected": drift,
        "optional_artifact_skip_drift_detected": drift,
    })


def test_sparse_history_classification(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5b(False)
    out = run_governance_monitoring_history()
    assert out["trend_classification"] == "insufficient_history_for_trend_analysis"
    assert out["ci_failure_required"] is False


def test_recurring_drift_detection_and_append_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5b(True)
    run_governance_monitoring_history()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d")
    history_file = Path("logs/history/tier3h5_monitoring") / run_id / "monitoring_summary.json"
    assert history_file.exists()
    first = history_file.read_text(encoding="utf-8")

    _seed_phase5b(False)
    out = run_governance_monitoring_history()
    assert history_file.read_text(encoding="utf-8") == first
    assert out["monitoring_history_run_status"] == "success"
    assert out["advisory_only_governance_verified"] is True
    assert out["exact_match_only_preserved"] is True
    assert out["tier3h4_freeze_boundary_preserved"] is True


def test_artifacts_emitted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5b(False)
    run_governance_monitoring_history()
    for path in [
        "logs/tier3h5_monitoring_history_context.json",
        "logs/tier3h5_governance_trend_analytics.json",
        "logs/tier3h5_drift_frequency_summary.json",
        "logs/tier3h5_orchestration_trend_summary.json",
        "logs/tier3h5_artifact_trend_summary.json",
        "logs/tier3h5_readiness_trend_summary.json",
        "logs/tier3h5_phase5c_history_summary.json",
    ]:
        assert Path(path).exists()
