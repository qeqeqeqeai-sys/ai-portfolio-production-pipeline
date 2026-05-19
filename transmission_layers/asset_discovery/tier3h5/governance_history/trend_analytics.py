from __future__ import annotations

import json
from typing import Any

from .artifact_trend_analysis import analyze_artifact_trends
from .drift_frequency_analysis import analyze_drift_frequency
from .hashing import stable_hash
from .orchestration_trend_analysis import analyze_orchestration_trends
from .readiness_trend_analysis import analyze_readiness_trends

TREND_DIMENSIONS = [
    "replay_stability_trend",
    "lineage_stability_trend",
    "normalization_drift_trend",
    "provenance_quality_trend",
    "cross_registry_stability_trend",
    "escalation_trend_status",
    "unresolved_growth_trend",
    "duplicate_lineage_trend",
]
SEVERITY_RANK = {"informational": 0, "advisory_attention": 1, "elevated_attention": 2, "governance_risk": 3, "governance_review_recommended": 4, "critical_governance_instability": 5}
ESCALATION_RANK = {"no_escalation": 0, "informational_monitoring": 0, "advisory_review": 1, "governance_attention_required": 2, "governance_review_recommended": 3, "critical_governance_attention": 4}


def _trend(series: list[float], higher_is_worse: bool = True) -> str:
    if len(series) < 2:
        return "insufficient_history"
    first, last = series[0], series[-1]
    if last == first:
        return "stable"
    worse = last > first if higher_is_worse else last < first
    return "degrading" if worse else "improving"


def _overall(dimension_statuses: dict[str, str]) -> str:
    statuses = set(dimension_statuses.values())
    if statuses == {"insufficient_history"}:
        return "insufficient_history"
    if "degrading" in statuses and "improving" in statuses:
        return "unstable"
    if "degrading" in statuses:
        return "degrading"
    if "improving" in statuses:
        return "improving"
    return "stable"


def analyze_governance_trends(incident_history: list[dict[str, Any]], escalation_history: list[dict[str, Any]], window: int = 5) -> dict[str, Any]:
    incidents = [e for e in incident_history if isinstance(e, dict)][-window:]
    escalations = [e for e in escalation_history if isinstance(e, dict)][-window:]
    severities = [SEVERITY_RANK.get(str(e.get("severity")), 0) for e in incidents]
    categories = [str(e.get("category", "")) for e in incidents]
    escalation_ranks = [ESCALATION_RANK.get(str(e.get("escalation_status")), 0) for e in escalations]
    dimensions = {
        "replay_stability_trend": _trend([v for v, c in zip(severities, categories) if c == "replay_governance_incident"]),
        "lineage_stability_trend": _trend([v for v, c in zip(severities, categories) if c == "lineage_integrity_incident"]),
        "normalization_drift_trend": _trend([v for v, c in zip(severities, categories) if c == "normalization_governance_incident"]),
        "provenance_quality_trend": _trend([v for v, c in zip(severities, categories) if c == "provenance_governance_incident"]),
        "cross_registry_stability_trend": _trend([v for v, c in zip(severities, categories) if c == "cross_registry_governance_incident"]),
        "escalation_trend_status": _trend(escalation_ranks),
        "unresolved_growth_trend": _trend([v for v, c in zip(severities, categories) if c in {"lineage_integrity_incident", "cross_registry_governance_incident"}]),
        "duplicate_lineage_trend": _trend([v for v, c in zip(severities, categories) if c == "lineage_integrity_incident"]),
    }
    out = {"governance_trend_status": _overall(dimensions), "trend_window": min(window, max(len(incidents), len(escalations))), **dimensions, "replay_mode": "advisory_only", "enforcement_enabled": False}
    out["governance_trend_hash"] = stable_hash(out)
    return out


def _classification(run_count: int, recurring: bool, findings: int) -> str:
    if run_count < 2:
        return "insufficient_history_for_trend_analysis"
    if recurring:
        return "recurring_drift_pattern"
    if findings:
        return "minor_variation"
    return "stable"


def analyze_monitoring_trends(history_runs: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = [json.loads(r["monitoring_summary"]) for r in history_runs]
    drift = analyze_drift_frequency(summaries)
    orchestration = analyze_orchestration_trends(summaries)
    artifact = analyze_artifact_trends(summaries)
    readiness = analyze_readiness_trends(summaries)
    findings = int(not orchestration["orchestration_stability_verified"]) + int(not artifact["artifact_consistency_verified"]) + int(not readiness["readiness_continuity_verified"]) + int(drift["drift_frequency_detected"])
    return {"trend_analysis_status": "completed", "trend_classification": _classification(len(summaries), drift["recurring_drift_detected"], findings), "trend_checks_executed": 4, "trend_checks_with_findings": findings, "trend_categories": {"drift_frequency": drift, "orchestration": orchestration, "artifact": artifact, "readiness": readiness}}
