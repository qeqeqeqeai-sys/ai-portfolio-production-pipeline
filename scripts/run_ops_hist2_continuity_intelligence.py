from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist2_historical_continuity_intelligence import (
    build_ops_hist2_continuity_intelligence,
    load_ops_hist1_snapshots_for_hist2,
    render_ops_hist2_continuity_markdown,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Run OPS-HIST-2 historical continuity intelligence")
    p.add_argument("--input-dir", default="reports/ops_hist1_50_symbol_backfill")
    p.add_argument("--json-output", default="reports/ops_hist2_continuity_intelligence.json")
    p.add_argument("--md-output", default="reports/ops_hist2_continuity_intelligence.md")
    args = p.parse_args()

    review = build_ops_hist2_continuity_intelligence(load_ops_hist1_snapshots_for_hist2(args.input_dir))
    Path(args.json_output).write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist2_continuity_markdown(review), encoding="utf-8")
    print(json.dumps({"status": "ok", "schema_version": review["schema_version"], "snapshot_count": review["reviewed_snapshot_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
