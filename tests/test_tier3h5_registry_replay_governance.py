import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.registry_replay_governance import (
    classify_replay_governance,
    compare_registry_snapshots,
    compute_replay_metrics,
    run_phase2c_replay_governance,
)


def _stable_rows():
    return [
        {
            "registry_snapshot_id": "snap-002",
            "source_name": "exchange_primary",
            "source_dataset_version": "2026.05",
            "ingestion_run_id": "run-002",
            "normalization_version": "tier3h5_phase2a_v1",
            "records_seen": 100,
            "records_accepted": 95,
            "records_rejected": 5,
            "duplicates": 2,
            "conflicts": 1,
            "normalization_failures": 1,
            "deterministic_id_collisions": 0,
        }
    ]


def test_stable_replay_classification_and_metrics() -> None:
    comp = compare_registry_snapshots(_stable_rows(), _stable_rows())
    metrics = compute_replay_metrics(comp)
    status = classify_replay_governance(metrics, baseline_available=True)
    assert status == "stable_replay"
    assert metrics["replay_exact_match"] is True
    assert metrics["replay_difference_count"] == 0


def test_metadata_structural_normalization_and_provenance_drift() -> None:
    prior = _stable_rows()
    current = [dict(prior[0], source_dataset_version="2026.06", duplicates=7, normalization_version="tier3h5_phase2a_v2")]
    comp = compare_registry_snapshots(current, prior)
    metrics = compute_replay_metrics(comp)
    assert metrics["replay_structural_difference_count"] >= 1
    assert metrics["replay_metadata_difference_count"] >= 1
    assert metrics["replay_normalization_difference_count"] >= 1
    assert metrics["replay_provenance_difference_count"] >= 1


def test_baseline_unavailable_handling() -> None:
    comp = compare_registry_snapshots(_stable_rows(), None)
    metrics = compute_replay_metrics(comp)
    status = classify_replay_governance(metrics, baseline_available=False)
    assert comp["status"] == "insufficient_replay_history"
    assert status == "replay_baseline_unavailable"


def test_phase2c_artifact_generation_and_advisory_guards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    prior = _stable_rows()
    current = [dict(prior[0], source_dataset_version="2026.06", records_seen=110, records_accepted=103)]

    result = run_phase2c_replay_governance(current_rows=current, prior_rows=prior)
    assert "summary" in result

    expected = [
        "logs/tier3h5_registry_drift_summary.json",
        "logs/tier3h5_registry_replay_governance_summary.json",
        "logs/tier3h5_registry_snapshot_comparison.json",
        "logs/tier3h5_registry_replay_metrics.json",
        "logs/tier3h5_phase2c_replay_governance_summary.json",
    ]
    for path in expected:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["enforcement_enabled"] is False
        assert payload["canonical_override_enabled"] is False

