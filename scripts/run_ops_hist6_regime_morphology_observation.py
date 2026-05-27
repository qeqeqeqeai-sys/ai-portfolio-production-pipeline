from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist6_regime_morphology_observation import (
    build_ops_hist6_regime_morphology_observation,
    load_ops_hist5_payload,
    load_ops_hist5_payloads_from_dir,
    render_ops_hist6_regime_morphology_markdown,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run OPS-HIST-6 regime morphology observation")
    p.add_argument("--input-json", default="reports/ops_hist5_temporal_regime_observation.json")
    p.add_argument("--input-dir", default="")
    p.add_argument("--json-output", default="reports/ops_hist6_regime_morphology_observation.json")
    p.add_argument("--md-output", default="reports/ops_hist6_regime_morphology_observation.md")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    payloads = []
    if args.input_dir:
        p = Path(args.input_dir)
        if p.exists() and p.is_dir():
            payloads = load_ops_hist5_payloads_from_dir(args.input_dir)
            payloads = [x for x in payloads if x and x.get("schema_version") == "ops_hist5_v1"]
    if not payloads:
        payloads = [load_ops_hist5_payload(args.input_json)]
    out = build_ops_hist6_regime_morphology_observation(payloads)
    Path(args.json_output).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist6_regime_morphology_markdown(out), encoding="utf-8")
    print(f"wrote {args.json_output} and {args.md_output}")


if __name__ == "__main__":
    main()
