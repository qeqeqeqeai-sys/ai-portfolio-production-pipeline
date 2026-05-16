import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transmission_layers.asset_discovery import tier3h_transmission_candidate_discovery as mod


def test_ai_theme_links_expected_candidates():
    row = {"theme_name": "ai"}
    syms = {x["candidate_symbol"] for x in mod.link_structural_entities(row)}
    assert "TICKER::NVDA" in syms
    assert "TICKER::AVGO" in syms
    assert "ETF::SMH" in syms


def test_semiconductor_gpu_node_links_semis():
    row = {"source_node_key": "semiconductor_gpu_supply_chain"}
    syms = {x["candidate_symbol"] for x in mod.link_structural_entities(row)}
    assert "TICKER::NVDA" in syms
    assert "TICKER::TSM" in syms


def test_data_center_links_cloud_infra():
    row = {"target_node_key": "data_center_power_demand"}
    syms = {x["candidate_symbol"] for x in mod.link_structural_entities(row)}
    assert "TICKER::MSFT" in syms
    assert "TICKER::AMZN" in syms


def test_unknown_theme_fallback_no_linked_ticker():
    out = mod.discover_candidates([{"theme_name": "unknown_x"}], "2026-05-16")
    assert out and out[0]["entity_link_method"] == "unresolved"


def test_candidate_add_not_for_regime_unknown():
    rows = [{"candidate_symbol": "REGIME::LOW", "identifier_type": "REGIME", "positive_transmission_score": 10, "evidence_count": 10}]
    out = mod.discover_candidates(rows, "2026-05-16")
    assert all(not (c["recommended_action"] == "candidate_add" and c["identifier_type"] in {"REGIME", "UNKNOWN"}) for c in out)


def test_no_main_universe_operations_present():
    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    banned_terms = ["monitored_universe", "delete from", "update monitored", "insert into monitored"]
    assert all(term not in source for term in banned_terms)
    assert 'table_name="tier3h_transmission_candidates"' in source.replace(" ", "")


def test_no_upstream_data_soft_fails_and_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = mod.main()
    assert rc == 0
    summary = json.loads((tmp_path / "logs/tier3h_candidate_discovery_summary.json").read_text())
    assert summary["upstream_row_count"] == 0


def test_sql_is_idempotent_and_new_columns_present():
    sql = Path("sql/tier3h_transmission_candidate_discovery.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists" in sql
    assert "add column if not exists linked_from_theme" in sql
    assert "add column if not exists entity_link_method" in sql
