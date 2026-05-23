from copy import deepcopy

from transmission_layers.expectation_failure.real_data.b2_market_ingestion_adapter import build_b2_controlled_ingestion_adapter
from transmission_layers.expectation_failure.real_data.b3_snapshot_assembler import assemble_b3_certified_snapshot_from_b2_candidate


def test_b3_assembler_valid_and_degraded_paths_and_immutability():
    raw = [
        {"symbol": "NVDA", "metric_name": "price", "metric_value": 99, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"},
        {"symbol": "NVDA", "metric_name": "realized_volatility", "metric_value": 33, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"},
        {"symbol": "SPY", "metric_name": "benchmark_relative_return", "metric_value": 25, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"},
    ]
    candidate = build_b2_controlled_ingestion_adapter(raw, "2026-05-21")["candidate"]
    frozen = deepcopy(candidate)
    out = assemble_b3_certified_snapshot_from_b2_candidate(candidate)
    assert out["b3_decision"] in {"CERTIFIED_SNAPSHOT_READY", "DEGRADED_SNAPSHOT_READY"}
    assert out["persistence_ready"] is True
    assert out["degraded_visibility"]["quarantined_record_count"] == len(candidate["quarantined_records"])
    assert candidate == frozen


def test_b3_assembler_blocks_malformed_candidate():
    malformed = {"accepted_records": [{"symbol": "UNKNOWN", "metric_name": "price", "metric_value": 1}]}
    out = assemble_b3_certified_snapshot_from_b2_candidate(malformed)
    assert out["b3_decision"] == "BLOCKED_SNAPSHOT_INVALID"
    assert out["persistence_ready"] is False

