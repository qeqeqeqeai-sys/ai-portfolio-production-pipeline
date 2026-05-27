from __future__ import annotations

from transmission_layers.expectation_failure.real_data.ops_hist2_historical_continuity_intelligence import (
    OPS_HIST2_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    build_ops_hist2_continuity_intelligence,
    render_ops_hist2_continuity_markdown,
)


def _snap(d: str, sid: str, posture: str, frag: float, res: float, norm: float = 100.0) -> dict:
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_id": sid,
        "snapshot_date": d,
        "posture": posture,
        "operational_diagnostics": {
            "fragmentation_avg": frag,
            "resilience_avg": res,
            "sector_hhi": 0.2,
            "volatility_avg": 0.3,
            "valuation_dispersion": 0.4,
            "normalization_completeness": norm,
            "fallback_usage": 0.0,
        },
    }


def test_fail_closed_when_no_snapshots() -> None:
    try:
        build_ops_hist2_continuity_intelligence([])
        assert False
    except ValueError:
        assert True


def test_schema_and_source_version_and_ordering_deterministic() -> None:
    snaps = [_snap("2026-01-03", "b", "stable", 1.1, 0.2), _snap("2026-01-02", "a", "stable", 1.0, 0.3)]
    out1 = build_ops_hist2_continuity_intelligence(snaps)
    out2 = build_ops_hist2_continuity_intelligence(snaps)
    assert out1 == out2
    assert out1["schema_version"] == OPS_HIST2_SCHEMA_VERSION
    assert out1["source_schema_version"] == SOURCE_SCHEMA_VERSION
    assert out1["canonical_table_payload"]["hist2_posture_transition_rows"][0]["snapshot_date"] == "2026-01-02"


def test_payload_schema_stability_and_classes_and_governance() -> None:
    snaps = [_snap("2026-01-02", "a", "stable", 1.0, 0.3, 100.0), _snap("2026-01-03", "b", "stressed", 1.2, 0.1, 95.0)]
    out = build_ops_hist2_continuity_intelligence(snaps)
    assert set(out["streamlit_continuity_payload"].keys()) == {
        "schema_version", "source_schema_version", "continuity_scorecard_panel", "posture_transition_timeline", "posture_persistence_panel",
        "fragmentation_drift_panel", "resilience_drift_panel", "sector_concentration_panel", "volatility_observation_panel", "valuation_dispersion_panel",
        "normalization_quality_panel", "fallback_usage_panel", "governance_boundary_panel",
    }
    assert set(out["canonical_table_payload"].keys()) == {
        "schema_version", "source_schema_version", "hist2_continuity_scorecard_rows", "hist2_posture_transition_rows", "hist2_fragmentation_drift_rows",
        "hist2_resilience_drift_rows", "hist2_sector_concentration_rows", "hist2_volatility_observation_rows", "hist2_valuation_dispersion_rows",
        "hist2_normalization_quality_rows", "hist2_fallback_usage_rows", "hist2_governance_rows",
    }
    scorecard = out["continuity_stability_scorecard"]
    assert scorecard["posture_continuity_class"] in {"stable_posture", "mixed_posture", "transition_heavy_posture"}
    assert scorecard["fragmentation_continuity_class"] in {"stable_fragmentation", "widening_fragmentation", "narrowing_fragmentation", "mixed_fragmentation"}
    assert scorecard["resilience_continuity_class"] in {"stable_resilience", "improving_resilience_observed", "weakening_resilience_observed", "mixed_resilience"}
    assert scorecard["normalization_quality_class"] in {"complete_or_high_quality", "partial_quality", "unstable_quality"}
    gov = out["governance_metadata"]
    assert gov["supabase_write_enabled"] is False
    assert gov["repo_writeback_enabled"] is False
    assert gov["orchestration_enabled"] is False
    assert gov["streaming_enabled"] is False
    assert gov["no_topology_activation"] is True
    assert gov["no_autonomous_replay"] is True


def test_markdown_stability_and_vocabulary_boundaries() -> None:
    out = build_ops_hist2_continuity_intelligence([_snap("2026-01-02", "a", "stable", 1.0, 0.3)])
    md1 = render_ops_hist2_continuity_markdown(out)
    md2 = render_ops_hist2_continuity_markdown(out)
    assert md1 == md2
    for token in ["expected return", "buy", "sell", "alpha", "recommendation to trade"]:
        assert token not in md1.lower()
