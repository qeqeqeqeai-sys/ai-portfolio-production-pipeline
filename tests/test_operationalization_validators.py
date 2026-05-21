from copy import deepcopy

from transmission_layers.operationalization.manifests import empty_manifest
from transmission_layers.operationalization.validators import validate_run_manifest


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def test_valid_empty_manifest_passes():
    manifest = empty_manifest(**_required_kwargs())
    result = validate_run_manifest(manifest)
    assert result["is_valid"] is True
    assert result["validation_status"] == "valid"
    assert result["errors"] == []


def test_manifest_missing_required_field_fails():
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")
    result = validate_run_manifest(manifest)
    assert result["is_valid"] is False
    assert "missing_required_field:run_id" in result["errors"]


def test_wrong_artifact_inventory_type_fails():
    manifest = empty_manifest(**_required_kwargs())
    manifest["artifact_inventory"] = "not-a-list"
    result = validate_run_manifest(manifest)
    assert result["artifact_inventory_valid"] is False
    assert "invalid_type:artifact_inventory:list_like_required" in result["errors"]


def test_wrong_checksum_inventory_type_fails():
    manifest = empty_manifest(**_required_kwargs())
    manifest["checksum_inventory"] = []
    result = validate_run_manifest(manifest)
    assert result["checksum_inventory_valid"] is False
    assert "invalid_type:checksum_inventory:mapping_like_required" in result["errors"]


def test_wrong_replay_compatibility_type_fails():
    manifest = empty_manifest(**_required_kwargs())
    manifest["replay_compatibility"] = 123
    result = validate_run_manifest(manifest)
    assert result["replay_compatibility_valid"] is False
    assert "invalid_type:replay_compatibility:mapping_like_required" in result["errors"]


def test_wrong_chronology_summary_type_fails():
    manifest = empty_manifest(**_required_kwargs())
    manifest["chronology_summary"] = 123
    result = validate_run_manifest(manifest)
    assert result["chronology_summary_valid"] is False
    assert "invalid_type:chronology_summary:mapping_like_required" in result["errors"]


def test_unknown_extra_field_warns_but_is_valid():
    manifest = empty_manifest(**_required_kwargs())
    manifest["zzz_unknown"] = "allowed"
    result = validate_run_manifest(manifest)
    assert result["is_valid"] is True
    assert result["warnings"] == ["unknown_field:zzz_unknown"]


def test_validation_output_is_stable_across_repeated_calls():
    manifest = empty_manifest(**_required_kwargs())
    manifest["b_unknown"] = 2
    manifest["a_unknown"] = 1
    first = validate_run_manifest(manifest)
    second = validate_run_manifest(manifest)
    assert first == second


def test_validator_does_not_mutate_input_manifest():
    manifest = empty_manifest(**_required_kwargs())
    manifest["artifact_inventory"] = [{"k": "v"}]
    before = deepcopy(manifest)
    _ = validate_run_manifest(manifest)
    assert manifest == before
