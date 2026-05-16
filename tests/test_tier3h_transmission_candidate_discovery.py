import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery import tier3h_transmission_candidate_discovery as mod



def test_runs_without_upstream_data_and_writes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = mod.main()
    assert rc == 0
    assert (tmp_path / "logs/tier3h_candidate_discovery_summary.json").exists()


def test_recommended_action_values_constrained():
    rows = [
        {"symbol": "AAA", "theme": "ai", "source": "t", "positive_score": 4, "negative_score": 0, "evidence_count": 5},
        {"symbol": "BBB", "theme": "ai", "source": "t", "positive_score": 2, "negative_score": 0.1, "evidence_count": 3},
        {"symbol": "CCC", "theme": "ai", "source": "t", "positive_score": 0.4, "negative_score": 0.2, "evidence_count": 1},
        {"symbol": "DDD", "theme": "ai", "source": "t", "positive_score": 0.1, "negative_score": 2.0, "evidence_count": 1},
    ]
    out = mod.discover_candidates(rows, "2026-05-16")
    assert out
    assert all(r["recommended_action"] in mod.ALLOWED_ACTIONS for r in out)


def test_no_main_universe_operations_present():
    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    banned_terms = ["monitored_universe", "delete from", "update monitored", "insert into monitored"]
    assert all(term not in source for term in banned_terms)


def test_sql_is_idempotent_safe_rerun():
    sql = Path("sql/tier3h_transmission_candidate_discovery.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists" in sql
    assert "create index if not exists" in sql