from copy import deepcopy

from transmission_layers.alpha.layer_a import (
    ALPHA_CLASSIFICATIONS,
    build_forward_return_windows,
    compute_decile_spread,
    compute_factor_decay,
    compute_factor_stability,
    compute_forward_return_separation,
    compute_hit_rate,
    compute_information_coefficient,
    compute_rank_information_coefficient,
    run_alpha_layer_a_predictive_validation,
)


def _records(n=20):
    rows = []
    for i in range(n):
        signal = float(i - (n / 2)) / 10.0
        rows.append({"timestamp": f"2026-01-{(i % 10) + 1:02d}", "asset_id": f"A{i:03d}", "signal": signal, "forward_return_5d": signal * 0.8, "forward_return_20d": signal * 0.6, "forward_return_60d": signal * 0.3})
    return rows


def test_ic_and_rank_ic_computation_and_ties():
    points = build_forward_return_windows(_records(), "5d")
    assert round(compute_information_coefficient(points), 6) == 1.0
    assert round(compute_rank_information_coefficient(points), 6) == 1.0
    tied = [
        {"timestamp": "2026-01-01", "asset_id": "a", "signal": 1.0, "forward_return_5d": 1.0},
        {"timestamp": "2026-01-01", "asset_id": "b", "signal": 1.0, "forward_return_5d": 2.0},
        {"timestamp": "2026-01-01", "asset_id": "c", "signal": 2.0, "forward_return_5d": 3.0},
    ]
    tied_points = build_forward_return_windows(tied, "5d")
    assert compute_rank_information_coefficient(tied_points) > 0


def test_forward_return_separation_and_decile_spread():
    points = build_forward_return_windows(_records(), "20d")
    assert compute_forward_return_separation(points) > 0
    assert compute_decile_spread(points) > 0
    assert compute_decile_spread(build_forward_return_windows(_records(9), "20d")) == 0.0


def test_hit_rate_stability_decay_and_window_alignment():
    rows = _records()
    points = build_forward_return_windows(rows, "60d")
    assert compute_hit_rate(points) == 1.0
    assert 0.0 <= compute_factor_stability(rows) <= 1.0
    assert compute_factor_decay(rows) == 0.0
    assert len(build_forward_return_windows([{"asset_id": "x", "signal": 0.1, "forward_return_5d": 0.1}], "5d")) == 0


def test_deterministic_repeated_output_and_fingerprint():
    rows = _records()
    first = run_alpha_layer_a_predictive_validation(signal_name="test_signal", window="5d", records=rows)
    second = run_alpha_layer_a_predictive_validation(signal_name="test_signal", window="5d", records=rows)
    assert first == second
    assert first["replay_metadata"]["fingerprint_sha256"] == second["replay_metadata"]["fingerprint_sha256"]


def test_insufficient_data_and_invalid_input():
    assert run_alpha_layer_a_predictive_validation(signal_name="x", window="5d", records=_records(2))["classification"] == "insufficient_data"
    assert run_alpha_layer_a_predictive_validation(signal_name="", window="99d", records=[])["classification"] == "invalid_input"


def test_immutable_input_safety_and_no_runtime_mutation_flags():
    rows = _records()
    snapshot = deepcopy(rows)
    result = run_alpha_layer_a_predictive_validation(signal_name="sig", window="20d", records=rows)
    assert rows == snapshot
    assert result["invariants"]["immutable_input_safe"] is True
    assert result["invariants"]["no_runtime_mutation"] is True
    assert result["invariants"]["no_adaptive_control"] is True
    assert result["invariants"]["no_black_box_ml"] is True
    assert result["invariants"]["no_trading_execution"] is True


def test_fixed_template_explanation_and_bounded_classification_labels_and_interpretability():
    result = run_alpha_layer_a_predictive_validation(signal_name="sig", window="20d", records=_records())
    assert result["classification"] in ALPHA_CLASSIFICATIONS
    assert result["explanation"].startswith("Predictive validation for signal=")
    assert "classification=" in result["explanation"]
    for field in ["IC=", "RankIC=", "Separation=", "DecileSpread=", "HitRate=", "Stability=", "Decay="]:
        assert field in result["explanation"]


def test_public_api_exports_and_no_trading_execution_behavior():
    assert callable(compute_information_coefficient)
    assert callable(compute_rank_information_coefficient)
    assert run_alpha_layer_a_predictive_validation(signal_name="sig", window="5d", records=_records())["invariants"]["no_trading_execution"] is True
