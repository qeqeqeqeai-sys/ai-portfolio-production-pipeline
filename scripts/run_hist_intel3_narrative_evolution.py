#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]

from transmission_layers.history_long.hist_intel3_narrative_evolution import (  # noqa: E402
    DEFAULT_EXPANDED_FACTS_PATH,
    DEFAULT_INTEL2_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    MAX_FACT_ROWS,
    run_hist_intel3,
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
    parser = argparse.ArgumentParser(description="Build HIST-INTEL-3 narrative evolution from local historical facts only.")
    parser.add_argument("--local-facts-json", help="Optional bounded JSON list of local observation fact rows.")
    parser.add_argument("--expanded-facts-path", default=DEFAULT_EXPANDED_FACTS_PATH)
    parser.add_argument("--hist-intel2-path", default=DEFAULT_INTEL2_PATH)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    args = parser.parse_args()

    supplied_facts = _read_local_facts(args.local_facts_json)
    default_path = None if supplied_facts else args.expanded_facts_path
    result = run_hist_intel3(
        observation_facts=supplied_facts,
        local_facts_path=default_path,
        intel2_path=args.hist_intel2_path,
        top_n=args.top_n,
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
    )
    findings = result["findings"]
    print(f"HIST-INTEL-3 status={result['status']} json={args.json_report_path} markdown={args.markdown_report_path}")
    diagnostics = result["transition_diagnostics"]
    print(
        "narrative_types="
        f"{result['narrative_types_generated']} "
        f"evolutions={len(findings['major_narrative_evolutions'])} "
        f"transitions={len(findings['regime_transition_candidates'])} "
        f"suppressed_same_state={diagnostics['rejected_same_state_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
