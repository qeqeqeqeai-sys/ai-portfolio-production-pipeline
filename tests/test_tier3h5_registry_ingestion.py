import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ingestion import SAMPLE_REGISTRY_SOURCES, run_registry_ingestion


def test_idempotent_upsert_behavior_and_duplicate_handling(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rows = SAMPLE_REGISTRY_SOURCES["nasdaq_listing_fixture"] + SAMPLE_REGISTRY_SOURCES["nasdaq_listing_fixture"]
    result1 = run_registry_ingestion("nasdaq_listing_fixture", rows)
    result2 = run_registry_ingestion("nasdaq_listing_fixture", rows)

    assert result1["summary"]["duplicate_records_detected"] == 1
    assert result1["summary"]["issuer_rows_upserted"] == 1
    assert result1["summary"]["security_rows_upserted"] == 1
    assert result1["summary"] == result2["summary"]


def test_provenance_persistence_and_summary_generation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_registry_ingestion("sec_issuer_fixture", SAMPLE_REGISTRY_SOURCES["sec_issuer_fixture"])
    assert result["provenance"].source_name == "sec_issuer_fixture"
    assert result["provenance"].schema_version == "tier3h5_phase1a_v1"

    summary_path = Path("logs/tier3h5_registry_foundation_summary.json")
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["source_name"] == "sec_issuer_fixture"
    assert "normalization_failures" in payload
