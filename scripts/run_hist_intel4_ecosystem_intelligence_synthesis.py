#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]

from transmission_layers.history_long.hist_intel4_ecosystem_intelligence_synthesis import (  # noqa: E402
    DEFAULT_FACT1_PATH,
    DEFAULT_FACT2_PATH,
    DEFAULT_INTEL2_PATH,
    DEFAULT_INTEL3_PATH,
    DEFAULT_JSON_REPORT_PATH,
    DEFAULT_MARKDOWN_REPORT_PATH,
    run_hist_intel4,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-INTEL-4 ecosystem synthesis from local historical artifacts only.")
    parser.add_argument("--fact1-path", default=DEFAULT_FACT1_PATH)
    parser.add_argument("--fact2-path", default=DEFAULT_FACT2_PATH)
    parser.add_argument("--intel2-path", default=DEFAULT_INTEL2_PATH)
    parser.add_argument("--intel3-path", default=DEFAULT_INTEL3_PATH)
    parser.add_argument("--json-report-path", default=DEFAULT_JSON_REPORT_PATH)
    parser.add_argument("--markdown-report-path", default=DEFAULT_MARKDOWN_REPORT_PATH)
    args = parser.parse_args()

    report = run_hist_intel4(
        fact1_path=args.fact1_path,
        fact2_path=args.fact2_path,
        intel2_path=args.intel2_path,
        intel3_path=args.intel3_path,
        json_report_path=args.json_report_path,
        markdown_report_path=args.markdown_report_path,
    )
    findings = report["findings"]
    print(f"HIST-INTEL-4 status={report['status']} json={args.json_report_path} markdown={args.markdown_report_path}")
    print(
        "identity="
        f"{findings['structural_identity']['identity']} "
        f"stability={findings['stability_assessment']['classification']} "
        f"transition={findings['transition_readiness_assessment']['classification']} "
        f"narrative={findings['narrative_continuity_assessment']['classification']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
