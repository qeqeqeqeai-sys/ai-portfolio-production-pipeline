import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_explainability_api import (
    explain_anomalies,
    inspect_lineage,
    inspect_replay,
    inspect_snapshot,
    run_phase4a_governance_explainability,
)


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_logs() -> None:
    _write("logs/tier3h5_phase3a_cross_registry_summary.json", {"deterministic_alias_count": 4, "unresolved_cross_registry_count": 1, "dual_listing_count": 1, "contributing_registries": ["xnas", "xnys"]})
    _write("logs/tier3h5_lineage_dedup_summary.json", {"duplicate_lineage_edges_collapsed": 2, "dedup_actions": [{"type": "edge_collapse"}]})
    _write("logs/tier3h5_registry_replay_continuity_lineage.json", {"compared_registry_snapshot_id": "snap-1", "prior_replay_snapshot_id": "snap-0", "replay_governance_status": "normalization_drift", "replay_lineage_depth": 3, "replay_difference_summary": {"difference_count": 2}, "replay_status_tags": ["transient_replay_difference", "normalization_drift"]})
    _write("logs/tier3h5_registry_replay_metrics.json", {"replay_consistency_ratio": 0.5})
    _write("logs/tier3h5_registry_replay_governance_summary.json", {"replay_status_tags": ["normalization_drift"]})
    _write("logs/tier3h5_registry_replay_baseline_history.json", {"history": [{"a": 1}, {"b": 2}]})
    archive = {"registry_snapshot_id": "snap-1", "issuer_records": [{"id": "i1"}], "security_records": [{"id": "s1"}], "lineage_summary": {"edges": 5}, "retention_governance": {"status": "retained"}, "archived_at_sgt": "2026-05-18T00:00:00Z"}
    _write("logs/tier3h5_canonical_registry_snapshot_archive.json", archive)
    from transmission_layers.asset_discovery.tier3h5.registry_snapshot_archive import _canonicalize, _snapshot_hash

    _write("logs/tier3h5_snapshot_archive_manifest.json", {"snapshot_hash": _snapshot_hash(_canonicalize(archive))})
    _write("logs/tier3h5_governance_operational_intelligence.json", {"governance_health_status": "advisory_attention", "replay_health_status": "replay_instability_detected", "lineage_health_status": "lineage_integrity_concern", "governance_trends": {"normalization_drift_rate": 0.5}})
    _write("logs/tier3h5_governance_anomaly_summary.json", {"anomalies": [{"category": "normalization_drift_spike", "status": "elevated_attention"}]})


def test_phase4a_explainability_and_audit_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_logs()

    out = run_phase4a_governance_explainability()
    assert out["phase_summary"]["phase"] == "tier3h5_phase4a"
    assert out["phase_summary"]["deterministic_explainability_enabled"] is True
    assert out["phase_summary"]["replay_mode"] == "advisory_only"
    assert out["phase_summary"]["enforcement_enabled"] is False
    assert out["phase_summary"]["canonical_override_enabled"] is False
    assert Path("logs/tier3h5_phase4a_explainability_audit_summary.json").exists()


def test_lineage_and_replay_interrogation_deterministic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_logs()

    l1 = inspect_lineage({"canonical_security_id": "sec-1"})
    l2 = inspect_lineage({"canonical_security_id": "sec-1"})
    r1 = inspect_replay()
    r2 = inspect_replay()

    assert l1["lineage_hash"] == l2["lineage_hash"]
    assert l1["lineage_hash_verified"] is True
    assert r1["replay_audit_hash"] == r2["replay_audit_hash"]
    assert r1["replay_hash_verified"] is True


def test_snapshot_and_anomaly_graceful_degradation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()

    snapshot = inspect_snapshot("snap-x")
    anomaly = explain_anomalies()

    assert snapshot["reconstruction_status"] in {"archive_unavailable", "snapshot_not_found"}
    assert anomaly["anomaly_explainability_status"] == "no_anomalies_detected"
