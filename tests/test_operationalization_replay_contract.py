from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import (
    assess_replay_contract,
    build_replay_plan_skeleton,
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


def test_valid_persisted_empty_manifest_export_is_replay_ready(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = assess_replay_contract(export_path)

    assert result["replay_ready"] is True
    assert result["replay_contract_status"] == "replay_ready"
    assert result["blocking_reasons"] == []


def test_invalid_verification_makes_replay_contract_not_ready(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_status"] = "written"
    _write_envelope(export_path, envelope)

    result = assess_replay_contract(export_path)
    assert result["replay_ready"] is False
    assert result["replay_contract_status"] == "not_replay_ready"


def test_replay_contract_output_stable_across_repeated_calls(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = assess_replay_contract(export_path)
    second = assess_replay_contract(export_path)
    assert first == second


def test_blocking_reasons_are_sorted_deterministically(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    _write_envelope(export_path, {"manifest": "bad"})

    result = assess_replay_contract(export_path)
    assert result["blocking_reasons"] == sorted(result["blocking_reasons"])


def test_replay_plan_skeleton_ready_for_verified_export(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_plan_skeleton(export_path)

    assert result["plan_status"] == "ready"
    assert all(step["status"] == "available" for step in result["replay_steps"][:4])
    assert result["replay_steps"][4]["status"] == "deferred"


def test_replay_plan_skeleton_blocked_for_invalid_export(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope.pop("manifest")
    _write_envelope(export_path, envelope)

    result = build_replay_plan_skeleton(export_path)
    assert result["plan_status"] == "blocked"
    assert all(step["status"] == "blocked" for step in result["replay_steps"][:4])
    assert result["replay_steps"][4]["status"] == "deferred"


def test_replay_steps_are_deterministic_and_exactly_named(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = build_replay_plan_skeleton(export_path)

    assert [step["step_name"] for step in result["replay_steps"]] == [
        "load_export_envelope",
        "verify_export_integrity",
        "validate_manifest_contract",
        "assess_replay_readiness",
        "await_explicit_replay_engine_phase",
    ]
    assert all(step["executes_runtime_logic"] is False for step in result["replay_steps"])


def test_replay_execution_enabled_is_always_false(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)

    contract = assess_replay_contract(export_path)
    plan = build_replay_plan_skeleton(export_path)

    assert contract["replay_contract_status"] in {"replay_ready", "not_replay_ready"}
    assert plan["replay_execution_enabled"] is False
    assert plan["summary"]["replay_execution_enabled"] is False


def test_no_replay_execution_or_file_writes_during_assessment_or_plan_build(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    before_mtime_ns = export_path.stat().st_mtime_ns
    before_content = export_path.read_text(encoding="utf-8")

    _ = assess_replay_contract(export_path)
    _ = build_replay_plan_skeleton(export_path)

    after_mtime_ns = export_path.stat().st_mtime_ns
    after_content = export_path.read_text(encoding="utf-8")
    assert before_mtime_ns == after_mtime_ns
    assert before_content == after_content


def test_public_api_export_works_from_operationalization(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    contract = assess_replay_contract(export_path)
    plan = build_replay_plan_skeleton(export_path)

    assert isinstance(contract, dict)
    assert isinstance(plan, dict)
