import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    FMP_LEGACY_QUOTE_ENDPOINT,
    FMP_STABLE_BATCH_QUOTE_ENDPOINT,
    GOVERNANCE_BOUNDARIES,
    OPS_LIVE1B_UNIVERSE_CAP,
    build_live_fmp_fetcher,
    get_ops_live1b_controlled_universe,
    run_ops_live1b_controlled_50_symbol_operational_ingest,
)


class _MockFmpResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def _mock_rows(symbols):
    rows = []
    for i, symbol in enumerate(symbols):
        rows.append({
            "symbol": symbol,
            "price": 100 + i,
            "marketCap": 2_000_000 + i,
            "sector": "Tech",
            "industry": "Software",
            "beta": 1.0,
            "pe": 20.0,
            "roe": 0.2,
            "debtToEquity": 0.4,
            "dispersion": 0.3,
        })
    return rows


def _stable_symbols_from_url(url):
    return parse_qs(urlparse(url).query).get("symbols", [""])[0].split(",")


def _fetcher(batch):
    out = []
    for i, s in enumerate(batch):
        out.append({
            "symbol": s,
            "price": 100 + i,
            "marketCap": 2_000_000 + i,
            "sector": "Tech" if i % 2 == 0 else "Finance",
            "industry": "Software" if i % 2 == 0 else "Banking",
            "beta": 1.0,
            "pe": 20.0,
            "roe": 0.2,
            "debtToEquity": 0.4,
            "dispersion": 0.3,
        })
    return out


def test_universe_cap_ordering_and_checksum(tmp_path):
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=_fetcher)
    universe = out["universe"]
    assert len(universe) == OPS_LIVE1B_UNIVERSE_CAP
    assert universe == sorted(universe)
    assert out["universe_metadata"]["universe_checksum"]


def test_missing_api_key_fail_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        run_ops_live1b_controlled_50_symbol_operational_ingest(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"))


def test_invalid_values_fail_closed(tmp_path):
    def bad_fetcher(batch):
        return [{"symbol": s, "price": float("nan"), "marketCap": -1, "sector": "Tech", "industry": "Software"} for s in batch]

    out = run_ops_live1b_controlled_50_symbol_operational_ingest(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=bad_fetcher)
    assert out["status"] == "failed_closed"


def test_payload_stability_and_snapshot_consistency(tmp_path):
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=_fetcher)
    payload = out["ops_live1b_payload"]
    assert payload["supabase_write_enabled"] is False
    assert payload["scheduling_enabled"] is False
    assert payload["orchestration_enabled"] is False
    assert payload["streaming_enabled"] is False
    sid = out["snapshot_identity"]["snapshot_id"]
    assert sid == payload["snapshot_id"]
    for key in ("streamlit_summary_cards", "streamlit_sector_summary", "streamlit_pressure_table", "streamlit_resilience_table", "streamlit_fragmentation_table", "streamlit_continuity_panel", "streamlit_integrity_panel", "streamlit_governance_panel", "streamlit_snapshot_metadata"):
        assert key in payload["streamlit_payloads"]
    for key in ("snapshot_metadata_rows", "symbol_snapshot_rows", "sector_summary_rows", "pressure_rows", "resilience_rows", "fragmentation_rows", "continuity_rows", "integrity_rows", "governance_rows", "compression_rows"):
        assert key in payload["canonical_tables"]
    assert payload["governance_boundaries"] == GOVERNANCE_BOUNDARIES


def test_governance_and_continuity_safe_structure(tmp_path):
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=_fetcher)
    row = out["ops_live1b_payload"]["canonical_tables"]["snapshot_metadata_rows"][0]
    assert row["observation_mode"] == "controlled_operational_observation"
    assert get_ops_live1b_controlled_universe() == sorted(get_ops_live1b_controlled_universe())


def _ops_live1b_diag(out):
    return out["ingestion_boundary_diagnostics"]


def test_ingestion_boundary_diagnostics_empty_payload(tmp_path):
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=lambda _batch: [],
    )

    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "failed_closed"
    assert diagnostics["fetch_status"] == "ok"
    assert diagnostics["failure_stage"] == "empty_fmp_payload"
    assert diagnostics["raw_row_count"] == 0
    assert diagnostics["accepted_row_count"] == 0
    assert diagnostics["rejected_row_count"] == 0
    assert diagnostics["sample_response_keys"] == []
    assert diagnostics["exception_type"] == ""
    assert diagnostics["exception_message"] == ""
    assert out["ops_live1b_payload"]["diagnostics"]["ingestion_boundary_diagnostics"] == diagnostics


def test_ingestion_boundary_diagnostics_invalid_payload_shape(tmp_path):
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=lambda _batch: {"Error Message": "entitlement required", "apikey": "should_not_be_persisted"},
    )

    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "failed_closed"
    assert diagnostics["fetch_status"] == "failed"
    assert diagnostics["failure_stage"] == "invalid_payload_shape"
    assert diagnostics["response_type"] == "dict"
    assert diagnostics["raw_row_count"] == 0
    assert diagnostics["accepted_row_count"] == 0
    assert diagnostics["sample_response_keys"] == ["Error Message", "apikey"]
    assert diagnostics["exception_type"] == "InvalidFmpPayloadShape"
    assert "should_not_be_persisted" not in diagnostics["exception_message"]


def test_ingestion_boundary_diagnostics_fetch_exception(tmp_path):
    def failing_fetcher(_batch):
        raise RuntimeError("provider unavailable apikey=secret-token&symbol=AAPL")

    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=failing_fetcher,
    )

    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "failed_closed"
    assert diagnostics["fetch_status"] == "failed"
    assert diagnostics["failure_stage"] == "fetch_failed"
    assert diagnostics["raw_row_count"] == 0
    assert diagnostics["accepted_row_count"] == 0
    assert diagnostics["exception_type"] == "RuntimeError"
    assert diagnostics["exception_message"] == "provider unavailable apikey=[REDACTED]&symbol=AAPL"


def test_ingestion_boundary_diagnostics_all_rows_rejected_by_symbol_filter(tmp_path):
    def rejected_fetcher(batch):
        return [
            {
                "symbol": f"NOT_{i}",
                "price": 100 + i,
                "marketCap": 2_000_000 + i,
                "sector": "Other",
                "industry": "Other",
            }
            for i, _ in enumerate(batch)
        ]

    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=rejected_fetcher,
    )

    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "failed_closed"
    assert diagnostics["fetch_status"] == "ok"
    assert diagnostics["failure_stage"] == "all_rows_rejected_by_symbol_filter"
    assert diagnostics["raw_row_count"] == OPS_LIVE1B_UNIVERSE_CAP
    assert diagnostics["accepted_row_count"] == 0
    assert diagnostics["rejected_row_count"] == OPS_LIVE1B_UNIVERSE_CAP
    assert diagnostics["dropped_due_to_batch_filter_count"] == OPS_LIVE1B_UNIVERSE_CAP
    assert diagnostics["sample_response_keys"] == ["industry", "marketCap", "price", "sector", "symbol"]
    assert diagnostics["rejected_row_reasons"] == [
        {"symbol": f"NOT_{i}", "rejection_reason": "symbol_not_in_canonicalized_batch"}
        for i in range(25)
    ]


def test_ingestion_boundary_diagnostics_successful_payload(tmp_path):
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=_fetcher,
    )

    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "ok"
    assert diagnostics["fetch_status"] == "ok"
    assert diagnostics["failure_stage"] == "success"
    assert diagnostics["response_type"] == "list"
    assert diagnostics["raw_row_count"] == OPS_LIVE1B_UNIVERSE_CAP
    assert diagnostics["accepted_row_count"] == OPS_LIVE1B_UNIVERSE_CAP
    assert diagnostics["rejected_row_count"] == 0
    assert diagnostics["sample_response_keys"] == [
        "beta",
        "debtToEquity",
        "dispersion",
        "industry",
        "marketCap",
        "pe",
        "price",
        "roe",
        "sector",
        "symbol",
    ]
    assert diagnostics["exception_type"] == ""
    assert diagnostics["exception_message"] == ""


def test_live_fmp_fetcher_falls_back_from_legacy_403_to_stable_success(tmp_path):
    urls = []

    def urlopen_fn(url, timeout):
        urls.append(url)
        if "/api/v3/quote/" in url:
            raise HTTPError(url, 403, "Forbidden", None, None)
        assert "/stable/batch-quote" in url
        return _MockFmpResponse(_mock_rows(_stable_symbols_from_url(url)))

    fetcher = build_live_fmp_fetcher("secret-key", urlopen_fn=urlopen_fn)
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=fetcher,
    )

    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "ok"
    assert diagnostics["failure_stage"] == "success"
    assert diagnostics["endpoint_strategy"] == "legacy_quote_then_stable_batch_quote"
    assert diagnostics["endpoint_attempts"] == [
        {
            "endpoint": FMP_LEGACY_QUOTE_ENDPOINT,
            "status": "failed",
            "failure_class": "http_403",
            "exception_type": "HTTPError",
            "exception_message": "HTTP Error 403: Forbidden",
        },
        {"endpoint": FMP_STABLE_BATCH_QUOTE_ENDPOINT, "status": "ok"},
    ]
    assert "/api/v3/quote/" in urls[0]
    assert "/stable/batch-quote" in urls[1]


def test_live_fmp_fetcher_both_endpoints_fail_closed_with_sanitized_diagnostics(tmp_path):
    def urlopen_fn(url, timeout):
        raise HTTPError(f"{url}&apikey=secret-key", 403, "Forbidden", None, None)

    fetcher = build_live_fmp_fetcher("secret-key", urlopen_fn=urlopen_fn)
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=fetcher,
    )

    serialized = json.dumps(out, sort_keys=True)
    diagnostics = _ops_live1b_diag(out)
    assert out["status"] == "failed_closed"
    assert diagnostics["fetch_status"] == "failed"
    assert diagnostics["failure_stage"] == "fetch_failed"
    assert diagnostics["exception_type"] == "LiveFmpFetchError"
    assert diagnostics["endpoint_attempts"] == [
        {
            "endpoint": FMP_LEGACY_QUOTE_ENDPOINT,
            "status": "failed",
            "failure_class": "http_403",
            "exception_type": "HTTPError",
            "exception_message": "HTTP Error 403: Forbidden",
        },
        {
            "endpoint": FMP_STABLE_BATCH_QUOTE_ENDPOINT,
            "status": "failed",
            "failure_class": "http_403",
            "exception_type": "HTTPError",
            "exception_message": "HTTP Error 403: Forbidden",
        },
    ]
    assert "secret-key" not in serialized
    assert "apikey=" not in serialized
    assert "financialmodelingprep.com" not in serialized


def test_live_fmp_fetcher_stable_endpoint_returns_list_rows():
    def urlopen_fn(url, timeout):
        if "/api/v3/quote/" in url:
            raise HTTPError(url, 403, "Forbidden", None, None)
        return _MockFmpResponse(_mock_rows(_stable_symbols_from_url(url)))

    fetcher = build_live_fmp_fetcher("secret-key", urlopen_fn=urlopen_fn)
    rows = fetcher(["AAPL", "MSFT"])

    assert [row["symbol"] for row in rows] == ["AAPL", "MSFT"]
    assert fetcher.last_endpoint_attempts == [
        {
            "endpoint": FMP_LEGACY_QUOTE_ENDPOINT,
            "status": "failed",
            "failure_class": "http_403",
            "exception_type": "HTTPError",
            "exception_message": "HTTP Error 403: Forbidden",
        },
        {"endpoint": FMP_STABLE_BATCH_QUOTE_ENDPOINT, "status": "ok"},
    ]


def test_live_fmp_fetcher_does_not_persist_api_key_in_endpoint_diagnostics(tmp_path):
    def urlopen_fn(url, timeout):
        raise RuntimeError(f"blocked url={url}")

    fetcher = build_live_fmp_fetcher("secret-key", urlopen_fn=urlopen_fn)
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(
        snapshot_date="2026-05-27",
        output_path=str(tmp_path / "out.json"),
        fetch_batch=fetcher,
    )

    serialized = json.dumps(out, sort_keys=True)
    assert out["status"] == "failed_closed"
    assert "secret-key" not in serialized
    assert "apikey=" not in serialized
    assert "financialmodelingprep.com" not in serialized
    assert "[REDACTED_URL]" in serialized
