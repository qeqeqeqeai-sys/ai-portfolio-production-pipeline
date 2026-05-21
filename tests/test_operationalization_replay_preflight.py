from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import build_replay_engine_preflight
from transmission_layers.operationalization.export_envelope import build_manifest_export_envelope
from transmission_layers.operationalization.export_persistence import persist_manifest_export_envelope
from transmission_layers.operationalization.manifests import empty_manifest
from transmission_layers.operationalization.serialization import stable_serialize


REQUIRED_PREFLIGHT_CHECKS = {
    "export_verification_passed",
    "replay_contract_ready",
    "replay_guardrails_passed",
    "replay_execution_disabled",
    "no_artifact_restore_policy",
    "no_scheduler_policy",
    "no_database_write_policy",
    "no_new_persistence_behavior_policy",
    "tier4_tier5_isolation_policy",
    "deterministic_report_policy",
}


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


def test_valid_persisted_empty_manifest_export_passes_preflight(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert result["preflight_status"] == "passed"


def test_invalid_export_verification_fails_preflight(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_status"] = "written"
    _write_envelope(export_path, envelope)

    result = build_replay_engine_preflight(export_path)
    assert result["preflight_status"] == "failed"
    assert "export_verification_passed" in result["failed_checks"]


def test_replay_contract_not_ready_fails_preflight(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_summary"]["readiness_status"] = "blocked"
    _write_envelope(export_path, envelope)

    result = build_replay_engine_preflight(export_path)
    assert result["preflight_status"] == "failed"
    assert "replay_contract_ready" in result["failed_checks"]


def test_guardrail_report_is_included_and_passed(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert result["guardrails"]["guardrail_status"] == "passed"


def test_replay_engine_allowed_to_execute_now_is_always_false(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert result["preflight_summary"]["replay_engine_allowed_to_execute_now"] is False


def test_future_engine_phase_required_is_always_true(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert result["preflight_summary"]["future_engine_phase_required"] is True


def test_preflight_checks_include_all_required_names(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert set(result["preflight_checks"].keys()) == REQUIRED_PREFLIGHT_CHECKS


def test_passed_failed_warning_lists_are_sorted_deterministically(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert result["passed_checks"] == sorted(result["passed_checks"])
    assert result["failed_checks"] == sorted(result["failed_checks"])
    assert result["warning_checks"] == sorted(result["warning_checks"])


def test_preflight_status_mirrors_failed_checks(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    expected = "passed" if not result["failed_checks"] else "failed"
    assert result["preflight_status"] == expected


def test_summary_counts_are_correct(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    summary = result["preflight_summary"]
    assert summary["total_checks"] == len(result["preflight_checks"])
    assert summary["passed_check_count"] == len(result["passed_checks"])
    assert summary["failed_check_count"] == len(result["failed_checks"])
    assert summary["warning_check_count"] == len(result["warning_checks"])


def test_output_stable_across_repeated_calls(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = build_replay_engine_preflight(export_path)
    second = build_replay_engine_preflight(export_path)
    assert first == second


def test_no_file_writes_during_preflight(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    before_mtime_ns = export_path.stat().st_mtime_ns
    before_content = export_path.read_text(encoding="utf-8")

    _ = build_replay_engine_preflight(export_path)

    after_mtime_ns = export_path.stat().st_mtime_ns
    after_content = export_path.read_text(encoding="utf-8")
    assert before_mtime_ns == after_mtime_ns
    assert before_content == after_content


def test_public_api_export_works_from_operationalization(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_engine_preflight(export_path)
    assert isinstance(result, dict)


def test_no_tier4_smoke_regression(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    _ = build_replay_engine_preflight(export_path)
    assert export_path.exists()
