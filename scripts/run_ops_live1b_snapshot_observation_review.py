import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_live1b_snapshot_observation_review import (
    build_ops_live1b_snapshot_observation_review,
    load_ops_live1b_snapshots,
    render_ops_live1b_observation_review_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OPS-LIVE-1B snapshot observation review")
    parser.add_argument("--input-dir", default="reports/ops_live1b_runs")
    parser.add_argument("--max-snapshots", type=int, default=30)
    parser.add_argument("--json-output", default="reports/ops_live1b_snapshot_observation_review.json")
    parser.add_argument("--md-output", default="reports/ops_live1b_snapshot_observation_review.md")
    args = parser.parse_args()

    snapshots = load_ops_live1b_snapshots(input_dir=args.input_dir, max_snapshots=args.max_snapshots)
    review = build_ops_live1b_snapshot_observation_review(snapshots)
    markdown = render_ops_live1b_observation_review_markdown(review)

    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(markdown + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
