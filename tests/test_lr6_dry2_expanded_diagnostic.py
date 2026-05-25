from transmission_layers.expectation_failure.replay_ecology.lr6_dry2_expanded_diagnostic import (
    build_lr6_dry2_contradiction_richness_diagnostics,
    build_lr6_dry2_dry1_comparison,
    build_lr6_dry2_expanded_window,
    build_lr6_dry2_governance_certification,
    build_lr6_dry2_monoculture_risk_diagnostics,
    build_lr6_dry2_propagation_pathway_diagnostics,
    build_lr6_dry2_replay_ecology_diagnostics,
    build_lr6_dry2_report_payload,
    build_lr6_dry2_saturation_risk_diagnostics,
    build_lr6_dry2_semantic_diversity_diagnostics,
    load_lr6_dry2_inputs,
)


def test_input_loading_determinism() -> None:
    assert load_lr6_dry2_inputs() == load_lr6_dry2_inputs()


def test_expanded_window_determinism_and_size_and_balance() -> None:
    inputs = load_lr6_dry2_inputs()
    window_a = build_lr6_dry2_expanded_window(inputs, max_entities=120)
    window_b = build_lr6_dry2_expanded_window(inputs, max_entities=120)
    assert window_a == window_b
    assert len(window_a["selected_entities"]) <= 120
    assert len(window_a["ecosystem_counts"]) == 12
    assert max(window_a["ecosystem_counts"].values()) <= 10


def test_diagnostic_calculations_and_stability_behavior() -> None:
    inputs = load_lr6_dry2_inputs()
    window = build_lr6_dry2_expanded_window(inputs, max_entities=120)
    diagnostics = {
        **build_lr6_dry2_replay_ecology_diagnostics(window, inputs),
        **build_lr6_dry2_semantic_diversity_diagnostics(window),
        **build_lr6_dry2_contradiction_richness_diagnostics(window),
        **build_lr6_dry2_propagation_pathway_diagnostics(window),
        **build_lr6_dry2_saturation_risk_diagnostics(window),
        **build_lr6_dry2_monoculture_risk_diagnostics(window),
        "dry_run_governance_score": 1.0,
        "dry1_to_dry2_stability_score": 1.0,
        "diagnostic_readiness_score": 0.8,
    }
    comparison = build_lr6_dry2_dry1_comparison(diagnostics, inputs, window)
    assert diagnostics["expanded_window_size"] == 120
    assert diagnostics["semantic_diversity_score"] > 0
    assert diagnostics["contradiction_richness_score"] > 0
    assert diagnostics["propagation_pathway_score"] > 0
    assert diagnostics["saturation_risk_score"] <= 1
    assert diagnostics["monoculture_risk_score"] <= 1
    assert comparison["window_size_increase"] == 60
    assert 0 <= comparison["ecosystem_balance_stability"] <= 1


def test_governance_and_dry_run_only_constraints() -> None:
    inputs = load_lr6_dry2_inputs()
    governance = build_lr6_dry2_governance_certification(inputs)
    payload = build_lr6_dry2_report_payload()
    assert governance["dry_run_only"] is True
    assert governance["no_replay_execution"] is True
    assert governance["no_replay_waves"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True
    assert governance["lr6_production_replay_activated"] is False
    assert payload["lr6_production_replay_activated"] is False
