from transmission_layers.operationalization.manifests import (
    build_run_manifest,
    empty_manifest,
    manifest_checksum,
)
from transmission_layers.operationalization.serialization import stable_serialize


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def test_manifest_contains_all_required_fields():
    manifest = build_run_manifest(**_required_kwargs())
    expected_fields = {
        "run_id",
        "run_type",
        "tier_scope",
        "generated_at_sgt",
        "schema_version",
        "execution_status",
        "artifact_inventory",
        "checksum_inventory",
        "replay_compatibility",
        "chronology_summary",
    }
    assert set(manifest.keys()) == expected_fields


def test_repeated_construction_with_same_inputs_is_identical():
    kwargs = _required_kwargs()
    kwargs["artifact_inventory"] = [{"kind": "summary", "path": "logs/summary.json"}]
    kwargs["checksum_inventory"] = {"summary": "op_1234abcd1234abcd"}
    first = build_run_manifest(**kwargs)
    second = build_run_manifest(**kwargs)
    assert first == second
    assert stable_serialize(first) == stable_serialize(second)


def test_manifest_checksum_is_stable():
    manifest = build_run_manifest(**_required_kwargs())
    assert manifest_checksum(manifest) == manifest_checksum(manifest)


def test_input_collections_are_not_mutated():
    artifact_inventory = [{"kind": "a", "path": "p"}]
    checksum_inventory = {"a": "manifest_abcdef1234567890"}
    manifest = build_run_manifest(
        **_required_kwargs(),
        artifact_inventory=artifact_inventory,
        checksum_inventory=checksum_inventory,
    )

    assert artifact_inventory == [{"kind": "a", "path": "p"}]
    assert checksum_inventory == {"a": "manifest_abcdef1234567890"}
    assert manifest["artifact_inventory"] is not artifact_inventory
    assert manifest["checksum_inventory"] is not checksum_inventory


def test_missing_optional_inputs_default_deterministically():
    manifest = build_run_manifest(**_required_kwargs())
    assert manifest["schema_version"] == "o1b.v1"
    assert manifest["execution_status"] == "pending"
    assert manifest["artifact_inventory"] == []
    assert manifest["checksum_inventory"] == {}
    assert manifest["replay_compatibility"] == "deterministic_payload_only"
    assert manifest["chronology_summary"] == "unspecified"


def test_empty_manifest_is_valid_shaped():
    manifest = empty_manifest(**_required_kwargs())
    assert manifest["artifact_inventory"] == []
    assert manifest["checksum_inventory"] == {}
    assert set(manifest.keys()) == {
        "run_id",
        "run_type",
        "tier_scope",
        "generated_at_sgt",
        "schema_version",
        "execution_status",
        "artifact_inventory",
        "checksum_inventory",
        "replay_compatibility",
        "chronology_summary",
    }


def test_changing_payload_changes_checksum():
    base = build_run_manifest(**_required_kwargs())
    changed = build_run_manifest(**_required_kwargs(), chronology_summary="phase_complete")
    assert manifest_checksum(base) != manifest_checksum(changed)
