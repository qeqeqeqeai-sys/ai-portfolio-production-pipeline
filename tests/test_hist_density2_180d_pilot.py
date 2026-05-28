from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_FIXTURE, DENSITY_MODE_REAL
from transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment import run_hist_density2


def test_hist_density2_config_and_governance(tmp_path):
    out = run_hist_density2(trading_days=180, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "out"), density_mode=DENSITY_MODE_FIXTURE)
    summary = out["density_summary"]
    assert summary["trading_days"] == 180
    assert summary["symbol_count"] == 50
    assert summary["mode"] == DENSITY_MODE_FIXTURE
    gov = summary["governance_flags"]
    assert gov["synthetic_fallback_enabled"] is False
    assert gov["replay_execution_enabled"] is False
    assert gov["persistence"] == "local_artifacts_only"
    assert gov["supabase_write_enabled"] is False


def test_symbol_universe_fixed_50():
    with pytest.raises(ValueError):
        run_hist_density2(trading_days=180, symbol_count=51, end_date="2026-05-27", density_mode=DENSITY_MODE_FIXTURE)


def test_summary_artifacts_and_telemetry_fields(tmp_path):
    run_hist_density2(trading_days=10, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "x"), density_mode=DENSITY_MODE_FIXTURE)
    md = Path('reports/hist_density_2_180d_enrichment_summary.md')
    js = Path('artifacts/hist_density_2_180d_summary.json')
    assert md.exists()
    assert js.exists()
    text = md.read_text(encoding="utf-8").lower()
    assert "governance certification" in text
    assert "prediction" in text and "trading" in text
    data = json.loads(js.read_text(encoding="utf-8"))
    keys = {"pilot_id","mode","requested_trading_days","resolved_trading_days","symbol_count","chunk_count","current_snapshot_index","elapsed_seconds","normalized_count","partial_count","failed_count","exact_date_matches","reconciled_prior_dates","missing_dates","endpoint_status_counts","estimated_remaining_snapshots","estimated_remaining_minutes"}
    assert keys.issubset(set(data["telemetry_summary"].keys()))
    assert "api_key" not in json.dumps(data).lower()


def test_real_mode_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        run_hist_density2(trading_days=5, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "real"), density_mode=DENSITY_MODE_REAL)
