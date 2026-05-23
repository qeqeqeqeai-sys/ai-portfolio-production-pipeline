from __future__ import annotations

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    build_d1_seed_payload,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_seed_manifests import stable_checksum


def test_remaining_business_required_fields_present_and_non_null() -> None:
    payload = build_d1_seed_payload()
    required_fields = {
        "dashboard_entity_facts": ("relative_fragility_band",),
        "dashboard_subsector_facts": ("fragile_entity_count",),
        "dashboard_alert_facts": ("alert_severity_band",),
        "dashboard_replay_facts": ("composite_score",),
        "dashboard_benchmark_facts": ("entity_fragility_score",),
        "dashboard_evidence_facts": ("source_value",),
    }
    for table, fields in required_fields.items():
        assert payload[table]
        for row in payload[table]:
            for field in fields:
                assert field in row
                assert row[field] is not None


def test_remaining_business_payload_is_deterministic_and_checksum_stable() -> None:
    first = build_d1_seed_payload()
    second = build_d1_seed_payload()
    assert first == second
    assert stable_checksum(first) == stable_checksum(second)
    assert first["dashboard_run_manifests"][0]["checksum"] == second["dashboard_run_manifests"][0]["checksum"]


def test_new_fields_are_bounded_and_controlled() -> None:
    payload = build_d1_seed_payload()

    for row in payload["dashboard_entity_facts"]:
        assert row["relative_fragility_band"] in {"LOW", "MODERATE", "HIGH"}

    for row in payload["dashboard_subsector_facts"]:
        assert isinstance(row["fragile_entity_count"], int)
        assert 0 <= row["fragile_entity_count"] <= row["entity_count"]

    for row in payload["dashboard_alert_facts"]:
        assert row["alert_severity_band"] in {"LOW", "MEDIUM", "HIGH"}

    for row in payload["dashboard_replay_facts"]:
        assert 0 <= int(row["composite_score"]) <= 100

    for row in payload["dashboard_benchmark_facts"]:
        assert 0 <= int(row["entity_fragility_score"]) <= 100

    for row in payload["dashboard_evidence_facts"]:
        assert isinstance(row["source_value"], (int, float))
        assert 0 <= float(row["source_value"]) <= 1


def test_no_random_datetime_now_or_uuid_usage_in_seed_module() -> None:
    module_text = open(
        "transmission_layers/expectation_failure/dashboard_operationalization/dashboard_d1_sample_data_seed.py",
        "r",
        encoding="utf-8",
    ).read().lower()
    assert "random." not in module_text
    assert "datetime.now" not in module_text
    assert "uuid" not in module_text
