from copy import deepcopy

from transmission_layers.expectation_failure.real_data.b1_market_snapshot_builder import build_deterministic_market_snapshot


def test_b1_market_snapshot_repeatability_and_ordering():
    entity_inputs = [{"ticker": "NVDA", "price_momentum_score": 80, "fundamental_health_score": 70, "expectation_pressure_score": 65}]
    benchmark_inputs = [{"symbol": "SOXX", "benchmark_pressure_score": 77}]
    out1 = build_deterministic_market_snapshot(entity_inputs, benchmark_inputs)
    out2 = build_deterministic_market_snapshot(entity_inputs, benchmark_inputs)
    assert out1 == out2
    assert [e["ticker"] for e in out1["entities"]][:3] == ["NVDA", "AMD", "TSM"]


def test_b1_market_snapshot_bounded_scoring_and_missing_data_visibility():
    entity_inputs = [{"ticker": "NVDA", "price_momentum_score": 150, "fundamental_health_score": None, "expectation_pressure_score": -12}]
    out = build_deterministic_market_snapshot(entity_inputs, raw_benchmark_inputs=[])
    nvda = out["entities"][0]
    assert nvda["price_momentum_score"] == 100
    assert nvda["fundamental_health_score"] == 50
    assert nvda["expectation_pressure_score"] == 0
    assert "clamped_price_momentum_score" in nvda["evidence_quality_flags"]
    assert "missing_fundamental_health_score" in nvda["evidence_quality_flags"]
    assert out["benchmarks"][0]["data_status"] == "missing"


def test_b1_market_snapshot_input_immutable_safety():
    entity_inputs = [{"ticker": "NVDA", "price_momentum_score": 10, "fundamental_health_score": 20, "expectation_pressure_score": 30}]
    benchmark_inputs = [{"symbol": "SOXX", "benchmark_pressure_score": 40}]
    original_entities = deepcopy(entity_inputs)
    original_benchmarks = deepcopy(benchmark_inputs)
    build_deterministic_market_snapshot(entity_inputs, benchmark_inputs)
    assert entity_inputs == original_entities
    assert benchmark_inputs == original_benchmarks
