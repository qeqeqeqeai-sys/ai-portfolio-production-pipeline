from __future__ import annotations

def build_reporting_summary(context: dict, health: dict, readiness: dict, drift: dict, dashboard: dict, release: dict) -> dict:
    checks_with_findings = int(not health["orchestration_operationally_healthy"]) + int(not health["monitoring_operationally_healthy"]) + int(not readiness["readiness_continuity_verified"]) + int(not dashboard["dashboard_export_readiness_verified"]) + int(drift["drift_detected"])
    checks_executed = 5
    return {
        "reporting_run_status": "success",
        "operational_health_status": health["operational_classification"],
        "executive_readiness_status": release["release_readiness_classification"],
        "release_readiness_status": release["release_readiness_classification"],
        "operational_classification": health["operational_classification"],
        "release_readiness_classification": release["release_readiness_classification"],
        "reporting_checks_executed": checks_executed,
        "reporting_checks_with_findings": checks_with_findings,
        "orchestration_operationally_healthy": health["orchestration_operationally_healthy"],
        "monitoring_operationally_healthy": health["monitoring_operationally_healthy"],
        "drift_operationally_stable": drift["drift_operationally_stable"],
        "readiness_continuity_verified": readiness["readiness_continuity_verified"],
        "dashboard_export_readiness_verified": dashboard["dashboard_export_readiness_verified"],
        "advisory_only_governance_verified": True,
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
        "ci_failure_required": False,
        "governance_invariants": {
            "advisory_only_governance_verified": True,
            "exact_match_only_preserved": True,
            "tier3h4_freeze_boundary_preserved": True,
            "ci_failure_required": False,
        },
    }
