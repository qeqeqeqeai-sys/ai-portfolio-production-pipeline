from __future__ import annotations

from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import run_hist_density3
from transmission_layers.expectation_failure.real_data.sde2_curated_symbol_ecology_expansion import get_sde2_curated_symbol_universe


def test_dry_run_uses_sde2_and_replacements(tmp_path):
    out = run_hist_density3(output_root=str(tmp_path), dry_run_config_only=True)
    symbols = out["config_preview"]["effective_symbols"]
    assert len(get_sde2_curated_symbol_universe()) == 241
    assert "RBT" not in symbols and "FANUY" not in symbols and "SENT" not in symbols
    assert "RBT" not in symbols and "FANUY" not in symbols and "SENT" not in symbols and "CYBR" not in symbols
    assert "ROK" in symbols and "ETN" in symbols and "CHKP" in symbols and "PANW" in symbols
    assert "ABB" in get_sde2_curated_symbol_universe() and "CYBR" in get_sde2_curated_symbol_universe()


def test_cache_flags_default_off_from_runner_workflow_text():
    text = Path('.github/workflows/hist_density3_curated_241_pilot.yml').read_text(encoding='utf-8')
    assert 'workflow_dispatch:' in text
    assert 'push:' not in text and 'pull_request:' not in text and 'schedule:' not in text
    assert 'default: "20"' in text
    assert 'expected_chunk_count:' in text
    assert 'dry_run_config_only:' in text and 'default: "false"' in text
    assert text.count('default: "false"') >= 5


def test_chunking_caps_and_artifacts(tmp_path):
    out = run_hist_density3(output_root=str(tmp_path), dry_run_config_only=True, max_symbols=241, symbol_chunk_size=50, trading_days=180)
    preview = out['config_preview']
    assert preview['chunk_plan']['symbol_chunk_count'] == 5
    assert preview['estimated_symbol_date_rows'] == preview['universe_telemetry']['effective_symbol_count'] * 180
    assert (Path(tmp_path) / 'hist_density3_config_preview.json').exists()
    assert (Path(tmp_path) / 'hist_density3_config_preview.md').exists()
    assert preview['governance_certification']['no_prediction_or_trading_execution'] is True


def test_real_run_routes_actual_chunk_symbols(monkeypatch, tmp_path):
    calls: list[dict] = []

    def _fake_run_hist_density2(**kwargs):
        calls.append(kwargs)
        return {"density_summary": {"telemetry_summary": {"requested_trading_days": kwargs["trading_days"]}}}

    monkeypatch.setattr('transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion.run_hist_density2', _fake_run_hist_density2)
    out = run_hist_density3(output_root=str(tmp_path), dry_run_config_only=False, trading_days=2, max_symbols=55, symbol_chunk_size=50)
    assert len(calls) == 2
    assert len(calls[0]["symbol_universe_override"]) == 50
    assert len(calls[1]["symbol_universe_override"]) == 5
    assert calls[0]["symbol_count"] == len(calls[0]["symbol_universe_override"])
    assert calls[1]["symbol_count"] == len(calls[1]["symbol_universe_override"])
    preview = run_hist_density3(output_root=str(tmp_path / "preview"), dry_run_config_only=True, trading_days=2, max_symbols=55, symbol_chunk_size=50)
    assert calls[0]["symbol_universe_override"] == preview["config_preview"]["chunk_symbols"][0]
    assert calls[1]["symbol_universe_override"] == preview["config_preview"]["chunk_symbols"][1]
    c0 = out["ops_hist_artifact_summary"]["chunk_results"][0]
    assert c0["chunk_symbol_count"] == 50
    assert isinstance(c0["chunk_symbol_digest"], str) and len(c0["chunk_symbol_digest"]) == 16


def test_dry_run_and_real_chunk_routing_match(monkeypatch, tmp_path):
    dry = run_hist_density3(output_root=str(tmp_path / 'dry'), dry_run_config_only=True, max_symbols=80, symbol_chunk_size=50)
    dry_chunks = dry["config_preview"]["chunk_symbols"]
    seen: list[list[str]] = []

    def _fake_run_hist_density2(**kwargs):
        seen.append(kwargs["symbol_universe_override"])
        return {"density_summary": {"telemetry_summary": {"requested_trading_days": kwargs["trading_days"]}}}

    monkeypatch.setattr('transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion.run_hist_density2', _fake_run_hist_density2)
    run_hist_density3(output_root=str(tmp_path / 'real'), dry_run_config_only=False, max_symbols=80, symbol_chunk_size=50, trading_days=1)
    assert seen == dry_chunks


def test_chunk_result_includes_failure_samples_and_aggregate_reasons(monkeypatch, tmp_path):
    def _fake_run_hist_density2(**kwargs):
        return {"density_summary": {"telemetry_summary": {"missing_record_sample_count": 1, "endpoint_failure_sample_count": 1, "affected_symbol_count": 1, "affected_date_count": 1, "top_failure_reasons": [{"reason": "HTTP_500", "count": 2}], "missing_record_samples": [{"symbol":"AAA","requested_snapshot_date":"2026-05-27"}], "endpoint_failure_samples": [{"symbol":"AAA","requested_snapshot_date":"2026-05-27","endpoint_name":"ep","attempt_index":1}]}}}
    monkeypatch.setattr('transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion.run_hist_density2', _fake_run_hist_density2)
    out = run_hist_density3(output_root=str(tmp_path / "real"), dry_run_config_only=False, max_symbols=55, symbol_chunk_size=50, trading_days=1)
    assert out["cache_telemetry"]["missing_record_sample_count"] == 2
    assert out["ops_hist_artifact_summary"]["chunk_results"][0]["missing_record_samples"]
    assert out["ops_hist_artifact_summary"]["top_failure_reasons"][0]["reason"] == "HTTP_500"


def test_universe_replacements_preserve_count_and_version(tmp_path):
    out = run_hist_density3(output_root=str(tmp_path), dry_run_config_only=True)
    preview = out["config_preview"]
    base = get_sde2_curated_symbol_universe()
    assert len(base) == 241
    assert len(preview["effective_symbols"]) == len(base)
    assert preview["universe_telemetry"]["effective_universe_version"].endswith("_effective")
    assert preview["sde2_universe_version"].startswith("SDE2_CURATED_SYMBOL_ECOLOGY")
    assert "ABB" in base and "CYBR" in base and "CFLT" in base
    assert "ETN" in preview["effective_symbols"] and "PANW" in preview["effective_symbols"] and "DDOG" in preview["effective_symbols"]
    assert "ABB" not in preview["effective_symbols"] and "CYBR" not in preview["effective_symbols"] and "CFLT" not in preview["effective_symbols"]


def test_stage5_preflight_and_fail_closed_raw_cache_writes(tmp_path):
    out = run_hist_density3(output_root=str(tmp_path), dry_run_config_only=True, trading_days=20, max_symbols=241, symbol_chunk_size=50, expected_chunk_count=5, raw_cache_enabled=False, raw_cache_write_enabled=False, cache_validation_mode=False, cache_only_validation=False, include_high_risk_symbols=False, apply_sde2_replacements=True)
    preflight = out["config_preview"]["preflight_validation"]
    assert preflight["requested_max_symbols"] == 241
    assert preflight["effective_symbol_count"] == 241
    assert preflight["chunk_count"] == 5
    assert preflight["chunk_sizes"] == [50, 50, 50, 50, 41]

    try:
        run_hist_density3(output_root=str(tmp_path / "bad"), dry_run_config_only=True, raw_cache_write_enabled=True)
        assert False, "expected fail closed on raw cache writes"
    except ValueError as exc:
        assert "raw cache writes are forbidden" in str(exc)
