#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist5_temporal_continuity_regimes import (
    build_ops_hist5_temporal_continuity_regimes,
    load_ops_hist4_payload,
    load_ops_hist4_payloads_from_dir,
    render_ops_hist5_temporal_regime_markdown,
)


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-json", default="reports/ops_hist4_recurrence_ecology.json")
    p.add_argument("--input-dir", default="")
    p.add_argument("--json-output", default="reports/ops_hist5_temporal_regime_observation.json")
    p.add_argument("--md-output", default="reports/ops_hist5_temporal_regime_observation.md")
    return p.parse_args()


def main() -> int:
    args = _parse()
    payloads = []
    if args.input_dir:
        payloads = [p for p in load_ops_hist4_payloads_from_dir(args.input_dir) if p.get("schema_version") == "ops_hist4_v1"]
    if not payloads:
        p = load_ops_hist4_payload(args.input_json)
        if p.get("schema_version") != "ops_hist4_v1":
            raise ValueError("OPS-HIST-5 requires source_schema_version ops_hist4_v1 payload")
        payloads = [p]
    out = build_ops_hist5_temporal_continuity_regimes(payloads)
    Path(args.json_output).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist5_temporal_regime_markdown(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
