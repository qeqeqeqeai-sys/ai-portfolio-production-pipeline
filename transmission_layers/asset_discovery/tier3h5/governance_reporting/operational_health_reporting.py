from __future__ import annotations

def classify_operational_health(context: dict) -> dict:
    loaded = context["loaded_input_count"]
    drift = bool(context["inputs"].get("logs/tier3h5_governance_drift_diagnostics.json", {}).get("drift_detected"))
    if loaded < 5:
        cls = "insufficient_operational_history"
    elif drift:
        cls = "operational_attention_recommended"
    elif context["missing_input_count"] > 0:
        cls = "healthy_with_minor_variation"
    else:
        cls = "healthy"
    return {
        "operational_classification": cls,
        "orchestration_operationally_healthy": loaded >= 3,
        "monitoring_operationally_healthy": loaded >= 7,
        "drift_operationally_stable": not drift,
    }
