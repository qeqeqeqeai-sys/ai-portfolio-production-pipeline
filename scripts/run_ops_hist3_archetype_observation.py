from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist3_historical_continuity_archetypes import (
    build_ops_hist3_historical_continuity_archetypes,
    load_ops_hist2_continuity_payload,
    render_ops_hist3_archetype_markdown,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Run OPS-HIST-3 historical continuity archetype observation")
    p.add_argument("--input-json", default="reports/ops_hist2_continuity_intelligence.json")
    p.add_argument("--json-output", default="reports/ops_hist3_archetype_observation.json")
    p.add_argument("--md-output", default="reports/ops_hist3_archetype_observation.md")
    args = p.parse_args()

    payload = load_ops_hist2_continuity_payload(args.input_json)
    out = build_ops_hist3_historical_continuity_archetypes(payload)
    Path(args.json_output).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.md_output).write_text(render_ops_hist3_archetype_markdown(out), encoding="utf-8")


if __name__ == "__main__":
    main()
