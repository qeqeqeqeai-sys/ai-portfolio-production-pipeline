from __future__ import annotations

import re

import pytest

from transmission_layers.expectation_failure.real_data.ops_hist6_regime_morphology_observation import (
    OPS_HIST6_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    build_ops_hist6_regime_morphology_observation,
    render_ops_hist6_regime_morphology_markdown,
)


def _hist5(i: int, temporal: str = "mixed_temporal_regime", transition: str = "moderate_transition_density", stability: str = "mixed_window_stability", frag: str = "moderate_regime_fragmentation") -> dict:
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_start_date": f"2026-02-0{i}",
        "snapshot_end_date": f"2026-02-1{i}",
        "reviewed_snapshot_count_total": 7 + i,
        "regime_depth": "multi_artifact_regime_observation",
        "temporal_regime_scorecard": {
            "temporal_regime_class": temporal,
            "regime_transition_class": transition,
            "regime_stability_class": stability,
            "regime_fragmentation_class": frag,
        },
    }


def test_fail_closed_missing_or_wrong_source() -> None:
    for bad in ([], [{}], [{"schema_version": "wrong"}]):
        with pytest.raises(ValueError):
            build_ops_hist6_regime_morphology_observation(bad)


def test_determinism_and_schema() -> None:
    data = [_hist5(1, "stable_temporal_regime"), _hist5(2, "fragmented_temporal_regime", frag="high_regime_fragmentation")]
    out1 = build_ops_hist6_regime_morphology_observation(data)
    out2 = build_ops_hist6_regime_morphology_observation(data)
    assert out1 == out2
    assert out1["schema_version"] == OPS_HIST6_SCHEMA_VERSION
    assert out1["source_schema_version"] == SOURCE_SCHEMA_VERSION


def test_single_and_multi_depth_and_classification_stability() -> None:
    single = build_ops_hist6_regime_morphology_observation(_hist5(1, "stable_temporal_regime", "low_transition_density", "stable_window_dominant", "low_regime_fragmentation"))
    assert single["morphology_depth"] == "single_artifact_morphology_observation"
    assert single["morphology_scorecard"]["transition_shape_class"] == "insufficient_transition_shape"

    multi = build_ops_hist6_regime_morphology_observation([
        _hist5(1, "stable_temporal_regime", "low_transition_density", "stable_window_dominant", "low_regime_fragmentation"),
        _hist5(2, "mixed_temporal_regime", "moderate_transition_density", "mixed_window_stability", "moderate_regime_fragmentation"),
        _hist5(3, "transition_heavy_temporal_regime", "high_transition_density", "unstable_window_dominant", "high_regime_fragmentation"),
    ])
    assert len(multi["morphology_observation_summary"]["transition_shape_rows"]) == 1
    assert len(multi["streamlit_morphology_payload"]["morphology_sequence_timeline"]) == 3
    assert multi["morphology_scorecard"]["regime_morphology_class"] in {"stable_regime_morphology", "gradual_regime_morphology", "mixed_regime_morphology", "discontinuous_regime_morphology"}
    assert multi["morphology_scorecard"]["transition_shape_class"] in {"smooth_transition_shape", "mixed_transition_shape", "abrupt_transition_shape", "insufficient_transition_shape"}
    assert multi["morphology_scorecard"]["fragmentation_propagation_class"] in {"low_fragmentation_propagation", "moderate_fragmentation_propagation", "high_fragmentation_propagation"}
    assert multi["morphology_scorecard"]["stability_deformation_class"] in {"low_stability_deformation", "moderate_stability_deformation", "high_stability_deformation"}


def test_payload_markdown_governance_and_vocab_bounds() -> None:
    out = build_ops_hist6_regime_morphology_observation([_hist5(1), _hist5(2)])
    assert set(out["streamlit_morphology_payload"].keys()) == {"schema_version", "source_schema_version", "morphology_scorecard_panel", "morphology_sequence_timeline", "transition_shape_table", "deformation_table", "fragmentation_propagation_panel", "stability_deformation_panel", "discontinuity_observation_panel", "persistence_morphology_panel", "morphology_evidence_table", "governance_boundary_panel"}
    assert set(out["canonical_table_payload"].keys()) == {"schema_version", "source_schema_version", "hist6_morphology_scorecard_rows", "hist6_morphology_sequence_rows", "hist6_transition_shape_rows", "hist6_deformation_rows", "hist6_fragmentation_propagation_rows", "hist6_stability_deformation_rows", "hist6_discontinuity_observation_rows", "hist6_persistence_morphology_rows", "hist6_morphology_evidence_rows", "hist6_governance_rows"}
    md1 = render_ops_hist6_regime_morphology_markdown(out)
    md2 = render_ops_hist6_regime_morphology_markdown(out)
    assert md1 == md2
    assert "## Explicit Forbidden Boundaries" in md1
    g = out["governance_metadata"]
    assert g["supabase_write_enabled"] is False and g["repo_writeback_enabled"] is False
    assert g["orchestration_enabled"] is False and g["streaming_enabled"] is False
    assert g["no_topology_activation"] is True and g["no_recursive_replay_operationalization"] is True
    lower_blob = (str(out) + md1).lower()
    for term in ["predict", "forecast", "buy", "sell", "alpha", "signal", "opportunity", "probability"]:
        assert re.search(rf"\\b{term}\\b", lower_blob) is None
