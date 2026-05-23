from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import build_d1_seed_payload, run_d1_controlled_seed
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import build_dashboard_read_table_inventory


def test_d1_payload_uses_canonical_physical_tables():
    payload = build_d1_seed_payload()
    assert "dashboard_certification_reports" in payload
    assert "dashboard_run_manifests" in payload
    assert "dashboard_report_metadata" not in payload
    assert "dashboard_export_manifest" not in payload


def test_d1_physical_write_tables_match_o6_expected_tables():
    result = run_d1_controlled_seed()
    planned_tables = [x["source_payload_key"] for x in result["write_plan"]["write_steps"]]
    assert set(planned_tables) == set(build_dashboard_read_table_inventory())


def test_script_supports_verify_readback_and_no_raw_sql():
    text = open("scripts/run_d1_dashboard_sample_seed.py", "r", encoding="utf-8").read()
    assert "--verify-readback" in text
    assert "target_tables_and_counts=" in text
    assert "_table_counts_from_write_plan" in text
    low = text.lower()
    assert "execute_sql" not in low
    assert "sql(" not in low
    assert "random" not in low
    assert "uuid" not in low
    assert "datetime.now" not in low
