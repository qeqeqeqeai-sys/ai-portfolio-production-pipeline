import io
import contextlib
from urllib.parse import parse_qs, urlparse
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
    _build_fmp_url,
    FMP_STABLE_HISTORICAL_PRICE_URL,
)


def test_build_fmp_url_for_stable_historical_price_shape():
    url = _build_fmp_url(
        FMP_STABLE_HISTORICAL_PRICE_URL,
        {"symbol": "AAPL", "from": "2026-05-27", "to": "2026-05-27", "apikey": "abc"},
    )
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    assert "stable/historical-price-eod/full" in url
    assert qs["symbol"] == ["AAPL"]
    assert qs["from"] == ["2026-05-27"]
    assert qs["to"] == ["2026-05-27"]
    assert qs["apikey"] == ["abc"]
    assert "?hp_d" not in url


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
        if "stable/historical-price-eod/full" in url:
            return _Resp(b'[{"date":"2026-05-27","adjClose":101.5,"volume":10}]')
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
        if "stable/historical-price-eod/full" in url:
            return _Resp(b'{"historical":[{"date":"2026-05-26","adjClose":101.5,"volume":10}]}')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":1234}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    fetcher(["AAPL"], "2026-05-26")
    rows = fetcher(["AAPL"], "2026-05-27")
    assert rows[0]["price"] == 101.5
    assert calls["profile"] == 1


def test_historical_price_single_symbol_403_all_fail_closed(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/historical-price-eod/full" in url:
            raise HTTPError(url, 403, "Forbidden", {}, io.BytesIO(b""))
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":1234}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Software"}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    with pytest.raises(RuntimeError):
        fetcher(["AAPL"], "2026-05-27")


def test_endpoint_fallback_full_to_light(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/historical-price-eod/full" in url:
            raise HTTPError(url, 403, "Forbidden", {}, io.BytesIO(b""))
        if "stable/historical-price-eod/light" in url:
            return _Resp(b'[{"date":"2026-05-27","close":111.0}]')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":1234}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Software"}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    rows = fetcher(["AAPL"], "2026-05-27")


def test_bounded_failure_samples_ordered_and_sanitized(tmp_path, monkeypatch):
    def fetcher(batch, snapshot_date):
        fetcher.last_profile_diagnostics = {
            "historical_price_symbol_diagnostics": [
                {"symbol": s, "endpoint_attempts": [
                    {"endpoint_family": "ep1", "failure_reason": "HTTP_500", "http_status": "HTTP_500", "record_count_returned": 0},
                    {"endpoint_family": "ep2", "failure_reason": "zero_records_returned", "http_status": "ok", "record_count_returned": 0},
                ]} for s in batch
            ]
        }
        return [{"symbol": s, "price": 100.0, "marketCap": 10.0, "sector": "T", "industry": "S", "beta": 1.0, "pe": 10.0, "roe": 0.2, "debtToEquity": 0.1, "dispersion": 0.3} for s in batch]
    out = run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, symbol_universe_override=[f"S{i:03d}" for i in range(40)], fetch_batch=fetcher, telemetry_max_samples=10)
    t = out["telemetry_summary"]
    assert t["missing_record_sample_count"] == 10
    assert t["endpoint_failure_sample_count"] == 10
    assert t["missing_record_samples"] == sorted(t["missing_record_samples"], key=lambda s: (s["requested_snapshot_date"], s["symbol"]))
    assert t["endpoint_failure_samples"] == sorted(t["endpoint_failure_samples"], key=lambda s: (s["requested_snapshot_date"], s["symbol"], s["endpoint_name"], s["attempt_index"]))
    blob = __import__("json").dumps(t).lower()
    assert "apikey" not in blob and "https://" not in blob and "historical\":" not in blob
    snap = __import__("json").loads((tmp_path / "ops_hist1_2026-05-27.json").read_text(encoding="utf-8"))
    for k in ("missing_record_samples", "endpoint_failure_samples", "affected_symbol_count", "affected_date_count", "top_failure_reasons"):
        assert k in snap
    assert len(snap["missing_record_samples"]) <= 10
    assert len(snap["endpoint_failure_samples"]) <= 10


def test_response_shape_data_and_reconciliation(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/historical-price-eod/full" in url:
            return _Resp(b'{"data":[{"date":"2026-05-26","adjClose":109.0}]}')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":1234}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Software"}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    rows = fetcher(["AAPL"], "2026-05-27")
    assert rows[0]["price"] == 109.0
    attempt = fetcher.last_profile_diagnostics["historical_price_symbol_diagnostics"][0]["endpoint_attempts"][0]
    assert attempt["date_reconciliation_used"] is True
    assert attempt["date_reconciliation_distance_days"] == 1


def test_market_cap_exact_match_reconciliation(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/historical-price-eod/full" in url:
            return _Resp(b'[{"date":"2026-05-27","adjClose":109.0}]')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"date":"2026-05-27","marketCap":2000},{"date":"2026-05-26","marketCap":1000}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Software"}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    row = build_historical_fmp_fetcher("test_key")(["AAPL"], "2026-05-27")[0]
    assert row["marketCap"] == 2000
    assert row["market_cap_exact_match_found"] is True
    assert row["market_cap_missing_after_reconciliation"] is False


def test_market_cap_nearest_prior_within_5_days_reconciliation(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/historical-price-eod/full" in url:
            return _Resp(b'[{"date":"2026-05-27","adjClose":109.0}]')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"date":"2026-05-25","marketCap":1500}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Software"}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    row = build_historical_fmp_fetcher("test_key")(["AAPL"], "2026-05-27")[0]
    assert row["marketCap"] == 1500
    assert row["market_cap_exact_match_found"] is False
    assert row["market_cap_reconciled_prior_date"] == "2026-05-25"
    assert row["market_cap_reconciliation_distance_days"] == 2
    assert row["market_cap_missing_after_reconciliation"] is False


def test_market_cap_reconciliation_debug_sample_emitted(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload

    def fake_urlopen(url, timeout=20):
        if "stable/historical-price-eod/full" in url:
            return _Resp(b'[{"date":"2026-05-27","adjClose":109.0}]')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"date":"2026-05-26","marketCap":1500}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Software"}]')
        raise AssertionError(url)

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    _ = fetcher(["AAPL"], "2026-05-27")
    samples = fetcher.last_profile_diagnostics["market_cap_reconciliation_debug_samples"]
    assert samples[0]["symbol"] == "AAPL"
    assert samples[0]["selected_market_cap_date"] == "2026-05-26"
    assert samples[0]["reconciled_market_cap_value"] == 1500


def test_market_cap_missing_outside_window_preserves_fail_closed(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{
            "symbol": s,
            "date": snapshot_date,
            "price": 101.0,
            "marketCap": None,
            "sector": "Tech",
            "industry": "Soft",
            "market_cap_missing_after_reconciliation": True,
        } for s in batch]

    with pytest.raises(RuntimeError, match="class=downstream_preflight_schema_mismatch"):
        run_ops_hist1_historical_backfill(
            snapshot_date="2026-05-27",
            output_dir=str(tmp_path),
            window_days=1,
            fetch_batch=fetcher,
            symbol_universe_override=["AAPL"],
        )


def test_bounded_snapshot_telemetry_interval_and_no_secret_leak(tmp_path):
    calls = []
    def fetcher(batch, snapshot_date):
        calls.append(snapshot_date)
        return [{"symbol": sym, "date": snapshot_date, "price": 101.0, "marketCap": 1000.0, "sector": "Tech", "industry": "Soft"} for sym in batch]

    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        out = run_ops_hist1_historical_backfill(
            snapshot_date="2026-05-27",
            output_dir=str(tmp_path),
            window_days=6,
            fetch_batch=fetcher,
            progress_interval=5,
        )
    text = capture.getvalue()
    assert out["status"] == "ok"
    assert text.count("[OPS-HIST-1]") >= 2
    assert "snapshot=5/6" in text
    assert "snapshot=6/6" in text
    assert "estimated_remaining_minutes=" in text
    assert "[OPS-HIST-1][historical_price]" in text
    assert "apikey" not in text.lower()
    assert len(text) < 20000


def test_runtime_error_contains_bounded_summary(monkeypatch):
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload
    def fake_urlopen(url, timeout=20):
        if "historical-price" in url:
            return _Resp(b'{"foo":"bar"}')
        if "historical-market-capitalization" in url:
            return _Resp(b'[]')
        if "stable/profile" in url:
            return _Resp(b'[]')
        raise AssertionError(url)
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    with pytest.raises(RuntimeError) as exc:
        fetcher(["AAPL"], "2026-05-27")
    msg = str(exc.value)
    assert "endpoint_status_counts=" in msg and "top_failure_reasons=" in msg
    assert "test_key" not in msg


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


def test_historical_fetcher_retries_are_bounded(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(url, timeout=20):
        calls["count"] += 1
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    with pytest.raises(RuntimeError) as exc:
        fetcher(["AAPL"], "2026-05-27")
    msg = str(exc.value)
    assert "request retries exhausted" in msg
    assert "attempts=3" in msg
    assert "timeout_seconds=20" in msg
    assert calls["count"] == 3


def test_snapshot_heartbeat_and_stuck_diagnostics_bounded(tmp_path, monkeypatch):
    monotonic_values = iter([0.0, 0.0, 61.0, 130.0, 150.0, 151.0, 152.0, 153.0, 154.0, 155.0])
    monkeypatch.setattr(
        "transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.time.monotonic",
        lambda: next(monotonic_values),
    )

    def fetcher(batch, snapshot_date, progress_callback=None):
        if progress_callback:
            progress_callback(1, str(batch[0]), "stable_historical_price_eod_full")
            progress_callback(2, str(batch[1]), "stable_historical_price_eod_full")
        return [{"symbol": sym, "date": snapshot_date, "price": 101.0, "marketCap": 1000.0, "sector": "Tech", "industry": "Soft"} for sym in batch]

    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        out = run_ops_hist1_historical_backfill(
            snapshot_date="2026-05-27",
            output_dir=str(tmp_path),
            window_days=1,
            fetch_batch=fetcher,
            progress_interval=1,
        )
    text = capture.getvalue()
    assert out["status"] == "ok"
    assert "snapshot_heartbeat=True" in text
    assert "snapshot_index=1/1" in text
    assert "snapshot_date=2026-05-27" in text
    assert "current_symbol_index=1/50" in text
    assert "elapsed_seconds_in_snapshot=61" in text
    assert "endpoint_family=stable_historical_price_eod_full" in text

def test_cached_rows_preferred_over_fmp_calls(monkeypatch):
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_ENABLED", "true")
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_WRITE_ENABLED", "false")
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.read_cached_historical_prices", lambda symbols, dates: ([{"symbol":"AAPL","price_date":"2026-05-27","adj_close":123.0,"source":"fmp"}], 0))
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.write_raw_historical_prices", lambda rows: (0,0))

    fetcher = build_historical_fmp_fetcher("test_key")
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no fmp price call expected")) if "historical-price" in str(a[0]) else type("R", (), {"__enter__":lambda s:s, "__exit__":lambda *x:False, "read":lambda s:b'[{"marketCap":1}]' if "market-cap" in str(a[0]) else b'[{"sector":"Tech","industry":"Soft"}]'})())
    rows = fetcher(["AAPL"], "2026-05-27")
    assert rows[0]["price"] == 123.0
    assert fetcher.last_profile_diagnostics["cache_hits"] == 1


def test_cache_only_validation_uses_cached_rows_without_any_fmp_calls(monkeypatch):
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_ENABLED", "true")
    monkeypatch.setenv("OPS_HIST_CACHE_ONLY_VALIDATION", "true")
    monkeypatch.setattr(
        "transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.read_cached_historical_prices",
        lambda symbols, dates: ([{"symbol": str(s).upper(), "price_date": dates[0], "close": 123.0, "adj_close": None, "source": "fmp"} for s in symbols], 0),
    )
    monkeypatch.setattr(
        "transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no FMP calls expected in cache-only validation mode")),
    )
    fetcher = build_historical_fmp_fetcher("test_key")
    rows = fetcher(["AAPL"], "2026-05-28")
    assert rows[0]["price"] == 123.0
    assert fetcher.last_profile_diagnostics["cache_hits"] == 1
    assert fetcher.last_profile_diagnostics["cache_misses"] == 0


def test_cache_write_only_when_enabled(monkeypatch):
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_ENABLED", "true")
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_WRITE_ENABLED", "true")
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.read_cached_historical_prices", lambda symbols, dates: ([], 0))
    called = {"n": 0}
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.raw_cache_write_readiness", lambda: {"ready": True, "reason": "ok"})
    monkeypatch.setattr(
        "transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.summarize_write_result",
        lambda rows: {"write_attempted_rows": called.__setitem__("n", len(rows)) or len(rows), "write_success_rows": len(rows), "write_failed_rows": 0, "write_status": "confirmed", "write_confirmation_limited": False, "error_reason_counts": {}},
    )
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload
    def fake_urlopen(url, timeout=20):
        if "historical-price" in url:
            return _Resp(b'[{"date":"2026-05-27","adjClose":111.0,"volume":1}]')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":123}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Soft"}]')
        raise AssertionError(url)
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    fetcher(["AAPL"], "2026-05-27")
    assert called["n"] >= 1
    assert fetcher.last_profile_diagnostics["cache_rows_written"] >= 1


def test_cache_write_enabled_misses_and_fetched_rows_must_attempt_write(monkeypatch):
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_ENABLED", "true")
    monkeypatch.setenv("OPS_HIST_RAW_CACHE_WRITE_ENABLED", "true")
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.read_cached_historical_prices", lambda symbols, dates: ([], 0))
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.raw_cache_write_readiness", lambda: {"ready": True, "reason": "ok"})
    monkeypatch.setattr(
        "transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.summarize_write_result",
        lambda rows: {"write_attempted_rows": 0, "write_success_rows": 0, "write_failed_rows": 0, "write_status": "disabled", "write_confirmation_limited": False, "error_reason_counts": {}},
    )
    class _Resp:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.payload
    def fake_urlopen(url, timeout=20):
        if "historical-price" in url:
            return _Resp(b'[{"date":"2026-05-27","adjClose":111.0,"volume":1}]')
        if "historical-market-capitalization" in url:
            return _Resp(b'[{"marketCap":123}]')
        if "stable/profile" in url:
            return _Resp(b'[{"sector":"Tech","industry":"Soft"}]')
        raise AssertionError(url)
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.urlopen", fake_urlopen)
    fetcher = build_historical_fmp_fetcher("test_key")
    with pytest.raises(RuntimeError, match="no write attempts were made"):
        fetcher(["AAPL"], "2026-05-27")


def test_mixed_valid_invalid_symbol_batch_isolated_and_preserved(tmp_path):
    def fetcher(batch, snapshot_date):
        out = []
        for sym in batch:
            if sym == "BAD":
                out.append({"symbol": sym, "date": snapshot_date, "price": "NaNxx", "marketCap": 1000, "sector": "Tech", "industry": "Soft"})
            else:
                out.append({"symbol": sym, "date": snapshot_date, "price": 101.0, "marketCap": 1000, "sector": "Tech", "industry": "Soft"})
        return out
    out = run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL", "BAD", "MSFT"])
    snap = load_ops_hist1_snapshots(str(tmp_path))[0]
    assert out["status"] == "ok"
    assert snap["adapter_diagnostics"]["preserved_normalized_symbol_count"] == 2
    assert snap["adapter_diagnostics"]["isolated_failed_symbol_count"] == 1
    assert "malformed_numeric_conversion" in snap["adapter_diagnostics"]["normalization_failure_reason_counts"]


def test_empty_endpoint_payload_fail_closed(tmp_path):
    def fetcher(_batch, _snapshot_date):
        return []
    with pytest.raises(RuntimeError):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL", "MSFT"])


def test_safe_ratio_breach_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_HIST1_MINIMUM_SAFE_RATIO", "0.8")
    def fetcher(batch, snapshot_date):
        return [{"symbol": batch[0], "date": snapshot_date, "price": 101.0, "marketCap": 1000, "sector": "Tech", "industry": "Soft"}]
    with pytest.raises(RuntimeError):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL", "MSFT", "NVDA"])


def test_stage_telemetry_lifecycle_fields_present(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{"symbol": s, "date": snapshot_date, "price": 100.0, "marketCap": 1, "sector": "Tech", "industry": "Soft"} for s in batch]
    run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL", "MSFT"])
    snap = load_ops_hist1_snapshots(str(tmp_path))[0]
    diag = snap["adapter_diagnostics"]
    assert diag["fetched_row_count"] == 2
    assert diag["pre_normalization_row_count"] == 2
    assert diag["reconciliation_retained_row_count"] == 2
    assert diag["normalization_retained_row_count"] == 2
    assert diag["final_preserved_symbol_count"] == 2


def test_empty_provider_payload_classified(tmp_path):
    def fetcher(_batch, _snapshot_date):
        return []
    with pytest.raises(RuntimeError, match="class=provider_empty_response"):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL"])


def test_unavailable_trading_day_classified(tmp_path):
    def fetcher(_batch, _snapshot_date):
        return []
    fetcher.last_profile_diagnostics = {
        "historical_price_symbol_diagnostics": [
            {"symbol": "AAPL", "endpoint_attempts": [{"failure_reason": "missing_reconciled_historical_date"}]}
        ]
    }
    with pytest.raises(RuntimeError, match="class=unavailable_trading_day"):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL"])


def test_all_rows_filtered_pre_normalization_classified(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{"symbol": s, "date": snapshot_date, "price": None, "marketCap": 1, "sector": "Tech", "industry": "Soft"} for s in batch]
    with pytest.raises(RuntimeError, match="class=all_symbols_filtered_pre_normalization"):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL", "MSFT"])


def test_downstream_preflight_schema_mismatch_fail_closed(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{"symbol": s, "date": snapshot_date, "price": 101.0, "marketCap": 1, "sector": "", "industry": ""} for s in batch]
    with pytest.raises(RuntimeError, match="class=downstream_preflight_schema_mismatch"):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL", "MSFT"])


def test_downstream_preflight_accepts_single_market_cap_alias_boundary(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{"symbol": s, "date": snapshot_date, "price": 101.0, "market_cap": 1, "sector": "Tech", "industry": "Soft"} for s in batch]

    run_ops_hist1_historical_backfill(
        snapshot_date="2026-05-27",
        output_dir=str(tmp_path),
        window_days=1,
        fetch_batch=fetcher,
        symbol_universe_override=["AAPL"],
    )
    snap = load_ops_hist1_snapshots(str(tmp_path))[0]
    assert snap["adapter_diagnostics"]["downstream_preflight_failure_reason_counts"] == {}


def test_downstream_ingestion_contract_mismatch_classified(tmp_path, monkeypatch):
    def fetcher(batch, snapshot_date):
        return [{"symbol": s, "date": snapshot_date, "price": 101.0, "marketCap": 1, "sector": "Tech", "industry": "Soft"} for s in batch]

    def fake_ingest(*_args, **_kwargs):
        return {"rows": [], "snapshot_ts": "2026-05-27T00:00:00Z", "snapshot_identity": {}, "status": "failed_closed"}

    monkeypatch.setattr(
        "transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation.ingest_controlled_daily_snapshot",
        fake_ingest,
    )
    with pytest.raises(RuntimeError, match="class=downstream_ingestion_normalization_contract_mismatch"):
        run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL"])


def test_governance_metadata_regression_preserved(tmp_path):
    def fetcher(batch, snapshot_date):
        return [{"symbol": s, "date": snapshot_date, "price": 100.0, "marketCap": 1, "sector": "Tech", "industry": "Soft"} for s in batch]

    run_ops_hist1_historical_backfill(snapshot_date="2026-05-27", output_dir=str(tmp_path), window_days=1, fetch_batch=fetcher, symbol_universe_override=["AAPL"])
    snap = load_ops_hist1_snapshots(str(tmp_path))[0]
    metadata = snap["governance_metadata"]
    assert metadata["supabase_write_enabled"] is False
    assert metadata["orchestration_enabled"] is False
    assert metadata["no_topology_activation"] is True
    assert metadata["no_prediction_or_trading_execution"] is True
    assert metadata["persistence_mode"] == "local_json_only"
