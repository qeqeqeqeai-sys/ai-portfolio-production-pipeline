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
from transmission_layers.asset_discovery.entity_resolution.resolve_discovered_entities import _extract_embedded_evidence


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
