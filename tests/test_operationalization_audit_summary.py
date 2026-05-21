from copy import deepcopy
from pathlib import Path

from transmission_layers.operationalization import build_operational_audit_summary
from transmission_layers.operationalization.manifests import empty_manifest


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def test_valid_empty_manifest_audit_succeeds_and_verifies(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = build_operational_audit_summary(manifest, tmp_path)
    assert result["audit_status"] == "success"
    assert result["operation_mode"] == "deterministic_audit"
    assert result["persistence"]["persistence_status"] == "written"
    assert result["verification"]["verification_status"] == "valid"
    assert result["verification"]["is_verified"] is True


def test_invalid_not_ready_manifest_skips_verification_with_not_applicable(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")

    result = build_operational_audit_summary(manifest, tmp_path)

    assert result["persistence"]["persistence_status"] == "not_ready"
    assert result["verification"] == {
        "verification_status": "not_applicable",
        "is_verified": False,
        "export_path": result["persistence"]["export_path"],
        "export_filename": result["persistence"]["export_filename"],
        "errors": [],
        "warnings": [],
        "integrity_check": {},
        "export_summary": {},
    }


def test_skipped_existing_persistence_still_verifies_existing_export(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    _ = build_operational_audit_summary(manifest, tmp_path)
    second = build_operational_audit_summary(manifest, tmp_path)

    assert second["persistence"]["persistence_status"] == "skipped_existing"
    assert second["verification"]["verification_status"] == "valid"
    assert second["verification"]["is_verified"] is True


def test_overwrite_true_produces_written_persistence_and_verifies(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    _ = build_operational_audit_summary(manifest, tmp_path)
    overwritten = build_operational_audit_summary(manifest, tmp_path, overwrite=True)

    assert overwritten["persistence"]["overwrite"] is True
    assert overwritten["persistence"]["persistence_status"] == "written"
    assert overwritten["verification"]["verification_status"] == "valid"


def test_audit_summary_fields_mirror_upstream_sections(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = build_operational_audit_summary(manifest, tmp_path)

    summary = result["audit_summary"]
    validation_summary = result["validation_report"]["summary"]
    export_summary = result["export_envelope"]["export_summary"]

    assert summary["validation_status"] == validation_summary["validation_status"]
    assert summary["readiness_status"] == validation_summary["readiness_status"]
    assert summary["readiness_classification"] == validation_summary["readiness_classification"]
    assert summary["export_status"] == result["export_envelope"]["export_status"]
    assert summary["export_ready"] == result["export_envelope"]["export_ready"]
    assert summary["persistence_status"] == result["persistence"]["persistence_status"]
    assert summary["verification_status"] == result["verification"]["verification_status"]
    assert summary["is_verified"] == result["verification"]["is_verified"]
    assert summary["error_count"] == validation_summary["error_count"]
    assert summary["warning_count"] == validation_summary["warning_count"]
    assert summary["blocking_reason_count"] == validation_summary["blocking_reason_count"]
    assert summary["artifact_count"] == export_summary["artifact_count"]
    assert summary["checksum_entry_count"] == export_summary["checksum_entry_count"]


def test_audit_output_stable_for_repeated_skipped_existing_calls(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    _ = build_operational_audit_summary(manifest, tmp_path)

    first = build_operational_audit_summary(manifest, tmp_path)
    second = build_operational_audit_summary(manifest, tmp_path)
    assert first == second


def test_input_manifest_is_not_mutated(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    before = deepcopy(manifest)
    _ = build_operational_audit_summary(manifest, tmp_path)
    assert manifest == before


def test_public_api_export_works_from_operationalization(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = build_operational_audit_summary(manifest, tmp_path)
    assert isinstance(result, dict)
    assert result["audit_status"] == "success"
