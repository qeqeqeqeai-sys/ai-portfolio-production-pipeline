from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_alert_escalation_interpretation,
    build_alert_reason_classification,
    build_alert_severity_label,
    build_alert_trigger_evidence,
    build_b5_evidence_chain,
    build_deterioration_alert_state,
    build_entity_alert_interpretation,
    build_phase_b5_alert_interpretation_report,
    build_subsector_alert_interpretation,
    build_universe_alert_interpretation,
)


def _entity(**kw):
    b = {
        "entity_id": "E1", "ticker": "AAA", "entity_name": "Alpha", "subsector": "Software", "snapshot_date": "2026-05-22",
        "ai_expectation_failure_score": 80, "valuation_stretch_score": 70, "fundamental_support_score": 30,
        "narrative_saturation_score": 82, "certainty_fragility_score": 75, "structural_weakness_score": 78,
    }
    b.update(kw)
    return b


def test_public_api_presence():
    assert callable(build_alert_trigger_evidence)


def test_normalization_and_triggers_and_immutability():
    e = _entity(ai_expectation_failure_score=-2, fundamental_support_score="bad", structural_weakness_score=None)
    original = deepcopy(e)
    b2 = {"downside_asymmetry_label": "HIGH_DOWNSIDE_ASYMMETRY"}
    b3 = {"fragility_delta": 21}
    b4 = {"composite_change_delta": 25}
    out = build_alert_trigger_evidence(e, b2, b3, b4)
    assert e == original
    assert out["normalized_scores"]["ai_expectation_failure_score"] == 0
    assert out["normalized_scores"]["fundamental_support_score"] == 50
    assert "invalid_fundamental_support_score" in out["evidence_quality_flags"]
    assert "missing_structural_weakness_score" in out["evidence_quality_flags"]
    assert out["asymmetry_trigger"] and out["benchmark_relative_trigger"] and out["historical_deterioration_trigger"]


def test_severity_and_state_and_reason_precedence():
    e = build_alert_trigger_evidence(_entity(), {"downside_asymmetry_label": "EXTREME_DOWNSIDE_ASYMMETRY"}, {"fragility_delta": 30}, {"composite_change_delta": 30})
    sev = build_alert_severity_label(e)
    st = build_deterioration_alert_state(_entity(), {"downside_asymmetry_label": "EXTREME_DOWNSIDE_ASYMMETRY"}, {"fragility_delta": 30}, {"composite_change_delta": 30})
    assert sev["alert_severity_label"] in {"CRITICAL_EXPECTATION_DETERIORATION_ALERT", "HIGH_EXPECTATION_DETERIORATION_ALERT"}
    assert st["alert_state"].startswith("ACTIVE_")
    assert build_alert_reason_classification(st) == "MULTI_DRIVER_ALERT"


def test_escalation_and_clearing():
    current = {"entity_id": "E1", "alert_state": "ACTIVE_HIGH_DETERIORATION", "alert_severity_score": 75}
    prior = {"entity_id": "E1", "alert_state": "NO_ACTIVE_ALERT", "alert_severity_score": 0}
    assert build_alert_escalation_interpretation(current, prior)["escalation_label"] == "ESCALATED_ALERT"
    assert build_alert_escalation_interpretation({"entity_id": "E1", "alert_state": "NO_ACTIVE_ALERT", "alert_severity_score": 0}, current)["escalation_label"] == "CLEARED_ALERT"


def test_entity_subsector_universe_evidence_and_report_determinism():
    e1 = _entity(entity_id="E1", subsector="Software")
    e2 = _entity(entity_id="E2", ticker="BBB", entity_name="Beta", subsector="Software", ai_expectation_failure_score=76)
    e3 = _entity(entity_id="E3", ticker="CCC", entity_name="Gamma", subsector="Semis", ai_expectation_failure_score=40, narrative_saturation_score=20, certainty_fragility_score=20, structural_weakness_score=20, fundamental_support_score=80)
    b2 = [{"entity_id": "E1", "downside_asymmetry_label": "HIGH_DOWNSIDE_ASYMMETRY"}]
    b3 = [{"entity_id": "E1", "benchmark_relative_label": "HIGH_RELATIVE_FRAGILITY", "fragility_delta": 25}]
    b4 = [{"entity_id": "E1", "change_label": "HIGH_FRAGILITY_DETERIORATION", "composite_change_delta": 20}]
    prior = [{"entity_id": "E1", "alert_state": "ACTIVE_ELEVATED_WATCHLIST", "alert_severity_score": 50}]

    ent = build_entity_alert_interpretation(e1, b2_context=b2[0], b3_context=b3[0], b4_context=b4[0], prior_alert_state=prior[0])
    assert ent["b2_context_used"]["downside_asymmetry_label"] == "HIGH_DOWNSIDE_ASYMMETRY"
    assert ent["explanation_template_id"] == "template_phase_b5_deterioration_alert_v1"
    banned = ["buy", "sell", "target price", "backtested alpha", "send alert automatically"]
    assert not any(x in ent["interpretation_summary"].lower() for x in banned)

    sub = build_subsector_alert_interpretation([ent, build_entity_alert_interpretation(e2), build_entity_alert_interpretation(e3)])
    uni = build_universe_alert_interpretation([ent, build_entity_alert_interpretation(e2), build_entity_alert_interpretation(e3)])
    assert sub and "subsector_alert_label" in sub[0]
    assert "universe_alert_label" in uni

    chain = build_b5_evidence_chain(ent, e1, b2[0], b3[0], b4[0])
    assert chain["phase_id"] == "B5" and "replay_trace" in chain

    report1 = build_phase_b5_alert_interpretation_report([e1, e2, e3], b2_outputs=b2, b3_outputs=b3, b4_outputs=b4, prior_alert_states=prior)
    report2 = build_phase_b5_alert_interpretation_report([e1, e2, e3], b2_outputs=b2, b3_outputs=b3, b4_outputs=b4, prior_alert_states=prior)
    assert report1 == report2
    assert report1["replay_metadata"]["input_checksum"] == report2["replay_metadata"]["input_checksum"]
    assert report1["phase_id"] == "B5"
