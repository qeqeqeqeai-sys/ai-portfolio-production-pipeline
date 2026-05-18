import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.registry_quality_freshness_governance import (
    load_phase2b_provenance_inputs,
    run_phase2b_quality_freshness_governance,
    summarize_registry_freshness,
    summarize_registry_quality,
    summarize_snapshot_lineage,
    summarize_source_precedence,
)


def _rows():
    return [
        {
            "source_name": "exchange_primary",
            "source_dataset_version": "2026.05",
            "registry_snapshot_id": "snap-001",
            "registry_effective_date": "2026-05-01",
            "ingestion_run_id": "run-001",
            "registry_region": "US",
            "exchange_source": "XNAS",
            "listing_source": "primary",
            "normalization_version": "tier3h5_phase2a_v1",
            "source_record_count": 100,
            "accepted_record_count": 95,
            "rejected_record_count": 5,
            "duplicate_record_count": 2,
            "conflict_record_count": 1,
            "normalization_failures": 2,
            "deterministic_id_collisions": 0,
        },
        {
            "source_name": "vendor_secondary",
            "source_dataset_version": None,
            "registry_snapshot_id": None,
            "registry_effective_date": None,
            "ingestion_run_id": "run-002",
            "registry_region": "US",
            "exchange_source": "XNYS",
            "listing_source": "secondary",
            "normalization_version": "tier3h5_phase2a_v1",
            "source_record_count": 100,
            "accepted_record_count": 85,
            "rejected_record_count": 15,
            "duplicate_record_count": 12,
            "conflict_record_count": 2,
            "normalization_failures": 1,
            "deterministic_id_collisions": 1,
        },
    ]


def test_loading_ingestion_and_resolution_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("logs/tier3h5_registry_foundation_summary.json").write_text(json.dumps(_rows()[0]), encoding="utf-8")
    Path("logs/tier3h5_registry_resolution_summary.json").write_text(
        json.dumps({"registry_resolution_attempts": 10, "registry_resolution_no_match": 1, "registry_resolution_invalid_input": 1}),
        encoding="utf-8",
    )
    loaded = load_phase2b_provenance_inputs()
    assert loaded["provenance_rows"][0]["source_name"] == "exchange_primary"
    assert loaded["resolution_summary"]["registry_resolution_attempts"] == 10


def test_freshness_classification_and_missing_fields() -> None:
    summary = summarize_registry_freshness(_rows(), as_of_date=date(2026, 5, 18))
    assert summary["registry_freshness_status_counts"]["fresh"] == 1
    assert summary["registry_freshness_status_counts"]["unknown_freshness"] == 1
    assert summary["missing_effective_date_count"] == 1
    assert summary["missing_dataset_version_count"] == 1
    assert summary["missing_snapshot_id_count"] == 1


def test_quality_density_calculation_and_status() -> None:
    summary = summarize_registry_quality(
        _rows(),
        resolution_summary={"registry_resolution_attempts": 100, "registry_resolution_no_match": 4, "registry_resolution_invalid_input": 1},
    )
    per_source = {row["source_name"]: row for row in summary["source_quality_breakdown"]}
    assert per_source["exchange_primary"]["quality_status"] == "complete"
    assert per_source["vendor_secondary"]["quality_status"] == "incomplete_provenance"
    assert summary["duplicate_density"] == 0.07
    assert summary["conflict_density"] == 0.015
    assert summary["unresolved_density"] == 0.05
    assert summary["normalization_failure_density"] == 0.015


def test_snapshot_lineage_and_precedence_advisory_only() -> None:
    lineage = summarize_snapshot_lineage(_rows())
    assert lineage["lineage"][0]["normalization_version"] == "tier3h5_phase2a_v1"
    precedence = summarize_source_precedence()
    assert precedence["source_precedence_mode"] == "advisory_only"
    assert precedence["source_precedence_applied"] is False


def test_combined_summary_and_replay_stability(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("logs/tier3h5_registry_resolution_summary.json").write_text(
        json.dumps({"registry_resolution_attempts": 50, "registry_resolution_no_match": 2, "registry_resolution_invalid_input": 1}),
        encoding="utf-8",
    )

    a = run_phase2b_quality_freshness_governance(_rows(), as_of_date=date(2026, 5, 18))
    b = run_phase2b_quality_freshness_governance(_rows(), as_of_date=date(2026, 5, 18))
    assert a == b
    assert a["phase"] == "tier3h5_phase2b_1"
    assert a["provenance_backed_population_enabled"] is True

    expected = [
        "logs/tier3h5_registry_freshness_summary.json",
        "logs/tier3h5_registry_quality_summary.json",
        "logs/tier3h5_registry_snapshot_lineage.json",
        "logs/tier3h5_source_precedence_diagnostics.json",
        "logs/tier3h5_phase2b_quality_freshness_summary.json",
    ]
    for path in expected:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["enforcement_enabled"] is False
        assert payload["canonical_override_enabled"] is False
