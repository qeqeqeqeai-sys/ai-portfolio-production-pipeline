from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_density4_findings_review import write_hist_density4_findings_review


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HIST-DENSITY-4 local artifact findings review")
    parser.add_argument("--source-root", default="reports/hist_density3_curated_241")
    parser.add_argument("--report-path", default="reports/hist_density4_241_symbol_findings_review.md")
    parser.add_argument("--artifact-path", default="artifacts/hist_density4_241_symbol_findings_review.json")
    args = parser.parse_args()
    artifact = write_hist_density4_findings_review(source_root=args.source_root, report_path=args.report_path, artifact_path=args.artifact_path)
    print(json.dumps({"status": artifact["status"], "source_mode": artifact["source_mode"], "report_path": args.report_path, "artifact_path": args.artifact_path}, sort_keys=True))


if __name__ == "__main__":
    main()
