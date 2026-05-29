from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_long.hist_fact1_observation_fact_expansion import (
    DEFAULT_EXPANDED_FACTS_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    DEFAULT_MAX_FACTS,
    run_hist_fact1_expansion,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-FACT-1 historical observation fact expansion from local artifacts only.")
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    parser.add_argument("--expanded-facts-path", default=DEFAULT_EXPANDED_FACTS_PATH)
    parser.add_argument("--max-facts", type=int, default=DEFAULT_MAX_FACTS)
    args = parser.parse_args()
    report = run_hist_fact1_expansion(
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
        expanded_facts_path=args.expanded_facts_path,
        max_facts=args.max_facts,
    )
    print(
        "HIST-FACT-1 "
        f"status={report['status']} "
        f"original_fact_count={report['original_fact_count']} "
        f"expanded_fact_count={report['expanded_fact_count']} "
        f"net_new_fact_count={report['net_new_fact_count']}"
    )


if __name__ == "__main__":
    main()
