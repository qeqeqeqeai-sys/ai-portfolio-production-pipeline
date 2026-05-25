from transmission_layers.expectation_failure.replay_ecology.lr6_dry4_saturation_guardrails import (
    build_lr6_dry4_adjusted_readiness_diagnostics,
    build_lr6_dry4_full_universe_window,
    build_lr6_dry4_governance_certification,
    build_lr6_dry4_guardrail_context,
    build_lr6_dry4_monoculture_guardrail_diagnostics,
    build_lr6_dry4_report_payload,
    build_lr6_dry4_saturation_guardrail_diagnostics,
    build_lr6_dry4_topology_pressure_annotations,
    certify_lr6_dry4_guardrailed_readiness,
    load_lr6_dry4_inputs,
)


def test_input_loading_determinism() -> None:
    assert load_lr6_dry4_inputs() == load_lr6_dry4_inputs()


def test_full_universe_window_size_remains_300() -> None:
    window = build_lr6_dry4_full_universe_window(load_lr6_dry4_inputs())
    assert window["full_universe_size"] == 300
    assert window["window_size_unchanged_from_dry3"] is True


def test_threshold_unchanged_and_adjusted_readiness() -> None:
    inputs = load_lr6_dry4_inputs()
    context = build_lr6_dry4_guardrail_context(inputs)
    adjusted = build_lr6_dry4_adjusted_readiness_diagnostics(inputs)
    assert context["readiness_threshold"] == 0.79
    assert adjusted["threshold_unchanged"] is True
    assert adjusted["adjusted_readiness_score"] == 0.790225


def test_saturation_monoculture_topology_guardrails() -> None:
    inputs = load_lr6_dry4_inputs()
    sat = build_lr6_dry4_saturation_guardrail_diagnostics(inputs)
    mono = build_lr6_dry4_monoculture_guardrail_diagnostics(inputs)
    topo = build_lr6_dry4_topology_pressure_annotations(inputs)
    assert sat["saturation_guardrail_classification"] == "scale_pressure_saturation"
    assert mono["cross_ecosystem_propagation_preserved"] is True
    assert topo["ecosystem_pressure_cap_review_required"] is False
    assert topo == build_lr6_dry4_topology_pressure_annotations(inputs)


def test_certification_no_fake_pass_and_no_activation() -> None:
    inputs = load_lr6_dry4_inputs()
    decision = certify_lr6_dry4_guardrailed_readiness(inputs)
    payload = build_lr6_dry4_report_payload()
    governance = build_lr6_dry4_governance_certification(inputs)
    assert decision["readiness_decision"] == "ready_for_governed_lr6_activation_proposal_preparation"
    assert decision["lr6_production_replay_activated"] is False
    assert payload["lr6_production_replay_activated"] is False
    assert governance["no_replay_execution"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True


def test_severe_breach_does_not_pass() -> None:
    inputs = load_lr6_dry4_inputs()
    inputs["lr6_dry3"]["diagnostic_scores"]["saturation_risk_score"] = 0.9
    inputs["lr6_dry3"]["ecosystem_counts_in_window"] = {"eco_a": 280, "eco_b": 20}
    adjusted = build_lr6_dry4_adjusted_readiness_diagnostics(inputs)
    decision = certify_lr6_dry4_guardrailed_readiness(inputs)
    assert adjusted["hard_pause"] is True
    assert adjusted["clears_threshold_under_guardrailed_interpretation"] is False
    assert decision["readiness_decision"] == "hard_pause_severe_guardrail_breach"
