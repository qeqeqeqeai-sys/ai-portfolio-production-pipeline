#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from collections import OrderedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transmission_layers.history_read_model.loader import DEFAULT_ARTIFACT_PATHS, build_read_model_rows, load_rows_to_supabase


def _client_from_env():
    from supabase import create_client  # type: ignore

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/load DB-1 SEFI history Supabase read-model rows from local artifacts only.")
    parser.add_argument("--artifact-path", action="append", dest="artifact_paths", help="Local completed SEFI/HIST artifact path. May be repeated.")
    parser.add_argument("--run-id", default=None, help="Optional deterministic run-id seed; artifact-specific run IDs remain unique.")
    parser.add_argument("--execute", action="store_true", help="Append rows to Supabase using env credentials; default is deterministic dry-run summary only.")
    args = parser.parse_args()

    paths = args.artifact_paths or list(DEFAULT_ARTIFACT_PATHS)
    rows = build_read_model_rows(paths, run_id=args.run_id)
    counts = OrderedDict((table, len(table_rows)) for table, table_rows in rows.items())
    if args.execute:
        load_rows_to_supabase(_client_from_env(), rows)
        mode = "supabase_append"
    else:
        mode = "dry_run_no_supabase_write"
    print(json.dumps({"status": "ok", "mode": mode, "tables": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
