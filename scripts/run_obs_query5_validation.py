#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_read_model.obs_query_validation import (  # noqa: E402
    run_obs_query5_validation,
    write_obs_query5_validation_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="OBS-QUERY-5 deterministic query quality validation over controlled DB-2 fact fixtures.")
    parser.add_argument("--output-json", help="Write deterministic JSON validation scorecard.")
    parser.add_argument("--output-md", help="Write deterministic Markdown validation summary.")
    args = parser.parse_args()

    result = run_obs_query5_validation()
    paths = write_obs_query5_validation_outputs(result, output_json=args.output_json, output_md=args.output_md)
    print(json.dumps({"status": result["overall_status"], "tests_executed": result["tests_executed"], "tests_passed": result["tests_passed"], "tests_failed": result["tests_failed"], **paths}, sort_keys=True))
    return 0 if result["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
