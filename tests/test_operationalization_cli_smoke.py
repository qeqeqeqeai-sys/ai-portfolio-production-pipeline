from __future__ import annotations

from pathlib import Path

import pytest

from transmission_layers.operationalization import run_operationalization_cli_smoke
from transmission_layers.operationalization.cli_smoke import main
from transmission_layers.operationalization.serialization import stable_serialize


def test_run_operationalization_cli_smoke_succeeds_for_valid_empty_manifest(tmp_path: Path):
    result = run_operationalization_cli_smoke(tmp_path)
    assert result["cli_status"] == "success"
    assert result["operation"] == "operationalization_cli_smoke"
    assert result["summary"]["is_verified"] is True


def test_repeated_call_with_same_export_dir_overwrite_false_is_stable(tmp_path: Path):
    _ = run_operationalization_cli_smoke(tmp_path)
    first = run_operationalization_cli_smoke(tmp_path, overwrite=False)
    second = run_operationalization_cli_smoke(tmp_path, overwrite=False)
    assert first == second
    assert first["summary"]["persistence_status"] == "skipped_existing"


def test_summary_mirrors_audit_summary_fields(tmp_path: Path):
    result = run_operationalization_cli_smoke(tmp_path)
    audit_summary = result["audit"]["audit_summary"]
    summary = result["summary"]

    assert summary["audit_status"] == result["audit"]["audit_status"]
    assert summary["operation_mode"] == result["audit"]["operation_mode"]
    assert summary["validation_status"] == audit_summary["validation_status"]
    assert summary["readiness_status"] == audit_summary["readiness_status"]
    assert summary["readiness_classification"] == audit_summary["readiness_classification"]
    assert summary["export_status"] == audit_summary["export_status"]
    assert summary["export_ready"] == audit_summary["export_ready"]
    assert summary["persistence_status"] == audit_summary["persistence_status"]
    assert summary["verification_status"] == audit_summary["verification_status"]
    assert summary["is_verified"] == audit_summary["is_verified"]


def test_overwrite_true_path_remains_deterministic_and_verified(tmp_path: Path):
    _ = run_operationalization_cli_smoke(tmp_path)
    first = run_operationalization_cli_smoke(tmp_path, overwrite=True)
    second = run_operationalization_cli_smoke(tmp_path, overwrite=True)
    assert first == second
    assert first["summary"]["persistence_status"] == "written"
    assert first["summary"]["is_verified"] is True


def test_main_returns_zero_for_valid_run_and_prints_stable_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    exit_code = main(["--export-dir", str(tmp_path), "--overwrite"])
    captured = capsys.readouterr()

    payload = run_operationalization_cli_smoke(tmp_path, overwrite=True)
    assert exit_code == 0
    assert captured.out.strip() == stable_serialize(payload)


def test_main_requires_export_dir_under_argparse_behavior():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code != 0


def test_public_api_export_works(tmp_path: Path):
    result = run_operationalization_cli_smoke(tmp_path)
    assert isinstance(result, dict)
    assert result["operation"] == "operationalization_cli_smoke"
