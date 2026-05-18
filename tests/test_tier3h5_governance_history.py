import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_explainability_api import inspect_governance_risk
from transmission_layers.asset_discovery.tier3h5.governance_history import (
    analyze_governance_trends,
    classify_historical_continuity,
    run_phase4c_governance_history,
    stable_hash,
)
from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import persist_governance_history
from transmission_layers.asset_discovery.tier3h5.governance_risk_intelligence import run_governance_risk_intelligence


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _seed_phase4b(replay_ratio: float = 0.5, unresolved: int = 2, normalization: int = 1, provenance: int = 1) -> None:
    _write("logs/tier3h5_phase3a_cross_registry_summary.json", {
        "deterministic_alias_count": 4,
        "unresolved_cross_registry_count": unresolved,
        "conflicting_cross_registry_count": 1 if unresolved else 0,
        "dual_listing_count": 1,
        "linkage_mode": "deterministic_exact_match_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    })
    _write("logs/tier3h5_lineage_dedup_summary.json", {"duplicate_lineage_edges_collapsed": unresolved, "linkage_mode": "deterministic_exact_match_only"})
    _write("logs/tier3h5_registry_replay_metrics.json", {
        "replay_consistency_ratio": replay_ratio,
        "replay_difference_count": 3 if replay_ratio < 0.9 else 0,
        "replay_normalization_difference_count": normalization,
        "replay_provenance_difference_count": provenance,
        "replay_metadata_difference_count": provenance,
        "governance_replay_stable": replay_ratio >= 0.9,
    })
    _write("logs/tier3h5_registry_replay_governance_summary.json", {
        "replay_governance_status": "normalization_drift" if normalization else "stable_replay",
        "replay_status_tags": ["normalization_drift"] if normalization else [],
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    })
    _write("logs/tier3h5_registry_replay_continuity_lineage.json", {"replay_governance_status": "normalization_drift" if normalization else "stable_replay", "replay_lineage_depth": 3})
    _write("logs/tier3h5_registry_replay_baseline_history.json", {"history": [{"replay_consistency_ratio": 1.0}, {"replay_consistency_ratio": 0.8}]})
    _write("logs/tier3h5_snapshot_archive_manifest.json", {"snapshot_hash_verified": provenance == 0})
    _write("logs/tier3h5_governance_operational_intelligence.json", {"governance_health_status": "advisory_attention", "replay_health_status": "replay_instability_detected"})
    _write("logs/tier3h5_governance_anomaly_summary.json", {"anomalies": [{"category": "normalization_drift_spike", "status": "elevated_attention"}] if normalization else []})
    run_governance_risk_intelligence()


def test_phase4c_persistence_artifacts_and_replay_safe_hashing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase4b()

    first = run_phase4c_governance_history()
    second = run_phase4c_governance_history()
    summary = _read("logs/tier3h5_phase4c_governance_history_summary.json")

    assert first["history_summary"] == second["history_summary"]
    assert summary["replay_mode"] == "advisory_only"
    assert summary["enforcement_enabled"] is False
    assert summary["historical_governance_status"] == "stable_governance_history_available"
    assert summary["governance_history_depth"] >= 3
    assert summary["governance_history_hash"]
    assert summary["governance_trend_hash"]
    assert summary["continuity_hash"]
    for path in [
        "logs/tier3h5_governance_history_summary.json",
        "logs/tier3h5_governance_trend_summary.json",
        "logs/tier3h5_governance_incident_history.json",
        "logs/tier3h5_governance_escalation_history.json",
        "logs/tier3h5_governance_watchlist_history.json",
        "logs/tier3h5_phase4c_governance_history_summary.json",
    ]:
        assert Path(path).exists()


def test_continuity_classifications_cover_persistent_recurring_stabilizing_transient_and_shallow() -> None:
    base = {"incident_key": "k", "category": "replay_governance_incident", "severity": "governance_risk"}
    assert classify_historical_continuity([])["historical_continuity_status"] == "insufficient_governance_history"
    assert classify_historical_continuity([base, dict(base)])["historical_continuity_status"] == "persistent_governance_risk"
    recurring = [dict(base, incident_key="a", severity="informational"), dict(base, incident_key="b"), dict(base, incident_key="a", severity="informational")]
    assert classify_historical_continuity(recurring)["historical_continuity_status"] == "recurring_governance_risk"
    stabilizing = [dict(base), dict(base, incident_key="z", severity="informational")]
    assert classify_historical_continuity(stabilizing)["historical_continuity_status"] == "stabilizing_governance_risk"
    transient = [dict(base, incident_key="a", severity="informational"), dict(base, incident_key="b", severity="advisory_attention")]
    assert classify_historical_continuity(transient)["historical_continuity_status"] == "transient_governance_risk"


def test_trend_analytics_dimensions_for_degrading_and_improving_history() -> None:
    incidents = [
        {"category": "replay_governance_incident", "severity": "advisory_attention"},
        {"category": "replay_governance_incident", "severity": "governance_review_recommended"},
        {"category": "lineage_integrity_incident", "severity": "advisory_attention"},
        {"category": "lineage_integrity_incident", "severity": "governance_risk"},
        {"category": "normalization_governance_incident", "severity": "elevated_attention"},
        {"category": "normalization_governance_incident", "severity": "critical_governance_instability"},
        {"category": "cross_registry_governance_incident", "severity": "advisory_attention"},
        {"category": "cross_registry_governance_incident", "severity": "governance_risk"},
        {"category": "provenance_governance_incident", "severity": "governance_review_recommended"},
        {"category": "provenance_governance_incident", "severity": "advisory_attention"},
    ]
    escalations = [{"escalation_status": "advisory_review"}, {"escalation_status": "critical_governance_attention"}]
    trend = analyze_governance_trends(incidents, escalations, window=20)
    assert trend["replay_stability_trend"] == "degrading"
    assert trend["lineage_stability_trend"] == "degrading"
    assert trend["normalization_drift_trend"] == "degrading"
    assert trend["cross_registry_stability_trend"] == "degrading"
    assert trend["provenance_quality_trend"] == "improving"
    assert trend["escalation_trend_status"] == "degrading"
    assert stable_hash(trend) == trend["governance_trend_hash"]


def test_graceful_degradation_when_history_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_phase4c_governance_history()
    assert out["history_summary"]["historical_governance_status"] == "governance_history_initializing"
    assert out["history_summary"]["historical_continuity_status"] == "insufficient_governance_history"
    assert out["trend_summary"]["governance_trend_status"] == "insufficient_history"


def test_explainability_continuity_and_regression_boundaries(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase4b()
    run_phase4c_governance_history()

    risk = inspect_governance_risk()
    summary = _read("logs/tier3h5_phase4c_governance_history_summary.json")
    assert risk["persistence_explanation"]["source"] == "persisted_governance_history_only"
    assert risk["trend_explanation"]["governance_trend_status"] == summary["governance_trend_status"]
    assert risk["continuity_explanation"]["classification_basis"] == "archived_summaries_and_persisted_history"
    assert risk["lifecycle_explanation"]["mutation_performed"] is False
    serialized = json.dumps(summary).lower()
    assert "fuzzy" not in serialized
    assert "semantic" not in serialized
    assert summary["enforcement_enabled"] is False
    assert summary["canonical_override_enabled"] is False
    assert summary["scoring_mutation_enabled"] is False
    assert summary["propagation_mutation_enabled"] is False
    assert _read("logs/tier3h5_phase3a_cross_registry_summary.json")["linkage_mode"] == "deterministic_exact_match_only"
