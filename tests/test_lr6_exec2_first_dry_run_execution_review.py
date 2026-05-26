from transmission_layers.expectation_failure.replay_ecology.lr6_exec2_first_dry_run_execution_review import (
    build_lr6_exec2_first_dry_run_execution_review,
)


def test_lr6_exec2_dry_run_review_is_deterministic_and_bounded():
    a = build_lr6_exec2_first_dry_run_execution_review()
    b = build_lr6_exec2_first_dry_run_execution_review()
    assert a == b
    assert a["dry_run_execution_review"]["dry_run_path_executed"] is True
    assert a["dry_run_execution_review"]["non_dry_activation_detected"] is False
    assert a["wave_assembly_review"]["candidate_count"] == 16
    assert a["execution_artifact_review"]["artifact_count"] == 8


def test_lr6_exec2_validation_checks_and_recommendation():
    out = build_lr6_exec2_first_dry_run_execution_review()
    checks = out["validation_checks"]
    assert checks["dry_run_true"] is True
    assert checks["execution_authorized_false"] is True
    assert checks["no_persistence_writes"] is True
    assert checks["governance_gating_intact"] is True
    assert checks["stop_after_first_wave_true"] is True
    assert checks["no_recursive_continuation"] is True
    assert checks["no_direct_sql_boundary"] is True
    assert checks["outputs_bounded_reviewable"] is True
    assert out["recommendation"]["decision"] == "proceed_to_one_bounded_governed_non_dry_observation_wave"


def test_lr6_exec2_role_attribution_is_preserved_and_not_all_unknown():
    out = build_lr6_exec2_first_dry_run_execution_review()
    role_review = out["wave_assembly_review"]["role_attribution"]
    required_roles = out["wave_assembly_review"]["required_roles_present"]
    assert role_review["known_role_metadata_count"] > 0
    assert role_review["unknown_role_metadata_count"] != role_review["total_candidates"]
    assert role_review["weak_signal_count"] > 0
    assert role_review["contradiction_carrier_count"] > 0
    assert role_review["propagation_bridge_count"] > 0
    assert role_review["role_metadata_preserved"] is True
    assert required_roles["weak_signal"] is True
    assert required_roles["contradiction"] is True
    assert required_roles["propagation"] is True
