from transmission_layers.expectation_failure.replay_ecology.lr6_run1_single_governed_observation_wave import (
    FINAL_DECISIONS,
    REQUIRED_APPROVAL_PHRASE,
    execute_lr6_run1_single_governed_observation_wave,
)


def test_lr6_run1_fails_closed_without_required_phrase():
    out = execute_lr6_run1_single_governed_observation_wave(approval_phrase="BAD", dry_run=False)
    assert out["approval"]["phrase_valid"] is False
    assert out["execution"]["execution"]["status"] == "GOVERNANCE_BLOCKED_FAIL_CLOSED"
    assert out["final_decision"] == FINAL_DECISIONS["continue_not_recommended"]


def test_lr6_run1_is_bounded_and_stops_after_first_wave_with_valid_phrase():
    out = execute_lr6_run1_single_governed_observation_wave(approval_phrase=REQUIRED_APPROVAL_PHRASE, dry_run=False)
    assert out["approval"]["phrase_valid"] is True
    assert out["validation"]["bounded_16_candidate_execution"] is True
    assert out["validation"]["stop_after_first_wave_enforced"] is True
    assert out["validation"]["no_recursive_continuation"] is True
    assert out["final_decision"] == FINAL_DECISIONS["ecology_improvement_not_sufficient"]
