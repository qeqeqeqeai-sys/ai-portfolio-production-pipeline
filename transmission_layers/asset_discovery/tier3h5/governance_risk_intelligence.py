from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PHASE = "tier3h5_phase4b"
LOG_DIR = Path("logs")

PHASE3A_SUMMARY_PATH = LOG_DIR / "tier3h5_phase3a_cross_registry_summary.json"
LINEAGE_DEDUP_PATH = LOG_DIR / "tier3h5_lineage_dedup_summary.json"
REPLAY_METRICS_PATH = LOG_DIR / "tier3h5_registry_replay_metrics.json"
REPLAY_GOVERNANCE_PATH = LOG_DIR / "tier3h5_registry_replay_governance_summary.json"
REPLAY_LINEAGE_PATH = LOG_DIR / "tier3h5_registry_replay_continuity_lineage.json"
REPLAY_HISTORY_PATH = LOG_DIR / "tier3h5_registry_replay_baseline_history.json"
REPLAY_CHAIN_PATH = LOG_DIR / "tier3h5_replay_chain_metrics.json"
SNAPSHOT_MANIFEST_PATH = LOG_DIR / "tier3h5_snapshot_archive_manifest.json"
GOV_INTELLIGENCE_PATH = LOG_DIR / "tier3h5_governance_operational_intelligence.json"
GOV_ANOMALY_PATH = LOG_DIR / "tier3h5_governance_anomaly_summary.json"
PHASE4A_SUMMARY_PATH = LOG_DIR / "tier3h5_phase4a_explainability_audit_summary.json"

RISK_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_risk_summary.json"
ESCALATION_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_escalation_summary.json"
INCIDENT_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_incident_summary.json"
WATCHLISTS_PATH = LOG_DIR / "tier3h5_governance_watchlists.json"
PHASE_SUMMARY_PATH = LOG_DIR / "tier3h5_phase4b_governance_risk_summary.json"

SEVERITY_LEVELS = [
    "informational",
    "advisory_attention",
    "elevated_attention",
    "governance_risk",
    "governance_review_recommended",
    "critical_governance_instability",
]

INCIDENT_CATEGORIES = [
    "replay_governance_incident",
    "lineage_integrity_incident",
    "alias_governance_incident",
    "provenance_governance_incident",
    "normalization_governance_incident",
    "cross_registry_governance_incident",
    "archival_governance_incident",
]

WATCHLIST_NAMES = [
    "unstable_lineage_watchlist",
    "replay_instability_watchlist",
    "unresolved_cross_registry_watchlist",
    "normalization_drift_watchlist",
    "provenance_degradation_watchlist",
    "duplicate_lineage_watchlist",
]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def severity_rank(severity: str) -> int:
    return SEVERITY_LEVELS.index(severity) if severity in SEVERITY_LEVELS else 0


def classify_governance_severity(category: str, metrics: dict[str, Any]) -> str:
    replay_ratio = _safe_float(metrics.get("replay_consistency_ratio"), 1.0)
    difference_count = _safe_int(metrics.get("replay_difference_count"))
    unresolved = _safe_int(metrics.get("unresolved_cross_registry_count"))
    conflicts = _safe_int(metrics.get("conflicting_cross_registry_count"))
    duplicates = _safe_int(metrics.get("duplicate_lineage_edges_collapsed"))
    normalization = _safe_int(metrics.get("replay_normalization_difference_count"))
    provenance = _safe_int(metrics.get("replay_provenance_difference_count")) + _safe_int(metrics.get("replay_metadata_difference_count"))
    archive_verified = metrics.get("snapshot_hash_verified")
    anomaly_status = str(metrics.get("anomaly_status") or "")

    if category == "replay_governance_incident":
        if replay_ratio < 0.4 or difference_count >= 5:
            return "critical_governance_instability"
        if replay_ratio < 0.6 or difference_count >= 3:
            return "governance_review_recommended"
        if replay_ratio < 0.9 or difference_count > 0:
            return "governance_risk"
        return "informational"
    if category == "lineage_integrity_incident":
        if unresolved + conflicts >= 5 or duplicates >= 5:
            return "governance_review_recommended"
        if unresolved + conflicts > 0 or duplicates > 0:
            return "elevated_attention"
        return "informational"
    if category == "normalization_governance_incident":
        if normalization >= 3 or anomaly_status == "elevated_attention":
            return "governance_review_recommended"
        if normalization > 0:
            return "governance_risk"
        return "informational"
    if category == "provenance_governance_incident":
        if provenance >= 3:
            return "governance_review_recommended"
        if provenance > 0 or archive_verified is False:
            return "elevated_attention"
        return "informational"
    if category == "cross_registry_governance_incident":
        if unresolved + conflicts >= 3:
            return "governance_risk"
        if unresolved + conflicts > 0:
            return "advisory_attention"
        return "informational"
    if category == "archival_governance_incident":
        if archive_verified is False:
            return "elevated_attention"
        if archive_verified is None:
            return "informational"
        return "informational"
    return "advisory_attention" if _safe_int(metrics.get("deterministic_alias_count")) > 0 else "informational"


def classify_escalation(severity_counts: dict[str, int]) -> str:
    highest = "informational"
    for severity, count in severity_counts.items():
        if count and severity_rank(severity) > severity_rank(highest):
            highest = severity
    return {
        "informational": "informational_monitoring" if severity_counts.get("informational", 0) else "no_escalation",
        "advisory_attention": "advisory_review",
        "elevated_attention": "governance_attention_required",
        "governance_risk": "governance_attention_required",
        "governance_review_recommended": "governance_review_recommended",
        "critical_governance_instability": "critical_governance_attention",
    }[highest]


def _incident(incident_id: str, category: str, severity: str, signal: str, entity: str, metrics: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "incident_id": incident_id,
        "category": category,
        "severity": severity,
        "signal": signal,
        "entity": entity,
        "evidence": dict(sorted(metrics.items())),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    payload["incident_hash"] = stable_hash(payload)
    return payload


def group_governance_incidents(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[tuple[str, str, str, str, dict[str, Any]]] = []
    if _safe_int(metrics.get("replay_difference_count")) > 0 or _safe_float(metrics.get("replay_consistency_ratio"), 1.0) < 0.9:
        candidates.append(("replay_governance_incident", "replay_continuity_variance", "registry_replay", "replay_consistency_ratio", {"replay_consistency_ratio": metrics.get("replay_consistency_ratio"), "replay_difference_count": metrics.get("replay_difference_count")}))
    if _safe_int(metrics.get("unresolved_cross_registry_count")) > 0 or _safe_int(metrics.get("duplicate_lineage_edges_collapsed")) > 0:
        candidates.append(("lineage_integrity_incident", "lineage_attention_signal", "canonical_lineage", "lineage_integrity", {"unresolved_cross_registry_count": metrics.get("unresolved_cross_registry_count"), "duplicate_lineage_edges_collapsed": metrics.get("duplicate_lineage_edges_collapsed")}))
    if _safe_int(metrics.get("deterministic_alias_count")) > 0:
        candidates.append(("alias_governance_incident", "alias_population_observed", "cross_registry_aliases", "deterministic_alias_count", {"deterministic_alias_count": metrics.get("deterministic_alias_count")}))
    if _safe_int(metrics.get("replay_provenance_difference_count")) > 0 or _safe_int(metrics.get("replay_metadata_difference_count")) > 0 or metrics.get("snapshot_hash_verified") is False:
        candidates.append(("provenance_governance_incident", "provenance_or_metadata_variance", "registry_provenance", "provenance_difference_count", {"replay_provenance_difference_count": metrics.get("replay_provenance_difference_count"), "replay_metadata_difference_count": metrics.get("replay_metadata_difference_count"), "snapshot_hash_verified": metrics.get("snapshot_hash_verified")}))
    if _safe_int(metrics.get("replay_normalization_difference_count")) > 0 or str(metrics.get("replay_governance_status")) == "normalization_drift":
        candidates.append(("normalization_governance_incident", "normalization_drift_signal", "normalization_replay", "normalization_difference_count", {"replay_normalization_difference_count": metrics.get("replay_normalization_difference_count"), "replay_governance_status": metrics.get("replay_governance_status")}))
    if _safe_int(metrics.get("unresolved_cross_registry_count")) > 0 or _safe_int(metrics.get("conflicting_cross_registry_count")) > 0:
        candidates.append(("cross_registry_governance_incident", "cross_registry_unresolved_signal", "cross_registry_identity", "unresolved_cross_registry_count", {"unresolved_cross_registry_count": metrics.get("unresolved_cross_registry_count"), "conflicting_cross_registry_count": metrics.get("conflicting_cross_registry_count")}))
    if "snapshot_hash_verified" in metrics and metrics.get("snapshot_hash_verified") is not True:
        candidates.append(("archival_governance_incident", "archive_verification_attention", "snapshot_archive", "snapshot_hash_verified", {"snapshot_hash_verified": metrics.get("snapshot_hash_verified")}))

    incidents = []
    for idx, (category, signal, entity, _sort_key, evidence) in enumerate(sorted(candidates, key=lambda x: (INCIDENT_CATEGORIES.index(x[0]), x[1], x[2])), start=1):
        severity = classify_governance_severity(category, {**metrics, **evidence})
        incidents.append(_incident(f"tier3h5-phase4b-incident-{idx:03d}", category, severity, signal, entity, evidence))
    return incidents


def generate_watchlists(_incidents: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    watchlists: dict[str, list[dict[str, Any]]] = {name: [] for name in WATCHLIST_NAMES}

    def add(name: str, item: dict[str, Any]) -> None:
        item = dict(item)
        item["watchlist_item_hash"] = stable_hash(item)
        watchlists[name].append(item)

    if _safe_float(metrics.get("replay_consistency_ratio"), 1.0) < 0.9 or _safe_int(metrics.get("replay_difference_count")) > 0:
        add("replay_instability_watchlist", {"entity": "registry_replay", "severity": classify_governance_severity("replay_governance_incident", metrics), "reason": "replay variance observed"})
    if _safe_int(metrics.get("unresolved_cross_registry_count")) > 0:
        add("unresolved_cross_registry_watchlist", {"entity": "cross_registry_identity", "severity": classify_governance_severity("cross_registry_governance_incident", metrics), "reason": "unresolved deterministic exact-match records"})
        add("unstable_lineage_watchlist", {"entity": "canonical_lineage", "severity": classify_governance_severity("lineage_integrity_incident", metrics), "reason": "unresolved lineage edges"})
    if _safe_int(metrics.get("duplicate_lineage_edges_collapsed")) > 0:
        add("duplicate_lineage_watchlist", {"entity": "canonical_lineage", "severity": classify_governance_severity("lineage_integrity_incident", metrics), "reason": "duplicate lineage edges collapsed upstream"})
    if _safe_int(metrics.get("replay_normalization_difference_count")) > 0 or str(metrics.get("replay_governance_status")) == "normalization_drift":
        add("normalization_drift_watchlist", {"entity": "normalization_replay", "severity": classify_governance_severity("normalization_governance_incident", metrics), "reason": "normalization drift signal"})
    if _safe_int(metrics.get("replay_provenance_difference_count")) > 0 or _safe_int(metrics.get("replay_metadata_difference_count")) > 0 or metrics.get("snapshot_hash_verified") is False:
        add("provenance_degradation_watchlist", {"entity": "registry_provenance", "severity": classify_governance_severity("provenance_governance_incident", metrics), "reason": "provenance or metadata variance"})

    for name in watchlists:
        watchlists[name] = sorted(watchlists[name], key=lambda x: (x["entity"], x["severity"], x["reason"]))
    return watchlists


def compute_risk_continuity(metrics: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    entries = [e for e in history.get("history", []) if isinstance(e, dict)]
    ratios = [_safe_float(e.get("replay_consistency_ratio"), 1.0) for e in entries]
    current_ratio = _safe_float(metrics.get("replay_consistency_ratio"), 1.0)
    series = ratios + [current_ratio]
    depth = len(series)
    if depth < 2:
        trend = "insufficient_risk_history"
    elif series[-1] < series[0]:
        trend = "increasing_governance_risk"
    elif series[-1] > series[0]:
        trend = "decreasing_governance_risk"
    else:
        trend = "stable_governance_risk"
    out = {
        "risk_history_depth": depth,
        "risk_history_status": "insufficient_risk_history" if depth < 2 else "risk_history_available",
        "replay_consistency_ratio_series": series,
        "longitudinal_risk_trend": trend,
        "graceful_degradation_applied": depth < 2,
    }
    out["risk_continuity_hash"] = stable_hash(out)
    return out


def _collect_metrics() -> tuple[dict[str, Any], dict[str, Any]]:
    phase3a = _load_json(PHASE3A_SUMMARY_PATH)
    dedup = _load_json(LINEAGE_DEDUP_PATH)
    replay_metrics = _load_json(REPLAY_METRICS_PATH)
    replay_governance = _load_json(REPLAY_GOVERNANCE_PATH)
    replay_lineage = _load_json(REPLAY_LINEAGE_PATH)
    replay_chain = _load_json(REPLAY_CHAIN_PATH)
    snapshot_manifest = _load_json(SNAPSHOT_MANIFEST_PATH)
    governance = _load_json(GOV_INTELLIGENCE_PATH)
    anomaly = _load_json(GOV_ANOMALY_PATH)
    phase4a = _load_json(PHASE4A_SUMMARY_PATH)
    history = _load_json(REPLAY_HISTORY_PATH)
    anomalies = anomaly.get("anomalies", []) if isinstance(anomaly.get("anomalies"), list) else []

    metrics = {
        "deterministic_alias_count": _safe_int(phase3a.get("deterministic_alias_count")),
        "unresolved_cross_registry_count": _safe_int(phase3a.get("unresolved_cross_registry_count")),
        "conflicting_cross_registry_count": _safe_int(phase3a.get("conflicting_cross_registry_count")),
        "dual_listing_count": _safe_int(phase3a.get("dual_listing_count")),
        "duplicate_lineage_edges_collapsed": _safe_int(dedup.get("duplicate_lineage_edges_collapsed")),
        "replay_consistency_ratio": _safe_float(replay_metrics.get("replay_consistency_ratio", replay_chain.get("replay_consistency_ratio", 1.0)), 1.0),
        "replay_difference_count": _safe_int(replay_metrics.get("replay_difference_count", replay_lineage.get("replay_difference_summary", {}).get("difference_count", 0) if isinstance(replay_lineage.get("replay_difference_summary"), dict) else 0)),
        "replay_normalization_difference_count": _safe_int(replay_metrics.get("replay_normalization_difference_count")),
        "replay_provenance_difference_count": _safe_int(replay_metrics.get("replay_provenance_difference_count")),
        "replay_metadata_difference_count": _safe_int(replay_metrics.get("replay_metadata_difference_count")),
        "replay_governance_status": replay_governance.get("replay_governance_status") or replay_lineage.get("replay_governance_status") or governance.get("replay_health_status") or "replay_history_unavailable",
        "snapshot_hash_verified": snapshot_manifest.get("snapshot_hash_verified") if "snapshot_hash_verified" in snapshot_manifest else None,
        "phase4a_audit_hash_verified": phase4a.get("audit_hash_verified"),
        "anomaly_count": len(anomalies),
        "anomaly_status": max([str(a.get("status", "informational")) for a in anomalies], default="informational"),
        "governance_health_status": governance.get("governance_health_status", "not_available"),
        "lineage_health_status": governance.get("lineage_health_status", "not_available"),
        "replay_health_status": governance.get("replay_health_status", "not_available"),
    }
    return metrics, history


def summarize_counts(items: list[str]) -> dict[str, int]:
    return {key: sum(1 for item in items if item == key) for key in sorted(set(items))}


def run_governance_risk_intelligence() -> dict[str, Any]:
    metrics, history = _collect_metrics()
    incidents = group_governance_incidents(metrics)
    severity_counts = {level: 0 for level in SEVERITY_LEVELS}
    for incident in incidents:
        severity_counts[incident["severity"]] += 1
    incident_counts = {category: 0 for category in INCIDENT_CATEGORIES}
    for incident in incidents:
        incident_counts[incident["category"]] += 1
    watchlists = generate_watchlists(incidents, metrics)
    watchlist_counts = {name: len(watchlists[name]) for name in WATCHLIST_NAMES}
    continuity = compute_risk_continuity(metrics, history)

    escalation_status = classify_escalation(severity_counts)
    highest_severity = max(SEVERITY_LEVELS, key=lambda s: (severity_counts[s] > 0, severity_rank(s))) if any(severity_counts.values()) else "informational"
    governance_review_recommended = escalation_status in {"governance_review_recommended", "critical_governance_attention"}

    risk_summary = {
        "phase": PHASE,
        "governance_risk_status": highest_severity,
        "severity_counts": severity_counts,
        "incident_counts": incident_counts,
        "watchlist_counts": watchlist_counts,
        "replay_risk_status": classify_governance_severity("replay_governance_incident", metrics),
        "lineage_risk_status": classify_governance_severity("lineage_integrity_incident", metrics),
        "risk_metrics": metrics,
        "risk_continuity": continuity,
        "deterministic_risk_classification_enabled": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    risk_summary["risk_summary_hash"] = stable_hash(risk_summary)

    escalation_summary = {
        "phase": PHASE,
        "escalation_status": escalation_status,
        "governance_review_recommended": governance_review_recommended,
        "advisory_only_escalation": True,
        "escalation_inputs": {"severity_counts": severity_counts, "incident_counts": incident_counts},
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    escalation_summary["escalation_summary_hash"] = stable_hash(escalation_summary)

    incident_summary = {
        "phase": PHASE,
        "incident_counts": incident_counts,
        "incidents": incidents,
        "deterministic_incident_grouping_enabled": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    incident_summary["incident_summary_hash"] = stable_hash(incident_summary)

    watchlist_summary = {
        "phase": PHASE,
        "watchlist_counts": watchlist_counts,
        "watchlists": watchlists,
        "deterministic_watchlist_generation_enabled": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    watchlist_summary["watchlist_summary_hash"] = stable_hash(watchlist_summary)

    phase_summary = {
        "phase": PHASE,
        "governance_risk_status": risk_summary["governance_risk_status"],
        "escalation_status": escalation_status,
        "incident_counts": incident_counts,
        "severity_counts": severity_counts,
        "watchlist_counts": watchlist_counts,
        "replay_risk_status": risk_summary["replay_risk_status"],
        "lineage_risk_status": risk_summary["lineage_risk_status"],
        "governance_review_recommended": governance_review_recommended,
        "deterministic_risk_classification_enabled": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
        "risk_summary_hash": risk_summary["risk_summary_hash"],
        "escalation_summary_hash": escalation_summary["escalation_summary_hash"],
        "incident_summary_hash": incident_summary["incident_summary_hash"],
        "watchlist_summary_hash": watchlist_summary["watchlist_summary_hash"],
        "risk_continuity_hash": continuity["risk_continuity_hash"],
    }
    phase_summary["phase4b_summary_hash"] = stable_hash(phase_summary)

    _write_json(RISK_SUMMARY_PATH, risk_summary)
    _write_json(ESCALATION_SUMMARY_PATH, escalation_summary)
    _write_json(INCIDENT_SUMMARY_PATH, incident_summary)
    _write_json(WATCHLISTS_PATH, watchlist_summary)
    _write_json(PHASE_SUMMARY_PATH, phase_summary)
    return {
        "risk_summary": risk_summary,
        "escalation_summary": escalation_summary,
        "incident_summary": incident_summary,
        "watchlist_summary": watchlist_summary,
        "phase_summary": phase_summary,
    }


if __name__ == "__main__":
    run_governance_risk_intelligence()
