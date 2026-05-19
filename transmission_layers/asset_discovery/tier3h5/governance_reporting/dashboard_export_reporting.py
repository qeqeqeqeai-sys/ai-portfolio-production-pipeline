from __future__ import annotations

def build_dashboard_export_readiness(context: dict) -> dict:
    required = [
        "logs/tier3h5_governance_trend_analytics.json",
        "logs/tier3h5_phase5c_history_summary.json",
    ]
    present = [p for p in required if p in context["inputs"]]
    return {
        "dashboard_export_readiness_verified": len(present) == len(required),
        "required_inputs": required,
        "present_inputs": present,
    }
