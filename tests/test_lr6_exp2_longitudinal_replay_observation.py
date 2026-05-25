from transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation import (
    build_lr6_exp2_dashboard_payload,
    build_longitudinal_replay_drift,
    build_propagation_evolution_observation,
    build_contradiction_ecology_evolution,
    build_saturation_evolution_observation,
    build_monoculture_drift_observation,
    build_ecosystem_interaction_evolution,
    certify_lr6_exp2_experimental_boundaries,
    _build_longitudinal_slices,
)


def test_deterministic_payload() -> None:
    assert build_lr6_exp2_dashboard_payload() == build_lr6_exp2_dashboard_payload()


def test_bounded_observation_sizes() -> None:
    payload = build_lr6_exp2_dashboard_payload(max_entities=80, slice_count=3)
    assert payload["observation_window"]["max_entities"] == 80
    assert payload["observation_window"]["slice_count"] == 3


def test_longitudinal_comparisons_deterministic() -> None:
    slices = _build_longitudinal_slices()
    assert build_longitudinal_replay_drift(slices) == build_longitudinal_replay_drift(slices)


def test_dimension_observations_present() -> None:
    slices = _build_longitudinal_slices()
    assert "propagation_entropy" in build_propagation_evolution_observation(slices)
    assert "contradiction_persistence" in build_contradiction_ecology_evolution(slices)
    assert "saturation_velocity" in build_saturation_evolution_observation(slices)
    assert "monoculture_drift" in build_monoculture_drift_observation(slices)
    assert "interaction_density_delta" in build_ecosystem_interaction_evolution(slices)


def test_certification_boundaries() -> None:
    cert = certify_lr6_exp2_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_prediction_or_trading"] is True
    assert cert["additive_architecture_preserved"] is True
    assert cert["anti_monoculture_controls_preserved"] is True


def test_no_prediction_or_trading_keys() -> None:
    payload = build_lr6_exp2_dashboard_payload()
    serialized = str(payload).lower()
    assert "trade_action" not in serialized
    assert "target_price" not in serialized
    assert "forecast" not in serialized
