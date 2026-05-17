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


def test_normalize_source_result_payload_preserves_raw_result_object():
    payload = mod.normalize_source_result_payload({
        "title": "Doc",
        "url": "https://example.com",
        "content": "Body",
        "score": 0.7,
        "metadata": {"lang": "en"},
        "extra_noise": "ignore",
    })
    assert payload["title"] == "Doc"
    assert payload["url"] == "https://example.com"
    assert payload["content"] == "Body"
    assert payload["score"] == 0.7
    assert payload["metadata"] == {"lang": "en"}
    assert payload["extra_noise"] == "ignore"


def test_phase2b_source_result_persistence_contains_raw_source_payload(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    monkeypatch.setenv("TIER3H4_TAVILY_ENABLED", "true")
    monkeypatch.setattr(mod, "_fetch_cached_evidence", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        mod,
        "_collect_tavily",
        lambda *args, **kwargs: ([{
            "url": "https://news.example.com/article",
            "title": "Grid Demand Rises",
            "content": "AI data center power demand trend",
            "score": 0.92,
            "published_date": "2026-05-16",
            "source_url": "https://news.example.com/article",
            "source_title": "Grid Demand Rises",
            "source_snippet": "AI data center power demand trend",
        }], None),
    )

    _, evidence_rows, _, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert len(evidence_rows) >= 1
    row = evidence_rows[0]
    assert row["source_url"] == "https://news.example.com/article"
    assert row["source_title"] == "Grid Demand Rises"
    assert row["source_domain"] == "news.example.com"
    assert "Title: Grid Demand Rises" in row["evidence_text"]
    assert "Snippet: AI data center power demand trend" in row["evidence_text"]
    assert isinstance(row["raw_evidence"], dict)
    assert "source_result" in row["raw_evidence"]
    assert row["raw_evidence"]["source_result"]["url"] == "https://news.example.com/article"
    assert row["raw_evidence"]["source_result"]["title"] == "Grid Demand Rises"
    assert row["raw_evidence"]["source_result"]["content"] == "AI data center power demand trend"
    assert "candidate_context" in row["raw_evidence"]
    assert row["raw_evidence"]["persistence_phase"] == "tier3h4c3_surgical_source_result_persistence"
    assert row.get("candidate_ticker") is None


def test_tavily_pre_aggregation_diagnostics_increment(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    monkeypatch.setenv("TIER3H4_TAVILY_ENABLED", "true")
    monkeypatch.setattr(mod, "_fetch_cached_evidence", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        mod,
        "_collect_tavily",
        lambda *args, **kwargs: ([{"url": "https://x.example.com/a", "title": "A", "content": "C"}], None),
    )
    _, evidence_rows, summary, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert evidence_rows
    assert summary["tavily_result_rows_seen_before_aggregation"] > 0
    assert summary["tavily_result_rows_persisted_before_aggregation"] > 0
    assert summary["source_level_evidence_rows_written"] > 0
    assert summary["tavily_result_loop_file"] == "transmission_layers/asset_discovery/tier3h4_dynamic_entity_discovery.py"
    assert summary["tavily_result_loop_function"] == "build_records"


def test_source_result_row_builder_deterministic_fields_and_no_inference():
    seed = mod.DiscoverySeed("ai_power_demand", "source_n", "target_n", None)
    item = {"pageTitle": "Doc", "link": "https://example.org/path", "raw_content": "Snippet body", "relevance_score": 0.33}
    row = mod.build_source_level_evidence_row_from_tavily_result(item=item, result_index=3, seed=seed, sgt_date="2026-05-16", query_text="q", candidate_asset_id="A", candidate_name="C", discovery_method="tavily_search")
    assert row is not None
    assert row["source_title"] == "Doc"
    assert row["source_url"] == "https://example.org/path"
    assert row["source_domain"] == "example.org"
    assert row["candidate_ticker"] is None
    assert "exchange" not in row
    assert row["raw_evidence"]["source_result"]["pageTitle"] == "Doc"


def test_candidate_aggregation_output_unchanged_shape(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    rows, evidence_rows, _, _ = mod.build_records([mod.DiscoverySeed("ai_power_demand", "a", "b", None)], "2026-05-16")
    assert rows and evidence_rows
    candidate = rows[0]
    assert candidate["candidate_type"] == "equity_candidate"
    assert isinstance(candidate["evidence_sources"], list)
    assert candidate["ticker"] is None
    assert candidate["exchange"] is None
