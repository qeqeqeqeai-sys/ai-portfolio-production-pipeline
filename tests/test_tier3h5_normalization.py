import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_registry_normalization import (
    compute_source_record_hash,
    normalize_exchange_code,
    normalize_issuer_name,
    normalize_security_type,
    normalize_ticker,
)


def test_normalization_is_deterministic() -> None:
    assert normalize_exchange_code(" nasdaq ") == "NASDAQ"
    assert normalize_ticker(" brk.b ") == "BRK-B"
    assert normalize_ticker("BRK/B") == "BRK-B"
    assert normalize_ticker("RDS.A") == "RDS-A"
    assert normalize_exchange_code("NYSEARCA") == "ARCA"
    assert normalize_exchange_code("AMEX") == "ARCA"
    assert normalize_exchange_code("NASDAQGS") == "NASDAQ"
    assert normalize_security_type("ETF") == "etf"
    assert normalize_security_type("preferred") == "preferred_share"
    assert normalize_issuer_name("Example Holdings Inc.") == "EXAMPLE HOLDINGS INC"


def test_source_hash_stability() -> None:
    row = {"issuer_name": "A", "ticker": "AAA", "exchange": "NYSE"}
    assert compute_source_record_hash(row) == compute_source_record_hash(dict(row))


def test_normalization_idempotency_and_reversibility_where_practical() -> None:
    assert normalize_ticker(normalize_ticker("BRK.B")) == "BRK-B"
    assert normalize_exchange_code(normalize_exchange_code("NASDAQGM")) == "NASDAQ"
    assert normalize_security_type(normalize_security_type("ADR")) == "adr"
