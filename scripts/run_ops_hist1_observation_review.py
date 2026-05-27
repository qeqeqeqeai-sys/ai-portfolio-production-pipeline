import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import (
    build_ops_hist1_observation_review,
    load_ops_hist1_snapshots,
    render_ops_hist1_observation_review_markdown,
)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run OPS-HIST-1 historical observation review")
    p.add_argument("--input-dir", default="reports/ops_hist1_50_symbol_backfill")
    p.add_argument("--json-output", default="reports/ops_hist1_observation_review.json")
    p.add_argument("--md-output", default="reports/ops_hist1_observation_review.md")
    args = p.parse_args()
    review = build_ops_hist1_observation_review(load_ops_hist1_snapshots(args.input_dir))
    Path(args.json_output).write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist1_observation_review_markdown(review), encoding="utf-8")
    print("ok")
