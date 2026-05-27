from __future__ import annotations

from transmission_layers.expectation_failure.real_data.ops_hist4_archetype_recurrence_ecology import (
    OPS_HIST4_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    build_ops_hist4_archetype_recurrence_ecology,
    render_ops_hist4_recurrence_markdown,
)


def _hist3(i: int, comp: str = "stable_continuity_composite") -> dict:
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_start_date": f"2026-01-0{i}",
        "snapshot_end_date": f"2026-01-0{i}",
        "reviewed_snapshot_count": 2,
        "dimension_archetypes": {"posture": "posture_stable_continuity", "volatility": "volatility_mixed_observed" if i % 2 else "volatility_stable_observed"},
        "composite_continuity_archetype": comp,
    }


def test_fail_closed_conditions() -> None:
    for bad in ([], [{}], [{"schema_version": "wrong"}]):
        try:
            build_ops_hist4_archetype_recurrence_ecology(bad)
            assert False
        except ValueError:
            assert True


def test_determinism_and_schema_versions() -> None:
    data = [_hist3(1), _hist3(2)]
    out1 = build_ops_hist4_archetype_recurrence_ecology(data)
    out2 = build_ops_hist4_archetype_recurrence_ecology(data)
    assert out1 == out2
    assert out1["schema_version"] == OPS_HIST4_SCHEMA_VERSION
    assert out1["source_schema_version"] == SOURCE_SCHEMA_VERSION


def test_single_and_multi_artifact_behavior_and_classes() -> None:
    single = build_ops_hist4_archetype_recurrence_ecology(_hist3(1))
    assert single["recurrence_depth"] == "single_artifact_observation"
    multi = build_ops_hist4_archetype_recurrence_ecology([_hist3(1), _hist3(2), _hist3(3, "transition_heavy_continuity_composite")])
    assert multi["artifact_count"] == 3
    assert multi["recurrence_ecology_scorecard"]["archetype_recurrence_class"] in {"low_recurrence_density", "moderate_recurrence_density", "high_recurrence_density"}
    assert multi["recurrence_ecology_scorecard"]["archetype_persistence_class"] in {"low_persistence", "moderate_persistence", "high_persistence"}
    assert multi["recurrence_ecology_scorecard"]["archetype_diversity_class"] in {"diversified_archetype_ecology", "balanced_archetype_ecology", "concentrated_archetype_ecology", "monoculture_archetype_ecology"}


def test_streamlit_canonical_markdown_governance_and_forbidden_boundaries() -> None:
    out = build_ops_hist4_archetype_recurrence_ecology([_hist3(1), _hist3(2)])
    assert set(out["streamlit_recurrence_payload"].keys()) == {"schema_version", "source_schema_version", "recurrence_ecology_scorecard_panel", "archetype_recurrence_table", "archetype_persistence_table", "composite_recurrence_panel", "archetype_diversity_panel", "monoculture_observation_panel", "recurring_dimension_panel", "persistent_dimension_panel", "recurrence_evidence_table", "governance_boundary_panel"}
    assert set(out["canonical_table_payload"].keys()) == {"schema_version", "source_schema_version", "hist4_recurrence_scorecard_rows", "hist4_archetype_recurrence_rows", "hist4_archetype_persistence_rows", "hist4_composite_recurrence_rows", "hist4_archetype_diversity_rows", "hist4_monoculture_observation_rows", "hist4_recurrence_evidence_rows", "hist4_governance_rows"}
    g = out["governance_metadata"]
    assert g["supabase_write_enabled"] is False and g["repo_writeback_enabled"] is False and g["orchestration_enabled"] is False and g["streaming_enabled"] is False
    assert g["no_autonomous_replay"] is True and g["no_topology_activation"] is True and g["no_prediction_or_trading_execution"] is True
    md = render_ops_hist4_recurrence_markdown(out).lower()
    for token in ["buy now", "sell now", "execute trade", "forecasted return", "activate topology", "start streaming"]:
        assert token not in md
