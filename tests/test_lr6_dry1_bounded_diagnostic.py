from transmission_layers.expectation_failure.replay_ecology.lr6_dry1_bounded_diagnostic import (
    build_lr6_dry1_bounded_window,
    build_lr6_dry1_contradiction_richness_diagnostics,
    build_lr6_dry1_governance_certification,
    build_lr6_dry1_monoculture_risk_diagnostics,
    build_lr6_dry1_propagation_pathway_diagnostics,
    build_lr6_dry1_report_payload,
    build_lr6_dry1_replay_ecology_diagnostics,
    build_lr6_dry1_saturation_risk_diagnostics,
    build_lr6_dry1_semantic_diversity_diagnostics,
    load_lr6_dry1_inputs,
)


def test_input_loading_determinism() -> None:
    assert load_lr6_dry1_inputs() == load_lr6_dry1_inputs()


def test_bounded_window_determinism_and_size() -> None:
    inputs = load_lr6_dry1_inputs()
    window_a = build_lr6_dry1_bounded_window(inputs, max_entities=60)
    window_b = build_lr6_dry1_bounded_window(inputs, max_entities=60)
    assert window_a == window_b
    assert len(window_a["selected_entities"]) <= 60


def test_ecosystem_diversity_and_monoculture_cap_preserved() -> None:
    inputs = load_lr6_dry1_inputs()
    window = build_lr6_dry1_bounded_window(inputs, max_entities=60)
    assert len(window["ecosystem_counts"]) == 12
    assert max(window["ecosystem_counts"].values()) / len(window["selected_entities"]) <= 0.22


def test_diagnostic_calculations_present() -> None:
    inputs = load_lr6_dry1_inputs()
    window = build_lr6_dry1_bounded_window(inputs, max_entities=60)
    assert build_lr6_dry1_replay_ecology_diagnostics(window, inputs)["bounded_window_size"] == 60
    assert build_lr6_dry1_semantic_diversity_diagnostics(window)["semantic_diversity_score"] > 0
    assert build_lr6_dry1_contradiction_richness_diagnostics(window)["contradiction_richness_score"] > 0
    assert build_lr6_dry1_propagation_pathway_diagnostics(window)["propagation_pathway_score"] > 0
    assert build_lr6_dry1_saturation_risk_diagnostics(window)["saturation_risk_score"] <= 1
    assert build_lr6_dry1_monoculture_risk_diagnostics(window)["monoculture_risk_score"] <= 1


def test_governance_and_no_activation_constraints() -> None:
    inputs = load_lr6_dry1_inputs()
    governance = build_lr6_dry1_governance_certification(inputs)
    payload = build_lr6_dry1_report_payload()
    assert governance["dry_run_only"] is True
    assert governance["no_replay_execution"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["lr6_production_replay_activated"] is False
    assert payload["lr6_production_replay_activated"] is False
