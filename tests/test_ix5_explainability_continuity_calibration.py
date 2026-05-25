from copy import deepcopy
from transmission_layers.expectation_failure.expectation_intelligence import (
    build_ix5_explainability_baseline_profile, build_ix5_explainability_delta_analysis,
    build_ix5_boundary_consistency_monitor, build_ix5_narrative_calibration_stability,
    build_ix5_operator_trust_continuity_summary, build_ix5_calibration_recommendations,
    build_ix5_dashboard_payload, certify_ix5_explainability_continuity_calibration,
    EXPLAINABILITY_INSUFFICIENT_HISTORY, EXPLAINABILITY_DEGRADED, EXPLAINABILITY_VOLATILE, EXPLAINABILITY_IMPROVED, EXPLAINABILITY_STABLE,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER

def _ix4(score=90, violations=None):
    return {
        "Interpretability Scorecard": {
            "evidence_traceability_strength": score, "grouping_explainability_strength": score, "compression_explainability_strength": score,
            "structural_clarity_strength": score, "caution_clarity_strength": score, "replay_grounding_strength": score,
            "non_predictive_boundary_strength": score, "non_execution_boundary_strength": score, "auditability_strength": score,
        },
        "Narrative Boundary Enforcement": {"boundary_violations": list(violations or []), "boundary_compliance_status": "COMPLIANT" if not violations else "VIOLATION_DETECTED"},
        "Narrative Explainability Analysis": {"evidence_transparency": score, "caution_transparency": score, "compression_transparency": score, "grouping_transparency": score, "non_predictive_clarity": score, "non_causal_framing_quality": score, "mixed_signal_ambiguity": []},
    }

def test_ix5_missing_history_and_determinism():
    cur=_ix4(88)
    snap=deepcopy(cur)
    base=build_ix5_explainability_baseline_profile(current_ix4_dashboard_payload=cur)
    delta=build_ix5_explainability_delta_analysis(current_ix4_dashboard_payload=cur)
    assert list(base.keys())[0]=="evidence_traceability_baseline"
    assert delta["delta_classification"]==EXPLAINABILITY_INSUFFICIENT_HISTORY
    assert cur==snap

def test_ix5_degraded_and_volatile_behaviors():
    deg=build_ix5_explainability_delta_analysis(current_ix4_dashboard_payload=_ix4(40), prior_ix4_dashboard_payload=_ix4(90))
    assert deg["delta_classification"]==EXPLAINABILITY_DEGRADED
    vol=build_ix5_explainability_delta_analysis(current_ix4_dashboard_payload=_ix4(90), prior_ix4_dashboard_payload={"Interpretability Scorecard": {"evidence_traceability_strength": 0}})
    assert vol["delta_classification"] in {EXPLAINABILITY_VOLATILE, EXPLAINABILITY_IMPROVED, EXPLAINABILITY_STABLE}

def test_ix5_full_payload_and_certification_and_language_notices():
    payload=build_ix5_dashboard_payload(current_ix4_dashboard_payload=_ix4(85, ["predictive_phrasing"]), prior_ix4_dashboard_payload=_ix4(80, ["predictive_phrasing"]))
    monitor=build_ix5_boundary_consistency_monitor(current_ix4_dashboard_payload=_ix4(85,["predictive_phrasing"]), prior_ix4_dashboard_payload=_ix4(80,["predictive_phrasing"]))
    stab=build_ix5_narrative_calibration_stability(current_ix4_dashboard_payload=_ix4(85))
    summ=build_ix5_operator_trust_continuity_summary(baseline_profile=payload["Explainability Baseline Profile"], delta_analysis=payload["Explainability Delta Analysis"], boundary_consistency_monitor=monitor, calibration_stability=stab)
    rec=build_ix5_calibration_recommendations(delta_analysis=payload["Explainability Delta Analysis"], boundary_consistency_monitor=monitor, calibration_stability=stab)
    cert=certify_ix5_explainability_continuity_calibration(dashboard_payload=payload)
    assert "Explicit Non-Predictive Notice" in payload and "Explicit Non-Execution Notice" in payload
    assert isinstance(summ, dict) and isinstance(rec, list)
    assert cert["bounded_score_movement_preserved"] is True

def test_d7_order_contains_ix5_after_ix4():
    assert D7_RENDER_SECTION_ORDER.index("ix5_explainability_continuity_calibration") > D7_RENDER_SECTION_ORDER.index("ix4_interpretability_hardening")
