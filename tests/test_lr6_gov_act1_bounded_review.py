from transmission_layers.expectation_failure.replay_ecology.lr6_gov_act1_bounded_review import (
    build_lr6_gov_act1_activation_risk_review,
    build_lr6_gov_act1_activation_scope_review,
    build_lr6_gov_act1_governance_gate_review,
    build_lr6_gov_act1_monoculture_guardrail_review,
    build_lr6_gov_act1_observability_review,
    build_lr6_gov_act1_operator_approval_review,
    build_lr6_gov_act1_pause_rollback_review,
    build_lr6_gov_act1_report_payload,
    build_lr6_gov_act1_reproducibility_review,
    build_lr6_gov_act1_saturation_guardrail_review,
    certify_lr6_gov_act1_review,
    load_lr6_gov_act1_inputs,
)


def test_lr6_gov_act1_review_determinism() -> None:
    assert load_lr6_gov_act1_inputs() == load_lr6_gov_act1_inputs()
    assert build_lr6_gov_act1_report_payload() == build_lr6_gov_act1_report_payload()


def test_scope_bounds_and_gate_presence() -> None:
    inputs = load_lr6_gov_act1_inputs()
    scope = build_lr6_gov_act1_activation_scope_review(inputs)
    gates = build_lr6_gov_act1_governance_gate_review(inputs)
    assert scope["scope_bounds_preserved"] is True
    assert scope["bounded_vs_full_universe"] is True
    assert gates["non_operator_gates_cleared"] is True


def test_required_reviews_presence() -> None:
    inputs = load_lr6_gov_act1_inputs()
    op = build_lr6_gov_act1_operator_approval_review(inputs)
    sat = build_lr6_gov_act1_saturation_guardrail_review(inputs)
    mono = build_lr6_gov_act1_monoculture_guardrail_review(inputs)
    pause = build_lr6_gov_act1_pause_rollback_review(inputs)
    obs = build_lr6_gov_act1_observability_review(inputs)
    repro = build_lr6_gov_act1_reproducibility_review(inputs)
    assert op["approval_phrase_defined"] is True
    assert sat["saturation_guardrails"]
    assert mono["monoculture_guardrails"]
    assert pause["pause_and_rollback_defined"] is True
    assert obs["observability_requirements_defined"] is True
    assert repro["reproducibility_requirements_defined"] is True


def test_unresolved_risks_and_non_activation() -> None:
    inputs = load_lr6_gov_act1_inputs()
    risk = build_lr6_gov_act1_activation_risk_review(inputs)
    cert = certify_lr6_gov_act1_review(inputs)
    payload = build_lr6_gov_act1_report_payload()
    assert "operator_approvals_not_completed" in risk["unresolved_governance_risks"]
    assert cert["lr6_production_replay_activated"] is False
    assert payload["lr6_production_replay_activated"] is False


def test_no_disallowed_logic_introduced() -> None:
    payload = build_lr6_gov_act1_report_payload()
    governance = payload["governance_certification_metadata"]
    assert governance["no_replay_execution"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True
