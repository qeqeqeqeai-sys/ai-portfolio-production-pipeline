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


def test_telemetry_samples_and_counters_wired(monkeypatch, tmp_path):
    def _fake_backfill(**kwargs):
        return {"telemetry_summary": {
            "normalized_symbol_total": 1, "partial_symbol_total": 0, "failed_symbol_total": 0,
            "exact_date_matches": 0, "reconciled_prior_dates": 0, "missing_dates": 1,
            "endpoint_success_counts": {}, "endpoint_failure_counts": {"HTTP_500": 1},
            "missing_record_samples": [{"symbol":"AAA","requested_snapshot_date":"2026-05-27","reconciliation_window_days":5,"exact_match_found":False,"reconciled_prior_date":None,"final_missing_after_reconciliation":True,"final_failure_reason":"HTTP_500"}],
            "endpoint_failure_samples": [{"symbol":"AAA","requested_snapshot_date":"2026-05-27","endpoint_name":"ep","attempt_index":1,"failure_reason":"HTTP_500","http_status":"HTTP_500","records_returned_count":0,"terminal_failure_for_symbol_date":True}],
            "top_failure_reasons": [{"reason":"HTTP_500","count":1}],
        }}
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.run_ops_hist1_historical_backfill", _fake_backfill)
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.load_ops_hist1_snapshots", lambda *_: [{"snapshot_id":"x","snapshot_date":"2026-05-27","canonical_payloads":{},"streamlit_payloads":{},"historical_window_checksum":"h","operational_diagnostics":{"normalization_completeness":1}}])
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist1_observation_review", lambda *_: {"ok": True})
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist2_continuity_intelligence", lambda *_: {"historical_continuity_rows": []})
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist3_historical_continuity_archetypes", lambda *_: {"archetype_transition_rows": []})
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist4_archetype_recurrence_ecology", lambda *_: {"recurrence_rows": []})
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist5_temporal_continuity_regimes", lambda *_: {"temporal_regime_rows": []})
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist6_regime_morphology_observation", lambda *_: {"morphology_rows": []})
    monkeypatch.setattr("transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment.build_ops_hist7_regime_ecology_saturation", lambda *_: {"saturation_rows": []})
    out = run_hist_density2(trading_days=2, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "out"), density_mode=DENSITY_MODE_REAL, fetch_batch=lambda *_: [])
    t = out["density_summary"]["telemetry_summary"]
    assert t["missing_record_sample_count"] >= 1
    assert t["endpoint_failure_sample_count"] >= 1
    assert "affected_symbol_count" in t and "affected_date_count" in t and "top_failure_reasons" in t
    assert t["telemetry_sample_limit_default"] == 25
    assert t["telemetry_sample_limit_hard_cap"] == 100
    written = json.loads((tmp_path / "out" / "manifests" / "density_summary.json").read_text(encoding="utf-8"))
    tw = written["density_summary"]["telemetry_summary"]
    for k in ("missing_record_samples", "endpoint_failure_samples", "affected_symbol_count", "affected_date_count", "top_failure_reasons"):
        assert k in tw
