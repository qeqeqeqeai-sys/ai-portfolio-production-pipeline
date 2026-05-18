import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.registry_quality_freshness_governance import (
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
            "source_record_count": 100,
            "accepted_record_count": 95,
            "rejected_record_count": 5,
            "duplicate_record_count": 2,
            "conflict_record_count": 1,
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
            "source_record_count": 100,
            "accepted_record_count": 85,
            "rejected_record_count": 15,
            "duplicate_record_count": 12,
            "conflict_record_count": 2,
            "deterministic_id_collisions": 1,
        },
    ]


def test_freshness_classification_and_missing_fields() -> None:
    summary = summarize_registry_freshness(_rows(), as_of_date=date(2026, 5, 18))
    assert summary["registry_freshness_status_counts"]["fresh"] == 1
    assert summary["registry_freshness_status_counts"]["unknown_freshness"] == 1
    assert summary["missing_effective_date_count"] == 1
    assert summary["missing_dataset_version_count"] == 1
    assert summary["missing_snapshot_id_count"] == 1


def test_stale_source_detection() -> None:
    rows = _rows()
    rows[0]["registry_effective_date"] = "2025-12-31"
    summary = summarize_registry_freshness(rows, as_of_date=date(2026, 5, 18))
    assert "exchange_primary" in summary["stale_registry_sources"]


def test_quality_status_and_density_calculation() -> None:
    summary = summarize_registry_quality(_rows())
    per_source = {row["source_name"]: row for row in summary["source_quality"]}
    assert per_source["exchange_primary"]["quality_status"] == "complete"
    assert per_source["vendor_secondary"]["quality_status"] == "incomplete_provenance"
    assert per_source["vendor_secondary"]["duplicate_density"] == 0.12


def test_snapshot_lineage_and_precedence_are_deterministic() -> None:
    lineage_a = summarize_snapshot_lineage(_rows())
    lineage_b = summarize_snapshot_lineage(_rows())
    assert lineage_a == lineage_b
    precedence = summarize_source_precedence()
    assert precedence["source_precedence_mode"] == "advisory_only"
    assert precedence["canonical_override_enabled"] is False


def test_artifact_outputs_and_replay_stability(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    a = run_phase2b_quality_freshness_governance(_rows(), as_of_date=date(2026, 5, 18))
    b = run_phase2b_quality_freshness_governance(_rows(), as_of_date=date(2026, 5, 18))
    assert a == b
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
