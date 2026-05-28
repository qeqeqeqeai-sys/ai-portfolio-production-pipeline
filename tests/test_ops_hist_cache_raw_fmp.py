from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_hist_cache_raw_fmp import (
    build_cache_key,
    cached_row_to_historical_input_row,
    compute_payload_hash,
    identify_missing_symbol_dates,
    normalize_fmp_historical_price_row,
)


def test_schema_contains_raw_fmp_historical_prices_table_and_constraint():
    sql = Path("supabase/migrations/20260528090000_create_raw_fmp_historical_prices.sql").read_text(encoding="utf-8").lower()
    assert "create table" in sql and "raw_fmp_historical_prices" in sql
    assert "unique(symbol, price_date, source)" in sql


def test_cache_key_and_payload_hash_deterministic():
    assert build_cache_key("aapl", "2026-05-27") == build_cache_key("AAPL", "2026-05-27")
    p = {"symbol": "AAPL", "date": "2026-05-27", "adjClose": 100}
    assert compute_payload_hash(p) == compute_payload_hash(dict(reversed(list(p.items()))))


def test_identify_missing_symbol_dates_and_normalization_fail_closed():
    row = normalize_fmp_historical_price_row({"symbol": "AAPL", "date": "2026-05-27", "adjClose": 10})
    assert row and row["symbol"] == "AAPL"
    assert normalize_fmp_historical_price_row({"symbol": "AAPL", "date": "bad-date", "adjClose": 10}) is None
    missing = identify_missing_symbol_dates(["AAPL", "MSFT"], ["2026-05-27"], [row])
    assert missing == {"MSFT": ["2026-05-27"]}


def test_cached_close_maps_to_ops_hist_canonical_price_shape():
    cached = {
        "symbol": "AAPL",
        "price_date": "2026-05-28",
        "close": 123.45,
        "adj_close": None,
        "volume": 1000,
    }
    row = cached_row_to_historical_input_row(cached, snapshot_date="2026-05-28", sector="Tech", industry="Software")
    assert row["symbol"] == "AAPL"
    assert row["date"] == "2026-05-28"
    assert row["price"] == 123.45
    assert row["close"] == 123.45
    assert row["adjClose"] is None
    assert row["adj_close"] is None
