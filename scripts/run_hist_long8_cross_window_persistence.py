from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_long.hist_long8_cross_window_persistence import (  # noqa: E402
    DEFAULT_HIST_LONG4_SOURCE_PATH,
    DEFAULT_REPORT_PATH,
    run_hist_long8,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-LONG-8 cross-window persistence analysis from local/read-model outputs only.")
    parser.add_argument("--hist-long4-source", default=DEFAULT_HIST_LONG4_SOURCE_PATH)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--enable-fact-emission", action="store_true", help="Build and emit DB-2 observation facts; dry-run remains default unless --write-facts is also set.")
    parser.add_argument("--write-facts", action="store_true", help="Persist facts through an injected client path; unavailable in this local runner.")
    args = parser.parse_args()
    result = run_hist_long8(
        hist_long4_source_path=args.hist_long4_source,
        report_path=args.report_path,
        enabled=args.enable_fact_emission,
        dry_run=not args.write_facts,
    )
    analysis = result["analysis"]
    print(json.dumps({
        "status": analysis["status"],
        "completed_windows": analysis["completed_windows"],
        "overall_stability_class": analysis["overall_stability_class"],
        "fact_rows": len(result["fact_rows"]),
        "dry_run": result["fact_emission"]["dry_run"],
        "report_path": args.report_path,
    }, sort_keys=True))
    return 0 if analysis["status"] in {"ok", "blocked"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
