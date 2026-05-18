import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_explainability_api import inspect_governance_risk
from transmission_layers.asset_discovery.tier3h5.governance_risk_intelligence import (
    classify_escalation,
    classify_governance_severity,
    compute_risk_continuity,
    generate_watchlists,
    group_governance_incidents,
    run_governance_risk_intelligence,
    stable_hash,
)


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _seed_logs() -> dict[str, dict]:
    payloads = {
        "logs/tier3h5_phase3a_cross_registry_summary.json": {
            "deterministic_alias_count": 4,
            "unresolved_cross_registry_count": 2,
            "conflicting_cross_registry_count": 1,
            "dual_listing_count": 1,
            "linkage_mode": "deterministic_exact_match_only",
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        },
        "logs/tier3h5_lineage_dedup_summary.json": {
            "duplicate_lineage_edges_collapsed": 2,
            "linkage_mode": "deterministic_exact_match_only",
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        },
        "logs/tier3h5_registry_replay_metrics.json": {
            "replay_consistency_ratio": 0.5,
            "replay_difference_count": 3,
            "replay_normalization_difference_count": 1,
            "replay_provenance_difference_count": 1,
            "replay_metadata_difference_count": 1,
            "governance_replay_stable": False,
        },
        "logs/tier3h5_registry_replay_governance_summary.json": {
            "replay_governance_status": "normalization_drift",
            "replay_status_tags": ["normalization_drift"],
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        },
        "logs/tier3h5_registry_replay_continuity_lineage.json": {
            "replay_governance_status": "normalization_drift",
            "replay_difference_summary": {"difference_count": 3},
            "replay_lineage_depth": 3,
        },
        "logs/tier3h5_registry_replay_baseline_history.json": {
            "history": [
                {"replay_consistency_ratio": 1.0, "replay_governance_status": "stable_replay"},
                {"replay_consistency_ratio": 0.8, "replay_governance_status": "metadata_drift"},
            ]
        },
        "logs/tier3h5_snapshot_archive_manifest.json": {"snapshot_hash_verified": False},
        "logs/tier3h5_governance_operational_intelligence.json": {
            "governance_health_status": "advisory_attention",
            "replay_health_status": "replay_instability_detected",
            "lineage_health_status": "lineage_integrity_concern",
        },
        "logs/tier3h5_governance_anomaly_summary.json": {
            "anomalies": [{"category": "normalization_drift_spike", "status": "elevated_attention"}]
        },
    }
    for path, payload in payloads.items():
        _write(path, payload)
    return copy.deepcopy(payloads)


def test_severity_escalation_incident_watchlist_hashing_deterministic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    metrics = {
        "replay_consistency_ratio": 0.5,
        "replay_difference_count": 3,
        "unresolved_cross_registry_count": 2,
        "conflicting_cross_registry_count": 1,
        "duplicate_lineage_edges_collapsed": 2,
        "replay_normalization_difference_count": 1,
        "replay_provenance_difference_count": 1,
        "replay_metadata_difference_count": 1,
        "deterministic_alias_count": 2,
        "snapshot_hash_verified": False,
        "replay_governance_status": "normalization_drift",
    }

    assert classify_governance_severity("replay_governance_incident", metrics) == "governance_review_recommended"
    assert classify_escalation({"informational": 1, "governance_review_recommended": 1}) == "governance_review_recommended"

    incidents_a = group_governance_incidents(metrics)
    incidents_b = group_governance_incidents(dict(reversed(list(metrics.items()))))
    assert incidents_a == incidents_b
    assert all(item["incident_hash"] == stable_hash({k: v for k, v in item.items() if k != "incident_hash"}) for item in incidents_a)

    watchlists = generate_watchlists(incidents_a, metrics)
    assert len(watchlists["replay_instability_watchlist"]) == 1
    assert len(watchlists["normalization_drift_watchlist"]) == 1
    assert len(watchlists["provenance_degradation_watchlist"]) == 1


def test_phase4b_outputs_required_fields_and_advisory_only_behavior(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    upstream = _seed_logs()

    out = run_governance_risk_intelligence()
    summary = out["phase_summary"]

    assert summary["phase"] == "tier3h5_phase4b"
    assert summary["deterministic_risk_classification_enabled"] is True
    assert summary["replay_mode"] == "advisory_only"
    assert summary["enforcement_enabled"] is False
    assert summary["canonical_override_enabled"] is False
    assert summary["escalation_status"] == "governance_review_recommended"
    assert summary["governance_review_recommended"] is True
    assert Path("logs/tier3h5_governance_risk_summary.json").exists()
    assert Path("logs/tier3h5_governance_escalation_summary.json").exists()
    assert Path("logs/tier3h5_governance_incident_summary.json").exists()
    assert Path("logs/tier3h5_governance_watchlists.json").exists()
    assert Path("logs/tier3h5_phase4b_governance_risk_summary.json").exists()

    escalation = _read("logs/tier3h5_governance_escalation_summary.json")
    assert escalation["advisory_only_escalation"] is True
    assert escalation["enforcement_enabled"] is False
    assert escalation["canonical_override_enabled"] is False

    for path, payload in upstream.items():
        assert _read(path) == payload


def test_explainability_api_integrates_governance_risk(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_logs()
    run_governance_risk_intelligence()

    risk = inspect_governance_risk()
    assert risk["risk_explainability_status"] == "explainable"
    assert risk["governance_risk_status"] == "governance_review_recommended"
    assert risk["escalation_status"] == "governance_review_recommended"
    assert risk["risk_explainability_hash"]
    assert risk["replay_mode"] == "advisory_only"
    assert risk["enforcement_enabled"] is False
    assert risk["canonical_override_enabled"] is False


def test_risk_continuity_trends_and_insufficient_history_graceful_degradation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    decreasing = compute_risk_continuity({"replay_consistency_ratio": 0.5}, {"history": [{"replay_consistency_ratio": 1.0}]})
    assert decreasing["longitudinal_risk_trend"] == "increasing_governance_risk"
    assert decreasing["risk_history_status"] == "risk_history_available"

    insufficient = compute_risk_continuity({"replay_consistency_ratio": 1.0}, {"history": []})
    assert insufficient["longitudinal_risk_trend"] == "insufficient_risk_history"
    assert insufficient["graceful_degradation_applied"] is True


def test_regression_invariance_flags_for_exact_match_freeze_boundary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_logs()
    run_governance_risk_intelligence()

    phase3a = _read("logs/tier3h5_phase3a_cross_registry_summary.json")
    dedup = _read("logs/tier3h5_lineage_dedup_summary.json")
    risk = _read("logs/tier3h5_governance_risk_summary.json")

    assert phase3a["linkage_mode"] == "deterministic_exact_match_only"
    assert dedup["linkage_mode"] == "deterministic_exact_match_only"
    assert risk["enforcement_enabled"] is False
    assert risk["canonical_override_enabled"] is False
    assert "fuzzy" not in json.dumps(risk).lower()
    assert "semantic" not in json.dumps(risk).lower()
    assert "scoring" not in json.dumps(risk).lower()
    assert "propagation" not in json.dumps(risk).lower()
