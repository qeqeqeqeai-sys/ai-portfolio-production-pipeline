from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]

from transmission_layers.history_long.hist_fact2_regime_evidence_expansion import (
    DEFAULT_EXPANDED_EVIDENCE_PATH,
    DEFAULT_FACT1_PATH,
    DEFAULT_INTEL2_PATH,
    DEFAULT_INTEL3_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    DEFAULT_MAX_FACTS,
    run_hist_fact2_expansion,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-FACT-2 historical regime evidence expansion from local artifacts only.")
    parser.add_argument("--fact1-path", default=DEFAULT_FACT1_PATH)
    parser.add_argument("--intel2-path", default=DEFAULT_INTEL2_PATH)
    parser.add_argument("--intel3-path", default=DEFAULT_INTEL3_PATH)
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    parser.add_argument("--expanded-evidence-path", default=DEFAULT_EXPANDED_EVIDENCE_PATH)
    parser.add_argument("--max-facts", type=int, default=DEFAULT_MAX_FACTS)
    args = parser.parse_args()
    report = run_hist_fact2_expansion(
        fact1_path=args.fact1_path,
        intel2_path=args.intel2_path,
        intel3_path=args.intel3_path,
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
        expanded_evidence_path=args.expanded_evidence_path,
        max_facts=args.max_facts,
    )
    print(
        "HIST-FACT-2 "
        f"status={report['status']} "
        f"source_fact_count={report['source_fact_count']} "
        f"expanded_fact_count={report['expanded_fact_count']} "
        f"net_new_fact_count={report['net_new_fact_count']} "
        f"transition_relevant_fact_count={report['transition_relevant_fact_count']}"
    )


if __name__ == "__main__":
    main()
