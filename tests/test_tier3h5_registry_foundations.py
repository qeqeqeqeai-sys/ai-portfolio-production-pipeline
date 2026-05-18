import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.exchange_registry_ingestion import (
    compute_source_record_hash,
    normalize_issuer_name,
    normalize_ticker,
    run_registry_ingestion,
)
from transmission_layers.asset_discovery.tier3h5.registry_sources import SAMPLE_STRUCTURED_SOURCE_ROWS


def test_deterministic_ticker_normalization() -> None:
    assert normalize_ticker(" aapl ") == "AAPL"
    assert normalize_ticker("Brk b") == "BRKB"


def test_deterministic_issuer_normalization() -> None:
    assert normalize_issuer_name("Example, Holdings Inc.") == "EXAMPLE HOLDINGS INC"


def test_source_record_hash_stability() -> None:
    row = {"a": 1, "b": "x"}
    assert compute_source_record_hash(row) == compute_source_record_hash({"b": "x", "a": 1})


def test_idempotent_upsert_behavior_and_duplicate_handling(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result1 = run_registry_ingestion("fixture_sec_sample", SAMPLE_STRUCTURED_SOURCE_ROWS)
    result2 = run_registry_ingestion("fixture_sec_sample", SAMPLE_STRUCTURED_SOURCE_ROWS)

    assert result1["summary"]["duplicate_records_detected"] == 1
    assert result1["summary"]["issuer_rows_upserted"] == 1
    assert result1["summary"]["security_rows_upserted"] == 1
    assert result1["summary"] == result2["summary"]


def test_summary_json_creation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_registry_ingestion("fixture_sec_sample", SAMPLE_STRUCTURED_SOURCE_ROWS)
    summary_path = Path("logs/tier3h5_registry_foundation_summary.json")
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["source_name"] == "fixture_sec_sample"


def test_tier3h4_file_unchanged() -> None:
    path = Path("transmission_layers/asset_discovery/tier3h4_dynamic_entity_discovery.py")
    text = path.read_text(encoding="utf-8")
    assert "TABLE_NAME = \"tier3h_dynamic_entity_discovery\"" in text
