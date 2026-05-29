#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.live_ops.ops_live2_observation_fact_accumulation import (
    MAX_LOCAL_INPUT_ROWS,
    build_ops_live2_report,
    run_ops_live2_accumulation,
)

DEFAULT_REPORT_PATH = "reports/ops_live2_observation_fact_accumulation.md"


def _synthetic_payload() -> list[dict[str, Any]]:
    return [
        {
            "observed_at": "2026-05-29T00:00:00Z",
            "source_phase": "OPS-LIVE-1B",
            "source_run_id": "local-synthetic-run",
            "entity_type": "phase",
            "entity_id": "OPS-LIVE-1B",
            "metric_name": "live_ingestion_completeness",
            "metric_value": 1.0,
            "payload_jsonb": {"source": "runner_synthetic_payload"},
        },
        {
            "observed_at": "2026-05-29T00:00:00Z",
            "source_phase": "OPS-LIVE-1B",
            "source_run_id": "local-synthetic-run",
            "entity_type": "symbol",
            "entity_id": "aapl",
            "metric_name": "live_symbol_weakness",
            "metric_value": 0.0,
            "window_days": 1,
            "payload_jsonb": {"source": "runner_synthetic_payload"},
        },
    ]


def _read_bounded_observations(path: str | None) -> tuple[list[Mapping[str, Any]], int]:
    if not path:
        payload = _synthetic_payload()
        return payload, len(payload)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        for key in ("live_observations", "observations", "ops_live2_observations"):
            value = payload.get(key)
            if isinstance(value, list):
                payload = value
                break
    if not isinstance(payload, list):
        raise ValueError("local input must be a JSON list or an object containing live_observations/observations")
    raw_count = len(payload)
    return [row for row in payload[:MAX_LOCAL_INPUT_ROWS] if isinstance(row, Mapping)], raw_count


def _build_env_supabase_client() -> Any:
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and a Supabase key env var are required for --enable-emission --write-facts")
    return create_client(url, key)


def main() -> int:
    parser = argparse.ArgumentParser(description="OPS-LIVE-2 controlled live observation fact accumulation.")
    parser.add_argument("--input-json", help="Optional local JSON list/object of bounded live observations; capped at 1000 rows.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--enable-emission", action="store_true", help="Enable DB-2 fact-row construction gate.")
    parser.add_argument("--write-facts", action="store_true", help="Write facts through an env-created Supabase client; requires --enable-emission.")
    args = parser.parse_args()

    if args.write_facts and not args.enable_emission:
        raise ValueError("--write-facts requires --enable-emission")

    observations, raw_observation_count = _read_bounded_observations(args.input_json)
    client = _build_env_supabase_client() if args.enable_emission and args.write_facts else None
    result = run_ops_live2_accumulation(
        live_observations=observations,
        client=client,
        enabled=args.enable_emission,
        dry_run=not args.write_facts,
        input_source=args.input_json or "local_synthetic_payload",
        raw_observation_count=raw_observation_count,
    )
    report = build_ops_live2_report(result)
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"OPS-LIVE-2 report written: {args.report_path}")
    print(
        "normalized_observations="
        f"{len(result['observations'])} fact_rows={len(result['fact_rows'])} "
        f"dry_run={result['fact_emission']['dry_run']} inserted_rows={result['fact_emission']['inserted_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
