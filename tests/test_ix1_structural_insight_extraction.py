from copy import deepcopy
from transmission_layers.expectation_failure.expectation_intelligence import (
    build_ix1_structural_insight_inventory, build_ix1_structural_anomaly_detection, build_ix1_transition_pattern_findings,
    build_ix1_expectation_structure_findings, build_ix1_insight_priority_ranking, build_ix1_operator_insight_summary,
    build_ix1_dashboard_payload, certify_ix1_structural_insight_extraction,
    CERTIFIED_STRUCTURAL_INSIGHT_EXTRACTION,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER

def _sample():
    replay=[{"contradiction_state":"persistent_contradiction"}]
    diversity=[{"theme":"ai"}]
    transitions=[{"transition_label":"repeat contradiction loop","transition_risk_score":80,"novelty_score":20}]
    drift=[{"expectation_decay_score":82,"semantic_saturation_score":78,"concentration_score":80,"replay_drift_score":75,"freshness_score":25,"semantic_exhaustion_risk":70}]
    return replay,diversity,transitions,drift

def test_ix1_end_to_end_deterministic_and_certified():
    r,d,t,c = _sample()
    inv=build_ix1_structural_insight_inventory(h1_h2_replay_interpretation=r, cd1_diversity_diagnostics=d, h3_transition_intelligence=t, cd4_drift_saturation_analysis=c)
    an=build_ix1_structural_anomaly_detection(structural_insight_inventory=inv,h3_transition_intelligence=t,cd4_drift_saturation_analysis=c)
    tp=build_ix1_transition_pattern_findings(h3_transition_intelligence=t)
    ef=build_ix1_expectation_structure_findings(structural_insight_inventory=inv,structural_anomaly_detection=an,transition_pattern_findings=tp)
    rank1=build_ix1_insight_priority_ranking(structural_anomaly_detection=an,transition_pattern_findings=tp,expectation_structure_findings=ef)
    rank2=build_ix1_insight_priority_ranking(structural_anomaly_detection=an,transition_pattern_findings=tp,expectation_structure_findings=ef)
    assert rank1==rank2
    summary=build_ix1_operator_insight_summary(insight_priority_ranking=rank1)
    payload=build_ix1_dashboard_payload(structural_insight_inventory=inv,structural_anomaly_detection=an,transition_pattern_findings=tp,expectation_structure_findings=ef,insight_priority_ranking=rank1,operator_insight_summary=summary)
    cert=certify_ix1_structural_insight_extraction(dashboard_payload=payload)
    assert cert["status"]==CERTIFIED_STRUCTURAL_INSIGHT_EXTRACTION
    assert payload["Explicit Non-Predictive Notice"]
    assert payload["Explicit Non-Execution Notice"]

def test_ix1_input_immutable_and_non_speculative_language():
    r,d,t,c=_sample(); rc=deepcopy(r)
    inv=build_ix1_structural_insight_inventory(h1_h2_replay_interpretation=r, cd1_diversity_diagnostics=d, h3_transition_intelligence=t, cd4_drift_saturation_analysis=c)
    assert r==rc
    text=str(inv).lower()
    for forbidden in ["predict","forecast","buy","sell","autonomous conclusion"]:
        assert forbidden not in text

def test_d7_order_contains_ix1_after_cd5():
    assert "ix1_structural_insight_extraction" in D7_RENDER_SECTION_ORDER
    assert D7_RENDER_SECTION_ORDER.index("ix1_structural_insight_extraction") > D7_RENDER_SECTION_ORDER.index("cd5_operator_adjudication_assist")
