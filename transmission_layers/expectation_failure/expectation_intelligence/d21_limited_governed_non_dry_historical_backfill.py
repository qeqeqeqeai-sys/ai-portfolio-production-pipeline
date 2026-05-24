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


def execute_d21_limited_governed_non_dry_historical_backfill(*, client: Any, approval_flags: Mapping[str, Any] | None = None, window_count: int = 1) -> OrderedDict[str, Any]:
    n = int(window_count)
    if n < 1 or n > 3:
        return OrderedDict([("status", "BACKFILL_WINDOW_COUNT_BLOCKED"), ("window_count", n), ("blocking_reasons", ["window_count_must_be_between_1_and_3"])])

    governance = validate_d8_b4_execution_governance(dry_run=False, client=client, approval_flags=approval_flags)
    if governance.get("status") != "GOVERNANCE_OK":
        return OrderedDict([("status", "REPLAY_PERSISTENCE_GOVERNANCE_BLOCKED"), ("governance", governance), ("window_count", n)])

    runs: list[OrderedDict[str, Any]] = []
    inserted_replay = 0
    inserted_manifest = 0
    for i in range(n):
        payload = _windowed_payload(i)
        d6 = execute_d6_operational_proving_cycle(payload=payload, client=client, dry_run=False)
        run = execute_d8_b4_governed_replay_persistence(client=client, approval_flags=approval_flags, dry_run=False)
        readback = run.get("readback") or {}
        inserted_replay = max(inserted_replay, int(readback.get("replay_metadata_row_count") or 0))
        inserted_manifest = max(inserted_manifest, int(readback.get("manifest_row_count") or 0))
        runs.append(OrderedDict([("window_index", i + 1), ("as_of_date", payload["sample_observations"][0]["as_of_date"]), ("d6_cycle_checksum", d6.get("cycle_checksum")), ("execution_status", run.get("status")), ("audit_manifest", run.get("audit_manifest")), ("readback", readback)]))

    post = build_d8_b4_post_execution_readback(client=client)
    rerun = execute_d8_b4_governed_replay_persistence(client=client, approval_flags=approval_flags, dry_run=False)

    return OrderedDict([
        ("status", "D21_LIMITED_BACKFILL_EXECUTED"),
        ("window_count_executed", n),
        ("governance_flags_used", OrderedDict(sorted(dict(approval_flags or {}).items()))),
        ("approved_persistence_path", "D8.B4 -> O6/O7/D3/D6 adapters"),
        ("window_runs", runs),
        ("rows_inserted", OrderedDict([("dashboard_replay_metadata_records", post.get("replay_metadata_row_count", 0)), ("dashboard_export_manifests", post.get("manifest_row_count", 0))])),
        ("duplicate_prevention_result", rerun.get("status")),
        ("checksum_lineage_verified", bool(post.get("lineage_checksum_present"))),
        ("d7_readback", post),
        ("d15_d19_enrichment", OrderedDict([("d15", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d16", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d17", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d18", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING"), ("d19", "REAL_HISTORICAL_PAYLOAD_AVAILABLE" if post.get("replay_metadata_row_count") else "HISTORICAL_PAYLOAD_MISSING")])),
        ("safety", OrderedDict([("no_direct_sql", True), ("approved_adapters_only", True), ("no_predictive_or_trading_behavior", True), ("no_autonomous_actions", True), ("full_history_backfill_executed", False)])),
    ])
