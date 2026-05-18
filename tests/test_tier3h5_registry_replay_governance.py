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


def _stable_rows(snapshot_id: str = "snap-002", run_id: str = "run-002", dataset_version: str = "2026.05"):
    return [
        {
            "registry_snapshot_id": snapshot_id,
            "source_name": "exchange_primary",
            "source_dataset_version": dataset_version,
            "ingestion_run_id": run_id,
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
        "logs/tier3h5_replay_baseline_manifest.json",
        "logs/tier3h5_replay_history_summary.json",
        "logs/tier3h5_replay_continuity_lineage.json",
        "logs/tier3h5_replay_chain_metrics.json",
        "logs/tier3h5_phase2c1_replay_persistence_summary.json",
        "logs/tier3h5_registry_replay_baseline_history.json",
    ]
    for path in expected:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["enforcement_enabled"] is False
        assert payload["canonical_override_enabled"] is False


def test_deterministic_baseline_loading_and_history_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()

    run_phase2c_replay_governance(current_rows=_stable_rows(snapshot_id="snap-100", run_id="run-100"), prior_rows=None)
    second = run_phase2c_replay_governance(current_rows=_stable_rows(snapshot_id="snap-101", run_id="run-101"), prior_rows=None)

    assert second["comparison"]["baseline_available"] is True
    assert "replay_history_established" in second["lineage"]["replay_status_tags"]


def test_transient_vs_persistent_drift_detection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()

    run_phase2c_replay_governance(current_rows=_stable_rows(snapshot_id="snap-200", run_id="run-200"), prior_rows=None)
    drift_once = [dict(_stable_rows(snapshot_id="snap-201", run_id="run-201")[0], normalization_version="tier3h5_phase2a_v9")]
    run_phase2c_replay_governance(current_rows=drift_once, prior_rows=None)

    continuity = json.loads(Path("logs/tier3h5_replay_continuity_lineage.json").read_text(encoding="utf-8"))
    assert continuity["drift_continuity_diagnostics"]["transient_drift_detected"] is True

    drift_twice = [dict(_stable_rows(snapshot_id="snap-202", run_id="run-202")[0], normalization_version="tier3h5_phase2a_v10")]
    run_phase2c_replay_governance(current_rows=drift_twice, prior_rows=None)

    continuity2 = json.loads(Path("logs/tier3h5_replay_continuity_lineage.json").read_text(encoding="utf-8"))
    assert continuity2["drift_continuity_diagnostics"]["persistent_drift_detected"] is True


def test_optional_snapshot_ids_serialize_as_json_null_in_phase2c_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    rows = _stable_rows(snapshot_id=None, run_id="run-null")

    run_phase2c_replay_governance(current_rows=rows, prior_rows=None)

    lineage = json.loads(Path("logs/tier3h5_replay_continuity_lineage.json").read_text(encoding="utf-8"))
    history = json.loads(Path("logs/tier3h5_replay_history_summary.json").read_text(encoding="utf-8"))
    baseline = json.loads(Path("logs/tier3h5_replay_baseline_manifest.json").read_text(encoding="utf-8"))
    serialized_lineage = Path("logs/tier3h5_replay_continuity_lineage.json").read_text(encoding="utf-8")

    assert lineage["compared_registry_snapshot_id"] is None
    assert history["latest_replay_snapshot_id"] is None
    assert baseline["replay_comparison_baseline_id"] is None
    assert '"None"' not in serialized_lineage
