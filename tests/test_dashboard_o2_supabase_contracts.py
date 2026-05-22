from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o1_export_schema import build_dashboard_o1_export_payload
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o2_supabase_contracts import (
    build_dashboard_o2_contract_report,
    build_dashboard_o2_upsert_payload,
    validate_dashboard_o2_payload,
)


def _payload():
    return build_dashboard_o1_export_payload(
        run_id="run-001",
        run_date_sgt="2026-05-22",
        entity_rows=[{"entity_id": "E1", "entity_name": "A", "ticker": "AAA", "subsector": "AI", "composite_score": 81}],
        alert_rows=[{"run_id": "run-001", "entity_id": "E1", "ticker": "AAA", "subsector": "AI", "alert_state": "watch"}],
        replay_rows=[{"run_id": "run-001", "replay_date_sgt": "2026-05-21", "entity_id": "E1", "replay_sequence": 1}],
        benchmark_rows=[{"run_id": "run-001", "entity_id": "E1", "benchmark_id": "QQQ"}],
        evidence_rows=[{"run_id": "run-001", "entity_id": "E1", "evidence_id": "EV1"}],
    )


def test_public_apis_exist_and_additive_exports():
    for name in [
        "build_dashboard_o2_table_contracts",
        "build_dashboard_o2_unique_key_contracts",
        "build_dashboard_o2_column_contracts",
        "build_dashboard_o2_upsert_payload",
        "validate_dashboard_o2_payload",
        "build_dashboard_o2_persistence_manifest",
        "build_dashboard_o2_contract_report",
        "build_dashboard_o1_export_payload",
    ]:
        assert hasattr(mod, name)


def test_determinism_order_checksum_and_immutability():
    p = _payload()
    original = deepcopy(p)
    a = build_dashboard_o2_upsert_payload(p)
    b = build_dashboard_o2_upsert_payload(deepcopy(p))
    assert a == b
    assert p == original
    assert a["persistence_manifest"]["checksum"] == b["persistence_manifest"]["checksum"]
    assert [c["table_name"] for c in a["table_contracts"]] == [
        "expectation_failure_dashboard_entity_facts",
        "expectation_failure_dashboard_subsector_facts",
        "expectation_failure_dashboard_alert_facts",
        "expectation_failure_dashboard_replay_facts",
        "expectation_failure_dashboard_benchmark_facts",
        "expectation_failure_dashboard_evidence_facts",
        "expectation_failure_dashboard_report_metadata",
        "expectation_failure_dashboard_export_manifest",
    ]


def test_contract_completeness_upsert_shape_and_manifest_counts():
    out = build_dashboard_o2_upsert_payload(_payload())
    for c in out["table_contracts"]:
        for key in ["table_name", "source_payload_key", "primary_unique_key", "columns", "required_columns", "nullable_columns", "deterministic_sort_key", "persistence_mode", "schema_version"]:
            assert key in c
    for b in out["upsert_batches"]:
        for key in ["table_name", "source_payload_key", "unique_key", "rows", "row_count", "deterministic_sort_key", "persistence_mode"]:
            assert key in b
    assert out["persistence_manifest"]["total_row_count"] == sum(b["row_count"] for b in out["upsert_batches"])


def test_required_groups_missing_column_duplicates_flat_rows_and_forbidden_language():
    p = _payload()
    bad = deepcopy(p)
    bad.pop("dashboard_alert_facts")
    assert validate_dashboard_o2_payload(bad)["validation_status"] == "invalid"

    bad2 = _payload()
    bad2["dashboard_entity_facts"][0].pop("entity_id")
    assert validate_dashboard_o2_payload(bad2)["validation_status"] == "invalid"

    bad3 = _payload()
    bad3["dashboard_entity_facts"].append(deepcopy(bad3["dashboard_entity_facts"][0]))
    assert validate_dashboard_o2_payload(bad3)["validation_status"] == "invalid"

    bad4 = _payload()
    bad4["dashboard_entity_facts"][0]["nested"] = {"x": 1}
    assert validate_dashboard_o2_payload(bad4)["validation_status"] == "invalid"

    bad5 = _payload()
    bad5["dashboard_entity_facts"][0]["entity_name"] = "buy now"
    assert validate_dashboard_o2_payload(bad5)["validation_status"] == "invalid"


def test_contract_report_and_no_side_effect_signals():
    report = build_dashboard_o2_contract_report(_payload())
    assert report["validation_summary"]["validation_status"] == "valid"
    flags = report["persistence_manifest"]["invariant_flags"]
    assert flags["no_database_writes"] and flags["no_network_calls"] and flags["no_file_writes"] and flags["no_streamlit_ui"]
