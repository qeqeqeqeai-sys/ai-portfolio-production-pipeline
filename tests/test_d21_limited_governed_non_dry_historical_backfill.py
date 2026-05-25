from pathlib import Path

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
    out = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=2, window_offset=0)
    assert out["status"] == "D21_LIMITED_BACKFILL_EXECUTED"
    assert out["window_count_executed"] == 2
    assert out["rows_inserted"]["dashboard_replay_metadata_records"] >= 1
    assert out["rows_inserted_semantics"] == "VISIBLE_PERSISTED_ROWS_AFTER_RUN"
    assert out["checksum_lineage_verified"] is True
    assert out["safety"]["no_direct_sql"] is True
    assert out["candidate_selection_mode"] == "DETERMINISTIC_WINDOW_OFFSET_SLICE"
    assert out["window_offset"] == 0
    assert out["selected_candidate_ids"] == ["W1", "W2"]


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


def test_d21_allows_window_count_1_2_3_and_blocks_4_and_0():
    allowed_1 = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=1)
    allowed_2 = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=2)
    allowed_3 = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=3)
    blocked_4 = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=4)
    blocked_0 = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=0)

    assert allowed_1["status"] == "D21_LIMITED_BACKFILL_EXECUTED"
    assert allowed_2["status"] == "D21_LIMITED_BACKFILL_EXECUTED"
    assert allowed_3["status"] == "D21_LIMITED_BACKFILL_EXECUTED"
    assert blocked_4["status"] == "BACKFILL_WINDOW_COUNT_BLOCKED"
    assert blocked_0["status"] == "BACKFILL_WINDOW_COUNT_BLOCKED"
    assert blocked_4["blocking_reasons"] == ["window_count_must_be_between_1_and_3"]


def test_d21_blocks_negative_window_count():
    blocked = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=-1)
    assert blocked["status"] == "BACKFILL_WINDOW_COUNT_BLOCKED"
    assert blocked["blocking_reasons"] == ["window_count_must_be_between_1_and_3"]


def test_d21_blocks_non_numeric_window_count():
    try:
        execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count="abc")
    except ValueError:
        pass
    else:
        assert False, "expected ValueError for non-numeric window_count"


def test_d21_workflow_window_count_range_and_approvals_unchanged():
    workflow = Path(".github/workflows/d21_limited_governed_backfill.yml").read_text(encoding="utf-8")
    assert "window_count must be 1, 2, or 3 for limited governed run" in workflow
    assert "I_APPROVE_D21_NON_DRY_BACKFILL" in workflow
    assert "I_APPROVE_APPEND_ONLY_PERSISTENCE" in workflow
    assert "I_APPROVE_DUPLICATE_PREVENTION" in workflow
    assert "I_APPROVE_CHECKSUM_LINEAGE" in workflow


def test_d21_script_default_and_window_count_gate():
    script = Path("scripts/run_d21_limited_governed_backfill.py").read_text(encoding="utf-8")
    assert 'os.getenv("D21_WINDOW_COUNT", "1")' in script
    assert 'os.getenv("D21_WINDOW_OFFSET", "0")' in script
    assert "window_count_must_be_1_or_2_or_3_for_limited_governed_run" in script


def test_d21_window_offset_behaviors():
    client = C()
    execute_d21_limited_governed_non_dry_historical_backfill(client=client, approval_flags=APPROVALS, window_count=1, window_offset=0)
    second_default = execute_d21_limited_governed_non_dry_historical_backfill(client=client, approval_flags=APPROVALS, window_count=1, window_offset=0)
    offset_novel = execute_d21_limited_governed_non_dry_historical_backfill(client=client, approval_flags=APPROVALS, window_count=1, window_offset=1)
    far_offset = execute_d21_limited_governed_non_dry_historical_backfill(client=client, approval_flags=APPROVALS, window_count=1, window_offset=999)

    assert second_default["selected_candidate_ids"] == ["W1"]
    assert second_default["rows_newly_inserted"]["dashboard_export_manifests"] == 0
    assert second_default["selected_candidate_already_existing_count"] >= 1
    assert offset_novel["selected_candidate_ids"] == ["W2"]
    assert offset_novel["selected_candidate_new_count"] >= 1
    assert offset_novel["next_recommended_window_offset"] == 2
    assert far_offset["selected_candidate_ids"] == ["W1000"]
    assert far_offset["window_offset"] == 999


def test_d21_blocks_negative_window_offset():
    blocked = execute_d21_limited_governed_non_dry_historical_backfill(client=C(), approval_flags=APPROVALS, window_count=1, window_offset=-1)
    assert blocked["status"] == "BACKFILL_WINDOW_OFFSET_BLOCKED"
    assert blocked["blocking_reasons"] == ["window_offset_must_be_zero_or_positive_integer"]
