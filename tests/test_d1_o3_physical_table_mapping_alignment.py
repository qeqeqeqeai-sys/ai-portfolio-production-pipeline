from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import run_d1_controlled_seed
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o2_supabase_contracts import build_dashboard_o2_table_contracts
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import build_dashboard_read_table_inventory


CANONICAL_TABLES = [
    "dashboard_entity_facts",
    "dashboard_subsector_facts",
    "dashboard_alert_facts",
    "dashboard_replay_facts",
    "dashboard_benchmark_facts",
    "dashboard_evidence_facts",
    "dashboard_certification_reports",
    "dashboard_run_manifests",
]


def test_o2_o3_o6_table_mapping_alignment_and_no_legacy_prefixes():
    contracts = build_dashboard_o2_table_contracts()
    assert [c["table_name"] for c in contracts] == CANONICAL_TABLES

    result = run_d1_controlled_seed(confirm_execute=False, dry_run=True, supabase_client=None)
    steps = result["write_plan"]["write_steps"]
    plan_tables = [s["table_name"] for s in steps]
    source_payload_tables = [s["source_payload_key"] for s in steps]

    assert plan_tables == CANONICAL_TABLES
    assert source_payload_tables == CANONICAL_TABLES
    assert all("expectation_failure_dashboard_" not in t for t in plan_tables)

    execution_tables = [r["table_name"] for r in result["execution_result"]["table_results"]]
    assert execution_tables == plan_tables

    o6_tables = build_dashboard_read_table_inventory()
    assert set(o6_tables) == set(CANONICAL_TABLES)
    assert set(execution_tables) == set(o6_tables)


def test_certification_and_run_manifest_table_targets_are_canonical():
    result = run_d1_controlled_seed(confirm_execute=False, dry_run=True, supabase_client=None)
    plan_tables = [s["table_name"] for s in result["write_plan"]["write_steps"]]
    assert "dashboard_certification_reports" in plan_tables
    assert "dashboard_run_manifests" in plan_tables
