import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transmission_layers.asset_discovery import tier3h4_dynamic_entity_discovery as mod


def test_scoring_function_expected_value():
    assert mod.compute_candidate_score(60, 70, 80, 50, 40) == 63.5


def test_query_deduplication_normalization():
    queries = ["AI power", " ai   power ", "AI   POWER", "other"]
    dedup = mod._deduplicate_queries(queries)
    assert dedup == ["AI power", "other"]


def test_tavily_disabled_fallback_behavior(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, evidence_rows, summary, ops = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert summary["fallback_mode"] is True
    assert rows and evidence_rows
    assert ops["executed_queries"] == 0


def test_cache_hit_reuse_behavior(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    monkeypatch.setenv("TIER3H4_TAVILY_ENABLED", "true")

    monkeypatch.setattr(mod, "_fetch_cached_evidence", lambda *args, **kwargs: [{"source_url": "https://www.reuters.com/a", "source_title": "t", "source_snippet": "s", "source_rank": 1, "retrieved_at": "2026-05-16T00:00:00+00:00", "cache_reused": True}])
    monkeypatch.setattr(mod, "_collect_tavily", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call tavily")))

    _, evidence_rows, _, ops = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert evidence_rows
    assert ops["cache_hits"] > 0
    assert all(r["cache_reused"] for r in evidence_rows)


def test_quota_exhaustion_handling_and_retry_limits(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    monkeypatch.setenv("TIER3H4_TAVILY_ENABLED", "true")
    monkeypatch.setattr(mod, "_fetch_cached_evidence", lambda *args, **kwargs: [])

    calls = {"n": 0}
    def fake_collect(*args, **kwargs):
        calls["n"] += 1
        return [], "quota_exhausted"
    monkeypatch.setattr(mod, "_collect_tavily", fake_collect)

    rows, evidence_rows, summary, ops = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert rows and evidence_rows
    assert summary["quota_exhausted"] is True
    assert ops["retry_events"] == 0
    assert calls["n"] >= 1


def test_transient_retry_no_infinite_loops(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    monkeypatch.setenv("TIER3H4_TAVILY_ENABLED", "true")
    monkeypatch.setattr(mod, "_fetch_cached_evidence", lambda *args, **kwargs: [])
    monkeypatch.setattr(mod.time, "sleep", lambda *_: None)
    seq = iter([("", "provider_unavailable"), ("", "rate_limited"), ([{"query_text": "q", "source_url": "https://example.com/a", "source_title": "t", "source_snippet": "ai data center", "source_rank": 1, "retrieved_at": "2026-05-16T00:00:00+00:00", "cache_reused": False}], None)])

    def fake_collect(*args, **kwargs):
        try:
            r = next(seq)
            return r if isinstance(r[0], list) else ([], r[1])
        except StopIteration:
            return [], "provider_unavailable"
    monkeypatch.setattr(mod, "_collect_tavily", fake_collect)

    _, evidence_rows, _, ops = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert evidence_rows
    assert ops["retry_events"] > 0
    assert ops["retry_events"] <= ops["executed_queries"]


def test_advisory_only_no_openai_no_monitored_universe_writes(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, _, _, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert all(r["llm_used"] is False for r in rows)
    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    assert "openai" not in source
    assert all(r["advisory_status"] in {"advisory_review", "advisory_rejected"} for r in rows)
