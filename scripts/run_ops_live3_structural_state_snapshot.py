#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.live_ops.ops_live3_structural_state_snapshot import MAX_FACT_ROWS, run_ops_live3_snapshot

DEFAULT_REPORT_PATH = "reports/ops_live3_structural_state_snapshot.md"
MAX_LOCAL_JSON_BYTES = 2_000_000


def _read_bounded_fact_rows(path: str | None) -> tuple[list[Mapping[str, Any]], int]:
    if not path:
        return [], 0
    source = Path(path)
    if source.suffix.lower() in {".md", ".markdown"}:
        raise ValueError("OPS-LIVE-3 does not parse markdown reports as source input")
    if source.stat().st_size > MAX_LOCAL_JSON_BYTES:
        raise ValueError("local facts JSON exceeds OPS-LIVE-3 bounded input size")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        for key in ("fact_rows", "facts", "observation_facts", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                payload = value
                break
    if not isinstance(payload, list):
        raise ValueError("local facts input must be a JSON list or object containing fact rows")
    raw_count = len(payload)
    return [row for row in payload[:MAX_FACT_ROWS] if isinstance(row, Mapping)], raw_count


def _build_env_supabase_client() -> Any:
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and a Supabase key env var are required for --use-supabase")
    return create_client(url, key)


def main() -> int:
    parser = argparse.ArgumentParser(description="OPS-LIVE-3 live structural state snapshot synthesis.")
    parser.add_argument("--local-facts-json", help="Optional bounded JSON list/object of local observation fact rows; capped at 1000 rows.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--use-supabase", action="store_true", help="Read sefi_observation_facts using an env-created Supabase client.")
    args = parser.parse_args()

    fact_rows, raw_count = _read_bounded_fact_rows(args.local_facts_json)
    client = _build_env_supabase_client() if args.use_supabase else None
    result = run_ops_live3_snapshot(client=client, fact_rows=fact_rows, limit=args.limit)
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(result["report"], encoding="utf-8")
    summary = result["summary"]
    print(f"OPS-LIVE-3 report written: {args.report_path}")
    print(
        f"source_behavior={result['snapshot']['source_behavior']} raw_local_rows={raw_count} "
        f"inspected_fact_count={result['snapshot']['inspected_fact_count']} "
        f"snapshot_status={summary['snapshot_status']} live_health_class={summary['live_health_class']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
