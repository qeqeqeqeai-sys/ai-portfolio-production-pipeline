from __future__ import annotations

from typing import Any

LIVE11_VERSION = "LR6_LIVE11_GOVERNANCE_MONITORING_HARDENING_AND_LONGITUDINAL_DRIFT_SURVEILLANCE_V2"
_ALLOWED_SCENARIOS = {"stable", "degrading", "improving", "stressed"}


def _bounded_index(index: int) -> int:
    return max(0, min(4, index))


def _scenario_delta(scenario: str, index: int) -> float:
    if scenario == "stable":
        return 0.0
    if scenario == "degrading":
        return float(index)
    if scenario == "improving":
        return float(-index)
    if scenario == "stressed":
        return float((index % 2) * 2 - 1)
    raise ValueError(f"Unsupported LIVE11 scenario: {scenario}")


def build_lr6_live11_governance_telemetry_context() -> dict[str, Any]:
    return {
        "telemetry_version": LIVE11_VERSION,
        "governance_lineage_reference": ["LIVE5", "LIVE6", "LIVE7", "LIVE8", "LIVE9", "LIVE10"],
        "surveillance_mode": "deterministic_longitudinal_governance_monitoring",
        "replay_richness_only_telemetry_scope": True,
        "deterministic_monitoring_certification": True,
        "synthetic_safe_telemetry_certification": True,
        "governance_continuity_certification": True,
        "drift_surveillance_enabled": True,
        "longitudinal_tracking_enabled": True,
        "max_snapshot_window": 5,
        "telemetry_layer_mode": "neutral_observational",
        "supported_scenarios": sorted(_ALLOWED_SCENARIOS),
    }


def build_lr6_live11_governance_snapshot(index: int, scenario: str = "stable") -> dict[str, Any]:
    bounded_index = _bounded_index(index)
    delta = _scenario_delta(scenario, bounded_index)
    base = {
        "replay_cohort_integrity_state": 0.99,
        "anomaly_frequency": 0.01,
        "detection_reliability": 0.98,
        "governance_boundary_state": 0.99,
        "append_only_integrity_state": 1.0,
        "stress_simulation_integrity_state": 0.97,
        "governance_confidence_state": 0.95,
        "historical_compatibility_state": 1.0,
        "monitoring_coverage_state": 0.98,
    }
    return {
        "snapshot_id": f"live11_snapshot_{scenario}_{bounded_index}",
        "window_index": bounded_index,
        "scenario": scenario,
        "replay_cohort_integrity_state": round(base["replay_cohort_integrity_state"] - (0.003 * delta), 4),
        "anomaly_detection_state": {
            "anomaly_frequency": round(base["anomaly_frequency"] + (0.004 * delta), 4),
            "detection_reliability": round(base["detection_reliability"] - (0.002 * delta), 4),
        },
        "governance_boundary_state": round(base["governance_boundary_state"] - (0.005 * delta), 4),
        "append_only_integrity_state": round(base["append_only_integrity_state"] - (0.002 * delta), 4),
        "stress_simulation_integrity_state": round(base["stress_simulation_integrity_state"] - (0.004 * delta), 4),
        "governance_confidence_state": round(base["governance_confidence_state"] - (0.008 * delta), 4),
        "advancement_gate_state": "ADVANCEMENT_READY_FOR_NEXT_STABILIZATION_PHASE" if scenario in {"stable", "improving"} else "ADVANCEMENT_REQUIRES_GOVERNANCE_REVIEW",
        "historical_compatibility_state": round(base["historical_compatibility_state"] - (0.002 * delta), 4),
        "monitoring_coverage_state": round(base["monitoring_coverage_state"] - (0.004 * delta), 4),
        "explainability": "Deterministic governance-only snapshot; drift/degradation is scenario-derived from telemetry inputs.",
    }


def build_lr6_live11_snapshot_series(scenario: str = "stable") -> list[dict[str, Any]]:
    return [build_lr6_live11_governance_snapshot(i, scenario=scenario) for i in range(5)]


def build_lr6_live11_drift_classification(score: int, dimensions: list[str]) -> dict[str, Any]:
    if score == 0:
        classification = "NO_GOVERNANCE_DRIFT"
        response = "Continue deterministic monitoring cadence and retain LIVE12 staging readiness checks."
        live12_safe = True
    elif score <= 2:
        classification = "LOW_GOVERNANCE_DRIFT"
        response = "Increase governance telemetry review frequency before LIVE12 progression decision."
        live12_safe = True
    elif score <= 5:
        classification = "MODERATE_GOVERNANCE_DRIFT"
        response = "Pause LIVE12 advancement and run targeted dry-run remediation simulations."
        live12_safe = False
    else:
        classification = "HIGH_GOVERNANCE_DRIFT"
        response = "Block LIVE12 and execute immediate governance hardening plus replay audit escalation."
        live12_safe = False
    return {
        "classification": classification,
        "deterministic_explanation": f"Drift score {score} computed from deterministic governance dimension deltas.",
        "affected_dimensions": dimensions,
        "recommended_operator_response": response,
        "live12_may_proceed_safely": live12_safe,
    }


def build_lr6_live11_governance_drift_review(snapshots: list[dict[str, Any]] | None = None, scenario: str = "stable") -> dict[str, Any]:
    snapshot_series = snapshots if snapshots is not None else build_lr6_live11_snapshot_series(scenario=scenario)
    baseline = snapshot_series[0]
    current = snapshot_series[-1]
    checks = {
        "governance_confidence_degradation": current["governance_confidence_state"] < baseline["governance_confidence_state"],
        "anomaly_frequency_increase": current["anomaly_detection_state"]["anomaly_frequency"] > baseline["anomaly_detection_state"]["anomaly_frequency"],
        "replay_cohort_instability_emergence": current["replay_cohort_integrity_state"] < baseline["replay_cohort_integrity_state"],
        "append_only_integrity_degradation": current["append_only_integrity_state"] < baseline["append_only_integrity_state"],
        "governance_boundary_weakening": current["governance_boundary_state"] < baseline["governance_boundary_state"],
        "monitoring_coverage_deterioration": current["monitoring_coverage_state"] < baseline["monitoring_coverage_state"],
        "stress_test_reliability_deterioration": current["stress_simulation_integrity_state"] < baseline["stress_simulation_integrity_state"],
        "historical_compatibility_drift": current["historical_compatibility_state"] < baseline["historical_compatibility_state"],
    }
    affected = [k for k, v in checks.items() if v]
    return {
        "scenario": current.get("scenario", scenario),
        "baseline_snapshot_id": baseline["snapshot_id"],
        "current_snapshot_id": current["snapshot_id"],
        "drift_checks": checks,
        "drift_classification": build_lr6_live11_drift_classification(len(affected), affected),
    }


def build_lr6_live11_longitudinal_trend_review(snapshots: list[dict[str, Any]] | None = None, scenario: str = "stable") -> dict[str, Any]:
    snapshot_series = snapshots if snapshots is not None else build_lr6_live11_snapshot_series(scenario=scenario)
    return {
        "scenario": scenario,
        "governance_confidence_trend": [s["governance_confidence_state"] for s in snapshot_series],
        "anomaly_trend": [s["anomaly_detection_state"]["anomaly_frequency"] for s in snapshot_series],
        "monitoring_reliability_trend": [s["monitoring_coverage_state"] for s in snapshot_series],
        "replay_cohort_stability_trend": [s["replay_cohort_integrity_state"] for s in snapshot_series],
        "governance_boundary_stability_trend": [s["governance_boundary_state"] for s in snapshot_series],
        "stress_simulation_reliability_trend": [s["stress_simulation_integrity_state"] for s in snapshot_series],
        "bounded_window": len(snapshot_series),
        "explainability_note": "Deterministic governance-only trend telemetry with no predictive semantics.",
    }


def build_lr6_live11_governance_degradation_review(drift_review: dict[str, Any] | None = None, scenario: str = "stable") -> dict[str, Any]:
    drift = drift_review or build_lr6_live11_governance_drift_review(scenario=scenario)
    level = drift["drift_classification"]["classification"]
    affected = drift["drift_classification"]["affected_dimensions"]
    severity = {
        "NO_GOVERNANCE_DRIFT": "none",
        "LOW_GOVERNANCE_DRIFT": "low",
        "MODERATE_GOVERNANCE_DRIFT": "moderate",
        "HIGH_GOVERNANCE_DRIFT": "high",
    }[level]
    return {
        "scenario": drift.get("scenario", scenario),
        "governance_degradation_severity": severity,
        "governance_instability_emergence": severity in {"moderate", "high"},
        "monitoring_blind_spot_emergence": "monitoring_coverage_deterioration" in affected,
        "replay_cohort_continuity_instability": "replay_cohort_instability_emergence" in affected,
        "classification_reference": level,
    }


def build_lr6_live11_governance_safeguards(degradation_review: dict[str, Any] | None = None, scenario: str = "stable") -> dict[str, Any]:
    degradation = degradation_review or build_lr6_live11_governance_degradation_review(scenario=scenario)
    return {
        "scenario": degradation.get("scenario", scenario),
        "require_additional_dry_run_simulation": degradation["governance_degradation_severity"] != "none",
        "require_operator_signoff_before_live12": degradation["governance_degradation_severity"] in {"moderate", "high"},
        "require_monitoring_coverage_audit": degradation["monitoring_blind_spot_emergence"],
        "require_replay_cohort_integrity_drill": degradation["replay_cohort_continuity_instability"],
        "safe_mode_enforced": True,
    }


def certify_lr6_live11_governance_monitoring_boundary() -> dict[str, Any]:
    return {
        "governance_monitoring_only": True,
        "longitudinal_surveillance_only": True,
        "live_persistence_enabled": False,
        "scaling_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only": True,
        "append_only_required": True,
        "deterministic_governance_required": True,
    }


def build_lr6_live11_supervisor_review(scenario: str = "stable") -> dict[str, Any]:
    snapshots = build_lr6_live11_snapshot_series(scenario=scenario)
    drift_review = build_lr6_live11_governance_drift_review(snapshots=snapshots, scenario=scenario)
    trends = build_lr6_live11_longitudinal_trend_review(snapshots=snapshots, scenario=scenario)
    degradation = build_lr6_live11_governance_degradation_review(drift_review=drift_review, scenario=scenario)
    safeguards = build_lr6_live11_governance_safeguards(degradation_review=degradation, scenario=scenario)
    live12 = "defer_live12_pending_governance_remediation" if not drift_review["drift_classification"]["live12_may_proceed_safely"] else "allow_live12_with_monitoring_hardening_guardrails"
    return {
        "objective": "Harden governance monitoring and establish deterministic longitudinal drift surveillance for replay-governance continuity.",
        "scenario": scenario,
        "governance_telemetry_context": build_lr6_live11_governance_telemetry_context(),
        "governance_continuity_snapshots": snapshots,
        "longitudinal_drift_findings": drift_review,
        "governance_trend_findings": trends,
        "governance_degradation_safeguards": safeguards,
        "governance_degradation_findings": degradation,
        "governance_continuity_assessment": "Continuity is observable via neutral telemetry; drift/degradation are scenario-derived from deterministic telemetry outputs.",
        "governance_boundary_certification": certify_lr6_live11_governance_monitoring_boundary(),
        "residual_risks": [
            "Scenario coverage may omit rare edge-case degradations until added to deterministic stress suites.",
            "Stable telemetry can mask latent future issues if stressed scenario audits are skipped.",
        ],
        "live12_recommendation": live12,
    }


def build_lr6_live11_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE11 — Governance Monitoring Hardening & Longitudinal Drift Surveillance",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## governance telemetry context",
        f"- {review.get('governance_telemetry_context')}",
        "",
        "## governance continuity snapshots",
        f"- {review.get('governance_continuity_snapshots')}",
        "",
        "## longitudinal drift findings",
        f"- {review.get('longitudinal_drift_findings')}",
        "",
        "## drift classifications",
        f"- {review.get('longitudinal_drift_findings', {}).get('drift_classification')}",
        "",
        "## governance trend findings",
        f"- {review.get('governance_trend_findings')}",
        "",
        "## governance degradation safeguards",
        f"- {review.get('governance_degradation_safeguards')}",
        "",
        "## governance continuity assessment",
        f"- {review.get('governance_continuity_assessment')}",
        "",
        "## governance boundary certification",
        f"- {review.get('governance_boundary_certification')}",
        "",
        "## residual risks",
        f"- {review.get('residual_risks')}",
        "",
        "## LIVE12 recommendation",
        f"- {review.get('live12_recommendation')}",
        "",
    ])
