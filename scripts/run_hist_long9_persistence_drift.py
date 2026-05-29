from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_long.hist_long9_persistence_drift import DEFAULT_REPORT_PATH, run_hist_long9  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HIST-LONG-9 persistence drift analysis from observation facts only.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--enable-fact-emission", action="store_true", help="Build and emit DB-2 observation facts; dry-run remains default unless --write-facts is also set.")
    parser.add_argument("--write-facts", action="store_true", help="Persist facts through an injected client path; unavailable in this local runner.")
    args = parser.parse_args()
    result = run_hist_long9(report_path=args.report_path, enabled=args.enable_fact_emission, dry_run=not args.write_facts)
    analysis = result["analysis"]
    print(json.dumps({
        "status": analysis["status"],
        "snapshot_count": analysis["snapshot_count"],
        "overall_drift_class": analysis["overall_drift_class"],
        "emerging_fragility_class": analysis["emerging_fragility_assessment"]["emerging_fragility_class"],
        "fact_rows": len(result["fact_rows"]),
        "dry_run": result["fact_emission"]["dry_run"],
        "report_path": args.report_path,
    }, sort_keys=True))
    return 0 if analysis["status"] in {"ok", "blocked"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
