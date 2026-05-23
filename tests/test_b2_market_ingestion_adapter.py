from copy import deepcopy

from transmission_layers.expectation_failure.real_data.b2_market_ingestion_adapter import build_b2_controlled_ingestion_adapter


def _sample_valid_records():
    return [
        {"symbol": "nvda", "observation_date": "2026-05-20", "metric_name": "price", "metric_value": 123.4, "source_name": "vendor_a", "source_timestamp": "2026-05-20", "currency": "USD", "data_quality_hint": "vendor_verified"},
        {"symbol": "SOXX", "observation_date": "2026-05-20", "metric_name": "benchmark_relative_return", "metric_value": 0.12, "source_name": "vendor_a", "source_timestamp": "2026-05-20", "currency": "USD", "data_quality_hint": "vendor_verified"},
    ]


def test_b2_adapter_acceptance_repeatability_and_checksum_stability():
    raw = _sample_valid_records()
    out1 = build_b2_controlled_ingestion_adapter(raw, as_of_date="2026-05-21")
    out2 = build_b2_controlled_ingestion_adapter(raw, as_of_date="2026-05-21")
    assert out1 == out2
    assert out1["candidate"]["accepted_records"]
    assert out1["certification"]["certification_status"] == "DEGRADED_INGESTION_READY"


def test_b2_adapter_quarantine_reasons_and_duplicate_handling_and_immutability():
    raw = _sample_valid_records() + [
        {"symbol": "XXXX", "observation_date": "2026-05-20", "metric_name": "price", "metric_value": 1, "source_name": "vendor_a", "source_timestamp": "2026-05-20", "currency": "USD"},
        {"symbol": "NVDA", "observation_date": "bad", "metric_name": "unsupported", "metric_value": None, "source_name": "vendor_a", "source_timestamp": "2026-05-01", "currency": "EUR"},
        {"symbol": "NVDA", "observation_date": "2026-05-20", "metric_name": "price", "metric_value": 123.4, "source_name": "vendor_a", "source_timestamp": "2026-05-20", "currency": "USD"},
    ]
    original = deepcopy(raw)
    out = build_b2_controlled_ingestion_adapter(raw, as_of_date="2026-05-21")
    reasons = {q["reason_code"] for q in out["candidate"]["quarantined_records"]}
    assert {"unknown_symbol", "unsupported_metric", "missing_value", "invalid_date", "stale_source_timestamp", "unsupported_currency", "duplicate_observation"}.issubset(reasons)
    assert raw == original
    assert out["certification"]["gates"]["no_network_execution"] is True
    assert out["certification"]["gates"]["no_database_write_behavior"] is True
