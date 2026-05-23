from __future__ import annotations

from pathlib import Path

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    FIXED_RUN_DATE_SGT,
    build_d1_sample_replay_metadata,
    build_d1_seed_payload,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o2_supabase_contracts import build_dashboard_o2_upsert_payload
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o3_supabase_write_adapter import build_dashboard_o3_write_plan
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_schema_verification import (
    build_dashboard_expected_column_inventory,
)

MIGRATION = Path("supabase/migrations/20260523_dashboard_contract_alignment_finalization.sql")


def test_d1_payload_has_deterministic_run_date_sgt_for_required_tables():
    payload = build_d1_seed_payload()
    required = [
        "dashboard_entity_facts",
        "dashboard_subsector_facts",
        "dashboard_alert_facts",
        "dashboard_benchmark_facts",
        "dashboard_evidence_facts",
        "dashboard_certification_reports",
        "dashboard_run_manifests",
    ]
    for table in required:
        assert payload[table]
        for row in payload[table]:
            assert row["run_date_sgt"] == FIXED_RUN_DATE_SGT


def test_replay_payload_type_alignment_and_determinism():
    first = build_d1_sample_replay_metadata()
    second = build_d1_sample_replay_metadata()
    assert first == second
    row = first[0]
    assert isinstance(row["replay_sequence"], int)
    assert isinstance(row["replay_batch_id"], str)


def test_o3_upsert_for_certification_reports_matches_new_unique_key():
    o2 = build_dashboard_o2_upsert_payload(build_d1_seed_payload())
    plan = build_dashboard_o3_write_plan(o2)
    cert_step = next(step for step in plan["write_steps"] if step["table_name"] == "dashboard_certification_reports")
    assert cert_step["on_conflict"] == "run_id,report_id"


def test_alignment_migration_exists_and_is_additive_only():
    assert MIGRATION.exists()
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "create unique index if not exists" in sql
    assert "dashboard_certification_reports" in sql
    assert "(run_id, report_id)" in sql
    assert "add column if not exists replay_batch_id text" in sql
    assert "drop table" not in sql
    assert "truncate" not in sql


def test_schema_inventory_covers_run_date_and_replay_fields():
    inventory = build_dashboard_expected_column_inventory()
    for table in (
        "dashboard_entity_facts",
        "dashboard_subsector_facts",
        "dashboard_alert_facts",
        "dashboard_benchmark_facts",
        "dashboard_evidence_facts",
        "dashboard_certification_reports",
        "dashboard_run_manifests",
    ):
        assert "run_date_sgt" in inventory[table]
    assert "replay_sequence" in inventory["dashboard_replay_facts"]
