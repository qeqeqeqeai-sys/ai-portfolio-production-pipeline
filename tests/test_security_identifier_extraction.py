import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transmission_layers.asset_discovery.security_identifier_extraction import extract_security_identifier


def test_nasdaq_nvda_pattern():
    r = extract_security_identifier({"candidate_name": "NASDAQ: NVDA"})
    assert r.extracted_ticker == "NVDA"
    assert r.normalized_exchange == "XNAS"
    assert r.identifier_status == "resolved"


def test_nyse_ibm_pattern_unresolved_no_registry_invention():
    r = extract_security_identifier({"candidate_name": "NYSE: IBM"})
    assert r.extracted_ticker == "IBM"
    assert r.normalized_exchange == "XNYS"
    assert r.canonical_security_id is None
    assert r.identifier_status == "unresolved"


def test_nysearca_qqq_with_explicit_field():
    r = extract_security_identifier({"ticker": "QQQ", "exchange": "NYSEARCA"})
    assert r.normalized_exchange == "ARCX"
    assert r.identifier_status in {"resolved", "unresolved"}


def test_ticker_only_ambiguity_unresolved():
    r = extract_security_identifier({"ticker": "IBM"})
    assert r.identifier_status == "unresolved"
    assert r.canonical_security_id is None


def test_etf_company_disambiguation_etf():
    r = extract_security_identifier({"candidate_name": "invesco qqq"})
    assert r.security_type == "etf"


def test_index_detection_unknown_if_not_in_registry():
    r = extract_security_identifier({"candidate_name": "S&P 500 index"})
    assert r.security_type == "unknown"


def test_invalid_uppercase_words_suppressed():
    for w in ["AI", "ON", "OR", "IT"]:
        r = extract_security_identifier({"ticker": w})
        assert r.extracted_ticker is None
        assert r.identifier_status == "suppressed"


def test_no_registry_match_unresolved_never_invented():
    r = extract_security_identifier({"ticker": "ZZZZ", "exchange": "NASDAQ"})
    assert r.canonical_security_id is None
    assert r.identifier_status == "unresolved"
