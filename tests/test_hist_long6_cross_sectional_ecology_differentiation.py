from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_long6_cross_sectional_ecology_differentiation import (
    build_hist_long6,
    write_hist_long6,
)


def _governance():
    return {
        "governance_mode": "observational_only",
        "prediction_enabled": False,
        "trading_execution_enabled": False,
        "replay_activation_enabled": False,
        "replay_execution_enabled": False,
        "topology_persistence_enabled": False,
        "supabase_write_enabled": False,
        "raw_cache_write_enabled": False,
        "local_artifacts_only": True,
    }


def _window(days: int):
    rows = days * 100
    sector_rows = [
        {"sector": "alpha", "symbol_count": 20, "share": 0.20},
        {"sector": "beta", "symbol_count": 15, "share": 0.15},
        {"sector": "gamma", "symbol_count": 10, "share": 0.10},
    ]
    subsector_rows = [
        {"subsector": "alpha_core", "symbol_count": 18, "share": 0.18},
        {"subsector": "beta_core", "symbol_count": 12, "share": 0.12},
        {"subsector": "gamma_core", "symbol_count": 8, "share": 0.08},
    ]
    return {
        "window_trading_days": days,
        "source_status": "ok",
        "effective_symbol_count": 100,
        "configured_symbol_count": 100,
        "normalized_rows": rows,
        "partial_count": 0,
        "failed_count": 0,
        "chunk_count": 5,
        "chunk_density_range": {"min": 1.0, "max": 1.0},
        "sector_hhi": {"universe_hhi": 0.07, "strongest_sectors": sector_rows},
        "subsector_hhi": {"universe_hhi": 0.05, "strongest_subsectors": subsector_rows},
        "weak_symbols": [],
        "weak_symbol_details": [],
        "provider_degradation": {"endpoint_failures": {}, "top_failure_reasons": []},
        "foxa_present": True,
        "foxa_weak": False,
    }


def _hist_long4(**overrides):
    payload = {
        "schema_version": "hist_long4_v1",
        "status": "ok",
        "all_three_real_windows_completed": True,
        "governance_certification": _governance(),
        "window_level_results": [_window(20), _window(60), _window(120)],
        "longitudinal_comparison": {"completed_window_count": 3, "windows": [20, 60, 120]},
    }
    payload.update(overrides)
    return payload


def _hist_long5b(**overrides):
    payload = {
        "schema_version": "hist_long5b_v1",
        "status": "ok",
        "completed_windows": [20, 60, 120],
        "governance_certification": _governance(),
        "foxa_longitudinal_assessment": {
            "present_all_windows": True,
            "weak_window_count": 0,
            "insufficient_granular_signal": True,
            "contribution_consistency": "insufficient granular signal",
        },
        "fragility_emergence_detection": {"classification": ["no_fragility_detected"], "fragile_windows": []},
    }
    payload.update(overrides)
    return payload


def test_source_verification_accepts_completed_stable_sources():
    artifact = build_hist_long6(_hist_long4(), _hist_long5b())

    assert artifact["status"] == "ok"
    checks = artifact["source_verification"]["preflight_checks"]
    assert checks["hist_long4_status_ok"] is True
    assert checks["all_three_real_windows_completed"] is True
    assert checks["hist_long4_windows"] == [20, 60, 120]
    assert checks["hist_long5b_completed_windows_exactly_20_60_120"] is True
    assert checks["hist_long6_governance_flags_disabled"] is True


def test_blocked_source_handling_for_bad_hist_long5b_windows():
    artifact = build_hist_long6(_hist_long4(), _hist_long5b(completed_windows=[20, 120]))

    assert artifact["status"] == "blocked"
    assert "hist_long5b_completed_windows_exactly_20_60_120" in artifact["source_verification"]["reason"]


def test_sector_and_subsector_differentiation_metrics_are_bounded_and_ordered():
    artifact = build_hist_long6(_hist_long4(), _hist_long5b())

    sectors = artifact["cross_sectional_differentiation"]["sector"]
    subsectors = artifact["cross_sectional_differentiation"]["subsector"]
    assert sectors[0]["sector"] == "alpha"
    assert sectors[0]["representation_label"] == "overrepresented"
    assert all(0.0 <= row["differentiation_score"] <= 1.0 for row in sectors)
    assert subsectors[0]["subsector"] == "alpha_core"
    assert artifact["findings"]["hidden_concentration_pockets"]


def test_stable_baseline_handling_marks_groups_stable_and_chunks_balanced():
    artifact = build_hist_long6(_hist_long4(), _hist_long5b())

    assert artifact["baseline_summary"]["normalized_rows"] == 12000
    assert {row["stability_label"] for row in artifact["cross_sectional_differentiation"]["sector"]} == {"stable_distinct"}
    assert {row["differentiation_score"] for row in artifact["cross_sectional_differentiation"]["chunk"]} == {0.0}


def test_insufficient_symbol_level_foxa_data_is_not_invented():
    artifact = build_hist_long6(_hist_long4(), _hist_long5b())

    foxa = artifact["foxa_assessment"]
    assert foxa["present_all_windows"] is True
    assert foxa["weak_window_count"] == 0
    assert foxa["stability_status"] == "stable_not_weak"
    assert foxa["symbol_level_signal"] == "insufficient_signal"


def test_no_forbidden_api_write_or_replay_paths_are_enabled():
    artifact = build_hist_long6(_hist_long4(), _hist_long5b())

    governance = artifact["governance_certification"]
    for key in (
        "fmp_calls_enabled",
        "provider_api_calls_enabled",
        "hist_long4_reexecution_enabled",
        "replay_activation_enabled",
        "replay_execution_enabled",
        "topology_persistence_enabled",
        "supabase_write_enabled",
        "raw_cache_write_enabled",
        "prediction_enabled",
        "trading_execution_enabled",
    ):
        assert governance[key] is False


def test_output_json_and_markdown_creation(tmp_path: Path):
    hist4 = tmp_path / "hist_long4.json"
    hist5 = tmp_path / "hist_long5b.json"
    artifact_path = tmp_path / "artifact.json"
    report_path = tmp_path / "report.md"
    hist4.write_text(json.dumps(_hist_long4()), encoding="utf-8")
    hist5.write_text(json.dumps(_hist_long5b()), encoding="utf-8")

    artifact = write_hist_long6(
        hist_long4_source_path=str(hist4),
        hist_long5b_source_path=str(hist5),
        artifact_path=str(artifact_path),
        report_path=str(report_path),
    )

    assert artifact["status"] == "ok"
    assert json.loads(artifact_path.read_text(encoding="utf-8"))["status"] == "ok"
    assert "## Sector Differentiation" in report_path.read_text(encoding="utf-8")
