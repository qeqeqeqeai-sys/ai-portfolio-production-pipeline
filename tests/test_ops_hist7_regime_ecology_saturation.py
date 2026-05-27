from __future__ import annotations

import re

import pytest

from transmission_layers.expectation_failure.real_data.ops_hist7_regime_ecology_saturation import (
    OPS_HIST7_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    build_ops_hist7_regime_ecology_saturation,
    render_ops_hist7_regime_ecology_saturation_markdown,
)


def _hist6(i: int, morph: str = "mixed_regime_morphology", shape: str = "mixed_transition_shape", frag: str = "moderate_fragmentation_propagation", stab: str = "moderate_stability_deformation") -> dict:
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_start_date": f"2026-03-0{i}",
        "snapshot_end_date": f"2026-03-1{i}",
        "reviewed_snapshot_count_total": 11 + i,
        "morphology_depth": "multi_artifact_morphology_observation",
        "morphology_scorecard": {
            "regime_morphology_class": morph,
            "transition_shape_class": shape,
            "fragmentation_propagation_class": frag,
            "stability_deformation_class": stab,
        },
    }


def test_fail_closed_missing_or_wrong_source() -> None:
    for bad in ([], [{}], [{"schema_version": "wrong"}]):
        with pytest.raises(ValueError):
            build_ops_hist7_regime_ecology_saturation(bad)


def test_determinism_schema_and_depth_modes() -> None:
    data = [_hist6(1, "stable_regime_morphology"), _hist6(2, "mixed_regime_morphology")]
    out1 = build_ops_hist7_regime_ecology_saturation(data)
    out2 = build_ops_hist7_regime_ecology_saturation(data)
    assert out1 == out2
    assert out1["schema_version"] == OPS_HIST7_SCHEMA_VERSION
    assert out1["source_schema_version"] == SOURCE_SCHEMA_VERSION
    single = build_ops_hist7_regime_ecology_saturation(_hist6(1))
    assert single["saturation_depth"] == "single_artifact_saturation_observation"


def test_multi_artifact_classification_and_payload_schemas() -> None:
    out = build_ops_hist7_regime_ecology_saturation([
        _hist6(1, "stable_regime_morphology", "smooth_transition_shape", "low_fragmentation_propagation", "low_stability_deformation"),
        _hist6(2, "stable_regime_morphology", "mixed_transition_shape", "moderate_fragmentation_propagation", "moderate_stability_deformation"),
        _hist6(3, "discontinuous_regime_morphology", "abrupt_transition_shape", "high_fragmentation_propagation", "high_stability_deformation"),
    ])
    sc = out["saturation_scorecard"]
    assert sc["ecology_saturation_class"] in {"low_ecology_saturation", "moderate_ecology_saturation", "high_ecology_saturation", "concentrated_ecology_saturation"}
    assert sc["structural_density_class"] in {"sparse_structural_density", "moderate_structural_density", "dense_structural_density", "highly_dense_structural_density"}
    assert sc["continuity_crowding_class"] in {"low_continuity_crowding", "moderate_continuity_crowding", "high_continuity_crowding"}
    assert sc["morphology_diversity_class"] in {"highly_diversified_morphology", "diversified_morphology", "moderately_concentrated_morphology", "concentrated_morphology"}
    assert sc["topology_concentration_class"] in {"distributed_topology", "mixed_topology", "concentrated_topology", "topology_monoculture"}
    assert sc["stability_density_class"] in {"low_stability_density", "moderate_stability_density", "high_stability_density"}
    assert set(out["streamlit_saturation_payload"].keys()) == {"schema_version", "source_schema_version", "saturation_scorecard_panel", "structural_density_timeline", "continuity_crowding_table", "recurrence_congestion_panel", "morphology_diversity_panel", "topology_concentration_panel", "stability_density_panel", "morphology_collapse_panel", "saturation_evidence_table", "governance_boundary_panel"}
    assert set(out["canonical_table_payload"].keys()) == {"schema_version", "source_schema_version", "hist7_saturation_scorecard_rows", "hist7_structural_density_rows", "hist7_continuity_crowding_rows", "hist7_recurrence_congestion_rows", "hist7_topology_concentration_rows", "hist7_morphology_diversity_rows", "hist7_stability_density_rows", "hist7_morphology_collapse_rows", "hist7_saturation_evidence_rows", "hist7_governance_rows"}


def test_markdown_governance_and_forbidden_vocabulary() -> None:
    out = build_ops_hist7_regime_ecology_saturation([_hist6(1), _hist6(2)])
    md1 = render_ops_hist7_regime_ecology_saturation_markdown(out)
    md2 = render_ops_hist7_regime_ecology_saturation_markdown(out)
    assert md1 == md2
    assert "## Explicit Forbidden Boundaries" in md1
    g = out["governance_metadata"]
    assert g["supabase_write_enabled"] is False and g["repo_writeback_enabled"] is False
    assert g["orchestration_enabled"] is False and g["streaming_enabled"] is False
    assert g["no_topology_activation"] is True and g["no_recursive_replay_operationalization"] is True
    lower_blob = (str(out) + md1).lower()
    for term in ["predict", "forecast", "buy", "sell", "alpha", "signal", "opportunity", "probability"]:
        assert re.search(rf"\\b{term}\\b", lower_blob) is None
