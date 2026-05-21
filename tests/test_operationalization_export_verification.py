from copy import deepcopy
from pathlib import Path

from transmission_layers.operationalization import (
    load_manifest_export_envelope,
    verify_manifest_export_envelope,
)
from transmission_layers.operationalization.export_envelope import build_manifest_export_envelope
from transmission_layers.operationalization.export_persistence import (
    build_export_filename,
    persist_manifest_export_envelope,
)
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


def test_persisted_valid_empty_manifest_export_verifies_successfully(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = verify_manifest_export_envelope(export_path)
    assert result["verification_status"] == "valid"
    assert result["is_verified"] is True
    assert result["errors"] == []


def test_load_manifest_export_envelope_returns_persisted_envelope_dict(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    expected = build_manifest_export_envelope(manifest)
    assert load_manifest_export_envelope(export_path) == expected


def test_missing_or_invalid_envelope_type_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["envelope_type"] = "not_manifest_export"
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["is_verified"] is False
    assert "invalid_envelope_type" in result["errors"]


def test_missing_or_invalid_export_status_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_status"] = "written"
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["is_verified"] is False
    assert "invalid_export_status" in result["errors"]


def test_missing_manifest_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope.pop("manifest")
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["is_verified"] is False
    assert "missing_manifest" in result["errors"]


def test_filename_mismatch_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    bad_path = export_path.parent / "manifest_export_deadbeef.json"
    _write_envelope(bad_path, envelope)
    result = verify_manifest_export_envelope(bad_path)
    assert result["is_verified"] is False
    assert "filename_manifest_checksum_mismatch" in result["errors"]


def test_export_ready_mismatch_against_readiness_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_ready"] = not envelope["validation_report"]["readiness"]["is_ready"]
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["is_verified"] is False
    assert "export_ready_readiness_mismatch" in result["errors"]


def test_missing_validation_report_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope.pop("validation_report")
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["is_verified"] is False
    assert "missing_validation_report" in result["errors"]


def test_missing_export_summary_fails_verification(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope.pop("export_summary")
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["is_verified"] is False
    assert "missing_export_summary" in result["errors"]
    assert result["export_summary"] == {}


def test_errors_are_deterministic_and_sorted(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    envelope = {
        "export_ready": True,
        "manifest": "not-a-mapping",
        "validation_report": "not-a-mapping",
        "export_summary": "not-a-mapping",
    }
    _write_envelope(export_path, envelope)
    result = verify_manifest_export_envelope(export_path)
    assert result["errors"] == sorted(result["errors"])
    assert result["verification_status"] == "invalid"


def test_verification_output_stable_across_repeated_calls(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = verify_manifest_export_envelope(export_path)
    second = verify_manifest_export_envelope(export_path)
    assert first == second


def test_load_and_verify_do_not_mutate_loaded_envelope(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    baseline = build_manifest_export_envelope(manifest)
    loaded = load_manifest_export_envelope(export_path)
    loaded_before = deepcopy(loaded)
    _ = verify_manifest_export_envelope(export_path)
    loaded_after = load_manifest_export_envelope(export_path)
    assert loaded == loaded_before
    assert loaded_after == baseline


def test_public_api_exports_work_from_operationalization(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = persist_manifest_export_envelope(manifest, tmp_path)
    export_path = Path(result["export_path"])
    filename = build_export_filename(manifest)
    loaded = load_manifest_export_envelope(export_path)
    verified = verify_manifest_export_envelope(export_path)
    assert export_path.name == filename
    assert isinstance(loaded, dict)
    assert verified["is_verified"] is True
