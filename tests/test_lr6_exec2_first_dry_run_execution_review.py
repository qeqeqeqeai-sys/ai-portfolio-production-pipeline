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
