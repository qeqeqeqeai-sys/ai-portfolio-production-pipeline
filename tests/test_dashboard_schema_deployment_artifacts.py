from pathlib import Path

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_dashboard_expected_column_inventory,
    build_dashboard_expected_table_inventory,
    build_dashboard_schema_deployment_manifest,
    build_dashboard_schema_verification_report_payload,
)

MIGRATION_PATH = Path("database/migrations/20260523_create_dashboard_operationalization_tables.sql")
EXPANSION_MIGRATION_PATH = Path("supabase/migrations/20260523_expand_dashboard_operationalization_schema.sql")


def test_migration_file_exists():
    assert MIGRATION_PATH.exists()


def test_expected_tables_and_columns_in_migration():
    base_sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    expansion_sql = EXPANSION_MIGRATION_PATH.read_text(encoding="utf-8").lower()
    combined_sql = f"{base_sql}\n{expansion_sql}"
    expected_columns = build_dashboard_expected_column_inventory()
    for table_name, columns in expected_columns.items():
        assert f"create table if not exists public.{table_name}" in base_sql
        for column in columns:
            assert f"{column.lower()}" in combined_sql


def test_migration_safety_guards():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    assert "drop table" not in sql
    assert " truncate " not in f" {sql} "
    assert " delete " not in f" {sql} "
    assert " for insert " not in sql
    assert " for update " not in sql
    assert " for delete " not in sql
    assert " all to " not in sql


def test_required_indexes_and_constraints_present():
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    required_markers = [
        "primary key (run_id, entity_id)",
        "primary key (run_id, subsector)",
        "primary key (run_id, entity_id, alert_state)",
        "primary key (run_id, replay_date_sgt, entity_id, replay_sequence)",
        "primary key (run_id, entity_id, benchmark_id)",
        "primary key (run_id, entity_id, evidence_id)",
        "primary key (run_id, export_manifest_checksum)",
        "primary key (run_id, checksum)",
        "idx_dashboard_entity_facts_run_id",
        "idx_dashboard_entity_facts_run_date_sgt",
        "idx_dashboard_entity_facts_entity_id",
        "idx_dashboard_entity_facts_ticker",
        "idx_dashboard_entity_facts_subsector",
    ]
    for marker in required_markers:
        assert marker in sql


def test_schema_manifest_is_deterministic_and_additive_api_exported():
    a = build_dashboard_schema_deployment_manifest()
    b = build_dashboard_schema_deployment_manifest()
    assert a == b
    assert a["checksum"] == b["checksum"]
    assert build_dashboard_expected_table_inventory() == list(build_dashboard_expected_column_inventory().keys())

    payload = build_dashboard_schema_verification_report_payload()
    assert payload["final_decision"] == "APPROVED_FOR_DASHBOARD_SCHEMA_EXPANSION_ALIGNMENT"
