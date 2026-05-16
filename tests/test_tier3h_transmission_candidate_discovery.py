import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery import tier3h_transmission_candidate_discovery as mod


def test_runs_without_upstream_data_and_writes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = mod.main()
    assert rc == 0
    summary = json.loads((tmp_path / "logs/tier3h_candidate_discovery_summary.json").read_text(encoding="utf-8"))
    assert summary["upstream_row_count"] == 0
    assert "source_columns_seen" in summary
    assert "candidate_identifier_type_counts" in summary


def test_resolver_precedence_ticker_node_theme_regime():
    ticker = mod.resolve_candidate_identifier({"ticker": "msft", "theme_name": "ai"})
    node = mod.resolve_candidate_identifier({"source_node": "Nvidia Supply Chain", "theme_name": "ai"})
    theme = mod.resolve_candidate_identifier({"theme_name": "generative ai"})
    regime = mod.resolve_candidate_identifier({"propagation_regime": "low_propagation"})

    assert ticker["candidate_symbol"] == "TICKER::MSFT"
    assert ticker["identifier_type"] == "TICKER"
    assert node["candidate_symbol"].startswith("NODE::")
    assert node["identifier_type"] == "NODE"
    assert theme["candidate_symbol"] == "THEME::GENERATIVE_AI"
    assert theme["identifier_type"] == "THEME"
    assert regime["candidate_symbol"] == "REGIME::LOW_PROPAGATION"
    assert regime["identifier_type"] == "REGIME"


def test_mocked_upstream_rows_generate_candidates_and_group_by_identifier():
    rows = [
        {"source_node": "Cloud GPU", "theme_name": "ai", "source": "phase4a", "transmission_score": 2.1, "propagation_score": 1.2, "evidence_count": 4},
        {"source_node": "Cloud GPU", "theme_name": "ai", "source": "phase4a", "transmission_score": 1.0, "evidence_count": 2},
    ]
    out = mod.discover_candidates(rows, "2026-05-16")
    assert out
    assert out[0]["candidate_symbol"].startswith("NODE::")
    assert out[0]["candidate_source"]
    assert out[0]["identifier_type"] == "NODE"


def test_regime_fallback_not_candidate_add():
    rows = [{"propagation_regime": "moderate_propagation", "source": "t", "positive_transmission_score": 10, "evidence_count": 10}]
    out = mod.discover_candidates(rows, "2026-05-16")
    assert out[0]["identifier_type"] == "REGIME"
    assert out[0]["recommended_action"] in {"watch", "reject"}


def test_no_main_universe_operations_present():
    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    banned_terms = ["monitored_universe", "delete from", "update monitored", "insert into monitored"]
    assert all(term not in source for term in banned_terms)
    assert 'table_name = "tier3h_transmission_candidates"' in source


def test_sql_is_idempotent_safe_rerun():
    sql = Path("sql/tier3h_transmission_candidate_discovery.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists" in sql
    assert "create index if not exists" in sql
    assert "add column if not exists identifier_type" in sql
