from __future__ import annotations

from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_dashboard_o10_closeout_scope,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    FIXED_TIMESTAMP,
    build_d1_sample_alerts,
    build_d1_sample_benchmarks,
    build_d1_sample_certification_reports,
    build_d1_sample_entities,
    build_d1_sample_evidence_chains,
    build_d1_sample_replay_metadata,
    build_d1_sample_subsectors,
    build_d1_seed_manifest,
    build_d1_seed_payload,
    build_d1_seed_report_payload,
    run_d1_controlled_seed,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_seed_manifests import stable_checksum


def _all_rows(payload):
    keys = [
        "dashboard_entity_facts", "dashboard_subsector_facts", "dashboard_alert_facts", "dashboard_replay_facts",
        "dashboard_benchmark_facts", "dashboard_evidence_facts", "dashboard_certification_reports", "dashboard_run_manifests",
    ]
    rows = []
    for key in keys:
        rows.extend(payload.get(key, []))
    return rows


def test_public_api_presence_and_o1_o10_smoke():
    assert callable(build_d1_sample_entities)
    assert callable(build_d1_seed_payload)
    assert callable(run_d1_controlled_seed)
    assert "O9" in build_dashboard_o10_closeout_scope()["reviewed_layers"]


def test_deterministic_output_checksum_and_ordering():
    a = build_d1_seed_payload()
    b = build_d1_seed_payload()
    assert a == b
    assert stable_checksum(a) == stable_checksum(b)
    assert list(build_d1_seed_manifest(a)["table_counts"].keys()) == [
        "dashboard_entity_facts", "dashboard_subsector_facts", "dashboard_alert_facts", "dashboard_replay_facts",
        "dashboard_benchmark_facts", "dashboard_evidence_facts", "dashboard_certification_reports",
    ]


def test_fixed_timestamp_id_inventory_bounded_scores_and_flags():
    payload = build_d1_seed_payload()
    ids = {"D1-ENTITY-001", "D1-SUBSECTOR-001", "D1-ALERT-001", "D1-REPLAY-20260101-0001"}
    found = set()
    for row in _all_rows(payload):
        assert row.get("sample_data_flag") is True
        if "as_of_sgt" in row:
            assert row["as_of_sgt"] == FIXED_TIMESTAMP
        for key, value in row.items():
            if key.endswith("_score"):
                assert 0 <= int(value) <= 100
            if isinstance(value, str) and value in ids:
                found.add(value)
    assert found == ids


def test_forbidden_language_absence_and_immutable_input_safety():
    payload = build_d1_seed_payload()
    forbidden = ("buy", "sell", "short", "target price", "recommendation", "forecast", "expected return")
    for row in _all_rows(payload):
        for value in row.values():
            if isinstance(value, str):
                low = value.lower()
                assert all(term not in low for term in forbidden)

    copy_a = build_d1_seed_payload()
    copy_b = deepcopy(copy_a)
    run_d1_controlled_seed()
    assert copy_a == copy_b


def test_dry_run_default_controlled_adapter_path_and_no_network():
    result = run_d1_controlled_seed()
    assert result["write_plan"]["execution_mode"] == "dry_run"
    assert result["write_plan"]["dry_run"] is True
    assert all(r["status"] == "simulated" for r in result["execution_result"]["table_results"])


def test_manifest_counts_replay_consistency_and_report_payload():
    payload = build_d1_seed_payload()
    manifest = build_d1_seed_manifest(payload)
    assert manifest["total_records"] == sum(manifest["table_counts"].values())
    replay = build_d1_sample_replay_metadata()
    assert replay[0]["replay_sequence"] == "D1-REPLAY-20260101-0001"
    report = build_d1_seed_report_payload()
    assert report["fixed_timestamp"] == FIXED_TIMESTAMP
