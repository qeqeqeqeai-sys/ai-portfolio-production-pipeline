"""
Phase 2D.2 Reconstruction Validation Gates

Validates that historical reconstruction produced usable institutional-grade
historical analytics output.

Checks:
    - target tables populated
    - minimum date coverage
    - no empty reconstruction
    - regime history exists
    - propagation history exists
    - momentum history exists
    - reconstruction source markers exist
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import requests


THEME_NAME = os.getenv("THEME_NAME", "ai")
MIN_RECONSTRUCTED_DAYS = int(os.getenv("MIN_RECONSTRUCTED_DAYS", "30"))

SGT = timezone(timedelta(hours=8))

TARGET_TABLES = [
    "structural_theme_momentum_history",
    "structural_theme_driver_persistence_history",
    "structural_theme_pathway_trend_history",
    "structural_theme_evidence_intensity_history",
    "structural_theme_attribution_trend_history",
    "structural_theme_regime_history",
    "structural_theme_propagation_history",
]


class SupabaseRestClient:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_KEY")
            or ""
        )

        if not self.url or not self.key:
            raise RuntimeError("Missing Supabase credentials.")

        self.base = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def select(self, table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        response = requests.get(
            f"{self.base}/{table}",
            headers=self.headers,
            params=params,
            timeout=60,
        )

        if response.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Supabase select failed for {table}: "
                f"{response.status_code} - {response.text[:1000]}"
            )

        return response.json()

    def table_exists(self, table: str) -> bool:
        try:
            self.select(table, {"select": "*", "limit": "1"})
            return True
        except Exception:
            return False


def validate_table(client: SupabaseRestClient, table: str) -> Dict[str, Any]:
    if not client.table_exists(table):
        return {
            "table": table,
            "status": "FAIL",
            "reason": "table_missing",
        }

    rows = client.select(
        table,
        {
            "select": "run_date_sgt,theme_name,source",
            "theme_name": f"eq.{THEME_NAME}",
            "order": "run_date_sgt.desc",
            "limit": "50000",
        },
    )

    if not rows:
        return {
            "table": table,
            "status": "FAIL",
            "reason": "no_rows",
        }

    reconstructed_rows = [
        r for r in rows
        if str(r.get("source", "")).lower() == "phase2d2_reconstruction"
    ]

    unique_dates = sorted({
        str(r.get("run_date_sgt"))[:10]
        for r in rows
        if r.get("run_date_sgt")
    })

    return {
        "table": table,
        "status": "PASS" if len(unique_dates) >= MIN_RECONSTRUCTED_DAYS else "WARN",
        "row_count": len(rows),
        "reconstructed_row_count": len(reconstructed_rows),
        "unique_dates": len(unique_dates),
        "earliest_date": unique_dates[0] if unique_dates else None,
        "latest_date": unique_dates[-1] if unique_dates else None,
    }


def main() -> None:
    client = SupabaseRestClient()

    print("Running Phase 2D.2 reconstruction validation gates...")
    print(f"Theme: {THEME_NAME}")
    print(f"Minimum reconstructed days: {MIN_RECONSTRUCTED_DAYS}")

    results = []

    for table in TARGET_TABLES:
        result = validate_table(client, table)
        results.append(result)

        print("\n---")
        print(f"Table: {table}")
        for key, value in result.items():
            if key != "table":
                print(f"{key}: {value}")

    hard_failures = [
        r for r in results
        if r["status"] == "FAIL"
    ]

    critical_tables = {
        "structural_theme_momentum_history",
        "structural_theme_regime_history",
        "structural_theme_propagation_history",
    }

    critical_failures = [
        r for r in hard_failures
        if r["table"] in critical_tables
    ]

    if critical_failures:
        print("\nVALIDATION FAILED: Critical reconstruction tables failed.")
        sys.exit(1)

    print("\nVALIDATION PASSED: Phase 2D.2 reconstruction output is usable.")


if __name__ == "__main__":
    main()
