from __future__ import annotations

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    SAMPLE_SCHEMA_VERSION,
    build_d1_seed_payload,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o2_supabase_contracts import (
    build_dashboard_o2_upsert_payload,
)


TICKER_TABLES = (
    "dashboard_entity_facts",
    "dashboard_alert_facts",
    "dashboard_replay_facts",
    "dashboard_benchmark_facts",
    "dashboard_evidence_facts",
)


def test_required_not_null_alignment_fields_present_in_d1_payload() -> None:
    payload = build_d1_seed_payload()

    for table in TICKER_TABLES:
        assert payload[table]
        for row in payload[table]:
            assert "ticker" in row
            assert isinstance(row["ticker"], str)
            assert row["ticker"]

    for row in payload["dashboard_subsector_facts"]:
        assert "entity_count" in row
        assert isinstance(row["entity_count"], int)

    for row in payload["dashboard_certification_reports"]:
        assert row["certification_status"] == "certified_deterministic_seed"

    manifests = payload["dashboard_run_manifests"]
    assert manifests
    assert manifests[0]["schema_version"] == SAMPLE_SCHEMA_VERSION


def test_final_payload_generation_is_deterministic_and_replayable() -> None:
    first = build_d1_seed_payload()
    second = build_d1_seed_payload()
    assert first == second


def test_o3_write_path_contract_and_checksums_stay_stable() -> None:
    first = build_d1_seed_payload()
    second = build_d1_seed_payload()

    assert first["dashboard_run_manifests"][0]["checksum"] == second["dashboard_run_manifests"][0]["checksum"]

    o2 = build_dashboard_o2_upsert_payload(first)
    by_table = {batch["table_name"]: batch for batch in o2["upsert_batches"]}

    assert by_table["dashboard_entity_facts"]["row_count"] > 0
    assert by_table["dashboard_subsector_facts"]["row_count"] > 0
    assert by_table["dashboard_alert_facts"]["row_count"] > 0
    assert by_table["dashboard_replay_facts"]["row_count"] > 0
    assert by_table["dashboard_benchmark_facts"]["row_count"] > 0
    assert by_table["dashboard_evidence_facts"]["row_count"] > 0
    assert by_table["dashboard_certification_reports"]["row_count"] > 0
    assert by_table["dashboard_run_manifests"]["row_count"] > 0
