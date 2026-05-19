from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_control_plane import run_governance_control_plane


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed() -> None:
    _write("logs/tier3h5_orchestration_summary.json", {"ok": True})
    _write("logs/tier3h5_monitoring_context.json", {"ok": True})
    _write("logs/tier3h5_governance_trend_analytics.json", {"ok": True})
    _write("logs/tier3h5_release_confidence_summary.json", {"ok": True})
    _write("logs/tier3h5_governance_lineage_manifest.json", {"ok": True})


def test_missing_optional_inputs_and_sparse_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_governance_control_plane()
    assert out["control_plane_run_status"] == "success"
    assert out["governance_transition_registry_status"] == "insufficient_state_history"


def test_deterministic_state_registry_and_manifest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed()
    a = run_governance_control_plane()
    b = run_governance_control_plane()
    assert a["control_plane_categories"]["state_registry"] == b["control_plane_categories"]["state_registry"]
    assert a["control_plane_categories"]["state_manifest"]["state_manifest_id"] == b["control_plane_categories"]["state_manifest"]["state_manifest_id"]


def test_transition_registry_exact_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed()
    run_governance_control_plane()
    _write("logs/tier3h5_phase5d_reporting_summary.json", {"new": "artifact"})
    out = run_governance_control_plane()
    assert out["transition_records_generated"] >= 1


def test_output_artifacts_and_invariants(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed()
    out = run_governance_control_plane()
    assert out["advisory_only_governance_verified"] is True
    assert out["exact_match_only_preserved"] is True
    assert out["tier3h4_freeze_boundary_preserved"] is True
    for path in [
        "logs/tier3h5_control_plane_context.json",
        "logs/tier3h5_governance_state_registry.json",
        "logs/tier3h5_governance_state_manifest.json",
        "logs/tier3h5_governance_transition_registry.json",
        "logs/tier3h5_governance_invariant_registry.json",
        "logs/tier3h5_operational_posture_registry.json",
        "logs/tier3h5_release_posture_registry.json",
        "logs/tier3h5_lineage_posture_registry.json",
        "logs/tier3h5_phase5f_control_plane_summary.json",
    ]:
        assert Path(path).exists()
