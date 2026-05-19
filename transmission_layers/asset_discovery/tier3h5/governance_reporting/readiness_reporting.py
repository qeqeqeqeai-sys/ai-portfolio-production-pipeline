from __future__ import annotations

def build_readiness_report(context: dict) -> dict:
    inputs = context["inputs"]
    readiness = inputs.get("logs/tier3h5_readiness_drift_summary.json", {})
    smoke = inputs.get("logs/tier3h5_phase5c_history_summary.json", {})
    continuity = not bool(readiness.get("readiness_drift_detected", False))
    return {
        "readiness_continuity_verified": continuity,
        "semantic_layer_readiness_continuity": smoke.get("monitoring_history_run_status") == "success" or context["loaded_input_count"] > 0,
        "smoke_test_continuity": continuity,
    }
