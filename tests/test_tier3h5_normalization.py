import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_registry_normalization import (
    compute_source_record_hash,
    normalize_exchange_code,
    normalize_issuer_name,
    normalize_ticker,
)


def test_ticker_normalization_stability() -> None:
    assert normalize_ticker(" aapl ") == "AAPL"
    assert normalize_ticker("Brk.B") == "BRKB"


def test_exchange_normalization_stability() -> None:
    assert normalize_exchange_code(" nasdaq ") == "NASDAQ"
    assert normalize_exchange_code("ny-se") == "NYSE"


def test_issuer_normalization_stability() -> None:
    assert normalize_issuer_name("Exámple,   Holdings Inc.") == "EXÁMPLE HOLDINGS INC"


def test_source_hash_stability() -> None:
    row = {"b": "x", "a": 1}
    assert compute_source_record_hash(row) == compute_source_record_hash({"a": 1, "b": "x"})
