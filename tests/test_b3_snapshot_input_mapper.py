from copy import deepcopy

from transmission_layers.expectation_failure.real_data.b3_snapshot_input_mapper import map_b2_candidate_to_b1_snapshot_inputs


def test_b3_mapper_deterministic_and_immutable_and_ordered():
    accepted = [
        {"symbol": "SPY", "metric_name": "benchmark_relative_return", "metric_value": 42, "source": "x", "source_timestamp": "2026-05-21"},
        {"symbol": "NVDA", "metric_name": "price", "metric_value": 100, "source": "x", "source_timestamp": "2026-05-21"},
        {"symbol": "NVDA", "metric_name": "realized_volatility", "metric_value": 45, "source": "x", "source_timestamp": "2026-05-21"},
    ]
    frozen = deepcopy(accepted)
    out1 = map_b2_candidate_to_b1_snapshot_inputs(accepted, "2026-05-21")
    out2 = map_b2_candidate_to_b1_snapshot_inputs(accepted, "2026-05-21")
    assert out1 == out2
    assert accepted == frozen
    assert out1["mapping_summary"]["entity_order"][0] == out1["b1_entity_score_inputs"][0]["ticker"]

