from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist7_regime_ecology_saturation import (
    build_ops_hist7_regime_ecology_saturation,
    load_ops_hist6_payload,
    load_ops_hist6_payloads_from_dir,
    render_ops_hist7_regime_ecology_saturation_markdown,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run OPS-HIST-7 regime ecology saturation observation")
    p.add_argument("--input-json", default="reports/ops_hist6_regime_morphology_observation.json")
    p.add_argument("--input-dir", default="")
    p.add_argument("--json-output", default="reports/ops_hist7_regime_ecology_saturation.json")
    p.add_argument("--md-output", default="reports/ops_hist7_regime_ecology_saturation.md")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    payloads = []
    if args.input_dir:
        payloads = load_ops_hist6_payloads_from_dir(args.input_dir)
    if not payloads:
        payloads = [load_ops_hist6_payload(args.input_json)]
    out = build_ops_hist7_regime_ecology_saturation(payloads)
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist7_regime_ecology_saturation_markdown(out), encoding="utf-8")


if __name__ == "__main__":
    main()
