from transmission_layers.expectation_failure.real_data import (
    assemble_b3_certified_snapshot_from_b2_candidate,
    build_b2_controlled_ingestion_adapter,
    build_deterministic_market_snapshot,
)


def test_b3_repeatability_checksum_and_contracts_and_exports():
    raw = [
        {"symbol": "NVDA", "metric_name": "price", "metric_value": 100, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"},
        {"symbol": "NVDA", "metric_name": "realized_volatility", "metric_value": 30, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"},
        {"symbol": "SPY", "metric_name": "benchmark_relative_return", "metric_value": 5, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"},
    ]
    candidate = build_b2_controlled_ingestion_adapter(raw, "2026-05-21")["candidate"]
    out1 = assemble_b3_certified_snapshot_from_b2_candidate(candidate)
    out2 = assemble_b3_certified_snapshot_from_b2_candidate(candidate)
    assert out1["deterministic_checksum"] == out2["deterministic_checksum"]
    assert out1["forbidden_capability_contract"]["trading"] == "disallowed"
    assert callable(build_deterministic_market_snapshot)

