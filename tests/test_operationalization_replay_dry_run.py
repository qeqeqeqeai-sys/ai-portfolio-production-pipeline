from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import execute_replay_dry_run
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


def test_valid_persisted_empty_manifest_export_produces_ready_dry_run(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    assert result["execution_mode"] == "dry_run"
    assert result["execution_status"] == "simulated"
    assert result["replay_plan"]["plan_status"] == "ready"


def test_invalid_export_produces_blocked_dry_run(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_status"] = "written"
    _write_envelope(export_path, envelope)

    result = execute_replay_dry_run(export_path)
    assert result["execution_status"] == "blocked"
    assert result["simulated_execution"]["simulation_status"] == "blocked"


def test_ready_plan_simulation_is_correct(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    simulation = result["simulated_execution"]

    assert simulation["simulation_status"] == "simulated"
    assert len(simulation["executed_steps"]) == 4
    assert simulation["blocked_steps"] == []
    assert len(simulation["deferred_steps"]) == 1


def test_blocked_plan_simulation_is_correct(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_summary"]["readiness_status"] = "blocked"
    _write_envelope(export_path, envelope)

    result = execute_replay_dry_run(export_path)
    simulation = result["simulated_execution"]

    assert simulation["simulation_status"] == "blocked"
    assert simulation["executed_steps"] == []
    assert len(simulation["blocked_steps"]) == 4
    assert len(simulation["deferred_steps"]) == 1


def test_deferred_step_always_remains_deferred(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    deferred = result["simulated_execution"]["deferred_steps"]
    assert deferred[0]["step_name"] == "await_explicit_replay_engine_phase"
    assert deferred[0]["status"] == "deferred"


def test_replay_execution_enabled_always_false(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    assert result["replay_execution_enabled"] is False


def test_runtime_logic_executed_always_false(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    assert result["simulated_execution"]["runtime_logic_executed"] is False


def test_artifacts_restored_always_false(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    assert result["simulated_execution"]["artifacts_restored"] is False


def test_intelligence_layers_executed_always_false(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    assert result["simulated_execution"]["intelligence_layers_executed"] is False


def test_execution_summary_counts_are_correct(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    summary = result["execution_summary"]
    simulation = result["simulated_execution"]

    assert summary["total_replay_steps"] == len(result["replay_plan"]["replay_steps"])
    assert summary["executed_step_count"] == len(simulation["executed_steps"])
    assert summary["deferred_step_count"] == len(simulation["deferred_steps"])
    assert summary["blocked_step_count"] == len(simulation["blocked_steps"])


def test_repeated_call_output_stability(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = execute_replay_dry_run(export_path)
    second = execute_replay_dry_run(export_path)
    assert first == second


def test_no_file_writes_during_dry_run_execution(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    before_mtime_ns = export_path.stat().st_mtime_ns
    before_content = export_path.read_text(encoding="utf-8")

    _ = execute_replay_dry_run(export_path)

    after_mtime_ns = export_path.stat().st_mtime_ns
    after_content = export_path.read_text(encoding="utf-8")
    assert before_mtime_ns == after_mtime_ns
    assert before_content == after_content


def test_public_api_export_works_from_operationalization(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = execute_replay_dry_run(export_path)
    assert isinstance(result, dict)


def test_no_tier4_smoke_regression(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    _ = execute_replay_dry_run(export_path)
    assert export_path.exists()
