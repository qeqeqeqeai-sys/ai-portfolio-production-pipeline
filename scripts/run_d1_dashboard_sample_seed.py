"""Safe CLI runner for deterministic D1 dashboard sample-data seed execution."""

from __future__ import annotations

import argparse
import os
import sys
from collections import OrderedDict
from typing import Any

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    build_d1_seed_payload,
    run_d1_controlled_seed,
)


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


def _table_counts_from_payload() -> OrderedDict:
    payload = build_d1_seed_payload()
    table_counts = OrderedDict()
    for key, value in payload.items():
        if key.startswith("dashboard_") and isinstance(value, list):
            table_counts[key] = len(value)
    return table_counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic D1 dashboard sample-data seed via O3 controlled write adapter.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate D1 controlled seed only (default behavior).")
    parser.add_argument("--execute", action="store_true", help="Execute controlled sample-data writes through O3 adapter.")
    args = parser.parse_args(argv)

    execute = bool(args.execute)
    dry_run = not execute

    print("WARNING: This command writes controlled deterministic sample data only when --execute is provided.")
    print(f"mode={'execute' if execute else 'dry_run'}")

    url, key, missing = _resolve_credentials()
    if missing:
        print(f"Missing required credentials: {', '.join(missing)}")
        return 2

    table_counts = _table_counts_from_payload()
    print("target_tables_and_counts=")
    for table_name, row_count in table_counts.items():
        print(f"- {table_name}: {row_count}")

    client = _build_client(url, key)
    result = run_d1_controlled_seed(confirm_execute=execute, dry_run=dry_run, supabase_client=client)

    manifest = result.get("seed_manifest", {})
    execution_result = result.get("execution_result", {})
    print("manifest_summary=")
    print(f"- run_id: {manifest.get('run_id')}")
    print(f"- checksum: {manifest.get('checksum')}")
    print(f"- total_row_count: {manifest.get('total_row_count')}")
    print(f"- execution_confirmed: {result.get('execution_confirmed')}")
    print(f"- execution_status: {execution_result.get('execution_status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
