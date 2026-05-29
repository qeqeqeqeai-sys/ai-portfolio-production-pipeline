#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_long.hist_intel1_historical_structural_findings import (  # noqa: E402
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    DEFAULT_SOURCE_PATHS,
    run_hist_intel1,
)

MAX_LOCAL_FACT_ROWS = 1000


def _read_local_facts(path: str | None) -> list[Mapping[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("--local-facts-json must point to a JSON list of bounded observation fact rows")
    return [row for row in payload[:MAX_LOCAL_FACT_ROWS] if isinstance(row, Mapping)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-INTEL-1 historical structural findings from local artifacts/facts only.")
    parser.add_argument("--source", action="append", dest="sources", help="Expected local source artifact path. Repeat to override defaults.")
    parser.add_argument("--local-facts-json", help="Optional bounded JSON list of local observation fact rows.")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    args = parser.parse_args()

    result = run_hist_intel1(
        source_paths=tuple(args.sources) if args.sources else DEFAULT_SOURCE_PATHS,
        observation_facts=_read_local_facts(args.local_facts_json),
        top_n=args.top_n,
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
    )
    print(f"HIST-INTEL-1 status={result['status']} json={args.json_report_path} markdown={args.markdown_report_path}")
    print(f"missing_sources={len(result['missing_sources'])} executive_summary_items={len(result['findings']['executive_summary'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
