from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_monitoring import run_governance_production_monitoring


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_phase5a() -> None:
    _write("logs/tier3h5_orchestration_summary.json", {"stages": [{"stage_name": "s1", "required": True}], "optional_artifacts_skipped": []})
    _write("logs/tier3h5_orchestration_runtime_context.json", {"ok": True})
    _write("logs/tier3h5_orchestration_guardrails.json", {"validation_results": [{"name": "basic", "status": "pass"}]})
    _write("logs/tier3h5_artifact_coordination_summary.json", {"artifact_inventory": ["a", "b"]})
    _write("logs/tier3h5_upload_coordination_summary.json", {"dashboard_inventory": ["d1"], "semantic_layer_ready": True, "smoke_tests": ["pass"], "operational_readiness": "ready"})
    _write("logs/tier3h5_phase5a_orchestration_summary.json", {"phase": "5a"})


def test_sparse_history_and_missing_optional(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5a()
    Path("logs/tier3h5_upload_coordination_summary.json").unlink()
    out = run_governance_production_monitoring()
    assert out["monitoring_history_status"] == "insufficient_monitoring_history"
    assert out["drift_severity"] == "insufficient_monitoring_history"


def test_no_drift_and_deterministic_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5a()
    first = run_governance_production_monitoring()
    second = run_governance_production_monitoring()
    assert second["monitoring_history_status"] == "history_available"
    assert second["drift_severity"] == "no_drift_detected"
    assert first["governance_invariants"] == second["governance_invariants"]


def test_detects_stage_artifact_validation_and_invariants(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5a()
    run_governance_production_monitoring()

    _seed_phase5a()
    _write("logs/tier3h5_orchestration_summary.json", {"stages": [{"stage_name": "s1", "required": True}, {"stage_name": "s2", "required": True}], "optional_artifacts_skipped": ["x"]})
    _write("logs/tier3h5_artifact_coordination_summary.json", {"artifact_inventory": ["a", "c"]})
    _write("logs/tier3h5_orchestration_guardrails.json", {"validation_results": [{"name": "basic", "status": "fail"}]})

    out = run_governance_production_monitoring()
    assert out["orchestration_drift_detected"] is True
    assert out["artifact_drift_detected"] is True
    assert out["validation_drift_detected"] is True
    assert out["optional_artifact_skip_drift_detected"] is True
    assert out["governance_invariants"]["advisory_only_governance_verified"] is True
    assert out["governance_invariants"]["exact_match_only_preserved"] is True
    assert out["governance_invariants"]["tier3h4_freeze_boundary_preserved"] is True
