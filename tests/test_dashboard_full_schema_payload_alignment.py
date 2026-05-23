from __future__ import annotations

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    DASHBOARD_REQUIRED_NOT_NULL_COLUMNS,
    build_d1_seed_payload,
    build_dashboard_required_field_alignment_report,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_seed_manifests import stable_checksum


def test_every_required_not_null_column_is_populated() -> None:
    payload = build_d1_seed_payload()
    for table, required_columns in DASHBOARD_REQUIRED_NOT_NULL_COLUMNS.items():
        assert payload[table]
        for row in payload[table]:
            for col in required_columns:
                assert col in row
                assert row[col] is not None


def test_payload_generation_is_deterministic_and_checksum_stable() -> None:
    first = build_d1_seed_payload()
    second = build_d1_seed_payload()
    assert first == second
    assert stable_checksum(first) == stable_checksum(second)
    assert first["dashboard_run_manifests"][0]["checksum"] == second["dashboard_run_manifests"][0]["checksum"]


def test_bounded_values_and_no_uncontrolled_generation() -> None:
    payload = build_d1_seed_payload()
    assert payload["dashboard_alert_facts"][0]["active_alert_flag"] in {True, False}
    assert 0 <= payload["dashboard_benchmark_facts"][0]["benchmark_fragility_score"] <= 100
    assert 0 <= payload["dashboard_evidence_facts"][0]["normalized_score"] <= 1

    module_text = open(
        "transmission_layers/expectation_failure/dashboard_operationalization/dashboard_d1_sample_data_seed.py",
        "r",
        encoding="utf-8",
    ).read().lower()
    assert "random." not in module_text
    assert "datetime.now" not in module_text
    assert "uuid" not in module_text


def test_schema_alignment_helper_is_deterministic_and_complete() -> None:
    first = build_dashboard_required_field_alignment_report()
    second = build_dashboard_required_field_alignment_report()

    assert first == second
    assert first["schema_alignment_status"] == "aligned"
    assert first["final_decision"] == "APPROVED_FOR_FULL_DASHBOARD_SCHEMA_PAYLOAD_ALIGNMENT"
    for table_report in first["table_reports"]:
        assert not table_report["missing_columns"]


def test_certification_and_manifest_rows_are_still_valid() -> None:
    payload = build_d1_seed_payload()
    cert = payload["dashboard_certification_reports"][0]
    manifest = payload["dashboard_run_manifests"][0]
    assert cert["run_id"] == manifest["run_id"]
    assert cert["run_date_sgt"] == manifest["run_date_sgt"]
    assert manifest["schema_version"]
    assert manifest["module_version"]
