#!/usr/bin/env python3
from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
import os
import sys
from typing import Any

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    resolve_streamlit_supabase_client,
)
from transmission_layers.expectation_failure.expectation_intelligence.d21_limited_governed_non_dry_historical_backfill import (
    execute_d21_limited_governed_non_dry_historical_backfill,
)

STATUS_CONNECTIVITY_FAILED = "CONNECTIVITY_FAILED_NO_WRITE"
STATUS_GOV_BLOCKED = "GOVERNANCE_BLOCKED_NO_WRITE"
STATUS_SUCCESS = "D21_EXECUTED_WINDOW_1_SUCCESS"
STATUS_EXEC_FAILED = "D21_EXECUTION_FAILED_AFTER_APPROVAL"

REQUIRED_APPROVALS = OrderedDict([
    ("execute_non_dry", "I_APPROVE_D21_NON_DRY_BACKFILL"),
    ("approve_append_only", "I_APPROVE_APPEND_ONLY_PERSISTENCE"),
    ("approve_duplicate_prevention", "I_APPROVE_DUPLICATE_PREVENTION"),
    ("approve_checksum_lineage", "I_APPROVE_CHECKSUM_LINEAGE"),
])


def _fingerprint(secret_value: str | None) -> str:
    if not secret_value:
        return "missing"
    return hashlib.sha256(secret_value.encode("utf-8")).hexdigest()[:12]


def _summary(status: str, **kwargs: Any) -> OrderedDict[str, Any]:
    out: OrderedDict[str, Any] = OrderedDict([("status", status)])
    out.update(kwargs)
    return out


def main() -> int:
    window_count = str(os.getenv("D21_WINDOW_COUNT", "1")).strip()
    approvals = {k: str(os.getenv(k.upper(), "")).strip() for k in REQUIRED_APPROVALS}

    if window_count != "1":
        print(json.dumps(_summary(STATUS_GOV_BLOCKED, blocking_reasons=["window_count_must_equal_1_for_first_live_run"], window_count=window_count), indent=2))
        return 2

    approval_failures = [f"{k}_invalid" for k, v in REQUIRED_APPROVALS.items() if approvals.get(k) != v]
    if approval_failures:
        print(json.dumps(_summary(STATUS_GOV_BLOCKED, blocking_reasons=approval_failures, approval_keys=list(REQUIRED_APPROVALS.keys())), indent=2))
        return 2

    runtime_config = build_streamlit_supabase_runtime_config(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY"),
    )
    resolution = resolve_streamlit_supabase_client(runtime_config)

    if resolution.get("client_resolved") is not True or resolution.get("client") is None:
        print(json.dumps(_summary(
            STATUS_CONNECTIVITY_FAILED,
            supabase_url_present=bool(runtime_config.get("supabase_url")),
            supabase_service_role_key_present=bool(runtime_config.get("supabase_key")),
            fingerprints=OrderedDict([
                ("supabase_url", _fingerprint(runtime_config.get("supabase_url"))),
                ("supabase_service_role_key", _fingerprint(runtime_config.get("supabase_key"))),
            ]),
            resolution_error_type=resolution.get("client_error_type"),
            resolution_error_message_short=resolution.get("client_error_message_short"),
        ), indent=2))
        return 3

    d21_approvals = {
        "approved_for_execution": True,
        "approved_by_governance": True,
        "approve_non_dry_run": "true",
        "approve_append_only_persistence": "true",
        "approve_duplicate_prevention": "true",
        "approve_checksum_lineage": "true",
    }

    try:
        out = execute_d21_limited_governed_non_dry_historical_backfill(
            client=resolution.get("client"),
            approval_flags=d21_approvals,
            window_count=1,
        )
    except Exception as exc:
        print(json.dumps(_summary(STATUS_EXEC_FAILED, error_type=type(exc).__name__, error_message_short=str(exc)[:200]), indent=2))
        return 4

    if out.get("status") != "D21_LIMITED_BACKFILL_EXECUTED":
        print(json.dumps(_summary(STATUS_EXEC_FAILED, d21_status=out.get("status"), result=out), indent=2))
        return 4

    print(json.dumps(_summary(
        STATUS_SUCCESS,
        execution_status=out.get("status"),
        rows_inserted=out.get("rows_inserted"),
        duplicate_prevention_result=out.get("duplicate_prevention_result"),
        checksum_lineage_result=out.get("checksum_lineage_verified"),
        d8_c_readback_result=out.get("window_runs", [{}])[-1].get("readback") if out.get("window_runs") else None,
        d7_readback_result=out.get("d7_readback"),
        d15_d19_enrichment_status=out.get("d15_d19_enrichment"),
        safety_confirmations=out.get("safety"),
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
