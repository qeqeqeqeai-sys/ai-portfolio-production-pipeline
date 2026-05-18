import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_operational_intelligence import run_governance_operational_intelligence


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def test_operational_intelligence_outputs_and_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write("logs/tier3h5_phase3a_cross_registry_summary.json", {"deterministic_alias_count": 4, "unresolved_cross_registry_count": 1, "dual_listing_count": 1})
    _write("logs/tier3h5_lineage_dedup_summary.json", {"duplicate_lineage_edges_collapsed": 2})
    _write("logs/tier3h5_registry_replay_baseline_history.json", {"history": [{"replay_consistency_ratio": 1.0, "replay_governance_status": "stable_replay"}, {"replay_consistency_ratio": 0.5, "replay_governance_status": "normalization_drift"}]})
    _write("logs/tier3h5_replay_chain_metrics.json", {"replay_consistency_ratio": 0.5, "replay_stable_chain_length": 0})

    out = run_governance_operational_intelligence()
    assert out["governance"]["phase"] == "tier3h5_phase3b"
    assert out["phase"]["replay_mode"] == "advisory_only"
    assert out["phase"]["enforcement_enabled"] is False
    assert out["phase"]["canonical_override_enabled"] is False
    assert out["anomaly"]["anomaly_summary_hash"]
    assert out["lineage"]["lineage_health_hash"]
    assert out["replay"]["replay_health_hash"]


def test_graceful_degradation_with_insufficient_history(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write("logs/tier3h5_phase3a_cross_registry_summary.json", {"deterministic_alias_count": 0, "unresolved_cross_registry_count": 0, "dual_listing_count": 0})
    _write("logs/tier3h5_lineage_dedup_summary.json", {})
    _write("logs/tier3h5_registry_replay_baseline_history.json", {"history": []})
    _write("logs/tier3h5_replay_chain_metrics.json", {})

    out = run_governance_operational_intelligence()
    assert out["governance"]["governance_history_status"] == "insufficient_governance_history"
    assert out["governance"]["governance_trends"]["governance_trend_windows"] == 1


def test_hash_stability_for_equivalent_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write("logs/tier3h5_phase3a_cross_registry_summary.json", {"deterministic_alias_count": 2, "unresolved_cross_registry_count": 0, "dual_listing_count": 1})
    _write("logs/tier3h5_lineage_dedup_summary.json", {"duplicate_lineage_edges_collapsed": 0})
    _write("logs/tier3h5_registry_replay_baseline_history.json", {"history": [{"replay_consistency_ratio": 1.0, "replay_governance_status": "stable_replay"}]})
    _write("logs/tier3h5_replay_chain_metrics.json", {"replay_consistency_ratio": 1.0, "replay_stable_chain_length": 1})

    a = run_governance_operational_intelligence()
    b = run_governance_operational_intelligence()
    assert a["governance"]["governance_intelligence_hash"] == b["governance"]["governance_intelligence_hash"]
    assert Path("logs/tier3h5_phase3b_operational_intelligence_summary.json").exists()
