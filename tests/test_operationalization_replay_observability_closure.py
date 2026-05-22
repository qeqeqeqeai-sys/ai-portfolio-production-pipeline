from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import (
    build_replay_integrity_diagnostics,
    build_replay_observability_summary,
    run_replay_observability_closure,
)
from transmission_layers.operationalization.export_envelope import build_manifest_export_envelope
from transmission_layers.operationalization.export_persistence import persist_manifest_export_envelope
from transmission_layers.operationalization.manifests import empty_manifest
from transmission_layers.operationalization.serialization import stable_serialize


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def _persist_valid_fixture(tmp_path: Path) -> tuple[dict, Path]:
    manifest = empty_manifest(**_required_kwargs())
    persisted = persist_manifest_export_envelope(manifest, tmp_path)
    return manifest, Path(persisted["export_path"])


def _write_envelope(path: Path, envelope: dict) -> None:
    path.write_text(stable_serialize(envelope), encoding="utf-8")


def test_deterministic_repeated_output(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = run_replay_observability_closure(export_path)
    second = run_replay_observability_closure(export_path)
    assert first == second


def test_checksum_signature_stability(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = run_replay_observability_closure(export_path)
    second = run_replay_observability_closure(export_path)
    assert first["checksum"] == second["checksum"]
    assert first["replay_integrity"]["replay_plan_checksum"] == second["replay_integrity"]["replay_plan_checksum"]


def test_immutable_input_safety_and_no_writes(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    before_text = export_path.read_text(encoding="utf-8")
    before_mtime = export_path.stat().st_mtime_ns
    _ = run_replay_observability_closure(export_path)
    after_text = export_path.read_text(encoding="utf-8")
    after_mtime = export_path.stat().st_mtime_ns
    assert before_text == after_text
    assert before_mtime == after_mtime


def test_valid_replay_ready_case(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_replay_observability_closure(export_path)
    assert result["status"] == "ready"
    assert result["replay_integrity"]["status"] == "ready"


def test_blocked_replay_case(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_summary"]["readiness_status"] = "blocked"
    _write_envelope(export_path, envelope)

    result = run_replay_observability_closure(export_path)
    assert result["status"] == "blocked"
    assert result["observability"]["degradation_state"] == "blocked"


def test_empty_minimal_replay_plan_handling(tmp_path: Path):
    minimal_path = tmp_path / "missing.json"
    result = run_replay_observability_closure(minimal_path)
    assert result["status"] == "invalid_input"
    assert result["observability"]["counts"]["total_replay_steps"] == 0


def test_no_runtime_execution_and_no_restore(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_replay_observability_closure(export_path)
    assert result["invariants"]["executes_runtime_logic"] is False
    assert result["invariants"]["restores_artifacts"] is False


def test_no_external_mutation_behavior(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_replay_observability_closure(export_path)
    assert result["invariants"]["mutates_external_state"] is False


def test_public_api_export(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert isinstance(build_replay_integrity_diagnostics(export_path), dict)
    assert isinstance(build_replay_observability_summary(export_path), dict)
    assert isinstance(run_replay_observability_closure(export_path), dict)
