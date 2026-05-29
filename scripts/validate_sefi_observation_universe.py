from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transmission_layers.expectation_failure.real_data.sefi_observation_universe import (
    build_sefi_observation_universe_rows,
    get_db_sefi_observation_universe,
    render_validation_report,
    validate_sefi_observation_universe_rows,
)

DEFAULT_REPORT_PATH = "reports/sefi_observation_universe_db_migration_readiness.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SEFI observation universe DB migration readiness.")
    parser.add_argument("--source", choices=("config", "db"), default="config")
    parser.add_argument("--write-report", default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()
    rows = get_db_sefi_observation_universe() if args.source == "db" else build_sefi_observation_universe_rows()
    validation = validate_sefi_observation_universe_rows(rows)
    report = render_validation_report(validation)
    path = Path(args.write_report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0 if validation.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
