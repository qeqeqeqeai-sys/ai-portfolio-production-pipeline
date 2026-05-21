from copy import deepcopy

from transmission_layers.operationalization.manifests import empty_manifest
from transmission_layers.operationalization.readiness import (
    assess_manifest_readiness,
    build_manifest_validation_report,
)


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def test_valid_empty_manifest_is_ready():
    manifest = empty_manifest(**_required_kwargs())
    result = assess_manifest_readiness(manifest)
    assert result["is_ready"] is True
    assert result["readiness_classification"] == "ready"


def test_invalid_manifest_is_not_ready_with_invalid_manifest_classification():
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")
    result = assess_manifest_readiness(manifest)
    assert result["is_ready"] is False
    assert result["readiness_classification"] == "invalid_manifest"


def test_replay_compatibility_failure_classifies_as_replay_incompatible():
    manifest = empty_manifest(**_required_kwargs())
    manifest["replay_compatibility"] = {"status": "incompatible"}
    result = assess_manifest_readiness(manifest)
    assert result["readiness_classification"] == "replay_incompatible"


def test_artifact_inventory_failure_classifies_as_artifact_inventory_invalid():
    manifest = empty_manifest(**_required_kwargs())
    manifest["artifact_inventory"] = [{"name": "artifact_a", "status": "invalid"}]
    result = assess_manifest_readiness(manifest)
    assert result["readiness_classification"] == "artifact_inventory_invalid"


def test_checksum_inventory_failure_classifies_as_checksum_inventory_invalid():
    manifest = empty_manifest(**_required_kwargs())
    manifest["checksum_inventory"] = {"status": "invalid"}
    result = assess_manifest_readiness(manifest)
    assert result["readiness_classification"] == "checksum_inventory_invalid"


def test_chronology_failure_classifies_as_chronology_invalid():
    manifest = empty_manifest(**_required_kwargs())
    manifest["chronology_summary"] = {"status": "invalid"}
    result = assess_manifest_readiness(manifest)
    assert result["readiness_classification"] == "chronology_invalid"


def test_classification_precedence_is_deterministic():
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")
    manifest["replay_compatibility"] = {"status": "incompatible"}
    manifest["chronology_summary"] = {"status": "invalid"}
    result = assess_manifest_readiness(manifest)
    assert result["readiness_classification"] == "invalid_manifest"


def test_unknown_extra_field_creates_warning_but_remains_ready():
    manifest = empty_manifest(**_required_kwargs())
    manifest["zzz_unknown"] = "allowed"
    result = assess_manifest_readiness(manifest)
    assert result["is_ready"] is True
    assert result["warnings"] == ["unknown_field:zzz_unknown"]


def test_report_contains_validation_readiness_and_summary():
    manifest = empty_manifest(**_required_kwargs())
    report = build_manifest_validation_report(manifest)
    assert report["report_status"] == "success"
    assert "validation" in report
    assert "readiness" in report
    assert "summary" in report


def test_report_summary_counts_are_correct():
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")
    manifest["a_unknown"] = 1
    report = build_manifest_validation_report(manifest)
    assert report["summary"]["error_count"] == 1
    assert report["summary"]["warning_count"] == 1
    assert report["summary"]["blocking_reason_count"] == 1


def test_readiness_output_stable_across_repeated_calls():
    manifest = empty_manifest(**_required_kwargs())
    manifest["b_unknown"] = 2
    manifest["a_unknown"] = 1
    first = assess_manifest_readiness(manifest)
    second = assess_manifest_readiness(manifest)
    assert first == second


def test_report_output_stable_across_repeated_calls():
    manifest = empty_manifest(**_required_kwargs())
    manifest["b_unknown"] = 2
    manifest["a_unknown"] = 1
    first = build_manifest_validation_report(manifest)
    second = build_manifest_validation_report(manifest)
    assert first == second


def test_readiness_and_report_do_not_mutate_input():
    manifest = empty_manifest(**_required_kwargs())
    manifest["a_unknown"] = 1
    before = deepcopy(manifest)
    _ = assess_manifest_readiness(manifest)
    _ = build_manifest_validation_report(manifest)
    assert manifest == before
