import json

import pytest

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    DEFAULT_PROBE_UNIVERSE,
    GOVERNANCE_BOUNDARIES,
    MAX_PROBE_UNIVERSE_SIZE,
    run_ops_live1a_controlled_fmp_probe,
)


def _good_fetcher(batch):
    rows = []
    for i, s in enumerate(batch):
        rows.append({
            "symbol": s,
            "price": 100 + i,
            "marketCap": 1_000_000 + i,
            "sector": "Tech",
            "industry": "Software",
            "beta": 1.1,
            "pe": 20.0,
            "roe": 0.2,
            "debtToEquity": 0.4,
            "dispersion": 0.2,
        })
    return rows


def test_probe_bounded_and_local_output(tmp_path):
    out = run_ops_live1a_controlled_fmp_probe(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=_good_fetcher)
    assert out["status"] == "ok"
    assert out["probe_size"] <= MAX_PROBE_UNIVERSE_SIZE
    assert out["probe_universe"] == sorted(DEFAULT_PROBE_UNIVERSE)
    assert out["dry_run_local_output_only"] is True
    assert out["supabase_write_enabled"] is False
    data = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert data["snapshot_identity"]["snapshot_id"]


def test_missing_required_fields_fail_closed(tmp_path):
    def bad_fetcher(batch):
        return [{"symbol": s, "price": 1.0} for s in batch]

    out = run_ops_live1a_controlled_fmp_probe(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=bad_fetcher)
    assert out["status"] == "failed_closed"


def test_invalid_values_fail_closed(tmp_path):
    def invalid_fetcher(batch):
        return [{"symbol": s, "price": float("nan"), "marketCap": -1, "sector": "Tech", "industry": "Soft"} for s in batch]

    out = run_ops_live1a_controlled_fmp_probe(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=invalid_fetcher)
    assert out["status"] == "failed_closed"
    assert out["diagnostics"]["invalid_values"]


def test_missing_env_key_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        run_ops_live1a_controlled_fmp_probe(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"))


def test_payload_shape_and_governance_boundary_preserved(tmp_path):
    out = run_ops_live1a_controlled_fmp_probe(snapshot_date="2026-05-27", output_path=str(tmp_path / "out.json"), fetch_batch=_good_fetcher)
    assert out["governance_boundaries"] == GOVERNANCE_BOUNDARIES
    for key in (
        "daily_ecosystem_posture",
        "dominant_structural_pressures",
        "strongest_resilience_pathways",
        "fragmentation_hotspots",
        "transition_state_summaries",
        "continuity_summaries",
        "normalization_observations",
        "compression_observability",
    ):
        assert key in out["payload_shape"]
