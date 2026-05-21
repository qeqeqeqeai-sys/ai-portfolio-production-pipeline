from copy import deepcopy

from transmission_layers.operationalization.export_envelope import (
    build_dry_run_operational_report,
    build_manifest_export_envelope,
)
from transmission_layers.operationalization.manifests import empty_manifest


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def test_valid_empty_manifest_builds_export_envelope():
    manifest = empty_manifest(**_required_kwargs())
    envelope = build_manifest_export_envelope(manifest)
    assert envelope["export_status"] == "dry_run"
    assert envelope["envelope_type"] == "manifest_export"
    assert envelope["export_ready"] is True


def test_valid_empty_manifest_dry_run_report_builds_successfully():
    manifest = empty_manifest(**_required_kwargs())
    report = build_dry_run_operational_report(manifest)
    assert report["report_status"] == "success"
    assert report["operation_mode"] == "dry_run"
    assert report["operation_type"] == "manifest_export"


def test_export_ready_true_only_when_readiness_is_ready():
    valid_manifest = empty_manifest(**_required_kwargs())
    invalid_manifest = empty_manifest(**_required_kwargs())
    invalid_manifest.pop("run_id")

    valid_envelope = build_manifest_export_envelope(valid_manifest)
    invalid_envelope = build_manifest_export_envelope(invalid_manifest)

    assert valid_envelope["validation_report"]["readiness"]["is_ready"] is True
    assert valid_envelope["export_ready"] is True
    assert invalid_envelope["validation_report"]["readiness"]["is_ready"] is False
    assert invalid_envelope["export_ready"] is False


def test_invalid_manifest_export_ready_false():
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")
    envelope = build_manifest_export_envelope(manifest)
    assert envelope["export_ready"] is False


def test_envelope_contains_copied_manifest_and_does_not_mutate_input():
    manifest = empty_manifest(**_required_kwargs())
    before = deepcopy(manifest)
    envelope = build_manifest_export_envelope(manifest)

    assert manifest == before
    assert envelope["manifest"] == manifest
    assert envelope["manifest"] is not manifest


def test_unknown_extra_fields_preserved_and_warning_non_blocking():
    manifest = empty_manifest(**_required_kwargs())
    manifest["unknown_extra"] = {"nested": ["value"]}
    envelope = build_manifest_export_envelope(manifest)

    assert envelope["manifest"]["unknown_extra"] == {"nested": ["value"]}
    assert envelope["validation_report"]["validation"]["warnings"] == ["unknown_field:unknown_extra"]
    assert envelope["export_ready"] is True


def test_artifact_count_deterministic_for_valid_artifact_inventory():
    manifest = empty_manifest(**_required_kwargs())
    manifest["artifact_inventory"] = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
    envelope = build_manifest_export_envelope(manifest)
    assert envelope["export_summary"]["artifact_count"] == 3


def test_checksum_entry_count_deterministic_for_valid_checksum_inventory():
    manifest = empty_manifest(**_required_kwargs())
    manifest["checksum_inventory"] = {"a": "x", "b": "y"}
    envelope = build_manifest_export_envelope(manifest)
    assert envelope["export_summary"]["checksum_entry_count"] == 2


def test_invalid_artifact_inventory_gives_artifact_count_zero():
    manifest = empty_manifest(**_required_kwargs())
    manifest["artifact_inventory"] = "invalid"
    envelope = build_manifest_export_envelope(manifest)
    assert envelope["export_summary"]["artifact_count"] == 0


def test_invalid_checksum_inventory_gives_checksum_entry_count_zero():
    manifest = empty_manifest(**_required_kwargs())
    manifest["checksum_inventory"] = ["invalid"]
    envelope = build_manifest_export_envelope(manifest)
    assert envelope["export_summary"]["checksum_entry_count"] == 0


def test_envelope_output_stable_across_repeated_calls():
    manifest = empty_manifest(**_required_kwargs())
    manifest["z_extra"] = 2
    manifest["a_extra"] = 1
    first = build_manifest_export_envelope(manifest)
    second = build_manifest_export_envelope(manifest)
    assert first == second


def test_dry_run_report_output_stable_across_repeated_calls():
    manifest = empty_manifest(**_required_kwargs())
    manifest["z_extra"] = 2
    manifest["a_extra"] = 1
    first = build_dry_run_operational_report(manifest)
    second = build_dry_run_operational_report(manifest)
    assert first == second


def test_dry_run_report_summary_mirrors_envelope_summary():
    manifest = empty_manifest(**_required_kwargs())
    manifest["unknown_extra"] = True

    report = build_dry_run_operational_report(manifest)
    envelope = report["export_envelope"]

    assert report["summary"]["export_status"] == envelope["export_status"]
    assert report["summary"]["export_ready"] == envelope["export_ready"]
    assert report["summary"]["validation_status"] == envelope["export_summary"]["validation_status"]
    assert report["summary"]["readiness_status"] == envelope["export_summary"]["readiness_status"]
    assert report["summary"]["readiness_classification"] == envelope["export_summary"]["readiness_classification"]
    assert report["summary"]["artifact_count"] == envelope["export_summary"]["artifact_count"]
    assert report["summary"]["checksum_entry_count"] == envelope["export_summary"]["checksum_entry_count"]
    assert report["summary"]["warning_count"] == envelope["export_summary"]["warning_count"]
    assert report["summary"]["blocking_reason_count"] == envelope["export_summary"]["blocking_reason_count"]
