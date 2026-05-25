from transmission_layers.expectation_failure.replay_ecology.lr6_gov_dec_operator_decision import (
    build_lr6_gov_dec_approval_validation,
    build_lr6_gov_dec_governance_boundary_inventory,
    build_lr6_gov_dec_operator_decision_state,
    build_lr6_gov_dec_report_payload,
    build_lr6_gov_dec_required_approval_phrases,
    build_lr6_gov_dec_rejection_or_deferral_paths,
    build_lr6_gov_dec_residual_risk_acknowledgement,
    certify_lr6_gov_dec_operator_decision_record,
    load_lr6_gov_dec_inputs,
)


def test_lr6_gov_dec_determinism() -> None:
    assert load_lr6_gov_dec_inputs() == load_lr6_gov_dec_inputs()
    assert build_lr6_gov_dec_report_payload() == build_lr6_gov_dec_report_payload()


def test_default_state_and_no_inferred_approval() -> None:
    inputs = load_lr6_gov_dec_inputs()
    state = build_lr6_gov_dec_operator_decision_state(inputs)
    validation = build_lr6_gov_dec_approval_validation(inputs)
    assert state["decision_state"] in {"pending_operator_decision", "approval_incomplete"}
    assert state["default_decision_state"] == "pending_operator_decision"
    assert validation["approval_inferred_from_artifacts"] is False
    assert validation["all_required_phrases_explicitly_supplied"] is False


def test_required_phrase_inventory_and_empty_placeholders() -> None:
    inv = build_lr6_gov_dec_required_approval_phrases(load_lr6_gov_dec_inputs())
    assert inv["required_phrase_inventory"]
    assert all(v is None for v in inv["provided_approval_phrase_placeholders"].values())


def test_incomplete_approval_cannot_pass_and_complete_can_be_represented() -> None:
    inputs = load_lr6_gov_dec_inputs()
    validation = build_lr6_gov_dec_approval_validation(inputs)
    assert validation["approval_validation_status"] == "incomplete"

    required = build_lr6_gov_dec_required_approval_phrases(inputs)["required_phrase_inventory"]
    complete_representation = {
        "all_required_phrases_explicitly_supplied": True,
        "missing_required_phrases": [],
        "approval_inferred_from_artifacts": False,
        "approval_validation_status": "complete",
        "provided": {p: True for p in required},
    }
    assert complete_representation["all_required_phrases_explicitly_supplied"] is True
    assert complete_representation["approval_validation_status"] == "complete"


def test_no_activation_and_boundary_integrity() -> None:
    payload = build_lr6_gov_dec_report_payload()
    cert = certify_lr6_gov_dec_operator_decision_record(load_lr6_gov_dec_inputs())
    boundaries = build_lr6_gov_dec_governance_boundary_inventory(load_lr6_gov_dec_inputs())
    assert payload["lr6_production_replay_activated"] is False
    assert cert["lr6_production_replay_activated"] is False
    assert boundaries["no_replay_execution"] is True
    assert boundaries["no_replay_waves"] is True
    assert boundaries["no_persistence_writes"] is True
    assert boundaries["no_direct_sql"] is True
    assert boundaries["no_external_apis"] is True
    assert boundaries["no_prediction_or_trading"] is True
    assert boundaries["additive_architecture_preserved"] is True


def test_residual_risk_and_deferral_paths_present() -> None:
    risks = build_lr6_gov_dec_residual_risk_acknowledgement(load_lr6_gov_dec_inputs())
    paths = build_lr6_gov_dec_rejection_or_deferral_paths(load_lr6_gov_dec_inputs())
    assert risks["residual_risk_acknowledgement_required"] is True
    assert risks["residual_risk_checklist"]
    assert paths["paths"]
