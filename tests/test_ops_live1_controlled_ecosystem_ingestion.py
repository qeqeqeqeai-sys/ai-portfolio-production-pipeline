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
    assert len(out) == MAX_CONTINUITY_WINDOW_DAYS
    assert out[-1]["id"] == 999


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
