from __future__ import annotations

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    EVIDENCE_SOURCE_METRIC,
    FIXED_RUN_DATE_SGT,
    FIXED_TIMESTAMP,
    MODULE_VERSION_LITERAL,
    build_d1_seed_payload,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_seed_manifests import stable_checksum


def _required_fields() -> dict[str, tuple[str, ...]]:
    return {
        "dashboard_entity_facts": ("composite_score",),
        "dashboard_subsector_facts": ("avg_composite_score",),
        "dashboard_alert_facts": ("subsector",),
        "dashboard_replay_facts": ("subsector",),
        "dashboard_benchmark_facts": ("subsector",),
        "dashboard_evidence_facts": ("source_metric",),
        "dashboard_certification_reports": ("export_manifest_checksum",),
        "dashboard_run_manifests": ("module_version",),
    }


def test_all_new_required_fields_present_and_non_null() -> None:
    payload = build_d1_seed_payload()
    for table, required in _required_fields().items():
        assert payload[table]
        for row in payload[table]:
            for field in required:
                assert field in row
                assert row[field] is not None


def test_deterministic_repeated_payload_generation_and_checksum_stability() -> None:
    first = build_d1_seed_payload()
    second = build_d1_seed_payload()
    assert first == second
    assert stable_checksum(first) == stable_checksum(second)
    assert first["dashboard_run_manifests"][0]["checksum"] == second["dashboard_run_manifests"][0]["checksum"]


def test_export_manifest_checksum_and_module_version_are_stable() -> None:
    payload = build_d1_seed_payload()
    cert_row = payload["dashboard_certification_reports"][0]
    manifest_row = payload["dashboard_run_manifests"][0]

    assert cert_row["export_manifest_checksum"] == stable_checksum(
        {"run_id": manifest_row["run_id"], "run_date_sgt": FIXED_RUN_DATE_SGT, "fixed_timestamp": FIXED_TIMESTAMP}
    )
    assert manifest_row["module_version"] == MODULE_VERSION_LITERAL


def test_subsector_propagation_and_bounded_numeric_scores() -> None:
    payload = build_d1_seed_payload()
    expected_subsector = "AI Infrastructure"

    assert payload["dashboard_alert_facts"][0]["subsector"] == expected_subsector
    assert payload["dashboard_replay_facts"][0]["subsector"] == expected_subsector
    assert payload["dashboard_benchmark_facts"][0]["subsector"] == expected_subsector
    assert payload["dashboard_evidence_facts"][0]["source_metric"] == EVIDENCE_SOURCE_METRIC

    for row in payload["dashboard_entity_facts"]:
        assert 0 <= int(row["composite_score"]) <= 100
    for row in payload["dashboard_subsector_facts"]:
        assert 0 <= int(row["avg_composite_score"]) <= 100


def test_no_random_datetime_now_or_uuid_usage_in_seed_module() -> None:
    module_text = open(
        "transmission_layers/expectation_failure/dashboard_operationalization/dashboard_d1_sample_data_seed.py",
        "r",
        encoding="utf-8",
    ).read()
    lowered = module_text.lower()
    assert "random." not in lowered
    assert "datetime.now" not in lowered
    assert "uuid" not in lowered
