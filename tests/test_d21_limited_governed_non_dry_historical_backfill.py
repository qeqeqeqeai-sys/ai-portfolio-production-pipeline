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


def test_d21_halts_without_required_governance_flags():
    out = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags={"approved_for_execution": True}, window_count=1)
    assert out["status"] == "REPLAY_PERSISTENCE_GOVERNANCE_BLOCKED"


def test_d21_executes_limited_backfill_and_reports_safety():
    out = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=2)
    assert out["status"] == "D21_LIMITED_BACKFILL_EXECUTED"
    assert out["window_count_executed"] == 2
    assert out["rows_inserted"]["dashboard_replay_metadata_records"] >= 1
    assert out["checksum_lineage_verified"] is True
    assert out["safety"]["no_direct_sql"] is True


def test_d21_blocks_out_of_bounds_window_count():
    out = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=4)
    assert out["status"] == "BACKFILL_WINDOW_COUNT_BLOCKED"
