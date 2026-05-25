from transmission_layers.expectation_failure.replay_ecology.lr6_governance_freeze import (
    build_lr6_active_governance_profile,
    build_lr6_experimental_mode_profile,
    build_lr6_frozen_governance_profile,
    build_lr6_governance_freeze_report_payload,
    build_lr6_governance_inventory,
    build_lr6_governance_recursion_diagnostics,
    build_lr6_governed_mode_profile,
    classify_lr6_governance_layers,
)


def test_governance_inventory_determinism() -> None:
    assert build_lr6_governance_inventory() == build_lr6_governance_inventory()


def test_classification_determinism() -> None:
    inventory = build_lr6_governance_inventory()
    assert classify_lr6_governance_layers(inventory) == classify_lr6_governance_layers(inventory)


def test_core_safety_rails_preserved() -> None:
    payload = build_lr6_governance_freeze_report_payload()
    rails = payload["retained_safety_rails"]
    for rule in [
        "bounded_replay_windows",
        "dry_run_first_policy",
        "saturation_guardrails",
        "monoculture_caps",
        "rollback_conditions",
        "observability_requirements",
        "deterministic_reproducibility",
        "no_direct_sql_enforcement",
        "additive_architecture_enforcement",
    ]:
        assert rule in rails


def test_frozen_layers_preserved_but_inactive() -> None:
    inventory = build_lr6_governance_inventory()
    classification = classify_lr6_governance_layers(inventory)
    frozen = build_lr6_frozen_governance_profile(classification)
    assert frozen["layers"]
    assert frozen["is_operational"] is False
    assert frozen["retained_for_history"] is True


def test_mode_profiles_exist() -> None:
    classification = classify_lr6_governance_layers(build_lr6_governance_inventory())
    experimental = build_lr6_experimental_mode_profile(classification)
    governed = build_lr6_governed_mode_profile(classification)
    active = build_lr6_active_governance_profile(classification)
    assert experimental["mode"] == "experimental_mode"
    assert governed["mode"] == "governed_mode"
    assert active["is_operational"] is True


def test_governance_recursion_diagnostics_present() -> None:
    classification = classify_lr6_governance_layers(build_lr6_governance_inventory())
    diagnostics = build_lr6_governance_recursion_diagnostics(classification)
    assert diagnostics["recursive_layer_count"] > 0
    assert diagnostics["active_recursive_layers"] == 0


def test_constraints_and_no_history_deletion() -> None:
    payload = build_lr6_governance_freeze_report_payload()
    cert = payload["governance_certification_metadata"]
    assert cert["historical_governance_deleted"] is False
    assert cert["no_replay_execution"] is True
    assert cert["no_replay_waves"] is True
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["no_prediction_or_trading"] is True
    assert cert["deterministic_reproducibility_preserved"] is True
