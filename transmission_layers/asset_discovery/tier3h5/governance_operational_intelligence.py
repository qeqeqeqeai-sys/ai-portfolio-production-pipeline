from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PHASE = "tier3h5_phase3b"
LOG_DIR = Path("logs")

GOVERNANCE_INTELLIGENCE_PATH = LOG_DIR / "tier3h5_governance_operational_intelligence.json"
LINEAGE_HEALTH_PATH = LOG_DIR / "tier3h5_lineage_health_summary.json"
REPLAY_HEALTH_PATH = LOG_DIR / "tier3h5_replay_health_summary.json"
ANOMALY_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_anomaly_summary.json"
PHASE_SUMMARY_PATH = LOG_DIR / "tier3h5_phase3b_operational_intelligence_summary.json"

PHASE3A_SUMMARY_PATH = LOG_DIR / "tier3h5_phase3a_cross_registry_summary.json"
LINEAGE_DEDUP_PATH = LOG_DIR / "tier3h5_lineage_dedup_summary.json"
REPLAY_HISTORY_PATH = LOG_DIR / "tier3h5_registry_replay_baseline_history.json"
REPLAY_CHAIN_PATH = LOG_DIR / "tier3h5_replay_chain_metrics.json"


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


def _ratio(n: int, d: int) -> float:
    return round(n / d, 6) if d > 0 else 0.0


def _history_status(depth: int) -> str:
    if depth <= 1:
        return "insufficient_governance_history"
    if depth <= 3:
        return "governance_history_initializing"
    return "stable_governance_history"


def _trend(values: list[float]) -> str:
    if len(values) < 2:
        return "insufficient_governance_history"
    if values[-1] > values[0]:
        return "increasing"
    if values[-1] < values[0]:
        return "decreasing"
    return "stable"


def run_governance_operational_intelligence() -> dict[str, Any]:
    phase3a = _load_json(PHASE3A_SUMMARY_PATH)
    lineage_dedup = _load_json(LINEAGE_DEDUP_PATH)
    replay_history = _load_json(REPLAY_HISTORY_PATH)
    replay_chain = _load_json(REPLAY_CHAIN_PATH)

    history_entries = [e for e in replay_history.get("history", []) if isinstance(e, dict)]
    history_depth = len(history_entries) + 1
    history_status = _history_status(history_depth)

    duplicate_now = int(lineage_dedup.get("duplicate_lineage_edges_collapsed", 0) or 0)
    unresolved_now = int(phase3a.get("unresolved_cross_registry_count", 0) or 0)
    alias_now = int(phase3a.get("deterministic_alias_count", 0) or 0)
    dual_now = int(phase3a.get("dual_listing_count", 0) or 0)

    replay_ratio_series = [float(e.get("replay_consistency_ratio", 0.0) or 0.0) for e in history_entries] + [float(replay_chain.get("replay_consistency_ratio", 1.0) or 1.0)]
    lineage_ratio_series = [_ratio(max(0, alias_now - unresolved_now), max(1, alias_now + unresolved_now))]
    provenance_series = [1.0 if str(e.get("replay_governance_status") or "") not in {"provenance_drift", "metadata_drift"} else 0.5 for e in history_entries] + [1.0]

    governance_trends = {
        "governance_trend_windows": history_depth,
        "replay_stability_ratio_trend": replay_ratio_series,
        "lineage_integrity_ratio_trend": lineage_ratio_series,
        "alias_growth_rate": round(alias_now / max(1, history_depth), 6),
        "unresolved_growth_rate": round(unresolved_now / max(1, history_depth), 6),
        "duplicate_edge_growth_rate": round(duplicate_now / max(1, history_depth), 6),
        "normalization_drift_rate": round(sum(1 for e in history_entries if str(e.get("replay_governance_status") or "") == "normalization_drift") / max(1, len(history_entries)), 6),
        "provenance_quality_trend": provenance_series,
    }

    anomalies: list[dict[str, Any]] = []
    if governance_trends["alias_growth_rate"] > 1.0:
        anomalies.append({"category": "sudden_alias_growth", "status": "advisory_warning"})
    if replay_ratio_series and replay_ratio_series[-1] < 0.6:
        anomalies.append({"category": "replay_instability_detected", "status": "governance_review_recommended"})
    if unresolved_now > 0:
        anomalies.append({"category": "unresolved_cross_registry_spike", "status": "advisory_warning"})
    if duplicate_now > 0:
        anomalies.append({"category": "duplicate_lineage_spike", "status": "informational"})
    if governance_trends["normalization_drift_rate"] > 0:
        anomalies.append({"category": "normalization_drift_spike", "status": "elevated_attention"})

    anomaly_counts: dict[str, int] = {}
    for a in anomalies:
        anomaly_counts[a["status"]] = anomaly_counts.get(a["status"], 0) + 1

    replay_stability_ratio = replay_ratio_series[-1] if replay_ratio_series else 1.0
    lineage_integrity_ratio = lineage_ratio_series[-1]
    alias_continuity_ratio = _ratio(alias_now, max(1, alias_now + unresolved_now))

    replay_health_status = "replay_instability_detected" if replay_stability_ratio < 0.6 else ("advisory_attention" if replay_stability_ratio < 0.9 else "healthy")
    lineage_health_status = "lineage_integrity_concern" if lineage_integrity_ratio < 0.5 else ("stable_growth" if alias_now > 0 else "healthy")
    governance_health_status = "governance_review_recommended" if any(a["status"] == "governance_review_recommended" for a in anomalies) else ("elevated_governance_attention" if any(a["status"] == "elevated_attention" for a in anomalies) else ("advisory_attention" if anomalies else "healthy"))

    lineage_health = {
        "phase": PHASE,
        "lineage_chain_length": history_depth,
        "stable_lineage_chain_length": 1 if lineage_health_status in {"healthy", "stable_growth"} else 0,
        "replay_stable_chain_length": int(replay_chain.get("replay_stable_chain_length", 0) or 0),
        "lineage_break_count": unresolved_now,
        "lineage_repair_count": int(dual_now),
        "alias_continuity_ratio": alias_continuity_ratio,
        "dual_listing_stability_ratio": _ratio(dual_now, max(1, alias_now)),
        "cross_registry_integrity_ratio": lineage_integrity_ratio,
        "lineage_integrity_trend": _trend(lineage_ratio_series),
        "replay_lineage_stability_trend": _trend(replay_ratio_series),
        "alias_lineage_health": lineage_health_status,
        "governance_lineage_health": governance_health_status,
        "lineage_health_hash": "",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    lineage_health["lineage_health_hash"] = _stable_hash({k: v for k, v in lineage_health.items() if k != "lineage_health_hash"})

    replay_health = {
        "phase": PHASE,
        "replay_stability_ratio": replay_stability_ratio,
        "replay_health_status": replay_health_status,
        "replay_stability_ratio_trend": replay_ratio_series,
        "replay_health_hash": "",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    replay_health["replay_health_hash"] = _stable_hash({k: v for k, v in replay_health.items() if k != "replay_health_hash"})

    anomaly_summary = {
        "phase": PHASE,
        "anomalies": anomalies,
        "anomaly_counts": anomaly_counts,
        "governance_review_recommended": any(a["status"] == "governance_review_recommended" for a in anomalies),
        "anomaly_summary_hash": "",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    anomaly_summary["anomaly_summary_hash"] = _stable_hash({k: v for k, v in anomaly_summary.items() if k != "anomaly_summary_hash"})

    governance = {
        "phase": PHASE,
        "governance_history_status": history_status,
        "governance_trend_status": _trend([float(x) for x in governance_trends["provenance_quality_trend"]]),
        "governance_trends": governance_trends,
        "governance_health_status": governance_health_status,
        "replay_health_status": replay_health_status,
        "lineage_health_status": lineage_health_status,
        "governance_intelligence_hash": "",
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }
    governance["governance_intelligence_hash"] = _stable_hash({k: v for k, v in governance.items() if k != "governance_intelligence_hash"})

    phase_summary = {
        "phase": PHASE,
        "governance_health_status": governance_health_status,
        "replay_health_status": replay_health_status,
        "lineage_health_status": lineage_health_status,
        "anomaly_counts": anomaly_counts,
        "governance_trend_status": governance["governance_trend_status"],
        "replay_stability_ratio": replay_stability_ratio,
        "lineage_integrity_ratio": lineage_integrity_ratio,
        "alias_continuity_ratio": alias_continuity_ratio,
        "governance_review_recommended": anomaly_summary["governance_review_recommended"],
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }

    _write_json(GOVERNANCE_INTELLIGENCE_PATH, governance)
    _write_json(LINEAGE_HEALTH_PATH, lineage_health)
    _write_json(REPLAY_HEALTH_PATH, replay_health)
    _write_json(ANOMALY_SUMMARY_PATH, anomaly_summary)
    _write_json(PHASE_SUMMARY_PATH, phase_summary)
    return {"governance": governance, "lineage": lineage_health, "replay": replay_health, "anomaly": anomaly_summary, "phase": phase_summary}


if __name__ == "__main__":
    run_governance_operational_intelligence()
