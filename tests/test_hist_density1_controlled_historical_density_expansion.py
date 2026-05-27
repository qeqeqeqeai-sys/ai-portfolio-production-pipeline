from __future__ import annotations

import json

import pytest

import transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion as hd1
from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import (
    DENSITY_MODE_FIXTURE,
    DENSITY_MODE_REAL,
    HIST_DENSITY1_SCHEMA_VERSION,
    MAX_SYMBOL_COUNT,
    MAX_TRADING_DAYS,
    render_hist_density1_markdown,
    run_hist_density1,
)


def _fetcher(batch):
    out = []
    for i, s in enumerate(batch):
        out.append({"symbol": s, "price": 100 + i, "marketCap": 1000000 + i, "sector": "Tech" if i % 2 == 0 else "Fin", "industry": "Soft", "beta": 1.0, "pe": 10.0 + i / 100, "roe": 0.2, "debtToEquity": 0.1, "dispersion": 0.3})
    return out


def test_fail_closed_limits():
    with pytest.raises(ValueError):
        run_hist_density1(trading_days=MAX_TRADING_DAYS + 1)
    with pytest.raises(ValueError):
        run_hist_density1(symbol_count=MAX_SYMBOL_COUNT + 1)


def test_real_mode_missing_api_key_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        run_hist_density1(trading_days=5, end_date="2026-05-27", output_root=str(tmp_path / "real"), density_mode=DENSITY_MODE_REAL)


def test_real_mode_uses_ops_hist1_and_chunking_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(hd1, "_deterministic_fixture_snapshots", lambda *_: (_ for _ in ()).throw(AssertionError("fixture path must not execute in real mode")))
    out1 = run_hist_density1(trading_days=120, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "a"), density_mode=DENSITY_MODE_REAL, fetch_batch=_fetcher)
    out2 = run_hist_density1(trading_days=120, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "b"), density_mode=DENSITY_MODE_REAL, fetch_batch=_fetcher)
    assert out1["execution_id"] == out2["execution_id"]
    assert out1["ops_hist1_chunks_generated"] == 2
    assert out1["real_snapshot_generation"] is True
    assert out1["synthetic_snapshot_generation"] is False
    assert out1["fmp_required"] is True
    assert out1["data_source_mode"] == DENSITY_MODE_REAL
    snap_files = list((tmp_path / "a" / "snapshots").glob("ops_hist1_*.json"))
    assert len(snap_files) >= 120


def test_synthetic_fixture_mode_explicit_and_deterministic(tmp_path):
    out1 = run_hist_density1(trading_days=5, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "x"), density_mode=DENSITY_MODE_FIXTURE)
    out2 = run_hist_density1(trading_days=5, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "y"), density_mode=DENSITY_MODE_FIXTURE)
    assert out1["execution_id"] == out2["execution_id"]
    assert out1["data_source_mode"] == DENSITY_MODE_FIXTURE
    assert out1["fixture_only"] is True
    assert out1["synthetic_snapshot_generation"] is True
    assert out1["real_snapshot_generation"] is False


def test_local_paths_payload_schemas_and_governance(tmp_path):
    out = run_hist_density1(trading_days=4, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "x"), density_mode=DENSITY_MODE_FIXTURE)
    for part in ["manifests", "snapshots", "continuity", "archetypes", "recurrence", "regimes", "morphology", "saturation"]:
        assert (tmp_path / "x" / part).exists()
    assert set(out["streamlit_payloads"].keys()) == {
        "density_execution_panel", "artifact_coverage_panel", "historical_window_panel", "continuity_density_panel", "recurrence_density_panel", "regime_density_panel", "morphology_density_panel", "saturation_density_panel", "governance_boundary_panel",
    }
    assert set(out["canonical_table_payloads"].keys()) == {
        "density_manifest_rows", "artifact_generation_rows", "historical_window_rows", "coverage_gap_rows", "continuity_density_rows", "recurrence_density_rows", "regime_density_rows", "morphology_density_rows", "saturation_density_rows", "governance_rows",
    }
    gov = out["governance_metadata"]
    for key in ["supabase_write_enabled", "repo_writeback_enabled", "orchestration_enabled", "streaming_enabled", "no_topology_activation", "no_autonomous_replay", "no_graph_execution_engines"]:
        assert key in gov
    assert gov["supabase_write_enabled"] is False
    text = json.dumps(out, sort_keys=True).lower()
    for token in ["forecast", "alpha", "signal", "recommendation", "opportunity", "execution priority", "optimization target", "future instability", "autonomous response"]:
        assert token not in text
    assert out["schema_version"] == HIST_DENSITY1_SCHEMA_VERSION
    md = render_hist_density1_markdown(out).lower()
    assert "density mode" in md
