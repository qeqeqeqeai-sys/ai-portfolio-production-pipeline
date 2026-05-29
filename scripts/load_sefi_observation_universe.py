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
    upsert_sefi_observation_universe,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage SEFI observation universe rows into public.sefi_observation_universe.")
    parser.add_argument("--execute", action="store_true", help="Perform Supabase upsert. Default is validation-only dry run.")
    args = parser.parse_args()
    rows = build_sefi_observation_universe_rows()
    result = upsert_sefi_observation_universe(rows, execute=args.execute)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"dry_run", "submitted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
