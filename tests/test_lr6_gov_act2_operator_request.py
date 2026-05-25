from transmission_layers.expectation_failure.replay_ecology.lr6_gov_act2_operator_request import (
    build_lr6_gov_act2_activation_request_scope,
    build_lr6_gov_act2_approval_phrase_inventory,
    build_lr6_gov_act2_governance_lock_review,
    build_lr6_gov_act2_monoculture_watch_conditions,
    build_lr6_gov_act2_observability_requirements,
    build_lr6_gov_act2_operator_completion_requirements,
    build_lr6_gov_act2_pause_rollback_controls,
    build_lr6_gov_act2_report_payload,
    build_lr6_gov_act2_residual_risk_register,
    build_lr6_gov_act2_saturation_watch_conditions,
    certify_lr6_gov_act2_activation_request_package,
    load_lr6_gov_act2_inputs,
)


def test_lr6_gov_act2_package_determinism() -> None:
    assert load_lr6_gov_act2_inputs() == load_lr6_gov_act2_inputs()
    assert build_lr6_gov_act2_report_payload() == build_lr6_gov_act2_report_payload()


def test_operator_requirements_and_phrase_inventory_present() -> None:
    inputs = load_lr6_gov_act2_inputs()
    requirements = build_lr6_gov_act2_operator_completion_requirements(inputs)
    phrases = build_lr6_gov_act2_approval_phrase_inventory(inputs)
    assert requirements["required_approver_roles"]
    assert requirements["activation_request_checklist"]
    assert phrases["required_primary_phrase"]
    assert len(phrases["required_secondary_phrases"]) >= 3


def test_scope_watch_controls_and_risk_register() -> None:
    inputs = load_lr6_gov_act2_inputs()
    scope = build_lr6_gov_act2_activation_request_scope(inputs)
    mono = build_lr6_gov_act2_monoculture_watch_conditions(inputs)
    sat = build_lr6_gov_act2_saturation_watch_conditions(inputs)
    pause = build_lr6_gov_act2_pause_rollback_controls(inputs)
    risks = build_lr6_gov_act2_residual_risk_register(inputs)
    assert scope["scope_preserved"] is True
    assert scope["first_activation_entity_count"] == 90
    assert scope["first_activation_window_days"] == 30
    assert mono["watch_status"] == "active"
    assert sat["watch_status"] == "active"
    assert pause["strict_pause_conditions_required"] is True
    assert pause["strict_rollback_conditions_required"] is True
    assert risks["residual_risks"]


def test_governance_lock_and_non_activation() -> None:
    inputs = load_lr6_gov_act2_inputs()
    lock = build_lr6_gov_act2_governance_lock_review(inputs)
    cert = certify_lr6_gov_act2_activation_request_package(inputs)
    payload = build_lr6_gov_act2_report_payload()
    assert lock["governance_lock_active"] is True
    assert cert["ready_for_operator_decision"] is True
    assert cert["lr6_production_replay_activated"] is False
    assert payload["lr6_production_replay_activated"] is False


def test_no_disallowed_logic_introduced() -> None:
    payload = build_lr6_gov_act2_report_payload()
    governance = payload["governance_certification_metadata"]
    observability = build_lr6_gov_act2_observability_requirements(load_lr6_gov_act2_inputs())
    assert governance["no_replay_execution"] is True
    assert governance["no_persistence_writes"] is True
    assert governance["no_direct_sql"] is True
    assert governance["no_external_apis"] is True
    assert governance["no_prediction_or_trading"] is True
    assert governance["additive_architecture_preserved"] is True
    assert "deterministic_reproducibility_payload_hash" in observability["requirements"]
