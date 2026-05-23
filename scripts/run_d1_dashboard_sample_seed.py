"""Safe CLI runner for deterministic D1 dashboard sample-data seed execution."""

from __future__ import annotations

import argparse
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import run_d1_controlled_seed
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import build_dashboard_read_table_inventory


class ReadbackVerificationError(Exception):
    """Raised when readback verification cannot complete."""


def _resolve_credentials() -> tuple[str, str, str, list[str]]:
    missing: list[str] = []
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")

    key = ""
    credential_source = "none"
    for env_name, source in (
        ("SUPABASE_SERVICE_ROLE_KEY", "service_role_key"),
        ("SUPABASE_ANON_KEY", "anon_key"),
        ("SUPABASE_KEY", "supabase_key"),
    ):
        candidate = (os.getenv(env_name) or "").strip()
        if candidate:
            key = candidate
            credential_source = source
            break

    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY|SUPABASE_ANON_KEY|SUPABASE_KEY")
    return url, key, credential_source, missing


def _safe_supabase_host(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower()
    return host or "unknown_host"


def _build_client(url: str, key: str) -> Any:
    from supabase import create_client  # type: ignore

    return create_client(url, key)


def _table_counts_from_write_plan(write_plan: dict[str, Any]) -> OrderedDict:
    table_counts = OrderedDict()
    for batch in write_plan.get("write_steps", []):
        table_counts[str(batch.get("source_payload_key"))] = int(batch.get("row_count", 0))
    return table_counts


def _table_write_statuses(execution_result: Mapping[str, Any]) -> OrderedDict:
    table_statuses = OrderedDict()
    for result in execution_result.get("table_results", []):
        table_name = str(result.get("table_name"))
        table_statuses[table_name] = str(result.get("status") or "unknown")
    return table_statuses


def _table_write_statuses_detailed(execution_result: Mapping[str, Any]) -> list[OrderedDict]:
    rows: list[OrderedDict] = []
    for result in execution_result.get("table_results", []):
        rows.append(OrderedDict([
            ("table", str(result.get("table_name"))),
            ("status", str(result.get("status") or "unknown")),
            ("attempted_row_count", int(result.get("attempted_row_count", 0))),
            ("inserted_or_affected_row_count", result.get("inserted_or_affected_row_count")),
            ("error_type", result.get("error_type")),
            ("error_message_short", result.get("error_message_short")),
            ("missing_payload_columns", list(result.get("missing_payload_columns", []))),
            ("extra_payload_columns", list(result.get("extra_payload_columns", []))),
            ("payload_sample_keys", list(result.get("payload_sample_keys", []))),
        ]))
    return rows


def _infer_readback_status(exc: Exception) -> str:
    msg = str(exc).lower()
    if any(x in msg for x in ("permission", "rls", "not authorized", "forbidden", "401", "403")):
        return "permission_denied"
    return "query_failed"


def _verify_readback_counts(*, client: Any, tables: list[str], run_id: str | None) -> OrderedDict:
    results = OrderedDict()
    for table in tables:
        try:
            query = client.table(table).select("*", count="exact")
            if run_id:
                query = query.eq("run_id", run_id)
            response = query.limit(1).execute()
            row_count = int(getattr(response, "count", 0) or 0)
            status = "ready" if row_count > 0 else "empty"
            results[table] = OrderedDict([("row_count", row_count), ("status", status)])
        except Exception as exc:
            results[table] = OrderedDict([("row_count", 0), ("status", _infer_readback_status(exc))])
    return results


def _verification_status(readback_results: OrderedDict) -> str:
    statuses = [v.get("status") for v in readback_results.values()]
    if any(s in {"query_failed", "permission_denied"} for s in statuses):
        return "verification_failed"
    if any(int(v.get("row_count", 0)) > 0 for v in readback_results.values()):
        return "verified_non_empty"
    return "verified_empty"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic D1 dashboard sample-data seed via O3 controlled write adapter.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate D1 controlled seed only (default behavior).")
    parser.add_argument("--execute", action="store_true", help="Execute controlled sample-data writes through O3 adapter.")
    parser.add_argument("--verify-readback", action="store_true", help="Read-only post-seed count verification for expected physical dashboard tables.")
    parser.add_argument("--strict-write-verification", action="store_true", help="Fail execution if any table status is not success.")
    args = parser.parse_args(argv)

    execute = bool(args.execute)
    dry_run = not execute

    print("WARNING: This command writes controlled deterministic sample data only when --execute is provided.")
    print(f"mode={'execute' if execute else 'dry_run'}")

    url, key, credential_source, missing = _resolve_credentials()
    if missing:
        print(f"Missing required credentials: {', '.join(missing)}")
        return 2

    print(f"supabase_project_host={_safe_supabase_host(url)}")
    print(f"credential_source={credential_source}")

    client = _build_client(url, key)
    result = run_d1_controlled_seed(confirm_execute=execute, dry_run=dry_run, supabase_client=client)

    table_counts = _table_counts_from_write_plan(result.get("write_plan", {}))
    print("target_tables_and_counts=")
    print("planned_table_row_counts=")
    for table_name, row_count in table_counts.items():
        print(f"- {table_name}: {row_count}")

    manifest = result.get("seed_manifest", {})
    execution_result = result.get("execution_result", {})
    print("manifest_summary=")
    print(f"- run_id: {manifest.get('run_id')}")
    print(f"- checksum: {manifest.get('checksum')}")
    print(f"- total_row_count: {manifest.get('total_row_count')}")
    print(f"- execution_confirmed: {result.get('execution_confirmed')}")
    print(f"- execution_status: {execution_result.get('execution_status')}")

    table_write_statuses = _table_write_statuses(execution_result)
    if table_write_statuses:
        print("write_result_statuses=")
        for table_name, status in table_write_statuses.items():
            print(f"- {table_name}: {status}")

    detailed_statuses = _table_write_statuses_detailed(execution_result)
    if detailed_statuses:
        print("write_result_statuses_detailed=")
        for item in detailed_statuses:
            print(f"- table={item['table']}, status={item['status']}, attempted_row_count={item['attempted_row_count']}, inserted_or_affected_row_count={item['inserted_or_affected_row_count']}, error_type={item['error_type']}, error_message_short={item['error_message_short']}, missing_payload_columns={item['missing_payload_columns']}, extra_payload_columns={item['extra_payload_columns']}, payload_sample_keys={item['payload_sample_keys']}")

    if execute and any(status == "failed" for status in table_write_statuses.values()):
        return 1
    if execute and args.strict_write_verification and any(status != "success" for status in table_write_statuses.values()):
        return 1

    verification_status = "not_requested"
    if args.verify_readback:
        expected_tables = list(build_dashboard_read_table_inventory())
        readback_results = _verify_readback_counts(client=client, tables=expected_tables, run_id=manifest.get("run_id"))
        print("readback_table_results=")
        for table_name, entry in readback_results.items():
            print(f"- {table_name}: row_count={entry['row_count']}, status={entry['status']}")

        verification_status = _verification_status(readback_results)
        print(f"verification_status: {verification_status}")

        if execute and verification_status != "verified_non_empty":
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
