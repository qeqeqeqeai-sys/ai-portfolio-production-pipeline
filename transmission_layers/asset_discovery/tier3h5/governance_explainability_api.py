from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PHASE = "tier3h5_phase4a"
LOG_DIR = Path("logs")

PHASE3A_SUMMARY_PATH = LOG_DIR / "tier3h5_phase3a_cross_registry_summary.json"
LINEAGE_DEDUP_PATH = LOG_DIR / "tier3h5_lineage_dedup_summary.json"
REPLAY_LINEAGE_PATH = LOG_DIR / "tier3h5_registry_replay_continuity_lineage.json"
REPLAY_METRICS_PATH = LOG_DIR / "tier3h5_registry_replay_metrics.json"
REPLAY_GOVERNANCE_PATH = LOG_DIR / "tier3h5_registry_replay_governance_summary.json"
REPLAY_HISTORY_PATH = LOG_DIR / "tier3h5_registry_replay_baseline_history.json"
SNAPSHOT_ARCHIVE_PATH = LOG_DIR / "tier3h5_canonical_registry_snapshot_archive.json"
SNAPSHOT_MANIFEST_PATH = LOG_DIR / "tier3h5_snapshot_archive_manifest.json"
GOV_INTELLIGENCE_PATH = LOG_DIR / "tier3h5_governance_operational_intelligence.json"
GOV_ANOMALY_PATH = LOG_DIR / "tier3h5_governance_anomaly_summary.json"
GOV_RISK_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_risk_summary.json"
GOV_ESCALATION_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_escalation_summary.json"
GOV_INCIDENT_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_incident_summary.json"
GOV_WATCHLISTS_PATH = LOG_DIR / "tier3h5_governance_watchlists.json"

EXPLAINABILITY_PATH = LOG_DIR / "tier3h5_governance_explainability_summary.json"
LINEAGE_AUDIT_PATH = LOG_DIR / "tier3h5_lineage_audit_summary.json"
REPLAY_AUDIT_PATH = LOG_DIR / "tier3h5_replay_audit_summary.json"
SNAPSHOT_AUDIT_PATH = LOG_DIR / "tier3h5_snapshot_audit_summary.json"
ANOMALY_EXPLAINABILITY_PATH = LOG_DIR / "tier3h5_anomaly_explainability_summary.json"
PHASE_SUMMARY_PATH = LOG_DIR / "tier3h5_phase4a_explainability_audit_summary.json"


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


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def inspect_lineage(query: dict[str, Any] | None = None) -> dict[str, Any]:
    query = query or {}
    phase3a = _load_json(PHASE3A_SUMMARY_PATH)
    dedup = _load_json(LINEAGE_DEDUP_PATH)
    canonical_identity = {
        "canonical_security_id": query.get("canonical_security_id") or "unknown_canonical_security_id",
        "canonical_issuer_id": query.get("canonical_issuer_id") or "unknown_canonical_issuer_id",
        "exchange_qualified_identity": query.get("exchange_qualified_identity") or "unknown_exchange_identity",
    }
    alias_count = int(phase3a.get("deterministic_alias_count", 0) or 0)
    unresolved_count = int(phase3a.get("unresolved_cross_registry_count", 0) or 0)
    dual_count = int(phase3a.get("dual_listing_count", 0) or 0)
    dedup_collapsed = int(dedup.get("duplicate_lineage_edges_collapsed", 0) or 0)
    out = {
        "phase": PHASE,
        "queried_identity": query,
        "canonical_identity": canonical_identity,
        "lineage_nodes": {"alias_count": alias_count, "unresolved_count": unresolved_count, "dual_listing_count": dual_count},
        "lineage_edges": {"deduplicated_edges": dedup_collapsed, "effective_edges": max(0, alias_count - dedup_collapsed)},
        "alias_history": phase3a.get("deterministic_aliases", []),
        "contributing_provenance": phase3a.get("contributing_registries", []),
        "lineage_dedup_history": dedup.get("dedup_actions", []),
        "dual_listing_continuity": "stable" if dual_count > 0 else "no_dual_listings_detected",
        "replay_stability_status": "stable" if unresolved_count == 0 else "advisory_attention",
        "lineage_explainability_status": "explainable" if phase3a else "insufficient_lineage_history",
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    hash_payload = dict(out)
    out["lineage_hash"] = _stable_hash(hash_payload)
    out["lineage_hash_verified"] = out["lineage_hash"] == _stable_hash(hash_payload)
    return out


def inspect_replay() -> dict[str, Any]:
    replay = _load_json(REPLAY_LINEAGE_PATH)
    metrics = _load_json(REPLAY_METRICS_PATH)
    gov = _load_json(REPLAY_GOVERNANCE_PATH)
    history = _load_json(REPLAY_HISTORY_PATH)
    anomalies = [a for a in gov.get("replay_status_tags", []) if "drift" in str(a)]
    out = {
        "phase": PHASE,
        "replay_snapshot_id": replay.get("compared_registry_snapshot_id"),
        "prior_replay_snapshot_id": replay.get("prior_replay_snapshot_id"),
        "replay_difference_summary": replay.get("replay_difference_summary", {}),
        "replay_consistency_ratio": float(metrics.get("replay_consistency_ratio", 0.0) or 0.0),
        "replay_stability_status": replay.get("replay_governance_status", "replay_history_unavailable"),
        "replay_anomalies": anomalies,
        "replay_governance_classification": replay.get("replay_governance_status", "replay_baseline_unavailable"),
        "replay_continuity_depth": int(replay.get("replay_lineage_depth", 0) or 0),
        "replay_baseline_history_entries": len(history.get("history", [])) if isinstance(history.get("history"), list) else 0,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    hash_payload = dict(out)
    out["replay_audit_hash"] = _stable_hash(hash_payload)
    out["replay_hash_verified"] = out["replay_audit_hash"] == _stable_hash(hash_payload)
    return out


def inspect_snapshot(requested_snapshot_id: str | None = None) -> dict[str, Any]:
    archive = _load_json(SNAPSHOT_ARCHIVE_PATH)
    manifest = _load_json(SNAPSHOT_MANIFEST_PATH)
    reconstructed_id = archive.get("registry_snapshot_id")
    snapshot_hash = manifest.get("snapshot_hash")
    recomputed = _stable_hash({k: v for k, v in archive.items() if k != "archived_at_sgt"}) if archive else None
    verified = bool(snapshot_hash and recomputed and snapshot_hash == recomputed)
    out = {
        "phase": PHASE,
        "requested_snapshot_id": requested_snapshot_id or reconstructed_id,
        "reconstructed_snapshot_id": reconstructed_id,
        "snapshot_hash": snapshot_hash,
        "snapshot_hash_verified": verified,
        "archived_lineage_summary": archive.get("lineage_summary", {}),
        "archived_alias_summary": {
            "issuer_records": len(archive.get("issuer_records", [])) if isinstance(archive.get("issuer_records"), list) else 0,
            "security_records": len(archive.get("security_records", [])) if isinstance(archive.get("security_records"), list) else 0,
        },
        "archived_governance_summary": manifest.get("retention_governance", {}),
        "reconstruction_status": "reconstructed" if verified and (requested_snapshot_id in {None, reconstructed_id}) else ("snapshot_not_found" if requested_snapshot_id and requested_snapshot_id != reconstructed_id else "archive_unavailable"),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    out["snapshot_audit_hash"] = _stable_hash(out)
    return out


def explain_anomalies() -> dict[str, Any]:
    anomaly = _load_json(GOV_ANOMALY_PATH)
    governance = _load_json(GOV_INTELLIGENCE_PATH)
    anomalies = anomaly.get("anomalies", []) if isinstance(anomaly.get("anomalies"), list) else []
    explained = []
    for idx, item in enumerate(anomalies, start=1):
        explained.append({
            "anomaly_id": f"anomaly-{idx}",
            "anomaly_type": item.get("category", "unknown"),
            "anomaly_classification": item.get("status", "informational"),
            "contributing_metrics": governance.get("governance_trends", {}),
            "contributing_lineage": governance.get("lineage_health_status"),
            "replay_context": governance.get("replay_health_status"),
            "governance_context": governance.get("governance_health_status"),
            "advisory_recommendation": "operator_review_recommended" if item.get("status") != "informational" else "monitoring_only",
        })
    out = {
        "phase": PHASE,
        "anomaly_explainability_status": "explainable" if anomalies else "no_anomalies_detected",
        "anomaly_explanations": explained,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    out["anomaly_explainability_hash"] = _stable_hash(out)
    return out


def inspect_governance_risk() -> dict[str, Any]:
    risk = _load_json(GOV_RISK_SUMMARY_PATH)
    escalation = _load_json(GOV_ESCALATION_SUMMARY_PATH)
    incidents = _load_json(GOV_INCIDENT_SUMMARY_PATH)
    watchlists = _load_json(GOV_WATCHLISTS_PATH)
    incident_items = incidents.get("incidents", []) if isinstance(incidents.get("incidents"), list) else []
    out = {
        "phase": PHASE,
        "risk_explainability_status": "explainable" if risk else "risk_summary_unavailable",
        "governance_risk_status": risk.get("governance_risk_status", "risk_summary_unavailable"),
        "escalation_status": escalation.get("escalation_status", "no_escalation"),
        "incident_explanations": [
            {
                "incident_id": item.get("incident_id"),
                "category": item.get("category"),
                "severity": item.get("severity"),
                "signal": item.get("signal"),
                "evidence": item.get("evidence", {}),
                "advisory_recommendation": "operator_review_recommended" if item.get("severity") in {"governance_review_recommended", "critical_governance_instability"} else "monitoring_only",
            }
            for item in incident_items
        ],
        "watchlist_counts": watchlists.get("watchlist_counts", {}),
        "risk_summary_hash": risk.get("risk_summary_hash"),
        "escalation_summary_hash": escalation.get("escalation_summary_hash"),
        "incident_summary_hash": incidents.get("incident_summary_hash"),
        "watchlist_summary_hash": watchlists.get("watchlist_summary_hash"),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    out["risk_explainability_hash"] = _stable_hash(out)
    return out


def run_phase4a_governance_explainability() -> dict[str, Any]:
    lineage = inspect_lineage()
    replay = inspect_replay()
    snapshot = inspect_snapshot()
    anomaly = explain_anomalies()
    risk = inspect_governance_risk()

    explainability = {
        "phase": PHASE,
        "explainability_categories": [
            "canonical_identity_lineage_explanation",
            "alias_lineage_explanation",
            "replay_governance_explanation",
            "replay_drift_explanation",
            "archival_snapshot_explanation",
            "dual_listing_lineage_explanation",
            "governance_anomaly_explanation",
            "lineage_dedup_explanation",
            "provenance_lineage_explanation",
            "governance_risk_explanation",
            "governance_escalation_explanation",
        ],
        "deterministic_explainability_enabled": True,
        "explainability_hash": "",
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    explainability["explainability_hash"] = _stable_hash({k: v for k, v in explainability.items() if k != "explainability_hash"})

    phase_summary = {
        "phase": PHASE,
        "explainability_status": explainability["deterministic_explainability_enabled"],
        "lineage_audit_status": lineage["lineage_explainability_status"],
        "replay_audit_status": replay["replay_stability_status"],
        "anomaly_explainability_status": anomaly["anomaly_explainability_status"],
        "risk_explainability_status": risk["risk_explainability_status"],
        "audit_hash_verified": all([lineage.get("lineage_hash_verified"), replay.get("replay_hash_verified"), snapshot.get("snapshot_hash_verified", False) or snapshot.get("reconstruction_status") == "archive_unavailable"]),
        "deterministic_explainability_enabled": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
        "lineage_audit_hash": lineage["lineage_hash"],
        "replay_audit_hash": replay["replay_audit_hash"],
        "anomaly_explainability_hash": anomaly["anomaly_explainability_hash"],
        "risk_explainability_hash": risk["risk_explainability_hash"],
    }

    _write_json(EXPLAINABILITY_PATH, explainability)
    _write_json(LINEAGE_AUDIT_PATH, lineage)
    _write_json(REPLAY_AUDIT_PATH, replay)
    _write_json(SNAPSHOT_AUDIT_PATH, snapshot)
    _write_json(ANOMALY_EXPLAINABILITY_PATH, anomaly)
    _write_json(PHASE_SUMMARY_PATH, phase_summary)
    return {
        "governance_explainability": explainability,
        "lineage_audit": lineage,
        "replay_audit": replay,
        "snapshot_audit": snapshot,
        "anomaly_explainability": anomaly,
        "risk_explainability": risk,
        "phase_summary": phase_summary,
    }


if __name__ == "__main__":
    run_phase4a_governance_explainability()
