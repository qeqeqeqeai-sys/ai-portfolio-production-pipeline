from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_FIXTURE
from transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment import run_hist_density2
from transmission_layers.expectation_failure.real_data.ops_hist_cache_raw_fmp import summarize_write_result


def test_cache_validation_artifacts_include_required_fields(tmp_path):
    out = run_hist_density2(trading_days=5, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "out"), density_mode=DENSITY_MODE_FIXTURE, cache_validation_mode=True)
    assert out["status"] == "ok"
    audit = json.loads((tmp_path / "out" / "cache_validation_audit.json").read_text(encoding="utf-8"))
    required = {"cache_enabled","cache_write_enabled","total_requested_symbol_date_rows","cache_hits","cache_misses","hit_ratio","rows_written","read_failures","write_failures","estimated_fmp_requests_avoided","endpoint_call_counts","cache_appeared_operational","warnings","second_run_expectations"}
    assert required.issubset(audit.keys())


def test_low_hit_ratio_warning_not_failure(tmp_path):
    run_hist_density2(trading_days=5, symbol_count=50, end_date="2026-05-27", output_root=str(tmp_path / "out"), density_mode=DENSITY_MODE_FIXTURE, raw_cache_enabled=True, cache_validation_mode=True)
    audit = json.loads((tmp_path / "out" / "cache_validation_audit.json").read_text(encoding="utf-8"))
    assert "low_cache_hit_ratio_first_run_possible" in audit["warnings"]


def test_unconfirmed_write_does_not_claim_success():
    class _Resp:
        data = None

    class _Table:
        def upsert(self, *_args, **_kwargs):
            return self

        def execute(self):
            return _Resp()

    class _Client:
        def table(self, _name):
            return _Table()

    rows = [{"symbol": "AAPL", "date": "2026-05-27", "adjClose": 10}]
    import os
    os.environ["OPS_HIST_RAW_CACHE_WRITE_ENABLED"] = "true"
    result = summarize_write_result(rows, client=_Client())
    assert result["write_status"] == "submitted_unconfirmed"
    assert result["write_success_rows"] is None
    assert result["write_confirmation_limited"] is True
