from __future__ import annotations

import re

import pytest

from transmission_layers.expectation_failure.real_data.ops_hist5_temporal_continuity_regimes import (
    OPS_HIST5_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    build_ops_hist5_temporal_continuity_regimes,
    render_ops_hist5_temporal_regime_markdown,
)


def _hist4(i: int, persistence: str = "moderate_persistence") -> dict:
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_start_date": f"2026-01-0{i}",
        "snapshot_end_date": f"2026-01-1{i}",
        "reviewed_snapshot_count_total": 5 + i,
        "recurrence_depth": "multi_artifact_observation",
        "recurrence_ecology_scorecard": {
            "archetype_persistence_class": persistence,
            "archetype_recurrence_class": "moderate_recurrence_density",
            "archetype_diversity_class": "balanced_archetype_ecology",
            "composite_recurrence_class": "mixed_composite_recurrence",
        },
    }


def test_fail_closed_missing_or_wrong_source() -> None:
    for bad in ([], [{}], [{"schema_version": "wrong"}]):
        with pytest.raises(ValueError):
            build_ops_hist5_temporal_continuity_regimes(bad)


def test_determinism_and_schema() -> None:
    data = [_hist4(1, "high_persistence"), _hist4(2, "low_persistence"), _hist4(3, "high_persistence")]
    out1 = build_ops_hist5_temporal_continuity_regimes(data)
    out2 = build_ops_hist5_temporal_continuity_regimes(data)
    assert out1 == out2
    assert out1["schema_version"] == OPS_HIST5_SCHEMA_VERSION
    assert out1["source_schema_version"] == SOURCE_SCHEMA_VERSION


def test_single_and_multi_depth_and_transition_stability() -> None:
    single = build_ops_hist5_temporal_continuity_regimes(_hist4(1, "high_persistence"))
    assert single["regime_depth"] == "single_artifact_regime_observation"
    multi = build_ops_hist5_temporal_continuity_regimes([_hist4(1, "high_persistence"), _hist4(2, "low_persistence"), _hist4(3, "high_persistence")])
    assert len(multi["temporal_regime_observation_summary"]["regime_sequence_rows"]) == 3
    assert len(multi["temporal_regime_observation_summary"]["regime_transition_rows"]) == 2
    assert multi["temporal_regime_scorecard"]["regime_transition_class"] in {"low_transition_density", "moderate_transition_density", "high_transition_density"}
    assert multi["temporal_regime_scorecard"]["regime_duration_class"] in {"short_duration_regime", "moderate_duration_regime", "long_duration_regime", "mixed_duration_regime"}
    assert multi["temporal_regime_scorecard"]["regime_fragmentation_class"] in {"low_regime_fragmentation", "moderate_regime_fragmentation", "high_regime_fragmentation"}
    assert multi["temporal_regime_scorecard"]["temporal_regime_class"] in {"stable_temporal_regime", "mixed_temporal_regime", "fragmented_temporal_regime", "transition_heavy_temporal_regime"}


def test_payload_schema_markdown_and_governance() -> None:
    out = build_ops_hist5_temporal_continuity_regimes([_hist4(1), _hist4(2)])
    assert set(out["streamlit_temporal_regime_payload"].keys()) == {"schema_version", "source_schema_version", "temporal_regime_scorecard_panel", "regime_sequence_timeline", "regime_duration_table", "regime_transition_table", "regime_stability_window_panel", "regime_fragmentation_panel", "regime_volatility_cluster_panel", "persistence_topology_panel", "regime_evidence_table", "governance_boundary_panel"}
    assert set(out["canonical_table_payload"].keys()) == {"schema_version", "source_schema_version", "hist5_temporal_regime_scorecard_rows", "hist5_regime_sequence_rows", "hist5_regime_duration_rows", "hist5_regime_transition_rows", "hist5_regime_stability_window_rows", "hist5_regime_fragmentation_rows", "hist5_regime_volatility_cluster_rows", "hist5_regime_persistence_topology_rows", "hist5_regime_evidence_rows", "hist5_governance_rows"}
    md1 = render_ops_hist5_temporal_regime_markdown(out)
    md2 = render_ops_hist5_temporal_regime_markdown(out)
    assert md1 == md2
    assert "## Explicit Forbidden Boundaries" in md1
    g = out["governance_metadata"]
    assert g["supabase_write_enabled"] is False and g["repo_writeback_enabled"] is False
    assert g["orchestration_enabled"] is False and g["streaming_enabled"] is False
    assert g["no_topology_activation"] is True and g["no_recursive_replay_operationalization"] is True
    lower_blob = (str(out) + md1).lower()
    for term in ["predict", "forecast", "buy", "sell", "alpha", "signal", "opportunity", "probability"]:
        assert re.search(rf"\\b{term}\\b", lower_blob) is None
