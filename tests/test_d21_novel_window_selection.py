from transmission_layers.expectation_failure.expectation_intelligence.d21_limited_governed_non_dry_historical_backfill import (
    execute_d21_limited_governed_non_dry_historical_backfill,
)
from tests.test_d8_b4_governed_replay_persistence_execution import C

APPROVALS = {
    "approved_for_execution": True,
    "approved_by_governance": True,
    "approve_non_dry_run": "true",
    "approve_append_only_persistence": "true",
    "approve_duplicate_prevention": "true",
    "approve_checksum_lineage": "true",
}


def test_deterministic_offset_window_selection_and_diagnostics_shape():
    out = execute_d21_limited_governed_non_dry_historical_backfill(
        client=C(), approval_flags=APPROVALS, window_count=2, window_offset=3
    )
    assert out["candidate_selection_mode"] == "DETERMINISTIC_WINDOW_OFFSET_SLICE"
    assert out["window_offset"] == 3
    assert out["selected_candidate_count"] == 2
    assert out["selected_candidate_ids"] == ["W4", "W5"]
    assert out["next_recommended_window_offset"] == 5


def test_offset_does_not_bypass_governance_approval_gates():
    blocked = execute_d21_limited_governed_non_dry_historical_backfill(
        client=C(), approval_flags={"approved_for_execution": True}, window_count=1, window_offset=5
    )
    assert blocked["status"] == "REPLAY_PERSISTENCE_GOVERNANCE_BLOCKED"
