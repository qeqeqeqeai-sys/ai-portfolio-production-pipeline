#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_read_model.observation_query import build_observation_intelligence_report

DEFAULT_REPORT_PATH = "reports/obs_query1_observation_fact_intelligence.md"
MAX_LOCAL_ROWS = 1000


def _read_bounded_rows(path: str | None) -> list[Mapping[str, Any]]:
    if not path:
        return []
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("local fact rows must be a JSON list")
    return [row for row in payload[:MAX_LOCAL_ROWS] if isinstance(row, Mapping)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build OBS-QUERY-1 intelligence from sefi_observation_facts or bounded local rows.")
    parser.add_argument("--local-facts-json", help="Optional bounded JSON list of observation fact rows for local dry-run.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    fact_rows = _read_bounded_rows(args.local_facts_json)
    result = build_observation_intelligence_report(fact_rows=fact_rows, report_path=args.report_path, limit=args.limit)
    summary = result["summary"]
    print(f"OBS-QUERY-1 report written: {args.report_path}")
    print(f"source_behavior={result['source_behavior']} rows={summary['row_count']} insufficient_data={summary['insufficient_data_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
