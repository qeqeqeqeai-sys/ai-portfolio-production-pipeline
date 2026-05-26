from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology.lr6_exec1_first_governed_bounded_enriched_replay_wave import (
    REQUIRED_APPROVALS,
    execute_lr6_exec1_first_wave,
)


def test_lr6_exec1_defaults_to_dry_run_and_stops_after_first_wave():
    out = execute_lr6_exec1_first_wave()
    assert out["execution"]["dry_run"] is True
    assert out["execution"]["status"] == "DRY_RUN_COMPLETED"
    assert out["execution"]["stop_after_first_wave_enforced"] is True
    assert out["execution"]["automatic_continuation_allowed"] is False
    assert out["execution"]["recursive_expansion_allowed"] is False
    assert out["execution_boundary_certification"]["dry_run_default"] is True


def test_lr6_exec1_non_dry_fails_closed_without_explicit_approvals():
    out = execute_lr6_exec1_first_wave(dry_run=False, approvals={})
    assert out["execution"]["status"] == "GOVERNANCE_BLOCKED_FAIL_CLOSED"
    assert out["execution"]["executed_non_dry"] is False
    assert out["governance_approval_validation"]["approved"] is False
    assert out["governance_approval_validation"]["fail_closed"] is True


def test_lr6_exec1_non_dry_requires_exact_approval_phrases():
    bad = dict(REQUIRED_APPROVALS)
    bad["ack_observation_only"] = "not_exact"
    out_bad = execute_lr6_exec1_first_wave(dry_run=False, approvals=bad)
    assert out_bad["execution"]["status"] == "GOVERNANCE_BLOCKED_FAIL_CLOSED"

    out_ok = execute_lr6_exec1_first_wave(dry_run=False, approvals=REQUIRED_APPROVALS)
    assert out_ok["execution"]["status"] == "NON_DRY_APPROVED_BUT_STOPPED_AFTER_FIRST_WAVE"
    assert out_ok["execution"]["executed_non_dry"] is True
    assert out_ok["execution"]["automatic_continuation_allowed"] is False


def test_lr6_exec1_is_bounded_and_produces_deterministic_artifacts():
    a = execute_lr6_exec1_first_wave()
    b = execute_lr6_exec1_first_wave()
    assert a == b
    assert a["wave_preparation"]["selected_count"] == 16
    assert len(a["execution_review_artifacts"]) == 8
    candidates = a["wave_preparation"]["selected_candidates"]
    assert any(c.get("weak_signal_bridge") is True for c in candidates)
    assert any(c.get("contradiction_carrier") is True for c in candidates)
    assert any(c.get("propagation_bridge") is True for c in candidates)
    assert all("source_basis" in c for c in candidates)


def test_lr6_exec1_no_prediction_trading_or_direct_sql_paths():
    text = Path("transmission_layers/expectation_failure/replay_ecology/lr6_exec1_first_governed_bounded_enriched_replay_wave.py").read_text(encoding="utf-8").lower()
    assert "prediction" in text
    assert "trading" in text
    assert "no_direct_sql" in text
    assert "select(" not in text
    assert "insert(" not in text
    assert "update(" not in text
    assert "delete(" not in text
