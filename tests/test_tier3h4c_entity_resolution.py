import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transmission_layers.asset_discovery.entity_resolution.canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
from transmission_layers.asset_discovery.entity_resolution.ticker_normalizer import normalize_ticker
from transmission_layers.asset_discovery.entity_resolution.exchange_normalizer import normalize_exchange
from transmission_layers.asset_discovery.entity_resolution.confidence_scoring import compute_confidence
from transmission_layers.asset_discovery.entity_resolution.disambiguation_rules import apply_rules
from transmission_layers.asset_discovery.entity_resolution.duplicate_consolidator import duplicate_group_key
from transmission_layers.asset_discovery.entity_resolution.canonical_registry import lookup_by_ticker, lookup_by_alias
from transmission_layers.asset_discovery.entity_resolution import audit_writer
from transmission_layers.asset_discovery.entity_resolution.resolve_discovered_entities import _extract_embedded_evidence, _normalize_embedded_evidence_rows, _aggregate_evidence_identifiers, build_enriched_evidence_text, extract_deterministic_title, extract_deterministic_snippet, LOG_PATH


def test_normalize_name():
    assert normalize_name("Acme, Inc.") == "acme"


def test_registry_ticker_match_and_inference():
    hit = lookup_by_ticker("NVDA")
    assert len(hit) == 1
    assert hit[0].exchange == "XNAS"


def test_registry_alias_match():
    hit = lookup_by_alias("google")
    assert hit and hit[0].ticker == "GOOGL"


def test_normalize_ticker():
    t, suspicious = normalize_ticker(" $ nvda ")
    assert t == "NVDA"
    assert not suspicious


def test_exchange_normalization():
    assert normalize_exchange("Nasdaq") == "XNAS"


def test_confidence_calibration_missing_exchange_not_auto_suppressed():
    flags = {"has_ticker": True, "has_exchange": False, "has_name": True, "source_count": 0, "has_evidence_urls": False,
             "suspicious_ticker": False, "generic_name": False, "etf_company_conflict": False, "missing_ticker": False,
             "registry_ticker_match": False, "registry_name_or_alias_match": False, "exchange_inferred_from_registry": False,
             "missing_exchange_without_registry": True}
    score = compute_confidence(flags)
    _, _, status = apply_rules(flags, score)
    assert status == "unresolved_review"


def test_suspicious_ticker_still_suppressed():
    flags = {"generic_name": False, "suspicious_ticker": True, "etf_company_conflict": False, "source_count": 2,
             "missing_ticker": False, "has_ticker": True, "missing_exchange_without_registry": False}
    _, reason, status = apply_rules(flags, 70)
    assert reason == "suspicious_ticker" and status == "suppressed"


def test_generic_entity_still_suppressed():
    flags = {"generic_name": True, "suspicious_ticker": False, "etf_company_conflict": False, "source_count": 1,
             "missing_ticker": True, "has_ticker": False, "missing_exchange_without_registry": False}
    _, reason, status = apply_rules(flags, 70)
    assert reason == "generic_name" and status == "suppressed"


def test_duplicate_grouping_ticker_exchange_priority():
    r1 = {"normalized_ticker": "NVDA", "normalized_exchange": "XNAS", "normalized_name": "nvidia", "asset_type_guess": "equity", "theme_name": "ai", "run_date_sgt": "2026-05-17", "evidence_urls": ["a"]}
    r2 = dict(r1)
    assert duplicate_group_key(r1) == duplicate_group_key(r2)


def test_duplicate_grouping_name_fallback():
    r1 = {"normalized_ticker": None, "normalized_exchange": None, "normalized_name": "nvidia", "asset_type_guess": "equity", "theme_name": "ai", "run_date_sgt": "2026-05-17", "evidence_urls": ["a"]}
    r2 = dict(r1)
    assert duplicate_group_key(r1) == duplicate_group_key(r2)


def test_source_table_fallback(monkeypatch):
    def fake_fetch(table, *_args):
        if table == "bad":
            return [], "read_failed:bad:404"
        return [{"id": 1}], None

    monkeypatch.setattr(audit_writer, "fetch_table_rows", fake_fetch)
    rows, meta = audit_writer.fetch_table_rows_with_fallback(["bad", "good"], "2026-05-17", "ai")
    assert rows and meta["table_selected"] == "good"
    assert meta["tables_attempted"] == ["bad", "good"]
    assert meta["warnings"] == ["read_failed:bad:404"]


def test_embedded_evidence_extraction():
    row = {"source_url": "https://a", "evidence_sources": [{"source_url": "https://b"}], "source_count": 3}
    urls, source_count = _extract_embedded_evidence(row)
    assert urls == ["https://a", "https://b"]
    assert source_count == 3


def test_write_payload_validation(monkeypatch):
    class R:
        status_code = 400
        def json(self):
            return {"code": "PGRST204", "message": "bad", "details": "missing column", "hint": "check payload"}
    monkeypatch.setattr(audit_writer.requests, "post", lambda *args, **kwargs: R())
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "k")
    result = audit_writer.write_audit_rows([{"run_date_sgt": "2026-05-17"}])
    assert result["status"] == "write_failed:400"
    assert result["write_error_code"] == "PGRST204"


def test_summary_shape_empty():
    assert is_generic_name("ai")
    assert guess_asset_type("ABC ETF Trust", None, {}) == "etf"


def test_phase1_migration_exists():
    p = Path("database/migrations/202605171200_create_tier3h_dynamic_entity_evidence.sql")
    assert p.exists()


def test_evidence_payload_columns_only():
    rows = _normalize_embedded_evidence_rows(
        {"candidate_name": "X", "source_url": "https://a", "source_node": "s", "target_node": "t", "llm_classification_json": {"a": 1}},
        "2026-05-17",
        "wf-1",
        "ai",
    )
    assert rows
    assert set(rows[0].keys()).issubset(audit_writer.EVIDENCE_COLUMNS)


def test_evidence_write_advisory_only_no_universe_writes():
    rows = _normalize_embedded_evidence_rows({"candidate_name": "X", "source_url": "https://a"}, "2026-05-17", None, "ai")
    assert all(r.get("extraction_method") == "embedded_candidate_fields" for r in rows)
    assert all("monitored_universe" not in k for r in rows for k in r.keys())


def test_phase1_no_invented_ticker_exchange():
    rows = _normalize_embedded_evidence_rows({"candidate_name": "X", "source_url": "https://a"}, "2026-05-17", None, "ai")
    assert rows[0].get("extracted_ticker") is None
    assert rows[0].get("extracted_exchange") is None


def test_conflicting_evidence_identifiers_aggregator():
    agg, conflict = _aggregate_evidence_identifiers([
        {"normalized_ticker": "NVDA", "normalized_exchange": "NASDAQ", "extracted_ticker": "NVDA", "extracted_exchange": "NASDAQ"},
        {"normalized_ticker": "AMD", "normalized_exchange": "NASDAQ", "extracted_ticker": "AMD", "extracted_exchange": "NASDAQ"},
    ])
    assert conflict is True
    assert agg["normalized_ticker"] is None


def test_main_uses_evidence_for_candidate_without_unboundlocalerror(monkeypatch):
    from transmission_layers.asset_discovery.entity_resolution import resolve_discovered_entities as mod

    def fake_fetch(tables, *_args):
        if "dynamic_entity_discovery" in tables[0]:
            return [{"candidate_asset_id": "1", "candidate_name": "NVIDIA"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}
        return [{"candidate_asset_id": "1", "source_url": "https://e", "normalized_ticker": "NVDA", "normalized_exchange": "XNAS", "extracted_ticker": "NVDA", "extracted_exchange": "XNAS"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}

    monkeypatch.setattr(mod, "fetch_table_rows_with_fallback", fake_fetch)
    monkeypatch.setattr(mod, "write_evidence_rows", lambda rows: {"status": "written", "rows_written": len(rows)})
    monkeypatch.setattr(mod, "write_audit_rows", lambda rows: {"status": "written", "rows": rows})

    assert mod.main() == 0


def test_main_candidate_without_evidence_rows_keeps_ticker_exchange_null(monkeypatch):
    from transmission_layers.asset_discovery.entity_resolution import resolve_discovered_entities as mod

    captured = {}

    def fake_fetch(tables, *_args):
        if "dynamic_entity_discovery" in tables[0]:
            return [{"candidate_asset_id": "2", "candidate_name": "Unknown Startup"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}
        return [], {"rows_read": 0, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}

    monkeypatch.setattr(mod, "fetch_table_rows_with_fallback", fake_fetch)
    monkeypatch.setattr(mod, "write_evidence_rows", lambda rows: {"status": "skipped:no_rows", "rows_written": 0})

    def fake_write_audit(rows):
        captured["rows"] = rows
        return {"status": "written"}

    monkeypatch.setattr(mod, "write_audit_rows", fake_write_audit)
    assert mod.main() == 0
    row = captured["rows"][0]
    assert row["normalized_ticker"] is None
    assert row["normalized_exchange"] is None
    assert row["resolution_status"] in {"suppressed", "unresolved_review", "resolved_medium_confidence", "resolved_high_confidence"}


def test_main_empty_evidence_table_non_blocking(monkeypatch):
    from transmission_layers.asset_discovery.entity_resolution import resolve_discovered_entities as mod

    def fake_fetch(tables, *_args):
        if "dynamic_entity_discovery" in tables[0]:
            return [{"candidate_asset_id": "3", "candidate_name": "Acme"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}
        return [], {"rows_read": 0, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}

    monkeypatch.setattr(mod, "fetch_table_rows_with_fallback", fake_fetch)
    monkeypatch.setattr(mod, "write_evidence_rows", lambda rows: {"status": "skipped:no_rows", "rows_written": 0})
    monkeypatch.setattr(mod, "write_audit_rows", lambda rows: {"status": "written"})

    assert mod.main() == 0


def test_build_enriched_evidence_text_includes_title_snippet_metadata_and_operational():
    text = build_enriched_evidence_text(
        "Utility infra update",
        "NASDAQ: NVDA mentioned in article",
        {"source_type": "news", "tavily_score": 0.82},
        {"weighted_score": 39.9, "suppression": "weak_thematic_relevance"},
    )
    assert "Title: Utility infra update" in text
    assert "Snippet: NASDAQ: NVDA mentioned in article" in text
    assert "Metadata:" in text and "source_type=news" in text
    assert "Operational:" in text and "weighted_score=39.9" in text


def test_phase2a_embedded_evidence_preserves_raw_and_enriches_without_inference():
    candidate = {
        "candidate_name": "MOCK::AI_POWER_DEMAND::1",
        "source_node": "data_center_load",
        "target_node": "grid_resilience",
        "evidence_sources": [{
            "source_url": "https://example.com/story",
            "source_title": "Grid supplier update",
            "source_snippet": "capital plans and procurement updates",
            "source_domain": "example.com",
            "quality": 88.8,
            "source_type": "news",
            "tavily_score": 0.75,
        }],
        "candidate_ticker": None,
        "candidate_exchange": None,
        "candidate_confidence_score": 39.9,
        "rejection_reason": "weak_thematic_relevance",
    }
    rows = _normalize_embedded_evidence_rows(candidate, "2026-05-17", "wf-1", "ai")
    assert rows and rows[0]["source_title"] == "Grid supplier update"
    assert "Snippet: capital plans and procurement updates" in rows[0]["evidence_text"]
    assert "Operational:" in rows[0]["evidence_text"]
    assert rows[0]["raw_evidence"]["source_result"]["source_url"] == "https://example.com/story"
    assert "candidate_context" in rows[0]["raw_evidence"]
    assert rows[0]["extracted_ticker"] is None
    assert rows[0]["extracted_exchange"] is None


def test_extract_deterministic_title_across_payload_shapes():
    assert extract_deterministic_title({"title": "A"}) == ("A", "title")
    assert extract_deterministic_title({"metadata": {"page_title": "B"}}) == ("B", "metadata.page_title")
    assert extract_deterministic_title({"raw": {"title": "C"}}) == ("C", "raw.title")


def test_extract_deterministic_snippet_across_payload_shapes():
    assert extract_deterministic_snippet({"content": "Alpha"}) == ("Alpha", "content")
    assert extract_deterministic_snippet({"metadata": {"snippet": "Beta"}}) == ("Beta", "metadata.snippet")
    assert extract_deterministic_snippet({"raw": {"raw_content": "Gamma"}}) == ("Gamma", "raw.raw_content")


def test_phase2a_payload_uses_fallback_fields_and_keeps_operational_metadata():
    candidate = {"candidate_name": "X", "source_url": "https://a", "candidate_confidence_score": 9.0, "rejection_reason": "weak"}
    source = {"pageTitle": "Fallback title", "raw": {"content": "Fallback snippet"}, "source_domain": "a", "quality": 1}
    rows = _normalize_embedded_evidence_rows({**candidate, "evidence_sources": [source]}, "2026-05-17", "wf-2", "ai")
    assert rows[0]["source_title"] == "Fallback title"
    assert "Snippet: Fallback snippet" in rows[0]["evidence_text"]
    assert "Operational:" in rows[0]["evidence_text"]


def test_main_phase2a_diagnostics_count_from_persisted_payload(monkeypatch):
    from transmission_layers.asset_discovery.entity_resolution import resolve_discovered_entities as mod
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    def fake_fetch(tables, *_args):
        if "dynamic_entity_discovery" in tables[0]:
            return [{"candidate_asset_id": "1", "candidate_name": "Acme"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}
        return [{
            "candidate_asset_id": "1",
            "candidate_name": "Acme",
            "source_title": "Doc title",
            "evidence_text": "Title: Doc title\n\nSnippet: body",
            "raw_evidence": {"source_result": {"pageTitle": "Doc title", "content": "body"}},
        }], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}

    monkeypatch.setattr(mod, "fetch_table_rows_with_fallback", fake_fetch)
    monkeypatch.setattr(mod, "write_evidence_rows", lambda rows: {"status": "written", "rows_written": len(rows)})
    monkeypatch.setattr(mod, "write_audit_rows", lambda rows: {"status": "written"})
    assert mod.main() == 0
    summary = __import__("json").loads(LOG_PATH.read_text())
    assert summary["evidence_rows_with_title"] == 1
    assert summary["evidence_rows_with_snippet"] == 1
    assert summary["enriched_evidence_rows_written"] == 1
    assert summary["source_level_evidence_rows_written"] == 1
    assert summary["evidence_rows_with_raw_source_payload"] == 1


def test_phase2b_one_source_result_persists_one_evidence_row_and_domain_derivation():
    candidate = {
        "candidate_name": "X",
        "theme_name": "ai",
        "evidence_sources": [{
            "title": "Site title",
            "url": "https://news.example.com/article",
            "content": "Deterministic snippet text",
            "score": 0.9,
        }],
        "candidate_ticker": None,
        "candidate_exchange": None,
    }
    rows = _normalize_embedded_evidence_rows(candidate, "2026-05-17", "wf-2", "ai")
    assert len(rows) == 1
    row = rows[0]
    assert row["source_title"] == "Site title"
    assert row["source_url"] == "https://news.example.com/article"
    assert row["source_domain"] == "news.example.com"
    assert row["evidence_rank"] == 1
    assert "Title: Site title" in row["evidence_text"]
    assert "Snippet: Deterministic snippet text" in row["evidence_text"]
    assert row["raw_evidence"]["source_result"]["url"] == "https://news.example.com/article"
    assert "candidate_context" in row["raw_evidence"]
    assert row["extracted_ticker"] is None
    assert row["extracted_exchange"] is None


def test_main_force_fresh_skips_persisted_evidence_read_and_preserves_non_persisted_mode(monkeypatch):
    from transmission_layers.asset_discovery.entity_resolution import resolve_discovered_entities as mod
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    monkeypatch.setenv("TIER3H4_FORCE_FRESH_EVIDENCE", "1")

    calls = {"evidence_fetch_called": 0}

    def fake_fetch(tables, *_args):
        if "dynamic_entity_discovery" in tables[0]:
            return [{"candidate_asset_id": "1", "candidate_name": "Acme", "evidence_sources": [{"source_url": "https://fresh.example.com", "source_title": "Fresh", "source_snippet": "New evidence"}]}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}
        calls["evidence_fetch_called"] += 1
        return [{"candidate_asset_id": "1", "source_url": "https://old.example.com"}] * 500, {"rows_read": 500, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}

    monkeypatch.setattr(mod, "fetch_table_rows_with_fallback", fake_fetch)
    monkeypatch.setattr(mod, "write_evidence_rows", lambda rows: {"status": "written", "rows_written": len(rows)})
    monkeypatch.setattr(mod, "write_audit_rows", lambda rows: {"status": "written"})

    assert mod.main() == 0
    assert calls["evidence_fetch_called"] == 0

    summary = __import__("json").loads(LOG_PATH.read_text())
    assert summary["force_fresh_evidence"] is True
    assert summary["evidence_table_read_skipped_due_to_force_fresh"] is True
    assert summary["evidence_rows_read"] == 0
    assert summary["evidence_join_rows_used"] == 0
    assert summary["evidence_source_mode"] != "persisted_evidence_table"
    assert summary["evidence_selected_reason"] != "separate evidence table rows found"


def test_main_default_mode_still_reads_persisted_evidence(monkeypatch):
    from transmission_layers.asset_discovery.entity_resolution import resolve_discovered_entities as mod
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    monkeypatch.delenv("TIER3H4_FORCE_FRESH_EVIDENCE", raising=False)

    def fake_fetch(tables, *_args):
        if "dynamic_entity_discovery" in tables[0]:
            return [{"candidate_asset_id": "1", "candidate_name": "Acme"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}
        return [{"candidate_asset_id": "1", "source_url": "https://persisted.example.com", "source_title": "Persisted", "evidence_text": "Title: Persisted\n\nSnippet: body"}], {"rows_read": 1, "table_selected": tables[0], "tables_attempted": tables, "warnings": []}

    monkeypatch.setattr(mod, "fetch_table_rows_with_fallback", fake_fetch)
    monkeypatch.setattr(mod, "write_evidence_rows", lambda rows: {"status": "written", "rows_written": len(rows)})
    monkeypatch.setattr(mod, "write_audit_rows", lambda rows: {"status": "written"})

    assert mod.main() == 0
    summary = __import__("json").loads(LOG_PATH.read_text())
    assert summary["force_fresh_evidence"] is False
    assert summary["evidence_table_read_skipped_due_to_force_fresh"] is False
    assert summary["evidence_source_mode"] == "persisted_evidence_table"
    assert summary["evidence_selected_reason"] == "separate evidence table rows found"
    assert summary["evidence_rows_read"] == 1
    assert summary["evidence_join_rows_used"] == 1
