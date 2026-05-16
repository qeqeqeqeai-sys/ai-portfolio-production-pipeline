import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transmission_layers.asset_discovery import tier3h4_dynamic_entity_discovery as mod


def test_scoring_function_expected_value():
    score = mod.compute_candidate_score(60, 70, 80, 50, 40)
    assert score == 63.5


def test_confidence_band_assignment():
    assert mod._score_band(80) == "high_confidence"
    assert mod._score_band(79.9) == "medium_confidence"
    assert mod._score_band(40) == "low_confidence"
    assert mod._score_band(39.9) == "rejected_or_noise"


def test_deterministic_query_generation():
    seed = mod.DiscoverySeed("ai_power_demand", "s", "t", None)
    queries = mod._generate_queries(seed)
    assert queries == mod._generate_queries(seed)
    assert any("public companies" in q for q in queries)


def test_tavily_disabled_fallback_behavior(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, evidence_rows, summary = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert summary["fallback_mode"] is True
    assert rows and evidence_rows


def test_evidence_normalization_and_domain_and_dedup(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    monkeypatch.setenv("TIER3H4_TAVILY_ENABLED", "true")

    def fake_collect(query_text, api_key, max_results=5):
        return [
            {"query_text": query_text, "source_title": " A title ", "source_url": "https://www.reuters.com/a", "source_snippet": "  foo   bar ", "source_domain": mod._normalize_domain("https://www.reuters.com/a"), "source_rank": 1, "retrieved_at": "2026-05-16T00:00:00+00:00"},
            {"query_text": query_text, "source_title": "dup", "source_url": "https://www.reuters.com/a", "source_snippet": "dup", "source_domain": "reuters.com", "source_rank": 2, "retrieved_at": "2026-05-16T00:00:00+00:00"},
        ], None

    monkeypatch.setattr(mod, "_collect_tavily", fake_collect)
    _, evidence_rows, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert evidence_rows
    assert all(e["source_domain"] == "reuters.com" for e in evidence_rows)
    assert all("  " not in e["source_snippet"] for e in evidence_rows)


def test_low_quality_single_source_cannot_be_high_confidence(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, _, _ = mod.build_records([mod.DiscoverySeed("unknown_theme", "a", "b", None)], "2026-05-16")
    assert rows[0]["candidate_confidence_band"] != "high_confidence"


def test_llm_used_false_and_no_openai_and_evidence_fields_present(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, evidence_rows, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert all(r["llm_used"] is False for r in rows)
    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    assert "openai" not in source
    assert all(k in evidence_rows[0] for k in ["query_text", "source_url", "source_domain", "source_snippet", "retrieved_at"])


def test_idempotency_fields_present_for_evidence_and_candidate_rows(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, evidence_rows, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", "ctx")], "2026-05-16")
    for key in ["run_date_sgt", "theme_name", "candidate_asset_id", "discovery_method"]:
        assert key in rows[0]
    for key in ["run_date_sgt", "theme_name", "query_text", "source_url"]:
        assert key in evidence_rows[0]
