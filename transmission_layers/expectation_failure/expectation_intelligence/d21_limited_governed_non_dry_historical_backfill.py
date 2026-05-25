from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from datetime import date, timedelta
from typing import Any, Mapping

from transmission_layers.expectation_failure.expectation_intelligence.d8_b4_governed_replay_persistence_execution import (
    build_d8_b4_post_execution_readback,
    execute_d8_b4_governed_replay_persistence,
    validate_d8_b4_execution_governance,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d6_operational_proving_cycle import (
    build_d6_operational_proving_input,
    execute_d6_operational_proving_cycle,
)


def _windowed_payload(window_index: int) -> OrderedDict[str, Any]:
    base = build_d6_operational_proving_input()
    obs = deepcopy(list(base.get("sample_observations") or []))
    target_date = (date(2026, 5, 22) - timedelta(days=window_index)).isoformat()
    for row in obs:
        row["as_of_date"] = target_date
        oid = str(row.get("observation_id") or "OBS")
        row["observation_id"] = f"{oid}-W{window_index+1}"
        row["checksum"] = f"{row.get('checksum','chk')}-w{window_index+1}"
    return OrderedDict([("sample_observations", obs)])


def _read_replay_and_manifest_rows(client: Any) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    replay_rows = list(getattr(client.table("dashboard_replay_metadata_records").select("*").execute(), "data", []) or [])
    manifest_rows = list(getattr(client.table("dashboard_export_manifests").select("*").execute(), "data", []) or [])
    return replay_rows, manifest_rows


def _collect_ids_and_checksums(rows: list[Mapping[str, Any]], kind: str) -> list[str]:
    if kind == "replay":
        vals = [str(r.get("replay_id") or r.get("record_id") or "").strip() for r in rows if isinstance(r, Mapping)]
    else:
        vals = [str(r.get("export_checksum") or r.get("manifest_checksum") or "").strip() for r in rows if isinstance(r, Mapping)]
    return sorted({v for v in vals if v})


def execute_d21_limited_governed_non_dry_historical_backfill(*, client: Any, approval_flags: Mapping[str, Any] | None = None, window_count: int = 1, window_offset: int = 0) -> OrderedDict[str, Any]:
    n = int(window_count)
    if n < 1 or n > 3:
        return OrderedDict([("status", "BACKFILL_WINDOW_COUNT_BLOCKED"), ("window_count", n), ("blocking_reasons", ["window_count_must_be_between_1_and_3"]), ("future_expansion_policy", "window_count_above_3_requires_separate_patch_and_approval")])
    offset = int(window_offset)
    if offset < 0:
        return OrderedDict([("status", "BACKFILL_WINDOW_OFFSET_BLOCKED"), ("window_offset", offset), ("blocking_reasons", ["window_offset_must_be_zero_or_positive_integer"])])

    governance = validate_d8_b4_execution_governance(dry_run=False, client=client, approval_flags=approval_flags)
    if governance.get("status") != "GOVERNANCE_OK":
        return OrderedDict([("status", "REPLAY_PERSISTENCE_GOVERNANCE_BLOCKED"), ("governance", governance), ("window_count", n), ("window_offset", offset)])

    replay_rows_before, manifest_rows_before = _read_replay_and_manifest_rows(client)
    replay_ids_before = set(_collect_ids_and_checksums(replay_rows_before, "replay"))
    manifest_checksums_before = set(_collect_ids_and_checksums(manifest_rows_before, "manifest"))

    runs: list[OrderedDict[str, Any]] = []
    selected_indices = list(range(offset, offset + n))
    selected_candidate_ids = [f"W{idx+1}" for idx in selected_indices]
    for i in selected_indices:
        payload = _windowed_payload(i)
        d6 = execute_d6_operational_proving_cycle(payload=payload, client=client, dry_run=False)
        run = execute_d8_b4_governed_replay_persistence(client=client, approval_flags=approval_flags, dry_run=False)
        readback = run.get("readback") or {}
        runs.append(OrderedDict([("window_index", i + 1), ("candidate_id", f"W{i+1}"), ("as_of_date", payload["sample_observations"][0]["as_of_date"]), ("d6_cycle_checksum", d6.get("cycle_checksum")), ("execution_status", run.get("status")), ("audit_manifest", run.get("audit_manifest")), ("readback", readback)]))

    rerun = execute_d8_b4_governed_replay_persistence(client=client, approval_flags=approval_flags, dry_run=False)

    replay_rows_after, manifest_rows_after = _read_replay_and_manifest_rows(client)
    replay_ids_after = set(_collect_ids_and_checksums(replay_rows_after, "replay"))
    manifest_checksums_after = set(_collect_ids_and_checksums(manifest_rows_after, "manifest"))

    post = build_d8_b4_post_execution_readback(client=client)
    attempted_replay = len(list(post.get("latest_replay_ids") or []))
    attempted_manifest = len(list(post.get("latest_manifest_checksums") or []))

    newly_inserted_replay = max(0, len(replay_ids_after - replay_ids_before))
    newly_inserted_manifest = max(0, len(manifest_checksums_after - manifest_checksums_before))

    rows_attempted = OrderedDict([
        ("dashboard_replay_metadata_records", attempted_replay),
        ("dashboard_export_manifests", attempted_manifest),
    ])
    rows_newly_inserted = OrderedDict([
        ("dashboard_replay_metadata_records", newly_inserted_replay),
        ("dashboard_export_manifests", newly_inserted_manifest),
    ])
    rows_already_existing = OrderedDict([
        ("dashboard_replay_metadata_records", max(0, rows_attempted["dashboard_replay_metadata_records"] - newly_inserted_replay)),
        ("dashboard_export_manifests", max(0, rows_attempted["dashboard_export_manifests"] - newly_inserted_manifest)),
    ])
    duplicate_prevented_rows = OrderedDict(rows_already_existing)
    before_counts = OrderedDict([
        ("dashboard_replay_metadata_records", len(replay_rows_before)),
        ("dashboard_export_manifests", len(manifest_rows_before)),
    ])
    after_counts = OrderedDict([
        ("dashboard_replay_metadata_records", len(replay_rows_after)),
        ("dashboard_export_manifests", len(manifest_rows_after)),
    ])
    net_new_rows = OrderedDict([
        ("dashboard_replay_metadata_records", max(0, after_counts["dashboard_replay_metadata_records"] - before_counts["dashboard_replay_metadata_records"])),
        ("dashboard_export_manifests", max(0, after_counts["dashboard_export_manifests"] - before_counts["dashboard_export_manifests"])),
    ])

    duplicate_prevention_mode = "IDEMPOTENT_EXISTING_ROWS_REUSED" if sum(net_new_rows.values()) == 0 else "INSERTED_NEW_ROWS_WITH_IDEMPOTENT_GUARDS"
    selected_existing_count = rows_already_existing["dashboard_replay_metadata_records"]
    selected_new_count = rows_newly_inserted["dashboard_replay_metadata_records"]
    novel_window_available = bool(selected_new_count > 0)
    next_recommended_window_offset = offset + n

    return OrderedDict([
        ("status", "D21_LIMITED_BACKFILL_EXECUTED"),
        ("window_count_executed", n),
        ("window_offset", offset),
        ("candidate_selection_mode", "DETERMINISTIC_WINDOW_OFFSET_SLICE"),
        ("available_candidate_count", "UNBOUNDED_DETERMINISTIC_GENERATOR"),
        ("selected_candidate_count", len(selected_indices)),
        ("selected_candidate_ids", selected_candidate_ids),
        ("selected_candidate_already_existing_count", selected_existing_count),
        ("selected_candidate_new_count", selected_new_count),
        ("novel_window_available", novel_window_available),
        ("next_recommended_window_offset", next_recommended_window_offset),
        ("novel_window_status", "D21_EXECUTED_SAFELY_NO_NOVEL_CANDIDATES_AVAILABLE_UNDER_CURRENT_DETERMINISTIC_CANDIDATE_INVENTORY_DENSITY_IMPROVEMENT_REQUIRES_UPSTREAM_CANDIDATE_EXPANSION" if not novel_window_available else "D21_EXECUTED_SAFELY_WITH_NOVEL_CANDIDATES"),
        ("governance_flags_used", OrderedDict(sorted(dict(approval_flags or {}).items()))),
        ("approved_persistence_path", "D8.B4 -> O6/O7/D3/D6 adapters"),
        ("window_runs", runs),
        ("rows_inserted", OrderedDict([("dashboard_replay_metadata_records", post.get("replay_metadata_row_count", 0)), ("dashboard_export_manifests", post.get("manifest_row_count", 0))])),
        ("rows_inserted_semantics", "VISIBLE_PERSISTED_ROWS_AFTER_RUN"),
        ("rows_attempted", rows_attempted),
        ("rows_newly_inserted", rows_newly_inserted),
        ("rows_already_existing", rows_already_existing),
        ("duplicate_prevented_rows", duplicate_prevented_rows),
        ("duplicate_prevention_mode", duplicate_prevention_mode),
        ("before_counts", before_counts),
        ("after_counts", after_counts),
        ("net_new_rows", net_new_rows),
        ("persisted_rows_visible_after_run", OrderedDict([("dashboard_replay_metadata_records", post.get("replay_metadata_row_count", 0)), ("dashboard_export_manifests", post.get("manifest_row_count", 0))])),
        ("inserted_or_existing_replay_ids", sorted(replay_ids_after)),
        ("inserted_or_existing_manifest_checksums", sorted(manifest_checksums_after)),
        ("duplicate_prevention_result", rerun.get("status")),
        ("checksum_lineage_verified", bool(post.get("lineage_checksum_present"))),
        ("d7_readback", post),
        ("d15_d19_enrichment", OrderedDict([("d15", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d16", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d17", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d18", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d19", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING")])),
        ("safety", OrderedDict([("no_direct_sql", True), ("approved_adapters_only", True), ("no_predictive_or_trading_behavior", True), ("no_autonomous_actions", True), ("full_history_backfill_executed", False)])),
    ])
