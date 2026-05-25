from transmission_layers.expectation_failure.replay_ecology.lr6_exp1_bounded_semantic_observation import (
    build_lr6_exp1_contradiction_observations,
    build_lr6_exp1_ecosystem_interaction_observations,
    build_lr6_exp1_experimental_mode_context,
    build_lr6_exp1_governance_certification,
    build_lr6_exp1_observation_summary,
    build_lr6_exp1_observation_window,
    build_lr6_exp1_propagation_observations,
    build_lr6_exp1_report_payload,
    build_lr6_exp1_semantic_replay_observations,
    build_lr6_exp1_transition_observations,
    load_lr6_exp1_inputs,
)


def test_input_loading_determinism() -> None:
    assert load_lr6_exp1_inputs() == load_lr6_exp1_inputs()


def test_experimental_mode_context_present() -> None:
    context = build_lr6_exp1_experimental_mode_context(load_lr6_exp1_inputs())
    assert context["mode"] == "experimental_mode"
    assert context["governed_lr6_active"] is False


def test_observation_window_deterministic_and_bounded() -> None:
    inputs = load_lr6_exp1_inputs()
    first = build_lr6_exp1_observation_window(inputs)
    second = build_lr6_exp1_observation_window(inputs)
    assert first == second
    assert len(first["selected_entity_ids"]) <= 90


def test_ecosystem_and_guardrails_preserved() -> None:
    window = build_lr6_exp1_observation_window(load_lr6_exp1_inputs())
    assert window["ecosystem_diversity_preserved"] is True
    assert window["saturation_guardrail_preserved"] is True
    assert window["monoculture_guardrail_preserved"] is True


def test_observation_calculations_present() -> None:
    window = build_lr6_exp1_observation_window(load_lr6_exp1_inputs())
    semantic = build_lr6_exp1_semantic_replay_observations(window)
    contradiction = build_lr6_exp1_contradiction_observations(window)
    propagation = build_lr6_exp1_propagation_observations(window)
    transition = build_lr6_exp1_transition_observations(window)
    ecosystem = build_lr6_exp1_ecosystem_interaction_observations(window)

    assert semantic["semantic_adjacency_richness"] > 0
    assert contradiction["contradiction_surface_diversity"] > 0
    assert propagation["propagation_pathway_diversity"] > 0
    assert transition["transition_topology_diversity"] > 0
    assert ecosystem["ecosystem_interaction_density"] > 0


def test_summary_determinism() -> None:
    payload1 = build_lr6_exp1_report_payload()
    payload2 = build_lr6_exp1_report_payload()
    assert payload1["observation_summary"] == payload2["observation_summary"]


def test_constraints_preserved_and_no_activation() -> None:
    cert = build_lr6_exp1_governance_certification()
    assert cert["governed_lr6_production_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["no_prediction_or_trading"] is True
    assert cert["additive_architecture_preserved"] is True


def test_observation_summary_reports_no_activation() -> None:
    payload = build_lr6_exp1_report_payload()
    summary = build_lr6_exp1_observation_summary(payload["observation_metrics"])
    assert summary["governed_lr6_production_activation"] is False
