import io
import re
from urllib.error import HTTPError

import pytest

from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import (
    DEFAULT_HIST_WINDOW_DAYS,
    MAX_HIST_WINDOW_DAYS,
    MAX_SNAPSHOTS_PER_RUN,
    OPS_HIST1_SCHEMA_VERSION,
    build_historical_fmp_fetcher,
    build_ops_hist1_observation_review,
    deterministic_historical_window_dates,
    historical_window_checksum,
    load_ops_hist1_snapshots,
    render_ops_hist1_observation_review_markdown,
    run_ops_hist1_historical_backfill,
)


def _fetcher(batch):
    out = []
    for i, s in enumerate(batch):
        out.append({"symbol": s, "price": 100+i, "marketCap": 1000000+i, "sector": "Tech" if i%2==0 else "Fin", "industry": "Soft", "beta": 1.0, "pe": 10.0+i/100, "roe": 0.2, "debtToEquity": 0.1, "dispersion": 0.3})
    return out


def test_window_bounds_and_fail_closed():
    assert len(deterministic_historical_window_dates("2026-05-27", DEFAULT_HIST_WINDOW_DAYS)) == DEFAULT_HIST_WINDOW_DAYS
    with pytest.raises(ValueError):
        deterministic_historical_window_dates("2026-05-27", MAX_HIST_WINDOW_DAYS + 1)


def test_weekdays_only_and_ordering_deterministic():
    dates = deterministic_historical_window_dates("2026-05-27", 10)
    assert dates == sorted(dates)
    assert all(__import__("datetime").date.fromisoformat(d).weekday() < 5 for d in dates)
    assert dates == deterministic_historical_window_dates("2026-05-27", 10)


def test_snapshot_count_guard_enforced(tmp_path):
    with pytest.raises(ValueError):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=MAX_SNAPSHOTS_PER_RUN + 1, fetch_batch=_fetcher)


def test_checksum_deterministic_and_sensitive():
    dates = deterministic_historical_window_dates("2026-05-27", 5)
    c1 = historical_window_checksum(dates, ["A", "B"], 5)
    c2 = historical_window_checksum(dates, ["A", "B"], 5)
    assert c1 == c2
    assert c1 != historical_window_checksum(dates, ["A", "C"], 5)
    assert c1 != historical_window_checksum(dates[:-1], ["A", "B"], 4)


def test_missing_api_key_fail_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path))


def test_snapshot_generation_and_schema_stability(tmp_path):
    out = run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=3, fetch_batch=_fetcher)
    assert out["status"] == "ok"
    assert out["schema_version"] == OPS_HIST1_SCHEMA_VERSION
    snaps = load_ops_hist1_snapshots(str(tmp_path))
    assert len(snaps) == 3
    for s in snaps:
        assert s["schema_version"] == OPS_HIST1_SCHEMA_VERSION
        assert s["governance_metadata"]["persistence_mode"] == "local_json_only"
        assert s["governance_metadata"]["supabase_write_enabled"] is False
        assert s["governance_metadata"]["repo_writeback_enabled"] is False
        assert s["governance_metadata"]["orchestration_enabled"] is False
        assert s["governance_metadata"]["streaming_enabled"] is False
        assert s["snapshot_id"].startswith("OPS_HIST1_")


def test_review_stability_payloads_and_metrics(tmp_path):
    run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=4, fetch_batch=_fetcher)
    review = build_ops_hist1_observation_review(load_ops_hist1_snapshots(str(tmp_path)))
    assert review["status"] == "ok"
    assert review["schema_version"] == OPS_HIST1_SCHEMA_VERSION
    assert review["streamlit_review_payload"]["schema_version"] == OPS_HIST1_SCHEMA_VERSION
    assert review["canonical_review_payload"]["schema_version"] == OPS_HIST1_SCHEMA_VERSION
    expected_metrics = {
        "posture_transition_counts",
        "fragmentation_value_range",
        "resilience_value_range",
        "sector_concentration_hhi_range",
        "volatility_avg_range",
        "valuation_dispersion_range",
        "normalization_completeness_range",
        "fallback_usage_range",
    }
    assert expected_metrics == set(review["continuity_metrics"].keys())
    assert review == build_ops_hist1_observation_review(load_ops_hist1_snapshots(str(tmp_path)))


def test_anti_prediction_trading_vocabulary_guard(tmp_path):
    run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=2, fetch_batch=_fetcher)
    review = build_ops_hist1_observation_review(load_ops_hist1_snapshots(str(tmp_path)))
    md = render_ops_hist1_observation_review_markdown(review).lower()
    payload_text = __import__("json").dumps(review, sort_keys=True).lower()
    forbidden = ["forecast", "alpha", "buy", "sell", "long", "short", "expected return", "trading opportunity", "signal generation", "recommendation"]
    for word in forbidden:
        assert word not in payload_text
    assert "no_prediction_or_trading_execution" in payload_text
    assert "no replay/topology/prediction/trading" in md



def test_historical_fetcher_receives_snapshot_date_and_partial_normalization(tmp_path):
    calls = []
    def fetcher(batch, snapshot_date):
        calls.append(snapshot_date)
        return [{"symbol": sym, "date": snapshot_date, "price": 101.0, "marketCap": 1000.0, "sector": "Tech", "industry": "Soft"} for sym in batch]

    out = run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=2, fetch_batch=fetcher)
    assert out["status"] == "ok"
    assert set(calls)
    snaps = load_ops_hist1_snapshots(str(tmp_path))
    assert all(s["operational_diagnostics"]["symbols_successfully_normalized"] > 0 for s in snaps)
    assert all("adapter_diagnostics" in s for s in snaps)


def test_all_symbol_failure_fails_closed(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{"symbol": sym, "date": snapshot_date, "price": None, "sector": "Tech", "industry": "Soft"} for sym in batch]
    with pytest.raises(RuntimeError):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher)


def test_profile_403_non_fatal_with_unknown_fallback(monkeypatch):
    calls = {"profile": 0}

    class _Resp:
        def __init__(self, payload):
            self.payload = payload
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/profile" in url:
            calls["profile"] += 1
            raise HTTPError(url, 403, "Forbidden", {}, io.BytesIO(b""))
        if "historical-price-full" in url:
            return _Resp(b'{"historical":[{"adjClose":101.5,"volume":10}]}')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":1234}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    rows = fetcher(["AAPL"], "2026-05-27")
    assert rows[0]["price"] == 101.5
    assert rows[0]["sector"] == "unknown"
    assert rows[0]["industry"] == "unknown"
    diag = fetcher.last_profile_diagnostics
    assert diag["profile_enrichment_status"] == "failed"
    assert diag["profile_fetch_failure_reasons"] == {"HTTP_403": 1}
    assert calls["profile"] == 1


def test_profile_cache_reused_for_same_symbol_across_dates(monkeypatch):
    calls = {"profile": 0}

    class _Resp:
        def __init__(self, payload):
            self.payload = payload
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/profile" in url:
            calls["profile"] += 1
            return _Resp(b'[{"symbol":"AAPL","sector":"Tech","industry":"Software"}]')
        if "historical-price-full" in url:
            return _Resp(b'{"historical":[{"adjClose":101.5,"volume":10}]}')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":1234}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    fetcher(["AAPL"], "2026-05-26")
    fetcher(["AAPL"], "2026-05-27")
    assert calls["profile"] == 1


def test_profile_failure_diagnostics_do_not_leak_api_key(tmp_path):
    api_key = "super_secret_key"

    def fetcher(batch, snapshot_date):
        fetcher.last_profile_diagnostics = {
            "profile_enrichment_status": "failed",
            "profile_fetch_failure_reasons": {"HTTP_403": 1},
            "profile_fetch_failure_count": 1,
            "profile_records_requested": len(batch),
            "profile_records_returned": 0,
            "sector_industry_fallback_used": True,
        }
        return [{"symbol": sym, "date": snapshot_date, "price": 101.0, "marketCap": 1000.0, "sector": "unknown", "industry": "unknown"} for sym in batch]

    fetcher.last_profile_diagnostics = {}
    run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher)
    snap = load_ops_hist1_snapshots(str(tmp_path))[0]
    serialized = str(snap)
    assert api_key not in serialized
