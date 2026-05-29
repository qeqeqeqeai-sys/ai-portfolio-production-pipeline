#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.history_read_model.analyst_consumption_views import (  # noqa: E402
    DEFAULT_LIMIT,
    VIEW_TYPES,
    build_consumption_view,
    write_consumption_view_outputs,
)

MAX_LOCAL_ROWS = 1000


def _build_env_supabase_client() -> Any | None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    from supabase import create_client

    return create_client(url, key)


def _read_bounded_rows(path: str | None) -> list[Mapping[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("local fact rows must be a JSON list")
    return [row for row in payload[:MAX_LOCAL_ROWS] if isinstance(row, Mapping)]


def main() -> int:
    parser = argparse.ArgumentParser(description="OBS-QUERY-4 deterministic analyst consumption views over DB-2 retrieval outputs.")
    parser.add_argument("--view-type", required=True, choices=VIEW_TYPES)
    parser.add_argument("--symbol", help="Symbol/entity filter when entity_type=symbol.")
    parser.add_argument("--taxonomy", help="Taxonomy/category/fact-type filter mapped to metric_name.")
    parser.add_argument("--snapshot-date", help="Observation snapshot date (YYYY-MM-DD); matched to loaded_at/created_at date.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Bounded per-section item limit; hard maximum is enforced by the retrieval module.")
    parser.add_argument("--output-json", help="Write deterministic JSON output.")
    parser.add_argument("--output-md", help="Write deterministic Markdown analyst view output.")
    parser.add_argument("--local-facts-json", help=argparse.SUPPRESS)
    args = parser.parse_args()

    fact_rows = _read_bounded_rows(args.local_facts_json)
    client = None if fact_rows else _build_env_supabase_client()
    result = build_consumption_view(
        view_type=args.view_type,
        client=client,
        fact_rows=fact_rows,
        symbol=args.symbol,
        taxonomy=args.taxonomy,
        snapshot_date=args.snapshot_date,
        limit=args.limit,
    )
    if client is None and not fact_rows:
        result["runtime_warnings"] = [
            "SUPABASE_URL and Supabase key env var were not both present; emitted deterministic empty OBS-QUERY-4 output without external provider calls."
        ]
    paths = write_consumption_view_outputs(result, output_json=args.output_json, output_md=args.output_md)
    print(json.dumps({"status": "ok", "view_type": result["view_type"], "section_count": len(result["sections"]), "effective_limit": result["effective_limit"], **paths}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
