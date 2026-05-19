from __future__ import annotations

def build_drift_report(context: dict) -> dict:
    inp = context["inputs"]
    summary = inp.get("logs/tier3h5_phase5b_monitoring_summary.json", {})
    drift_detected = bool(summary.get("drift_detected", False))
    return {
        "drift_detected": drift_detected,
        "drift_operationally_stable": not drift_detected,
        "drift_categories": {
            "orchestration": bool(summary.get("orchestration_drift_detected", False)),
            "artifact": bool(summary.get("artifact_drift_detected", False)),
            "validation": bool(summary.get("validation_drift_detected", False)),
            "readiness": bool(summary.get("readiness_drift_detected", False)),
        },
    }
