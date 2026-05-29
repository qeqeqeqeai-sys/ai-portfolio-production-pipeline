from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.expectation_failure.real_data.hist_long5_analysis_only_review import write_hist_long5_analysis


def _completed_hist_long4() -> dict:
    windows = []
    for days in (20, 60, 120):
        rows = 241 * days
        windows.append({
            "window_trading_days": days,
            "normalized_rows": rows,
            "completeness": 1.0,
            "partial_count": 0,
            "failed_count": 0,
            "endpoint_failures": {},
            "weak_symbols": [] if days < 120 else ["XYZ"],
            "replay_density": 1.0,
            "sector_hhi": {"universe_hhi": 0.08},
        })
    return {
        "status": "ok",
        "all_three_real_windows_completed": True,
        "governance_certification": {
            "prediction_enabled": False,
            "trading_execution_enabled": False,
            "replay_activation_enabled": False,
            "replay_execution_enabled": False,
            "topology_persistence_enabled": False,
            "supabase_write_enabled": False,
            "raw_cache_write_enabled": False,
        },
        "window_level_results": windows,
        "bounded_diagnostics": {
            "replay_persistence_trend": "stable",
            "concentration_trend": "stable",
            "strongest_recurring_sectors": [{"sector": "technology", "window_count": 3}],
            "strongest_recurring_subsectors": [{"subsector": "cloud", "window_count": 3}],
            "recurring_weak_symbols": [],
        },
        "longitudinal_comparison": {
            "ecology_stability": {"morphology_persistence": {"assessment": "stable_across_completed_real_windows"}},
            "weak_symbol_analysis": {
                "foxa_stability": {"assessment": "stable_not_weak", "weak_windows": []},
                "provider_degradation_recurrence": [],
            },
        },
    }


def test_hist_long5_consumes_completed_hist_long4_without_reexecution(tmp_path):
    source = tmp_path / "hist_long4.json"
    source.write_text(json.dumps(_completed_hist_long4()), encoding="utf-8")
    artifact = write_hist_long5_analysis(
        source_artifact_path=str(source),
        report_path=str(tmp_path / "report.md"),
        artifact_path=str(tmp_path / "artifact.json"),
    )

    assert artifact["status"] == "ok"
    assert artifact["source_windows"] == [20, 60, 120]
    assert artifact["governance_certification"]["fmp_calls_enabled"] is False
    assert artifact["governance_certification"]["hist_long4_reexecution_enabled"] is False
    assert artifact["ingestion_continuity"]["normalized_rows"] == [4820, 14460, 28920]
    assert artifact["ecology_persistence"]["replay_persistence_trend"] == "stable"
    assert artifact["fragility_watchlist"]["foxa_assessment"]["assessment"] == "stable_not_weak"


def test_hist_long5_fails_closed_on_blocked_hist_long4(tmp_path):
    source = tmp_path / "hist_long4_blocked.json"
    source.write_text(json.dumps({"status": "blocked", "all_three_real_windows_completed": False, "window_level_results": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="source HIST-LONG-4 artifact must be completed"):
        write_hist_long5_analysis(source_artifact_path=str(source), report_path=str(tmp_path / "report.md"), artifact_path=str(tmp_path / "artifact.json"))

    assert not (tmp_path / "report.md").exists()
    assert not (tmp_path / "artifact.json").exists()
