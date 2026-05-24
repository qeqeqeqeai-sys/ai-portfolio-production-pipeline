from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_e1_expectation_intelligence_payload,
    build_e2_evidence_interpretation_payload,
    build_e3_temporal_drift_report,
    build_e4_expectation_framing_drift,
    build_e4_narrative_drift_profile,
    build_e4_semantic_contradiction_clusters,
    build_e4_semantic_memory_supervisor_summary,
    build_e4_semantic_narrative_drift_report,
    build_e4_semantic_theme_memory,
    build_e4_theme_evidence_support_profile,
    build_e4_theme_inventory,
    build_e4_theme_memory_index,
    classify_e4_theme_category,
    extract_e4_semantic_theme_signals,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _run(run_id, ts, txt):
    findings=[{"finding_id":"F1","finding_type":"fragility","finding_severity":"HIGH","payload":{"finding_summary":txt}}]
    narratives=[{"narrative_section":"context","payload":{"text":txt}}]
    evidence=[{"evidence_ref":"E1","finding_id":"F1","payload":{"evidence_summary":txt, "linked_finding_ids":["F1"]}}]
    e1=build_e1_expectation_intelligence_payload(findings,narratives,evidence)
    e2=build_e2_evidence_interpretation_payload(findings,narratives,evidence,e1)
    e3=build_e3_temporal_drift_report([{"run_id":"x","run_timestamp":"2026-01-01T00:00:00Z","e1_payload":e1,"e2_payload":e2,"findings":findings,"narratives":narratives},{"run_id":"y","run_timestamp":"2026-01-02T00:00:00Z","e1_payload":e1,"e2_payload":e2,"findings":findings,"narratives":narratives}])
    return {"run_id":run_id,"run_timestamp":ts,"e1_payload":e1,"e2_payload":e2,"e3_payload":e3,"findings":findings,"narratives":narratives,"evidence_highlights":evidence}


def test_e4_api_repeatability_immutability_and_bounds():
    runs=[_run("r1","2026-01-01T00:00:00Z","valuation momentum contradiction caveat"),_run("r2","2026-01-02T00:00:00Z","concentration deterior contradiction")]
    c=deepcopy(runs)
    a=build_e4_semantic_narrative_drift_report(runs)
    b=build_e4_semantic_narrative_drift_report(deepcopy(runs))
    assert a["e4_checksum"]==b["e4_checksum"]
    assert runs==c
    assert a["forbidden_capability_inventory"]["writes"] is False
    for row in a["theme_evidence_support_profile"]:
        assert 0 <= row["theme_support_score"] <= 100
        assert row["theme_support_band"] in {"strong","moderate","weak","insufficient"}


def test_e4_core_components_and_ordering_and_insufficient_history():
    runs=[_run("r1","2026-01-01T00:00:00Z","momentum contradiction"),_run("r2","2026-01-02T00:00:00Z","momentum concentration caveat")]
    assert classify_e4_theme_category("valuation stretch")=="valuation_pressure"
    sigs=extract_e4_semantic_theme_signals(runs[0])
    inv=build_e4_theme_inventory(runs)
    mem=build_e4_semantic_theme_memory(runs)
    idx=build_e4_theme_memory_index(runs)
    nd=build_e4_narrative_drift_profile(runs)
    cc=build_e4_semantic_contradiction_clusters(runs)
    fd=build_e4_expectation_framing_drift(runs)
    esp=build_e4_theme_evidence_support_profile(runs)
    sup=build_e4_semantic_memory_supervisor_summary(runs)
    assert sigs and inv and mem and idx["theme_count"]>=1
    assert nd["narrative_drift_direction"] in {"reinforcing","deteriorating","easing","mixed","stable","unknown"}
    assert fd["framing_shift_direction"] in {"reinforcing","deteriorating","easing","mixed","stable","unknown"}
    assert isinstance(cc,list) and isinstance(esp,list)
    assert "persisted_themes" in sup
    cats=[m["theme_category"] for m in mem]
    assert cats==sorted(cats)
    degraded=build_e4_semantic_narrative_drift_report([runs[0]])
    assert degraded["theme_memory_index"]["history_sufficiency"]=="insufficient_history"


def test_e4_additive_d7_and_e1_e2_e3_compatibility():
    runs=[_run("r1","2026-01-01T00:00:00Z","valuation contradiction"),_run("r2","2026-01-02T00:00:00Z","valuation concentration contradiction")]
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]},narratives_payload={"rows":[]},evidence_payload={"rows":[]},integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}},historical_runs_payloads=runs)
    assert "e1_expectation_intelligence" in vm and "e2_evidence_interpretation" in vm and "e3_temporal_expectation_memory" in vm
    assert "e4_semantic_theme_memory" in vm
