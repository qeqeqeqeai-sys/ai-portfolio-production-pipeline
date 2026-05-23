"""B4 contract constants for controlled snapshot persistence."""

from __future__ import annotations

from copy import deepcopy

B4_APPROVED_TABLE_NAMES = {
    "snapshots": "dashboard_market_snapshots",
    "audit": "dashboard_market_snapshot_audit",
    "fragility": "dashboard_market_fragility_payloads",
}

B4_FORBIDDEN_CAPABILITY_CONTRACT = {
    "supabase_client_creation": "disallowed",
    "environment_variable_reads": "disallowed",
    "autonomous_writes": "disallowed",
    "vendor_api_fetching": "disallowed",
    "dashboard_ui_mutation": "disallowed",
    "trading": "disallowed",
    "prediction": "disallowed",
    "target_prices": "disallowed",
    "portfolio_optimization": "disallowed",
    "autonomous_notifications": "disallowed",
}

B4_ALLOWED_B3_DECISIONS = {"CERTIFIED_SNAPSHOT_READY", "DEGRADED_SNAPSHOT_READY"}
B4_BLOCKED_B3_DECISION = "BLOCKED_SNAPSHOT_INVALID"


def resolve_b4_table_names(overrides: dict | None = None) -> dict:
    merged = deepcopy(B4_APPROVED_TABLE_NAMES)
    if overrides:
        for key, value in overrides.items():
            if key in merged and isinstance(value, str) and value:
                merged[key] = value
    return merged
