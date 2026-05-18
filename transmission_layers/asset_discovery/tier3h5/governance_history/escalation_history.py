from __future__ import annotations

from typing import Any

from .hashing import stable_hash


def normalize_escalation(summary: dict[str, Any]) -> dict[str, Any]:
    row = {
        "escalation_history_id": f"tier3h5-escalation-history-{stable_hash(summary.get('escalation_status', 'no_escalation'))[:16]}",
        "escalation_status": summary.get("escalation_status", "no_escalation"),
        "governance_review_recommended": bool(summary.get("governance_review_recommended", False)),
        "escalation_inputs": summary.get("escalation_inputs", {}),
        "escalation_summary_hash": summary.get("escalation_summary_hash"),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    row["escalation_history_hash"] = stable_hash(row)
    return row
