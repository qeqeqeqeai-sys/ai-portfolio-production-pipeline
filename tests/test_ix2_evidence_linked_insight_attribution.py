from copy import deepcopy
from transmission_layers.expectation_failure.expectation_intelligence.ix2_evidence_linked_insight_attribution import (
    build_ix2_insight_evidence_map, build_ix2_insight_lineage_index, build_ix2_cross_run_delta_tracker,
    build_ix2_evidence_strength_scorecard, build_ix2_delta_interpretation_summary,
    build_ix2_evidence_linked_operator_summary, build_ix2_dashboard_payload,
    certify_ix2_evidence_linked_insight_attribution, build_ix2_report_payload, build_ix2_report_markdown,
    CERTIFIED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION, INSUFFICIENT_HISTORY, MISSING_EVIDENCE_ATTRIBUTION,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER, build_d7_dashboard_view_model


def _sample():
    ix1=[{"insight_id":"ix1_001","bucket":"HIGH","summary":"contradiction loop"},{"insight_id":"ix1_002","bucket":"MODERATE","summary":"semantic fragility"}]
    replay=[{"replay_ref":"r1","confidence_state":"unstable","continuity_state":"fractured","contradiction_state":"present"}]
    h3=[{"transition_ref":"t1","chain_signature":"contradiction loop","regime_state":"volatile"}]
    cd4=[{"diagnostic_ref":"d1","theme_family":"theme_a","semantic_theme":"theme_a"}]
    return ix1,replay,h3,cd4


def test_ix2_api_and_determinism_and_bounds():
    ix1,replay,h3,cd4=_sample(); orig=deepcopy(ix1)
    m1=build_ix2_insight_evidence_map(ix1_insight_priority_ranking=ix1,h1_h2_replay_interpretation=replay,h3_transition_intelligence=h3,cd4_drift_saturation_analysis=cd4)
    m2=build_ix2_insight_evidence_map(ix1_insight_priority_ranking=ix1,h1_h2_replay_interpretation=replay,h3_transition_intelligence=h3,cd4_drift_saturation_analysis=cd4)
    assert m1==m2 and ix1==orig
    l=build_ix2_insight_lineage_index(insight_evidence_map=m1)
    d=build_ix2_cross_run_delta_tracker(current_insight_evidence_map=m1,prior_insight_evidence_map=None)
    s=build_ix2_evidence_strength_scorecard(insight_evidence_map=m1,cross_run_delta_tracker=d)
    ds=build_ix2_delta_interpretation_summary(cross_run_delta_tracker=d,evidence_strength_scorecard=s,insight_evidence_map=m1)
    os=build_ix2_evidence_linked_operator_summary(insight_evidence_map=m1,cross_run_delta_tracker=d,evidence_strength_scorecard=s)
    p=build_ix2_dashboard_payload(insight_evidence_map=m1,insight_lineage_index=l,cross_run_delta_tracker=d,evidence_strength_scorecard=s,delta_interpretation_summary=ds,evidence_linked_operator_summary=os)
    c=certify_ix2_evidence_linked_insight_attribution(dashboard_payload=p)
    assert c["status"]==CERTIFIED_EVIDENCE_LINKED_INSIGHT_ATTRIBUTION
    assert p["Explicit Non-Predictive Notice"] and p["Explicit Non-Execution Notice"]
    for row in s:
        assert 0<=row["overall_strength"]<=100
        for v in row["scores"].values(): assert 0<=v<=100
    assert all(r["delta_classification"]==INSUFFICIENT_HISTORY for r in d)


def test_ix2_missing_partial_thin_and_language_constraints():
    m=build_ix2_insight_evidence_map(ix1_insight_priority_ranking=[{"insight_id":"ix1_003","summary":"unknown","bucket":"LOW"}],h1_h2_replay_interpretation=[],h3_transition_intelligence=[],cd4_drift_saturation_analysis=[])
    assert m[0]["attribution_completeness_status"]==MISSING_EVIDENCE_ATTRIBUTION
    text=str(m).lower()+str(build_ix2_report_markdown(report_payload=build_ix2_report_payload(dashboard_payload={},certification={}))).lower()
    for bad in ["buy","sell","autonomous conclusion"]:
        assert bad not in text


def test_ix2_d7_ordering_and_integration():
    assert D7_RENDER_SECTION_ORDER.index("ix2_evidence_linked_insight_attribution") > D7_RENDER_SECTION_ORDER.index("ix1_structural_insight_extraction")
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]},narratives_payload={"rows":[]},evidence_payload={"rows":[]},integrity_payload={})
    assert "ix2_evidence_linked_insight_attribution" in vm
