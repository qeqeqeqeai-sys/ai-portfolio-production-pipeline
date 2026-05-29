from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_long7_intra_group_structural_contrast import (
    TARGET_GROUPS,
    build_hist_long7,
    write_hist_long7,
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
    sectors = [
        {"sector": "semiconductors", "symbol_count": 20, "share": 0.082988},
        {"sector": "consumer_discretionary", "symbol_count": 19, "share": 0.078838},
        {"sector": "commodities", "symbol_count": 16, "share": 0.06639},
        {"sector": "energy_utilities", "symbol_count": 17, "share": 0.070539},
    ]
    subsectors = [{"subsector": row["sector"], "symbol_count": row["symbol_count"], "share": row["share"]} for row in sectors]
    return {
        "window_trading_days": days,
        "source_status": "ok",
        "effective_symbol_count": 241,
        "configured_symbol_count": 241,
        "normalized_rows": days * 241,
        "partial_count": 0,
        "failed_count": 0,
        "sector_hhi": {"universe_hhi": 0.061, "strongest_sectors": sectors},
        "subsector_hhi": {"universe_hhi": 0.061, "strongest_subsectors": subsectors},
        "provider_degradation": {"endpoint_failures": {}, "top_failure_reasons": []},
        "weak_symbols": [],
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
        "replay_evolution_classification": {"classification": "stable"},
        "concentration_evolution_classification": {"classification": "stable_balanced"},
        "fragility_emergence_detection": {"classification": ["no_fragility_detected"], "fragile_windows": []},
    }
    payload.update(overrides)
    return payload


def _h6_sector(name: str, contribution: float, share: float, count: int):
    return {
        "sector": name,
        "symbol_count": count,
        "symbol_share": share,
        "concentration_contribution": contribution,
        "differentiation_score": contribution / 10,
        "stability_label": "stable_distinct",
    }


def _hist_long6(**overrides):
    sectors = [
        _h6_sector("semiconductors", 0.112772, 0.082988, 20),
        _h6_sector("consumer_discretionary", 0.101768, 0.078838, 19),
        _h6_sector("commodities", 0.072179, 0.06639, 16),
    ]
    payload = {
        "schema_version": "hist_long6_v1",
        "status": "ok",
        "governance_certification": _governance(),
        "cross_sectional_differentiation": {"sector": sectors},
        "findings": {
            "strongest_differentiated_sectors": sectors,
            "hidden_concentration_pockets": [
                sectors[0],
                {"subsector": "semiconductors", "concentration_contribution": 0.112772},
                sectors[1],
                {"subsector": "consumer_discretionary", "concentration_contribution": 0.101768},
            ],
        },
    }
    payload.update(overrides)
    return payload


def test_prerequisites_fail_closed_on_provider_degradation():
    hist4 = _hist_long4()
    hist4["window_level_results"][0]["provider_degradation"] = {"endpoint_failures": {"x": 1}, "top_failure_reasons": []}

    artifact = build_hist_long7(hist4, _hist_long5b(), _hist_long6())

    assert artifact["status"] == "blocked"
    assert "hist_long4_no_partial_failed_provider_degradation" in artifact["source_verification"]["reason"]


def test_no_forbidden_api_provider_supabase_replay_or_trading_paths():
    artifact = build_hist_long7(_hist_long4(), _hist_long5b(), _hist_long6())

    governance = artifact["governance_certification"]
    for key in (
        "fmp_calls_enabled",
        "provider_api_calls_enabled",
        "replay_activation_enabled",
        "replay_execution_enabled",
        "supabase_write_enabled",
        "prediction_enabled",
        "trading_execution_enabled",
    ):
        assert governance[key] is False


def test_deterministic_output_for_same_inputs():
    a = build_hist_long7(_hist_long4(), _hist_long5b(), _hist_long6())
    b = build_hist_long7(copy.deepcopy(_hist_long4()), copy.deepcopy(_hist_long5b()), copy.deepcopy(_hist_long6()))

    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_target_group_restriction_metric_bounds_and_classification_presence():
    artifact = build_hist_long7(_hist_long4(), _hist_long5b(), _hist_long6())

    groups = artifact["group_morphology_decomposition"]
    assert [row["group"] for row in groups] == TARGET_GROUPS
    for row in groups:
        assert row["morphology_classifications"]
        for key in (
            "intra_group_dispersion",
            "leader_tail_gap",
            "anchor_dependency_score",
            "subcluster_separation_score",
            "morphology_persistence_score",
            "window_alignment_score",
            "internal_contradiction_score",
            "breadth_of_differentiation",
            "structural_coherence_score",
            "hidden_concentration_intensity",
        ):
            assert 0.0 <= row["metrics"][key] <= 1.0


def test_report_creation_and_not_hist_long6_summary_only(tmp_path: Path):
    hist4 = tmp_path / "hist4.json"
    hist5 = tmp_path / "hist5.json"
    hist6 = tmp_path / "hist6.json"
    artifact_path = tmp_path / "hist7.json"
    report_path = tmp_path / "hist7.md"
    hist4.write_text(json.dumps(_hist_long4()), encoding="utf-8")
    hist5.write_text(json.dumps(_hist_long5b()), encoding="utf-8")
    hist6.write_text(json.dumps(_hist_long6()), encoding="utf-8")

    artifact = write_hist_long7(
        hist_long4_source_path=str(hist4),
        hist_long5b_source_path=str(hist5),
        hist_long6_source_path=str(hist6),
        artifact_path=str(artifact_path),
        report_path=str(report_path),
    )

    assert artifact["status"] == "ok"
    assert artifact["cross_group_findings"]["not_hist_long6_summary_only"] is True
    report_text = report_path.read_text(encoding="utf-8")
    assert "Group-by-Group Morphology Decomposition" in report_text
    assert "Leader/tail contrast" in report_text
