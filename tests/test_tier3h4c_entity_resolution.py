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


def test_normalize_name():
    assert normalize_name("Acme, Inc.") == "acme"


def test_normalize_ticker():
    t, suspicious = normalize_ticker(" $ nvda ")
    assert t == "NVDA"
    assert not suspicious


def test_exchange_normalization():
    assert normalize_exchange("Nasdaq") == "XNAS"
    assert normalize_exchange("NYSE Arca") == "ARCX"


def test_etf_company_classification():
    assert guess_asset_type("ABC ETF Trust", None, {}) == "etf"
    assert guess_asset_type("NVIDIA Corporation", "NVDA", {}) == "equity"


def test_generic_name_suppression():
    flags = {"generic_name": True, "suspicious_ticker": False, "etf_company_conflict": False, "source_count": 1, "missing_exchange_for_ambiguous": False, "missing_ticker": True}
    _, reason, status = apply_rules(flags, 75)
    assert reason == "generic_name"
    assert status == "suppressed"


def test_suspicious_ticker_suppression():
    _, suspicious = normalize_ticker("TOOLONGGGG")
    assert suspicious


def test_confidence_clamping():
    score = compute_confidence({"has_ticker": True, "has_exchange": True, "has_name": True, "asset_type_known": True, "source_count": 3, "has_evidence_urls": True, "etf_company_conflict": False, "suspicious_ticker": False, "generic_name": False})
    assert 0 <= score <= 100


def test_duplicate_group_key_stability():
    row = {"normalized_ticker": "NVDA", "normalized_exchange": "XNAS", "normalized_name": "nvidia", "asset_type_guess": "equity", "theme_name": "ai", "run_date_sgt": "2026-05-17"}
    assert duplicate_group_key(row) == duplicate_group_key(dict(row))


def test_summary_shape_empty():
    assert is_generic_name("ai")
