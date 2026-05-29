#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_long.hist_intel1b_fact_native_historical_findings import (  # noqa: E402
    DEFAULT_COMPACT_SOURCE_PATHS,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    MAX_LOCAL_FACT_ROWS,
    run_hist_intel1b,
)


def _read_local_facts(path: str | None) -> list[Mapping[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("--local-facts-json must point to a JSON list of bounded observation fact rows")
    return [row for row in payload[:MAX_LOCAL_FACT_ROWS] if isinstance(row, Mapping)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-INTEL-1B fact-native historical findings from local facts only.")
    parser.add_argument("--local-facts-json", help="Optional bounded JSON list of local observation fact rows.")
    parser.add_argument("--compact-source", action="append", dest="compact_sources", help="Optional compact local fallback artifact path. Repeat to override defaults.")
    parser.add_argument("--use-default-compact-sources", action="store_true", help="Use known compact HIST artifacts as local fallback sources.")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    args = parser.parse_args()

    compact_sources = tuple(args.compact_sources or ())
    if args.use_default_compact_sources and not compact_sources:
        compact_sources = DEFAULT_COMPACT_SOURCE_PATHS
    result = run_hist_intel1b(
        observation_facts=_read_local_facts(args.local_facts_json),
        compact_source_paths=compact_sources,
        top_n=args.top_n,
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
    )
    print(f"HIST-INTEL-1B status={result['status']} json={args.json_report_path} markdown={args.markdown_report_path}")
    print(f"ecosystem_rows={result['fact_native_ecosystem_rows']} suppressed_pipeline_diagnostics={result['pipeline_diagnostic_rows_suppressed']} executive_summary_items={len(result['findings']['executive_summary'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
