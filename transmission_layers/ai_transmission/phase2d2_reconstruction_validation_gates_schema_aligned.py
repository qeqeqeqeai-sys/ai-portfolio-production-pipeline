"""
Phase 2D.2 Reconstruction Validation Gates

Schema-aligned validation gates for the user's actual Phase 2D tables.

Validated tables:
    - structural_theme_momentum_history
    - structural_theme_regime_history
    - structural_theme_propagation_history
    - structural_theme_evidence_intensity_history

Important:
    This version does NOT check for non-existent columns such as "source".
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests


THEME_NAME = os.getenv("THEME_NAME", "ai")
MIN_RECONSTRUCTED_DAYS = int(os.getenv("MIN_RECONSTRUCTED_DAYS", "30"))

SGT = timezone(timedelta(hours=8))


TARGET_TABLES = {
    "structural_theme_momentum_history": {
        "required_columns": [
            "run_date_sgt",
            "theme_name",
            "entity",
            "theme_score",
            "momentum_7d",
            "momentum_30d",
            "acceleration_7d",
            "acceleration_30d",
            "momentum_persistence_days",
            "structural_momentum_score",
            "momentum_regime",
        ],
        "critical_metrics": [
            "structural_momentum_score",
            "momentum_regime",
        ],
    },
    "structural_theme_regime_history": {
        "required_columns": [
            "run_date_sgt",
            "theme_name",
            "entity",
            "previous_regime",
            "current_regime",
            "regime_changed",
            "regime_duration_days",
            "transition_type",
        ],
        "critical_metrics": [
            "current_regime",
            "transition_type",
        ],
    },
    "structural_theme_propagation_history": {
        "required_columns": [
            "run_date_sgt",
            "theme_name",
            "source_entity",
            "target_entity",
            "pathway_name",
            "propagation_score",
            "previous_score",
            "score_change",
            "momentum_7d",
            "momentum_30d",
            "acceleration_7d",
            "acceleration_30d",
            "evidence_intensity",
            "attribution_strength",
            "pathway_stability_score",
            "regime",
        ],
        "critical_metrics": [
            "propagation_score",
            "regime",
        ],
    },
    "structural_theme_evidence_intensity_history": {
        "required_columns": [
            "run_date_sgt",
            "theme_name",
            "entity",
            "pathway_name",
            "evidence_count",
            "high_confidence_evidence_count",
            "avg_evidence_strength",
            "rolling_evidence_7d",
            "rolling_evidence_30d",
            "evidence_spike_score",
            "evidence_regime",
        ],
        "critical_metrics": [
            "avg_evidence_strength",
            "evidence_regime",
        ],
    },
}


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

        if response.status_code == 204 or not response.text:
            return []

        return response.json()

    def table_exists(self, table: str) -> bool:
        try:
            self.select(table, {"select": "*", "limit": "1"})
            return True
        except Exception:
            return False


def validate_table(client: SupabaseRestClient, table: str, config: Dict[str, Any]) -> Dict[str, Any]:
    if not client.table_exists(table):
        return {
            "table": table,
            "status": "FAIL",
            "reason": "table_missing",
            "row_count": 0,
            "unique_dates": 0,
        }

    required_columns = config["required_columns"]
    critical_metrics = config["critical_metrics"]

    select_cols = ",".join(required_columns)

    rows = client.select(
        table,
        {
            "select": select_cols,
            "theme_name": f"eq.{THEME_NAME}",
            "order": "run_date_sgt.desc",
            "limit": "50000",
        },
    )

    if not rows:
        return {
            "table": table,
            "status": "FAIL",
            "reason": "no_rows_for_theme",
            "row_count": 0,
            "unique_dates": 0,
        }

    unique_dates = sorted({
        str(row.get("run_date_sgt"))[:10]
        for row in rows
        if row.get("run_date_sgt")
    })

    null_metric_counts: Dict[str, int] = {}
    for metric in critical_metrics:
        null_metric_counts[metric] = sum(
            1 for row in rows
            if row.get(metric) is None
        )

    non_null_metric_ok = all(
        null_metric_counts[metric] < len(rows)
        for metric in critical_metrics
    )

    if len(unique_dates) < MIN_RECONSTRUCTED_DAYS:
        status = "WARN"
        reason = "below_minimum_reconstructed_days"
    elif not non_null_metric_ok:
        status = "WARN"
        reason = "some_critical_metrics_all_null"
    else:
        status = "PASS"
        reason = "ok"

    return {
        "table": table,
        "status": status,
        "reason": reason,
        "row_count": len(rows),
        "unique_dates": len(unique_dates),
        "earliest_date": unique_dates[0] if unique_dates else None,
        "latest_date": unique_dates[-1] if unique_dates else None,
        "null_metric_counts": null_metric_counts,
    }


def main() -> None:
    client = SupabaseRestClient()

    print("Running Phase 2D.2 reconstruction validation gates...")
    print(f"Theme: {THEME_NAME}")
    print(f"Minimum reconstructed days: {MIN_RECONSTRUCTED_DAYS}")

    results: List[Dict[str, Any]] = []

    for table, config in TARGET_TABLES.items():
        result = validate_table(client, table, config)
        results.append(result)

        print("\n---")
        print(f"Table: {table}")
        print(f"Status: {result.get('status')}")
        print(f"Reason: {result.get('reason')}")
        print(f"Rows: {result.get('row_count')}")
        print(f"Unique dates: {result.get('unique_dates')}")
        print(f"Earliest date: {result.get('earliest_date')}")
        print(f"Latest date: {result.get('latest_date')}")
        print(f"Null metric counts: {result.get('null_metric_counts')}")

    hard_failures = [r for r in results if r["status"] == "FAIL"]

    # Warn-level results should not fail the workflow.
    # This is important because early reconstruction may have fewer than 30 days.
    if hard_failures:
        print("\nVALIDATION FAILED: One or more critical reconstruction tables failed.")
        for failure in hard_failures:
            print(f"- {failure['table']}: {failure.get('reason')}")
        sys.exit(1)

    print("\nVALIDATION PASSED: Phase 2D.2 reconstruction tables are populated and schema-aligned.")

    warnings = [r for r in results if r["status"] == "WARN"]
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning['table']}: {warning.get('reason')}")


if __name__ == "__main__":
    main()
