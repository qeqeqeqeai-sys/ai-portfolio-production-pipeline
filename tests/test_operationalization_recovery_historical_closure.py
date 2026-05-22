from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import (
    build_historical_reconstruction_summary,
    build_recovery_safety_diagnostics,
    run_recovery_historical_closure,
    run_replay_observability_closure,
)
from transmission_layers.operationalization.export_envelope import build_manifest_export_envelope
from transmission_layers.operationalization.export_persistence import persist_manifest_export_envelope
from transmission_layers.operationalization.manifests import empty_manifest
from transmission_layers.operationalization.serialization import stable_serialize


def _required_kwargs():
    return {
        "run_id": "run_20260522_1001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-22T08:00:00+08:00",
    }


def _persist_valid_fixture(tmp_path: Path) -> tuple[dict, Path]:
    manifest = empty_manifest(**_required_kwargs())
    persisted = persist_manifest_export_envelope(manifest, tmp_path)
    return manifest, Path(persisted["export_path"])


def _write_envelope(path: Path, envelope: dict) -> None:
    path.write_text(stable_serialize(envelope), encoding="utf-8")


def test_deterministic_repeated_output(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert run_recovery_historical_closure(export_path) == run_recovery_historical_closure(export_path)


def test_checksum_stability(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = run_recovery_historical_closure(export_path)
    second = run_recovery_historical_closure(export_path)
    assert first["checksum"] == second["checksum"]


def test_immutable_input_safety_and_no_writes(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    before_text = export_path.read_text(encoding="utf-8")
    before_mtime = export_path.stat().st_mtime_ns
    _ = run_recovery_historical_closure(export_path)
    assert before_text == export_path.read_text(encoding="utf-8")
    assert before_mtime == export_path.stat().st_mtime_ns


def test_recovery_ready_case(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_recovery_historical_closure(export_path)
    assert result["status"] == "ready"
    assert result["recovery_safety"]["status"] == "ready"


def test_recovery_blocked_case(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_ready"] = False
    _write_envelope(export_path, envelope)
    result = run_recovery_historical_closure(export_path)
    assert result["status"] == "blocked"
    assert result["recovery_safety"]["status"] == "blocked"


def test_historical_reconstruction_degraded_case(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_summary"]["readiness_status"] = "blocked"
    _write_envelope(export_path, envelope)
    result = build_historical_reconstruction_summary(export_path)
    assert result["status"] == "degraded"


def test_invalid_and_minimal_input_case(tmp_path: Path):
    result = run_recovery_historical_closure(tmp_path / "missing.json")
    assert result["status"] == "invalid_input"


def test_no_runtime_restore_or_mutation_invariants(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_recovery_historical_closure(export_path)
    assert result["invariants"]["executes_runtime_logic"] is False
    assert result["invariants"]["restores_artifacts"] is False
    assert result["invariants"]["mutates_external_state"] is False


def test_public_api_export(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert isinstance(build_recovery_safety_diagnostics(export_path), dict)
    assert isinstance(build_historical_reconstruction_summary(export_path), dict)
    assert isinstance(run_recovery_historical_closure(export_path), dict)


def test_o1_replay_observability_non_regression(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert run_replay_observability_closure(export_path)["status"] == "ready"
