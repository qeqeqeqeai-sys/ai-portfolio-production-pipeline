from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    GOVERNANCE_BOUNDARIES,
    MAX_CONTINUITY_WINDOW_DAYS,
    MAX_DASHBOARD_PAYLOAD_ROWS,
    MAX_INGESTION_BATCH_SIZE,
    MAX_SNAPSHOT_ROWS,
    MAX_STRUCTURAL_SUMMARY_ITEMS,
    accumulate_longitudinal_continuity,
    build_normalized_operational_surfaces,
    build_operator_payloads,
    fetch_controlled_fmp_snapshot_batch,
    ingest_controlled_daily_snapshot,
)


def _symbols(n: int) -> list[str]:
    return [f"S{i:03d}" for i in range(1, n + 1)]


def _fetcher_ok(batch):
    for idx, s in enumerate(batch):
        yield {
            "symbol": s,
            "price": 100 + idx,
            "marketCap": 1_000_000 + idx,
            "sector": "Tech",
            "industry": "Software",
            "beta": 1.2,
            "pe": 22.0,
            "roe": 0.18,
            "debtToEquity": 0.4,
            "dispersion": 0.3,
        }


def test_deterministic_ingestion_behavior_and_bounds():
    symbols = _symbols(300)
    a = ingest_controlled_daily_snapshot(symbols, "2026-05-27", _fetcher_ok)
    b = ingest_controlled_daily_snapshot(symbols, "2026-05-27", _fetcher_ok)
    assert a == b
    assert a["status"] == "ok"
    assert a["batches"] == 6
    assert len(a["rows"]) <= MAX_SNAPSHOT_ROWS
    assert len(a["operator_payload"]["dominant_structural_pressures"]) <= MAX_STRUCTURAL_SUMMARY_ITEMS


def test_fail_closed_and_lightweight_retry():
    calls = {"n": 0}

    def flaky(batch):
        calls["n"] += 1
        raise RuntimeError("fail")

    out = ingest_controlled_daily_snapshot(_symbols(30), "2026-05-27", flaky)
    assert out["status"] == "failed_closed"
    assert calls["n"] == 2


def test_normalization_and_payload_stability():
    rows = list(_fetcher_ok(_symbols(40)))
    normalized = [
        {
            "symbol": r["symbol"],
            "snapshot_ts": "2026-05-27T00:00:00Z",
            "price_state": r["price"],
            "market_cap": r["marketCap"],
            "sector": r["sector"],
            "subsector": r["industry"],
            "volatility_structure": r["beta"],
            "valuation_structure": r["pe"],
            "profitability_structure": r["roe"],
            "leverage_liquidity_structure": r["debtToEquity"],
            "breadth_dispersion_structure": r["dispersion"],
            "ecosystem_continuity_ts": "2026-05-27T00:00:00Z",
        }
        for r in rows
    ]
    s1 = build_normalized_operational_surfaces(normalized, "2026-05-27T00:00:00Z")
    s2 = build_normalized_operational_surfaces(normalized, "2026-05-27T00:00:00Z")
    assert s1 == s2
    p = build_operator_payloads(s1)
    assert p["normalization_observations"]["bounded"] is True
    assert p["normalization_observations"]["row_count"] <= MAX_DASHBOARD_PAYLOAD_ROWS


def test_continuity_accumulation_stability_and_window_bounds():
    history = [{"snapshot_ts": f"2026-01-{i:02d}T00:00:00Z", "id": i} for i in range(1, 95)]
    out = accumulate_longitudinal_continuity(history, {"snapshot_ts": "2026-05-27T00:00:00Z", "id": 999})
    assert len(out["continuity_history"]) == MAX_CONTINUITY_WINDOW_DAYS
    assert out["continuity_history"][-1]["id"] == 999
    md = out["continuity_retention_metadata"]
    assert md["retention_truncated"] is True
    assert md["earliest_snapshot_retained"] == out["continuity_history"][0]["snapshot_ts"]
    assert md["latest_snapshot_retained"] == "2026-05-27T00:00:00Z"
    assert md["snapshots_suppressed_by_retention"] == 5


def test_governance_boundaries_and_no_autonomous_behavior():
    out = ingest_controlled_daily_snapshot(_symbols(10), "2026-05-27", _fetcher_ok)
    assert out["governance_boundaries"] == GOVERNANCE_BOUNDARIES
    assert out["governance_boundaries"]["no_autonomous_replay"] is True
    assert out["governance_boundaries"]["no_topology_activation"] is True
    assert out["governance_boundaries"]["no_prediction_or_trading_execution"] is True
    assert out["governance_boundaries"]["no_graph_execution_engines"] is True
    assert out["governance_boundaries"]["no_high_frequency_streaming"] is True


def test_explicit_operational_boundedness_thresholds():
    assert MAX_INGESTION_BATCH_SIZE == 50
    assert MAX_SNAPSHOT_ROWS == 300
    assert MAX_CONTINUITY_WINDOW_DAYS == 90
    assert MAX_DASHBOARD_PAYLOAD_ROWS == 120
    assert MAX_STRUCTURAL_SUMMARY_ITEMS == 12


def test_adapter_boundary_supports_synthetic_batch_fetch_data():
    symbols = _symbols(10)
    rows = fetch_controlled_fmp_snapshot_batch(symbols, _fetcher_ok)
    assert len(rows) == 10
    out = ingest_controlled_daily_snapshot(symbols, "2026-05-27", _fetcher_ok)
    assert out["status"] == "ok"


def test_snapshot_identity_deterministic_and_symbol_order_invariant():
    base = _symbols(10)
    a = ingest_controlled_daily_snapshot(base, "2026-05-27", _fetcher_ok)
    b = ingest_controlled_daily_snapshot(list(reversed(base)), "2026-05-27", _fetcher_ok)
    c = ingest_controlled_daily_snapshot(base[:-1], "2026-05-27", _fetcher_ok)
    assert a["snapshot_identity"]["snapshot_id"] == b["snapshot_identity"]["snapshot_id"]
    assert a["snapshot_identity"]["snapshot_id"] != c["snapshot_identity"]["snapshot_id"]
    assert a["snapshot_identity"] == a["surfaces"]["snapshot_identity"] == a["operator_payload"]["snapshot_identity"]


def test_integrity_fail_closed_for_nan_negative_blank_symbol_and_missing_fields():
    def bad_fetcher(_batch):
        return [
            {"symbol": "BAD1", "price": float("nan"), "marketCap": 100, "sector": "Tech", "industry": "Software"},
            {"symbol": "BAD2", "price": -1.0, "marketCap": 100, "sector": "Tech", "industry": "Software"},
            {"symbol": "BAD3", "price": 1.0, "marketCap": -10, "sector": "Tech", "industry": "Software"},
            {"symbol": "", "price": 1.0, "marketCap": 100, "sector": "Tech", "industry": "Software"},
        ]

    out = ingest_controlled_daily_snapshot(["BAD1", "BAD2", "BAD3", ""], "2026-05-27", bad_fetcher)
    assert out["status"] == "failed_closed"
    assert out["integrity"]["invalid_numeric_values"]
    assert out["integrity"]["invalid_financial_values"]
    assert out["integrity"]["missing_symbols"]


def test_valid_zero_values_are_intentionally_accepted():
    def zero_fetcher(batch):
        for s in batch:
            yield {
                "symbol": s,
                "price": 0.0,
                "marketCap": 0.0,
                "sector": "Tech",
                "industry": "Software",
                "beta": 0.0,
                "pe": 0.0,
                "roe": 0.0,
                "debtToEquity": 0.0,
                "dispersion": 0.0,
            }

    out = ingest_controlled_daily_snapshot(_symbols(8), "2026-05-27", zero_fetcher)
    assert out["status"] == "ok"


def test_compression_observability_metadata_and_summary_limits():
    out = ingest_controlled_daily_snapshot(_symbols(250), "2026-05-27", _fetcher_ok)
    c = out["operator_payload"]["compression_observability"]
    assert c["input_rows"] == 250
    assert c["emitted_payload_rows"] == MAX_DASHBOARD_PAYLOAD_ROWS
    assert c["suppressed_rows"] == 130
    assert c["summary_items_emitted"] <= MAX_STRUCTURAL_SUMMARY_ITEMS


def test_posture_classification_is_deterministic_and_explainable():
    out = ingest_controlled_daily_snapshot(_symbols(12), "2026-05-27", _fetcher_ok)
    posture = out["surfaces"]["ecosystem_posture_snapshot"][0]
    assert posture["posture"] in {"stable_resilient", "balanced", "pressure_building", "fragmented_pressure", "fragile"}
    assert posture["drivers"]["reasons"]
    out2 = ingest_controlled_daily_snapshot(_symbols(12), "2026-05-27", _fetcher_ok)
    assert posture == out2["surfaces"]["ecosystem_posture_snapshot"][0]


def test_canonicalized_ingest_boundary_accepts_mixed_case_whitespace_symbols():
    def mixed_fetcher(_batch):
        return [
            {"symbol": " aapl ", "price": 280.14, "marketCap": 1, "sector": "Technology", "industry": "Consumer Electronics"},
            {"symbol": "msft", "price": 420.0, "marketCap": 2, "sector": "Technology", "industry": "Software"},
        ]

    out = ingest_controlled_daily_snapshot([" AAPL ", "msft"], "2026-05-01", mixed_fetcher)

    assert out["status"] == "ok"
    assert [r["symbol"] for r in out["rows"]] == ["AAPL", "MSFT"]
    assert out["ingestion_boundary_diagnostics"]["canonicalized_batch_symbols_sample"] == ["AAPL", "MSFT"]
    assert out["ingestion_boundary_diagnostics"]["canonicalized_row_symbols_sample"] == ["AAPL", "MSFT"]


def test_ingest_boundary_drops_rows_not_in_canonicalized_batch_with_reason():
    def noisy_fetcher(batch):
        rows = list(_fetcher_ok(batch))
        rows.append({"symbol": " TSLA ", "price": 1.0, "marketCap": 1, "sector": "Auto", "industry": "EV"})
        return rows

    out = ingest_controlled_daily_snapshot([" aapl "], "2026-05-01", noisy_fetcher)

    assert out["status"] == "ok"
    diagnostics = out["ingestion_boundary_diagnostics"]
    assert diagnostics["canonicalized_batch_symbols_sample"] == ["AAPL"]
    assert diagnostics["canonicalized_row_symbols_sample"] == ["AAPL", "TSLA"]
    assert diagnostics["dropped_due_to_batch_filter_count"] == 1
    assert diagnostics["rejected_row_reasons"] == [{"symbol": "TSLA", "rejection_reason": "symbol_not_in_canonicalized_batch"}]


def test_duplicate_elision_only_removes_true_duplicates_after_canonicalization():
    def duplicate_fetcher(_batch):
        row = {"price": 280.14, "marketCap": 1, "sector": "Technology", "industry": "Consumer Electronics"}
        return [{"symbol": " AAPL ", **row}, {"symbol": "aapl", **row}]

    out = ingest_controlled_daily_snapshot(["AAPL"], "2026-05-01", duplicate_fetcher)

    assert out["status"] == "ok"
    assert len(out["rows"]) == 1
    assert out["rows"][0]["symbol"] == "AAPL"
    diagnostics = out["ingestion_boundary_diagnostics"]
    assert diagnostics["duplicate_elision_count"] == 1
    assert diagnostics["rejected_row_reasons"] == [{"symbol": "AAPL", "rejection_reason": "duplicate_symbol_after_canonicalization"}]


def test_conflicting_duplicate_after_canonicalization_still_fails_closed():
    def conflicting_duplicate_fetcher(_batch):
        return [
            {"symbol": " AAPL ", "price": 280.14, "marketCap": 1, "sector": "Technology", "industry": "Consumer Electronics"},
            {"symbol": "aapl", "price": 281.14, "marketCap": 1, "sector": "Technology", "industry": "Consumer Electronics"},
        ]

    out = ingest_controlled_daily_snapshot(["AAPL"], "2026-05-01", conflicting_duplicate_fetcher)

    assert out["status"] == "failed_closed"
    assert out["integrity"]["duplicate_count"] == 1
    assert out["ingestion_boundary_diagnostics"]["duplicate_elision_count"] == 0
