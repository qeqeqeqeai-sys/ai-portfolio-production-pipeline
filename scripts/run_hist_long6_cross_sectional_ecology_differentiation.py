from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_long6_cross_sectional_ecology_differentiation import (
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_HIST_LONG4_SOURCE_PATH,
    DEFAULT_HIST_LONG5B_SOURCE_PATH,
    DEFAULT_REPORT_PATH,
    write_hist_long6,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-LONG-6 cross-sectional ecology differentiation from local artifacts only.")
    parser.add_argument("--hist-long4-source", default=DEFAULT_HIST_LONG4_SOURCE_PATH)
    parser.add_argument("--hist-long5b-source", default=DEFAULT_HIST_LONG5B_SOURCE_PATH)
    parser.add_argument("--artifact-path", default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()
    artifact = write_hist_long6(
        hist_long4_source_path=args.hist_long4_source,
        hist_long5b_source_path=args.hist_long5b_source,
        artifact_path=args.artifact_path,
        report_path=args.report_path,
    )
    print(json.dumps({"status": artifact["status"], "artifact_path": args.artifact_path, "report_path": args.report_path}, sort_keys=True))
    return 0 if artifact["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
