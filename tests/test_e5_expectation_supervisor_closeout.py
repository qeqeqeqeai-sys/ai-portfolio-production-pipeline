from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_e1_expectation_intelligence_payload,
    build_e2_evidence_interpretation_payload,
    build_e3_temporal_drift_report,
    build_e4_semantic_narrative_drift_report,
    build_e5_caveat_consolidation,
    build_e5_composite_synthesis,
    build_e5_evidence_contradiction_synthesis,
    build_e5_expectation_intelligence_envelope,
    build_e5_expectation_regime_synthesis,
    build_e5_supervisor_closeout,
    build_e5_temporal_semantic_synthesis,
    certify_e5_expectation_operational_usefulness,
    classify_e5_expectation_regime,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _run(run_id, ts, txt):
    findings=[{"finding_id":"F1","finding_type":"fragility","finding_severity":"HIGH","payload":{"finding_summary":txt}}]
    narratives=[{"narrative_section":"context","payload":{"text":txt}}]
    evidence=[{"evidence_ref":"E1","finding_id":"F1","payload":{"evidence_summary":txt, "linked_finding_ids":["F1"]}}]
    e1=build_e1_expectation_intelligence_payload(findings,narratives,evidence)
    e2=build_e2_evidence_interpretation_payload(findings,narratives,evidence,e1)
    return {"run_id":run_id,"run_timestamp":ts,"e1_payload":e1,"e2_payload":e2,"findings":findings,"narratives":narratives,"evidence_highlights":evidence}


def test_e5_api_repeatability_immutability_and_bounds():
    runs=[_run("r1","2026-01-01T00:00:00Z","valuation contradiction caveat"),_run("r2","2026-01-02T00:00:00Z","concentration deterior contradiction")]
    e1=runs[-1]["e1_payload"]; e2=runs[-1]["e2_payload"]; e3=build_e3_temporal_drift_report(runs); e4=build_e4_semantic_narrative_drift_report(runs)
    snap=deepcopy((e1,e2,e3,e4))
    a=build_e5_expectation_intelligence_envelope(e1_payload=e1,e2_payload=e2,e3_payload=e3,e4_payload=e4,d7_context={"findings":runs[-1]["findings"]})
    b=build_e5_expectation_intelligence_envelope(e1_payload=deepcopy(e1),e2_payload=deepcopy(e2),e3_payload=deepcopy(e3),e4_payload=deepcopy(e4),d7_context={"findings":runs[-1]["findings"]})
    assert a["e5_checksum"]==b["e5_checksum"]
    assert (e1,e2,e3,e4)==snap
    assert a["e5_governance_flags"]["no_writes"] is True


def test_e5_core_synthesis_components_and_degraded_handling():
    runs=[_run("r1","2026-01-01T00:00:00Z","momentum contradiction"),_run("r2","2026-01-02T00:00:00Z","momentum concentration caveat")]
    e1,e2=runs[-1]["e1_payload"],runs[-1]["e2_payload"]
    e3,e4=build_e3_temporal_drift_report(runs),build_e4_semantic_narrative_drift_report(runs)
    regime=build_e5_expectation_regime_synthesis(e1,e2,e3,e4)
    evidence=build_e5_evidence_contradiction_synthesis(e1,e2,e4)
    ts=build_e5_temporal_semantic_synthesis(e3,e4)
    caveat=build_e5_caveat_consolidation(e2,e3,e4)
    cert=certify_e5_expectation_operational_usefulness(e1,e2,e3,e4,caveat)
    close=build_e5_supervisor_closeout(regime,evidence,ts,caveat,cert)
    assert regime["dominant_expectation_regime"] in {"structurally_supported_expectation","concentrated_fragility_expectation","contradiction_heavy_expectation","exhaustion_risk_expectation","semantically_deteriorating_expectation","evidence_supported_expectation","caveat_heavy_expectation","mixed_expectation_regime","insufficient_intelligence"}
    assert isinstance(evidence["unresolved_contradiction_clusters"], list)
    assert isinstance(ts["persistent_theme_inventory"], list)
    assert caveat["confidence_band"] in {"high","moderate","low"}
    assert cert["e5_operational_status"] in {"OPERATIONALLY_USABLE","DEGRADED_OPERATIONAL_INTELLIGENCE","LIMITED_INTERPRETABILITY","BLOCKED_EXPECTATION_INTELLIGENCE"}
    assert close["operational_usefulness"]==cert["e5_operational_status"]
    assert classify_e5_expectation_regime({}, {}, {}, {})=="insufficient_intelligence"


def test_e5_additive_d7_and_e1_e2_e3_e4_compatibility():
    runs=[_run("r1","2026-01-01T00:00:00Z","valuation contradiction"),_run("r2","2026-01-02T00:00:00Z","valuation concentration contradiction")]
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]},narratives_payload={"rows":[]},evidence_payload={"rows":[]},integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}},historical_runs_payloads=runs)
    assert "e5_expectation_supervisor_closeout" in vm
    assert "e5_operational_status" in vm["supervisor_summary"]
    comp=build_e5_composite_synthesis(vm["e1_expectation_intelligence"],vm["e2_evidence_interpretation"],vm["e3_temporal_expectation_memory"],vm["e4_semantic_theme_memory"])
    assert "e5_supervisor_closeout" in comp
