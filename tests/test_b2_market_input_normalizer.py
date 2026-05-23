from copy import deepcopy

from transmission_layers.expectation_failure.real_data.b2_market_input_normalizer import normalize_market_input_records


def test_b2_normalizer_repeatability_and_immutable_input():
    raw = [{"symbol": "nvda", "observation_date": "2026-05-20", "metric_name": "price", "metric_value": "123.45", "source_timestamp": "2026-05-20", "currency": "usd"}]
    original = deepcopy(raw)
    out1 = normalize_market_input_records(raw)
    out2 = normalize_market_input_records(raw)
    assert out1 == out2
    assert raw == original
    assert out1[0]["symbol"] == "NVDA"
    assert out1[0]["metric_name"] == "price"


def test_b2_normalizer_bounds_numeric_values():
    raw = [{"symbol": "NVDA", "observation_date": "2026-05-20", "metric_name": "forward_pe", "metric_value": 9999, "source_timestamp": "2026-05-20", "currency": "USD"}]
    out = normalize_market_input_records(raw)
    assert out[0]["metric_value"] == 500.0
    assert out[0]["normalization_flags"]["metric_value_clamped"] is True
