from copy import deepcopy

from transmission_layers.expectation_failure import *


def _snapshots():
    prior = [
        {"entity_id": "1", "ticker": "AAA", "entity_name": "A", "subsector": "S1", "snapshot_date": "2026-01-01", "ai_expectation_failure_score": 60, "valuation_stretch_score": 50, "fundamental_support_score": 70, "narrative_saturation_score": 45, "certainty_fragility_score": 40, "structural_weakness_score": 50},
        {"entity_id": "2", "ticker": "BBB", "entity_name": "B", "subsector": "S1", "snapshot_date": "2026-01-01", "ai_expectation_failure_score": 80, "valuation_stretch_score": 75, "fundamental_support_score": 30, "narrative_saturation_score": 80, "certainty_fragility_score": 85, "structural_weakness_score": 80},
    ]
    current = [
        {"entity_id": "1", "ticker": "AAA", "entity_name": "A", "subsector": "S1", "snapshot_date": "2026-02-01", "ai_expectation_failure_score": 90, "valuation_stretch_score": 90, "fundamental_support_score": 40, "narrative_saturation_score": 60, "certainty_fragility_score": 60, "structural_weakness_score": 70, "downside_asymmetry_label": "EXTREME"},
        {"entity_id": "3", "ticker": "CCC", "entity_name": "C", "subsector": "S2", "snapshot_date": "2026-02-01", "ai_expectation_failure_score": "bad", "valuation_stretch_score": -10, "fundamental_support_score": None, "narrative_saturation_score": 40, "certainty_fragility_score": 110, "structural_weakness_score": 50},
    ]
    return current, prior


def test_public_apis_present():
    for name in ["build_historical_snapshot_summary", "build_fragility_change_delta", "build_fragility_change_label", "build_historical_deterioration_interpretation", "build_historical_improvement_interpretation", "build_historical_stability_interpretation", "build_entity_replay_interpretation", "build_subsector_replay_interpretation", "build_universe_replay_interpretation", "build_b4_evidence_chain", "build_phase_b4_historical_replay_report"]:
        assert name in globals()


def test_b4_report_determinism_and_immutability_and_checksums():
    current, prior = _snapshots()
    c0, p0 = deepcopy(current), deepcopy(prior)
    r1 = build_phase_b4_historical_replay_report(current, prior, b2_current_outputs={"x": 1}, b2_prior_outputs={"x": 0}, b3_current_outputs={"y": 1}, b3_prior_outputs={"y": 0})
    r2 = build_phase_b4_historical_replay_report(current, prior, b2_current_outputs={"x": 1}, b2_prior_outputs={"x": 0}, b3_current_outputs={"y": 1}, b3_prior_outputs={"y": 0})
    assert r1 == r2
    assert r1["replay_metadata"]["input_checksum"] == r2["replay_metadata"]["input_checksum"]
    assert current == c0 and prior == p0


def test_snapshot_summary_and_clamping_missing_invalid():
    current, _ = _snapshots()
    s = build_historical_snapshot_summary(current)
    assert s["entity_count"] == 2
    assert s["fragile_entity_count"] >= 1
    flags = s["evidence_quality_flags"]
    assert "invalid_ai_expectation_failure_score" in flags
    assert "missing_fundamental_support_score" in flags
    assert "clamped_valuation_stretch_score" in flags


def test_delta_labels_drivers_and_support_inversion():
    current, prior = _snapshots()
    d = build_fragility_change_delta(current[0], prior[0])
    assert d["fundamental_support_delta"] == 30
    assert d["direction"] == "FRAGILITY_DETERIORATED"
    assert build_fragility_change_label(d["composite_change_delta"]) in {"MODERATE_FRAGILITY_DETERIORATION", "HIGH_FRAGILITY_DETERIORATION", "SEVERE_FRAGILITY_DETERIORATION"}
    det = build_historical_deterioration_interpretation(current[0], prior[0])
    assert det["deterioration_driver"].endswith("_deterioration")
    imp = build_historical_improvement_interpretation(prior[0], current[0])
    assert imp["improvement_driver"].endswith("_improvement")


def test_stability_entity_subsector_universe_and_evidence_chain():
    cur = {"entity_id": "x", "ai_expectation_failure_score": 72, "valuation_stretch_score": 60, "fundamental_support_score": 40, "narrative_saturation_score": 60, "certainty_fragility_score": 60, "structural_weakness_score": 60}
    pri = {"entity_id": "x", "ai_expectation_failure_score": 70, "valuation_stretch_score": 60, "fundamental_support_score": 40, "narrative_saturation_score": 60, "certainty_fragility_score": 60, "structural_weakness_score": 60}
    st = build_historical_stability_interpretation(cur, pri)
    assert st["stability_label"] in {"PERSISTENT_HIGH_FRAGILITY", "MIXED_STABLE_FRAGILITY", "PERSISTENT_MODERATE_FRAGILITY"}
    current, prior = _snapshots()
    e = build_entity_replay_interpretation(current[0], prior[0], {"current": "b2c", "prior": "b2p"}, {"current": "b3c", "prior": "b3p"})
    assert e["explanation_template_id"] == "template_phase_b4_historical_replay_v1"
    assert e["b2_current_context_used"] == "b2c" and e["b3_prior_context_used"] == "b3p"
    ch = build_b4_evidence_chain(e, current[0], prior[0])
    assert ch["phase_id"] == "B4" and "replay_trace" in ch
    subs = build_subsector_replay_interpretation(current, prior)
    uni = build_universe_replay_interpretation(current, prior)
    assert isinstance(subs, list) and uni["matched_entity_count"] == 1


def test_no_prohibited_language_and_b123_regression():
    current, prior = _snapshots()
    r = build_phase_b4_historical_replay_report(current, prior)
    text = json_dump = str(r)
    for bad in ["buy", "sell", "target price", "backtested alpha", "P&L"]:
        assert bad not in text
    # ensure B1/B2/B3 APIs still callable
    assert callable(build_phase_b1_heatmap_report)
    assert callable(build_phase_b2_asymmetry_report)
    assert callable(build_phase_b3_benchmark_relative_report)
