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
    assert out["rows_inserted_semantics"] == "VISIBLE_PERSISTED_ROWS_AFTER_RUN"
    assert out["checksum_lineage_verified"] is True
    assert out["safety"]["no_direct_sql"] is True


def test_d21_first_and_second_run_insert_accounting_is_explicit_and_deterministic():
    client = C()
    first = execute_d21_limited_governed_non_dry_historical_backfill(client=client, approval_flags=APPROVALS, window_count=1)
    second = execute_d21_limited_governed_non_dry_historical_backfill(client=client, approval_flags=APPROVALS, window_count=1)

    assert first["rows_attempted"] == second["rows_attempted"]
    assert first["rows_newly_inserted"]["dashboard_replay_metadata_records"] > 0
    assert first["rows_newly_inserted"]["dashboard_export_manifests"] > 0
    assert sum(first["net_new_rows"].values()) > 0

    assert second["rows_newly_inserted"]["dashboard_export_manifests"] == 0
    assert second["rows_already_existing"]["dashboard_export_manifests"] == second["rows_attempted"]["dashboard_export_manifests"]
    assert second["duplicate_prevented_rows"]["dashboard_export_manifests"] == second["rows_attempted"]["dashboard_export_manifests"]
    assert second["duplicate_prevention_mode"] in {"IDEMPOTENT_EXISTING_ROWS_REUSED", "INSERTED_NEW_ROWS_WITH_IDEMPOTENT_GUARDS"}
    assert second["duplicate_prevention_result"] == "REPLAY_PERSISTENCE_OPERATIONAL"

    for field in [
        "rows_inserted",
        "duplicate_prevention_result",
        "checksum_lineage_verified",
        "d7_readback",
        "d15_d19_enrichment",
        "safety",
        "before_counts",
        "after_counts",
        "inserted_or_existing_replay_ids",
        "inserted_or_existing_manifest_checksums",
    ]:
        assert field in second


def test_d21_blocks_out_of_bounds_window_count():
    out = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=4)
    assert out["status"] == "BACKFILL_WINDOW_COUNT_BLOCKED"
