from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist4_archetype_recurrence_ecology import (
    build_ops_hist4_archetype_recurrence_ecology,
    load_ops_hist3_payload,
    load_ops_hist3_payloads_from_dir,
    render_ops_hist4_recurrence_markdown,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run OPS-HIST-4 archetype recurrence ecology observation")
    p.add_argument("--input-json", default="reports/ops_hist3_archetype_observation.json")
    p.add_argument("--input-dir", default="")
    p.add_argument("--json-output", default="reports/ops_hist4_recurrence_ecology.json")
    p.add_argument("--md-output", default="reports/ops_hist4_recurrence_ecology.md")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    payloads = []
    if args.input_dir:
        payloads = [p for p in load_ops_hist3_payloads_from_dir(args.input_dir) if p.get("schema_version") == "ops_hist3_v1"]
    out = build_ops_hist4_archetype_recurrence_ecology(payloads if payloads else load_ops_hist3_payload(args.input_json))
    Path(args.json_output).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist4_recurrence_markdown(out), encoding="utf-8")


if __name__ == "__main__":
    main()
