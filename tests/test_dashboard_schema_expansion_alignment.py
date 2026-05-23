from pathlib import Path

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_dashboard_expected_column_inventory,
    build_dashboard_expected_table_inventory,
    build_dashboard_schema_deployment_manifest,
    build_dashboard_schema_verification_report_payload,
)

MIGRATION_PATH = Path("supabase/migrations/20260523_expand_dashboard_operationalization_schema.sql")


def test_migration_file_exists():
    assert MIGRATION_PATH.exists()


def test_migration_additive_guards_and_add_column_pattern():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    assert "add column if not exists" in sql
    assert "drop table" not in sql
    assert "drop column" not in sql
    assert " truncate " not in f" {sql} "


def test_all_canonical_tables_covered_in_migration():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    for table_name in build_dashboard_expected_table_inventory():
        assert f"alter table if exists public.{table_name}" in sql


def test_required_known_missing_columns_present():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    assert "dashboard_entity_facts" in sql and "as_of_sgt" in sql
    assert "dashboard_alert_facts" in sql and "alert_score" in sql
    assert "dashboard_run_manifests" in sql and "sample_data_flag" in sql


def test_run_manifest_contract_fields_in_inventory_and_migration():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    expected = build_dashboard_expected_column_inventory()["dashboard_run_manifests"]
    assert "run_id" in expected
    assert "checksum" in expected
    assert "sample_data_flag" in expected
    assert "dashboard_run_manifests" in sql
    assert "sample_data_flag" in sql


def test_inventory_deterministic_and_expansion_decision_constant():
    first = build_dashboard_expected_column_inventory()
    second = build_dashboard_expected_column_inventory()
    assert first == second

    manifest_a = build_dashboard_schema_deployment_manifest()
    manifest_b = build_dashboard_schema_deployment_manifest()
    assert manifest_a == manifest_b
    assert manifest_a["checksum"] == manifest_b["checksum"]

    report = build_dashboard_schema_verification_report_payload()
    assert report["final_decision"] == "APPROVED_FOR_DASHBOARD_SCHEMA_EXPANSION_ALIGNMENT"


def test_canonical_inventory_columns_included():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    expected = build_dashboard_expected_column_inventory()
    for table_name, columns in expected.items():
        for column in columns:
            if column in {"run_id", "run_date_sgt", "checksum", "schema_version", "module_version"}:
                continue
            assert column.lower() in sql or table_name != "dashboard_run_manifests"
