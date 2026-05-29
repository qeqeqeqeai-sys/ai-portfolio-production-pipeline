#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_long.hist_intel2_taxonomy_weighted_intelligence import (  # noqa: E402
    DEFAULT_EXPANDED_FACTS_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    MAX_FACT_ROWS,
    run_hist_intel2,
)


def _read_local_facts(path: str | None) -> list[Mapping[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload[:MAX_FACT_ROWS] if isinstance(row, Mapping)]
    if isinstance(payload, Mapping) and isinstance(payload.get("expanded_facts"), list):
        return [row for row in payload["expanded_facts"][:MAX_FACT_ROWS] if isinstance(row, Mapping)]
    raise ValueError("--local-facts-json must point to a JSON list or an object with expanded_facts")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-INTEL-2 taxonomy-weighted intelligence from local facts only.")
    parser.add_argument("--local-facts-json", help="Optional bounded JSON list of local observation fact rows.")
    parser.add_argument("--expanded-facts-path", default=DEFAULT_EXPANDED_FACTS_PATH, help="Default local HIST-FACT-1 expanded facts path used when --local-facts-json is omitted.")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    args = parser.parse_args()

    supplied_facts = _read_local_facts(args.local_facts_json)
    default_path = None if supplied_facts else args.expanded_facts_path
    result = run_hist_intel2(
        observation_facts=supplied_facts,
        local_facts_path=default_path,
        top_n=args.top_n,
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
    )
    print(f"HIST-INTEL-2 status={result['status']} json={args.json_report_path} markdown={args.markdown_report_path}")
    print(f"tier_counts={dict(result['taxonomy_tier_counts'])} suppressed_operational_diagnostics={result['operational_diagnostic_rows_suppressed']} executive_summary_items={len(result['findings']['executive_summary'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
