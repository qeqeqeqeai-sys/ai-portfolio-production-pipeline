from transmission_layers.expectation_failure.replay_ecology.lr6_prep_governed_activation_proposal import (
    build_lr6_prep_activation_gates,
    build_lr6_prep_bounded_first_activation_scope,
    build_lr6_prep_governance_boundary_inventory,
    build_lr6_prep_monoculture_guardrails,
    build_lr6_prep_operator_approval_requirements,
    build_lr6_prep_pause_conditions,
    build_lr6_prep_readiness_summary,
    build_lr6_prep_report_payload,
    build_lr6_prep_rollback_conditions,
    build_lr6_prep_saturation_guardrails,
    certify_lr6_prep_activation_proposal,
    load_lr6_prep_inputs,
)


def test_lr6_prep_proposal_determinism() -> None:
    assert build_lr6_prep_report_payload() == build_lr6_prep_report_payload()
    assert load_lr6_prep_inputs() == load_lr6_prep_inputs()


def test_readiness_and_gate_presence() -> None:
    inputs = load_lr6_prep_inputs()
    summary = build_lr6_prep_readiness_summary(inputs)
    gates = build_lr6_prep_activation_gates(inputs)
    assert summary["adjusted_readiness_score"] == 0.790225
    assert summary["readiness_threshold"] == 0.79
    assert summary["threshold_cleared"] is True
    assert gates["gate_readiness_threshold_met"] is True
    assert gates["gate_no_severe_saturation_breach"] is True
    assert gates["gate_no_severe_monoculture_breach"] is True


def test_scope_and_approval_requirements() -> None:
    inputs = load_lr6_prep_inputs()
    scope = build_lr6_prep_bounded_first_activation_scope(inputs)
    approval = build_lr6_prep_operator_approval_requirements(inputs)
    assert 60 <= scope["proposed_entity_count"] <= 120
    assert scope["proposed_entity_count"] < scope["full_universe_size"]
    assert len(scope["proposed_entity_ids"]) == scope["proposed_entity_count"]
    assert approval["required_approval_phrase"]


def test_guardrails_pause_rollback_governance_presence() -> None:
    inputs = load_lr6_prep_inputs()
    sat = build_lr6_prep_saturation_guardrails(inputs)
    mono = build_lr6_prep_monoculture_guardrails(inputs)
    pause = build_lr6_prep_pause_conditions(inputs)
    rollback = build_lr6_prep_rollback_conditions(inputs)
    governance = build_lr6_prep_governance_boundary_inventory(inputs)
    assert sat["severe_threshold"] == 0.85
    assert mono["severe_threshold"] == 0.25
    assert pause
    assert rollback
    assert governance["no_replay_execution"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True


def test_proposal_not_activation_and_no_write_logic() -> None:
    payload = build_lr6_prep_report_payload()
    cert = certify_lr6_prep_activation_proposal(load_lr6_prep_inputs())
    assert payload["lr6_production_replay_activated"] is False
    assert cert["lr6_production_replay_activated"] is False
