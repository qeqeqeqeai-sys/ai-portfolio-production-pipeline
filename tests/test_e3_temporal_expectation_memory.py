from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_e1_expectation_intelligence_payload,
    build_e2_evidence_interpretation_payload,
    build_e3_contradiction_drift,
    build_e3_evidence_support_drift,
    build_e3_exhaustion_risk_drift,
    build_e3_expectation_pressure_drift,
    build_e3_fragility_concentration_drift,
    build_e3_semantic_pressure_drift,
    build_e3_temporal_drift_report,
    build_e3_temporal_memory_index,
    normalize_e3_temporal_runs,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _run(run_id, ts, severe=1, contradiction_text="", extra_theme="valuation"):
    findings=[{"finding_id":"F1","finding_type":"liquidity","finding_severity":"HIGH" if severe else "LOW","payload":{"finding_summary":contradiction_text}}, {"finding_id":"F2","finding_type":extra_theme,"finding_severity":"LOW"}]
    narratives=[{"narrative_section":"context","payload":{"text":f"supportive deterior divergence {contradiction_text}"}}]
    evidence=[{"evidence_ref":"E1","finding_id":"F1","payload":{"evidence_summary":"specific contradiction conflict evidence summary with recency and confidence", "linked_finding_ids":["F1"],"kpi_references":["k1"],"confidence":"high","as_of":"2026-01-01"}}]
    e1=build_e1_expectation_intelligence_payload(findings,narratives,evidence)
    e2=build_e2_evidence_interpretation_payload(findings,narratives,evidence,e1)
    return {"run_id":run_id,"run_timestamp":ts,"e1_payload":e1,"e2_payload":e2,"findings":findings,"narratives":narratives}


def test_e3_exports_repeatability_immutability_and_checksum():
    runs=[_run("r2","2026-01-02T00:00:00Z"),_run("r1","2026-01-01T00:00:00Z")]
    clone=deepcopy(runs)
    a=build_e3_temporal_drift_report(runs)
    b=build_e3_temporal_drift_report(deepcopy(runs))
    assert a["e3_checksum"]==b["e3_checksum"]
    assert runs==clone
    assert a["forbidden_capability_inventory"]["writes"] is False


def test_e3_normalization_ordering_ties_missing_timestamps_and_stable():
    runs=[_run("b",None),_run("a","2026-01-01T00:00:00Z"),_run("a","2026-01-01T00:00:00Z")]
    norm=normalize_e3_temporal_runs(runs)
    assert [r["run_id"] for r in norm][:2]==["a","a"]
    assert norm[-1]["run_timestamp"] is None
    idx=build_e3_temporal_memory_index(runs)
    assert idx["run_count"]==3


def test_e3_insufficient_history_degraded_behavior():
    report=build_e3_temporal_drift_report([_run("r1","2026-01-01T00:00:00Z")])
    assert report["history_sufficiency"]=="insufficient_history"
    assert report["temporal_supervisor_summary"]["status"]=="insufficient_history"


def test_e3_drift_components_and_bounded_categories():
    runs=[_run("r1","2026-01-01T00:00:00Z",severe=0,contradiction_text="",extra_theme="valuation"), _run("r2","2026-01-02T00:00:00Z",severe=1,contradiction_text="contradiction divergence conflict",extra_theme="credit")]
    pd=build_e3_expectation_pressure_drift(runs)
    cd=build_e3_contradiction_drift(runs)
    ed=build_e3_evidence_support_drift(runs)
    fd=build_e3_fragility_concentration_drift(runs)
    sd=build_e3_semantic_pressure_drift(runs)
    xd=build_e3_exhaustion_risk_drift(runs)
    assert pd["pressure_direction"] in {"rising","easing","stable","unknown"}
    assert cd["contradiction_persistence_label"] in {"newly_emerging","persistent","fading","resolved","insufficient_history"}
    assert ed["evidence_support_direction"] in {"rising","easing","stable","unknown"}
    assert fd["concentration_direction"] in {"broadening","narrowing","stable"}
    assert sd["semantic_pressure_direction"] in {"rising","mixed","stable"}
    assert xd["exhaustion_direction"] in {"rising","easing","stable","unknown"}


def test_e3_additive_d7_integration_and_e1_e2_compatibility():
    vm=build_d7_dashboard_view_model(
        findings_payload={"rows":[]}, narratives_payload={"rows":[]}, evidence_payload={"rows":[]}, integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}}, historical_runs_payloads=[_run("r1","2026-01-01T00:00:00Z"),_run("r2","2026-01-02T00:00:00Z")]
    )
    assert "e1_expectation_intelligence" in vm and "e2_evidence_interpretation" in vm and "e3_temporal_expectation_memory" in vm
    assert "e3_temporal_history_sufficiency" in vm["supervisor_summary"]
