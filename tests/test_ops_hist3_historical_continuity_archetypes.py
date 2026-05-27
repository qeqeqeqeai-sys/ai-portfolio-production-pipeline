from __future__ import annotations

from transmission_layers.expectation_failure.real_data.ops_hist3_historical_continuity_archetypes import (
    OPS_HIST3_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    build_ops_hist3_historical_continuity_archetypes,
    render_ops_hist3_archetype_markdown,
)


def _hist2() -> dict:
    rows = [
        {"snapshot_id": "a", "snapshot_date": "2026-01-02", "posture": "stable", "posture_transition": "initial", "fragmentation_value": 1.0, "resilience_value": 0.5, "sector_concentration_hhi": 0.2, "volatility_avg": 0.3, "valuation_dispersion": 0.4, "normalization_completeness": 100.0, "fallback_usage": 0.0},
        {"snapshot_id": "b", "snapshot_date": "2026-01-03", "posture": "stressed", "posture_transition": "changed", "fragmentation_value": 1.2, "resilience_value": 0.4, "sector_concentration_hhi": 0.3, "volatility_avg": 0.5, "valuation_dispersion": 0.6, "normalization_completeness": 95.0, "fallback_usage": 0.1},
    ]
    return {"schema_version": SOURCE_SCHEMA_VERSION, "streamlit_continuity_payload": {"posture_transition_timeline": rows}}


def test_fail_closed_no_payload_and_wrong_source_schema() -> None:
    for bad in ({}, {"schema_version": "wrong", "streamlit_continuity_payload": {"posture_transition_timeline": [{"snapshot_date": "2026-01-02", "snapshot_id": "a"}]}}):
        try:
            build_ops_hist3_historical_continuity_archetypes(bad)
            assert False
        except ValueError:
            assert True


def test_deterministic_schema_versions_and_archetype_stability() -> None:
    out1 = build_ops_hist3_historical_continuity_archetypes(_hist2())
    out2 = build_ops_hist3_historical_continuity_archetypes(_hist2())
    assert out1 == out2
    assert out1["schema_version"] == OPS_HIST3_SCHEMA_VERSION
    assert out1["source_schema_version"] == SOURCE_SCHEMA_VERSION
    assert out1["composite_continuity_archetype"] in {"stable_continuity_composite", "mixed_continuity_composite", "fragile_continuity_composite", "transition_heavy_continuity_composite"}
    assert out1["dimension_archetypes"]["posture"] in {"posture_stable_continuity", "posture_mixed_continuity", "posture_transition_heavy_continuity"}


def test_streamlit_and_canonical_schema_stability_and_governance_boundaries() -> None:
    out = build_ops_hist3_historical_continuity_archetypes(_hist2())
    assert set(out["streamlit_archetype_payload"].keys()) == {"schema_version", "source_schema_version", "archetype_scorecard_panel", "archetype_dimension_table", "composite_archetype_panel", "stable_archetype_panel", "mixed_archetype_panel", "fragile_archetype_panel", "archetype_evidence_table", "governance_boundary_panel"}
    assert set(out["canonical_table_payload"].keys()) == {"schema_version", "source_schema_version", "hist3_archetype_rows", "hist3_archetype_evidence_rows", "hist3_composite_archetype_rows", "hist3_archetype_count_rows", "hist3_archetype_dimension_rows", "hist3_governance_rows"}
    g = out["governance_metadata"]
    assert g["supabase_write_enabled"] is False and g["repo_writeback_enabled"] is False and g["orchestration_enabled"] is False and g["streaming_enabled"] is False
    assert g["no_autonomous_replay"] is True and g["no_topology_activation"] is True and g["no_prediction_or_trading_execution"] is True


def test_markdown_stability_and_forbidden_affirmative_vocabulary() -> None:
    md1 = render_ops_hist3_archetype_markdown(build_ops_hist3_historical_continuity_archetypes(_hist2()))
    md2 = render_ops_hist3_archetype_markdown(build_ops_hist3_historical_continuity_archetypes(_hist2()))
    assert md1 == md2
    for token in ["buy now", "sell now", "execute trade", "forecasted return", "activate topology", "start streaming"]:
        assert token not in md1.lower()
