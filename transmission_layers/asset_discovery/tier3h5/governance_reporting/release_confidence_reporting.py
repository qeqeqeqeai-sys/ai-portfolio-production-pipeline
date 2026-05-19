from __future__ import annotations

def classify_release_readiness(health: dict, readiness: dict, dashboard: dict, context: dict) -> dict:
    if context["loaded_input_count"] < 5:
        c = "insufficient_operational_history"
    elif health["operational_classification"] == "operational_attention_recommended":
        c = "operational_review_recommended"
    elif not readiness["readiness_continuity_verified"] or not dashboard["dashboard_export_readiness_verified"]:
        c = "operationally_ready_with_advisory_findings"
    else:
        c = "operationally_ready"
    return {"release_readiness_classification": c}
