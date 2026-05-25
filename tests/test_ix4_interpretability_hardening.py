from transmission_layers.expectation_failure.expectation_intelligence import (
    build_ix4_cluster_explainability_cards,build_ix4_narrative_explainability_analysis,build_ix4_interpretability_scorecard,
    build_ix4_narrative_boundary_enforcement,build_ix4_operator_explainability_summary,build_ix4_auditability_preview,
    build_ix4_dashboard_payload,certify_ix4_interpretability_hardening,NON_PREDICTIVE_NOTICE,NON_EXECUTION_NOTICE,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER, build_d7_dashboard_view_model


def _ix3():
    clusters=[{"cluster_id":"c1","cluster_type":"semantic fragility clusters","member_insight_refs":["i1","i2"],"evidence_refs":["e1","e2"],"compression_eligibility_status":"ELIGIBLE_FOR_COMPRESSION"}]
    pr=[{"cluster_id":"c1","priority_bucket":"HIGH_SIGNIFICANCE_STRUCTURAL_NARRATIVE"}]
    narr=[{"narrative_id":"n1","cluster_id":"c1","compressed_finding":"Cluster compresses 2 findings.","supporting_evidence_refs":["e1"],"caution_flags":[]}]
    return clusters,pr,narr

def test_ix4_api_and_determinism_and_notices():
    c,p,n=_ix3(); cards1=build_ix4_cluster_explainability_cards(ix3_cluster_inventory=c,ix3_cluster_priority_ranking=p,ix3_compressed_structural_narratives=n); cards2=build_ix4_cluster_explainability_cards(ix3_cluster_inventory=c,ix3_cluster_priority_ranking=p,ix3_compressed_structural_narratives=n)
    assert cards1==cards2 and cards1[0]["cluster_id"]=="c1"
    b=build_ix4_narrative_boundary_enforcement(narratives=n); a=build_ix4_narrative_explainability_analysis(ix3_compressed_structural_narratives=n,ix4_cluster_explainability_cards=cards1); s=build_ix4_interpretability_scorecard(cluster_explainability_cards=cards1,narrative_explainability_analysis=a,boundary_enforcement=b)
    assert all(0<=float(v)<=100 for v in s.values())
    d=build_ix4_dashboard_payload(ix3_cluster_inventory=c,ix3_cluster_priority_ranking=p,ix3_compressed_structural_narratives=n)
    assert d["Explicit Non-Predictive Notice"]==NON_PREDICTIVE_NOTICE
    assert d["Explicit Non-Execution Notice"]==NON_EXECUTION_NOTICE
    cert=certify_ix4_interpretability_hardening(dashboard_payload=d)
    assert cert["status"] in {"CERTIFIED_INTERPRETABILITY_HARDENING","DEGRADED_INTERPRETABILITY_HARDENING"}

def test_ix4_boundary_detection_and_operator_and_audit_preview():
    c,p,n=_ix3(); n=[{**n[0],"compressed_finding":"This will rise and buy now because it causes gains."}]
    cards=build_ix4_cluster_explainability_cards(ix3_cluster_inventory=c,ix3_cluster_priority_ranking=p,ix3_compressed_structural_narratives=n)
    b=build_ix4_narrative_boundary_enforcement(narratives=n)
    assert "predictive_phrasing" in b["boundary_violations"] and "trading_language" in b["boundary_violations"]
    a=build_ix4_narrative_explainability_analysis(ix3_compressed_structural_narratives=n,ix4_cluster_explainability_cards=cards)
    o=build_ix4_operator_explainability_summary(cluster_explainability_cards=cards,narrative_explainability_analysis=a,boundary_enforcement=b)
    pv=build_ix4_auditability_preview(cluster_explainability_cards=cards,boundary_enforcement=b)
    assert "best_explained_narratives" in o and "narrative_lineage_previews" in pv

def test_ix4_d7_order_and_integration():
    assert D7_RENDER_SECTION_ORDER.index("ix4_interpretability_hardening") > D7_RENDER_SECTION_ORDER.index("ix3_structural_narrative_compression")
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]},narratives_payload={"rows":[]},evidence_payload={"rows":[]},integrity_payload={})
    assert "ix4_interpretability_hardening" in vm
