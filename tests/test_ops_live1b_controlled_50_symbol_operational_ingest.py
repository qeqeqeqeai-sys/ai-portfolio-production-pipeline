import pytest

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    GOVERNANCE_BOUNDARIES,
    OPS_LIVE1B_UNIVERSE_CAP,
    get_ops_live1b_controlled_universe,
    run_ops_live1b_controlled_50_symbol_operational_ingest,
)


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
