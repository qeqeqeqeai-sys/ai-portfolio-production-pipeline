from transmission_layers.expectation_failure.replay_ecology.lr6_dry3_full_universe_certification import (
    build_lr6_dry3_contradiction_richness_diagnostics,
    build_lr6_dry3_dry_sequence_comparison,
    build_lr6_dry3_full_universe_window,
    build_lr6_dry3_governance_certification,
    build_lr6_dry3_monoculture_risk_diagnostics,
    build_lr6_dry3_propagation_pathway_diagnostics,
    build_lr6_dry3_replay_ecology_diagnostics,
    build_lr6_dry3_report_payload,
    build_lr6_dry3_saturation_risk_diagnostics,
    build_lr6_dry3_semantic_diversity_diagnostics,
    load_lr6_dry3_inputs,
)


def test_input_loading_determinism() -> None:
    assert load_lr6_dry3_inputs() == load_lr6_dry3_inputs()


def test_full_universe_window_determinism_size_and_inclusion() -> None:
    inputs = load_lr6_dry3_inputs()
    window_a = build_lr6_dry3_full_universe_window(inputs, max_entities=300)
    window_b = build_lr6_dry3_full_universe_window(inputs, max_entities=300)
    assert window_a == window_b
    assert len(window_a["selected_entities"]) == 300
    source_ids = {e["entity_id"] for e in inputs["pruned_universe"]["selected_entities"]}
    assert source_ids == {e["entity_id"] for e in window_a["selected_entities"]}
    assert len(window_a["ecosystem_counts"]) == 12


def test_diagnostics_sequence_and_stability_behavior() -> None:
    inputs = load_lr6_dry3_inputs()
    window = build_lr6_dry3_full_universe_window(inputs, max_entities=300)
    diagnostics = {
        **build_lr6_dry3_replay_ecology_diagnostics(window, inputs),
        **build_lr6_dry3_semantic_diversity_diagnostics(window),
        **build_lr6_dry3_contradiction_richness_diagnostics(window),
        **build_lr6_dry3_propagation_pathway_diagnostics(window),
        **build_lr6_dry3_saturation_risk_diagnostics(window),
        **build_lr6_dry3_monoculture_risk_diagnostics(window),
        "dry_run_governance_score": 1.0,
        "dry_sequence_stability_score": 1.0,
        "diagnostic_readiness_score": 0.8,
    }
    comparison = build_lr6_dry3_dry_sequence_comparison(diagnostics, inputs, window)
    assert diagnostics["full_universe_size"] == 300
    assert diagnostics["semantic_diversity_score"] > 0
    assert diagnostics["contradiction_richness_score"] > 0
    assert diagnostics["propagation_pathway_score"] > 0
    assert diagnostics["saturation_risk_score"] <= 1
    assert diagnostics["monoculture_risk_score"] <= 1
    assert comparison["window_size_progression"] == [60, 120, 300]
    assert 0 <= comparison["ecosystem_balance_stability"] <= 1


def test_governance_and_non_activation_constraints() -> None:
    inputs = load_lr6_dry3_inputs()
    governance = build_lr6_dry3_governance_certification(inputs)
    payload = build_lr6_dry3_report_payload()
    assert governance["dry_run_only"] is True
    assert governance["no_replay_execution"] is True
    assert governance["no_replay_waves"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True
    assert governance["deterministic_reproducibility_preserved"] is True
    assert governance["lr6_production_replay_activated"] is False
    assert payload["lr6_production_replay_activated"] is False
    assert payload["diagnostic_scores"]["governed_activation_proposal_readiness_flag"] in {True, False}
