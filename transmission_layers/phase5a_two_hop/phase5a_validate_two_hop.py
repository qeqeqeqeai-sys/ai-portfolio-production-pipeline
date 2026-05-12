"""Phase 5A validation hooks for controlled two-hop propagation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import requests

SGT = timezone(timedelta(hours=8))


def today_sgt() -> str:
    return datetime.now(SGT).date().isoformat()


class SupabaseRestClient:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
        if not self.url or not self.key:
            raise RuntimeError("Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY")
        self.base = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def get(self, table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base}/{table}", headers=self.headers, params=params, timeout=60)
        if r.status_code >= 300:
            raise RuntimeError(f"GET {table} failed {r.status_code}: {r.text[:1000]}")
        return r.json()


def main() -> None:
    run_date = os.getenv("RUN_DATE_SGT", today_sgt())
    theme_name = os.getenv("THEME_NAME", "ai")
    min_rows = int(os.getenv("MIN_TWO_HOP_ROWS", "1"))
    client = SupabaseRestClient()

    rows = client.get(
        "structural_theme_graph_two_hop_propagation",
        {
            "run_date_sgt": f"eq.{run_date}",
            "theme_name": f"eq.{theme_name}",
            "select": "source_node_id,intermediate_node_id,target_node_id,path_hash,two_hop_path_score,two_hop_confidence,two_hop_transmission_potential",
            "limit": "5000",
        },
    )

    failures: List[str] = []
    warnings: List[str] = []

    if len(rows) < min_rows:
        failures.append(f"Expected at least {min_rows} two-hop rows, found {len(rows)}")

    seen = set()
    for r in rows:
        nodes = [r.get("source_node_id"), r.get("intermediate_node_id"), r.get("target_node_id")]
        if len(set(nodes)) != 3:
            failures.append(f"Cycle or repeated node detected: {nodes}")
        path_hash = r.get("path_hash")
        if path_hash in seen:
            failures.append(f"Duplicate path_hash detected: {path_hash}")
        seen.add(path_hash)
        for field in ["two_hop_path_score", "two_hop_confidence", "two_hop_transmission_potential"]:
            val = r.get(field)
            if val is None:
                warnings.append(f"Missing {field} for path {path_hash}")
                continue
            f = float(val)
            if not 0 <= f <= 1:
                failures.append(f"{field} out of range for path {path_hash}: {f}")

    result = {
        "status": "failed" if failures else "passed",
        "run_date_sgt": run_date,
        "theme_name": theme_name,
        "rows_checked": len(rows),
        "failures": failures,
        "warnings": warnings[:50],
    }
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
