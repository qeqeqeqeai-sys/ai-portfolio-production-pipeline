import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ingestion import run_registry_ingestion
from transmission_layers.asset_discovery.tier3h5.canonical_registry_sample_sources import SAMPLE_REGISTRY_SOURCES


def test_duplicate_handling_and_idempotent_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rows = SAMPLE_REGISTRY_SOURCES["fixture_us_listings"] * 2
    first = run_registry_ingestion("fixture_us_listings", rows)
    second = run_registry_ingestion("fixture_us_listings", rows)
    assert first["summary"] == second["summary"]
    assert first["summary"]["duplicate_records_detected"] == 1


def test_summary_json_is_written(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_registry_ingestion("fixture_cross_listing", SAMPLE_REGISTRY_SOURCES["fixture_cross_listing"])
    summary_file = Path("logs/tier3h5_registry_foundation_summary.json")
    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    for key in [
        "issuer_rows_upserted",
        "security_rows_upserted",
        "provenance_rows_inserted",
        "normalization_failures",
        "deterministic_id_collisions",
    ]:
        assert key in payload
