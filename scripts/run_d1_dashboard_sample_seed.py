"""Safe CLI runner for deterministic D1 dashboard sample-data seed execution."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from collections import OrderedDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Any

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import run_d1_controlled_seed
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import build_dashboard_read_table_inventory


def _resolve_credentials() -> tuple[str, str, list[str]]:
    missing: list[str] = []
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_ANON_KEY|SUPABASE_KEY")
    return url, key, missing


def _build_client(url: str, key: str) -> Any:
    from supabase import create_client  # type: ignore

    return create_client(url, key)


def _table_counts_from_write_plan(write_plan: dict[str, Any]) -> OrderedDict:
    table_counts = OrderedDict()
    for batch in write_plan.get("write_steps", []):
        table_counts[str(batch.get("source_payload_key"))] = int(batch.get("row_count", 0))
    return table_counts


def _verify_readback_counts(*, client: Any, tables: list[str], run_id: str | None) -> OrderedDict:
    counts = OrderedDict()
    for table in tables:
        query = client.table(table).select("*", count="exact")
        if run_id:
            query = query.eq("run_id", run_id)
        response = query.limit(1).execute()
        counts[table] = int(getattr(response, "count", 0) or 0)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic D1 dashboard sample-data seed via O3 controlled write adapter.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate D1 controlled seed only (default behavior).")
    parser.add_argument("--execute", action="store_true", help="Execute controlled sample-data writes through O3 adapter.")
    parser.add_argument("--verify-readback", action="store_true", help="Read-only post-seed count verification for expected physical dashboard tables.")
    args = parser.parse_args(argv)

    execute = bool(args.execute)
    dry_run = not execute

    print("WARNING: This command writes controlled deterministic sample data only when --execute is provided.")
    print(f"mode={'execute' if execute else 'dry_run'}")

    url, key, missing = _resolve_credentials()
    if missing:
        print(f"Missing required credentials: {', '.join(missing)}")
        return 2

    client = _build_client(url, key)
    result = run_d1_controlled_seed(confirm_execute=execute, dry_run=dry_run, supabase_client=client)

    table_counts = _table_counts_from_write_plan(result.get("write_plan", {}))
    print("target_tables_and_counts=")
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

    if args.verify_readback:
        expected_tables = list(build_dashboard_read_table_inventory())
        readback_counts = _verify_readback_counts(client=client, tables=expected_tables, run_id=manifest.get("run_id"))
        print("readback_row_counts=")
        for table_name, row_count in readback_counts.items():
            print(f"- {table_name}: {row_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
