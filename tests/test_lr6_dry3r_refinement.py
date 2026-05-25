from transmission_layers.expectation_failure.replay_ecology.lr6_dry3r_refinement import (
    build_lr6_dry3r_dry_sequence_comparison,
    build_lr6_dry3r_ecosystem_pressure_diagnostics,
    build_lr6_dry3r_governance_certification,
    build_lr6_dry3r_monoculture_driver_diagnostics,
    build_lr6_dry3r_refined_certification,
    build_lr6_dry3r_refinement_actions,
    build_lr6_dry3r_report_payload,
    build_lr6_dry3r_saturation_driver_diagnostics,
    build_lr6_dry3r_threshold_gap_analysis,
    load_lr6_dry3r_inputs,
)


def test_input_loading_determinism() -> None:
    assert load_lr6_dry3r_inputs() == load_lr6_dry3r_inputs()


def test_threshold_gap_calculation() -> None:
    gap = build_lr6_dry3r_threshold_gap_analysis(load_lr6_dry3r_inputs())
    assert gap["threshold_gap"] == 0.006775
    assert gap["gap_bps"] == 68


def test_saturation_monoculture_and_ecosystem_diagnostics() -> None:
    inputs = load_lr6_dry3r_inputs()
    sat = build_lr6_dry3r_saturation_driver_diagnostics(inputs)
    mono = build_lr6_dry3r_monoculture_driver_diagnostics(inputs)
    eco = build_lr6_dry3r_ecosystem_pressure_diagnostics(inputs)
    assert sat["saturation_risk_delta_vs_dry2"] == 0.075757
    assert mono["monoculture_risk_delta_vs_dry2"] == 0.075757
    assert eco["low_connectivity_cluster_signal"] in {"present", "not_present"}


def test_refinement_and_governance_constraints() -> None:
    inputs = load_lr6_dry3r_inputs()
    actions = build_lr6_dry3r_refinement_actions(inputs)
    refined = build_lr6_dry3r_refined_certification(inputs)
    governance = build_lr6_dry3r_governance_certification(inputs)
    payload = build_lr6_dry3r_report_payload()
    assert actions == build_lr6_dry3r_refinement_actions(inputs)
    assert refined["threshold_unchanged"] is True
    assert refined["readiness_threshold"] == 0.79
    assert refined["lr6_production_replay_activated"] is False
    assert governance["no_replay_execution"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True
    assert payload["lr6_production_replay_activated"] is False


def test_dry_sequence_comparison_determinism() -> None:
    inputs = load_lr6_dry3r_inputs()
    assert build_lr6_dry3r_dry_sequence_comparison(inputs) == build_lr6_dry3r_dry_sequence_comparison(inputs)
