from copy import deepcopy
from pathlib import Path

from transmission_layers.operationalization import (
    build_export_filename,
    persist_manifest_export_envelope,
)
from transmission_layers.operationalization.export_envelope import build_manifest_export_envelope
from transmission_layers.operationalization.manifests import empty_manifest, manifest_checksum
from transmission_layers.operationalization.serialization import stable_serialize


def _required_kwargs():
    return {
        "run_id": "run_20260521_0001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-21T08:00:00+08:00",
    }


def test_build_export_filename_is_deterministic():
    manifest = empty_manifest(**_required_kwargs())
    first = build_export_filename(manifest)
    second = build_export_filename(manifest)
    assert first == second


def test_build_export_filename_uses_manifest_checksum():
    manifest = empty_manifest(**_required_kwargs())
    checksum = manifest_checksum(manifest)
    assert build_export_filename(manifest) == f"manifest_export_{checksum}.json"


def test_valid_empty_manifest_writes_export_file(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = persist_manifest_export_envelope(manifest, tmp_path)
    assert result["persistence_status"] == "written"
    assert Path(result["export_path"]).exists()


def test_written_file_content_is_deterministic_and_matches_envelope(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = persist_manifest_export_envelope(manifest, tmp_path)
    written = Path(result["export_path"]).read_text(encoding="utf-8")
    expected = stable_serialize(build_manifest_export_envelope(manifest))
    assert written == expected


def test_skipped_existing_when_overwrite_false(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    persist_manifest_export_envelope(manifest, tmp_path)
    result = persist_manifest_export_envelope(manifest, tmp_path, overwrite=False)
    assert result["persistence_status"] == "skipped_existing"
    assert result["bytes_written"] == 0


def test_overwrite_true_rewrites_deterministically(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    first = persist_manifest_export_envelope(manifest, tmp_path)
    second = persist_manifest_export_envelope(manifest, tmp_path, overwrite=True)
    assert first["export_path"] == second["export_path"]
    assert first["export_filename"] == second["export_filename"]
    assert second["persistence_status"] == "written"
    assert second["bytes_written"] == first["bytes_written"]


def test_invalid_not_ready_manifest_does_not_write(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    manifest.pop("run_id")
    result = persist_manifest_export_envelope(manifest, tmp_path)
    assert result["persistence_status"] == "not_ready"
    assert result["bytes_written"] == 0
    assert Path(result["export_path"]).exists() is False


def test_bytes_written_deterministic_and_nonzero_only_on_write(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    written = persist_manifest_export_envelope(manifest, tmp_path)
    skipped = persist_manifest_export_envelope(manifest, tmp_path)
    assert written["bytes_written"] > 0
    assert skipped["bytes_written"] == 0


def test_integrity_check_flags_correct_for_written(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    result = persist_manifest_export_envelope(manifest, tmp_path)
    assert result["integrity_check"]["checksum_matches_filename"] is True
    assert result["integrity_check"]["file_written"] is True
    assert result["integrity_check"]["export_path_present"] is True


def test_export_path_and_filename_deterministic_across_calls(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    first = persist_manifest_export_envelope(manifest, tmp_path)
    second = persist_manifest_export_envelope(manifest, tmp_path)
    assert first["export_path"] == second["export_path"]
    assert first["export_filename"] == second["export_filename"]


def test_output_stable_for_repeated_skipped_existing(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    persist_manifest_export_envelope(manifest, tmp_path)
    first = persist_manifest_export_envelope(manifest, tmp_path)
    second = persist_manifest_export_envelope(manifest, tmp_path)
    assert first == second


def test_input_manifest_is_not_mutated(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    before = deepcopy(manifest)
    persist_manifest_export_envelope(manifest, tmp_path)
    assert manifest == before


def test_public_api_exported_from_operationalization_module(tmp_path: Path):
    manifest = empty_manifest(**_required_kwargs())
    filename = build_export_filename(manifest)
    result = persist_manifest_export_envelope(manifest, tmp_path)
    assert filename == result["export_filename"]
