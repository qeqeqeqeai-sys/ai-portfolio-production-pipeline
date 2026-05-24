from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_e1_expectation_intelligence_payload,
    build_e2_evidence_interpretation_payload,
    build_e2_evidence_quality_profile,
    build_e2_evidence_finding_linkages,
    classify_e2_evidence_quality_band,
    classify_e2_linkage_strength,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _sample():
    findings=[{"finding_id":"F1","finding_type":"valuation","finding_title":"Valuation strain high","finding_severity":"HIGH","payload":{"finding_summary":"Valuation stretch contradicts earnings support","contradiction_or_divergence_notes":"contradiction with growth narrative"}}]
    narratives=[{"narrative_section":"expectation_pressure","related_finding_ids":["F1"],"payload":{"narrative_text":"Expectation pressure is elevated."}}]
    evidence=[{"finding_id":"F1","evidence_ref":"E1","created_at":"2026-05-01T00:00:00Z","payload":{"evidence_summary":"Valuation multiples diverged from earnings trend indicating contradiction.","kpi_references":["PE_ratio"],"confidence":"high","as_of":"2026-05-01"}}]
    return findings,narratives,evidence


def test_e2_exports_and_classifiers():
    assert classify_e2_evidence_quality_band(80) == "strong"
    assert classify_e2_linkage_strength(20) == "insufficient"


def test_e2_deterministic_repeatable_immutable_and_bounded():
    f,n,e=_sample()
    src=deepcopy((f,n,e))
    e1=build_e1_expectation_intelligence_payload(f,n,e)
    a=build_e2_evidence_interpretation_payload(f,n,e,e1)
    b=build_e2_evidence_interpretation_payload(deepcopy(f),deepcopy(n),deepcopy(e),deepcopy(e1))
    assert a==b
    assert (f,n,e)==src
    assert a["e2_checksum"]==b["e2_checksum"]
    for row in a["evidence_quality_profiles"]:
        assert 0 <= row["evidence_quality_score"] <= 100
        assert row["evidence_quality_band"] in {"strong","moderate","weak","insufficient"}


def test_e2_linkage_chains_buckets_contradictions_caveats_brief():
    f,n,e=_sample()
    e1=build_e1_expectation_intelligence_payload(f,n,e)
    payload=build_e2_evidence_interpretation_payload(f,n,e,e1)
    assert payload["evidence_finding_linkages"]
    assert payload["interpretation_support_chains"]
    assert "strong_supporting_evidence" in payload["evidence_support_buckets"]
    assert isinstance(payload["contradiction_evidence_map"], list)
    assert isinstance(payload["confidence_caveats"], list)
    assert "what_supports_this" in payload["strategist_evidence_brief"]
    assert payload["forbidden_capability_inventory"]["prediction_engine"] is False


def test_e2_graceful_partial_payload_and_stable_sorting():
    q=build_e2_evidence_quality_profile([{"evidence_ref":"B","payload":{}},{"evidence_ref":"A","payload":{}}])
    assert [x["evidence_ref"] for x in q]==["A","B"]
    links=build_e2_evidence_finding_linkages([{"evidence_ref":"E"}], [{"finding_id":"F"}])
    assert links[0]["linkage_strength_band"]=="insufficient"


def test_e2_additive_d7_and_e1_compatibility():
    f,n,e=_sample()
    vm=build_d7_dashboard_view_model(findings_payload={"rows":f}, narratives_payload={"rows":n}, evidence_payload={"rows":e}, integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}})
    assert "e1_expectation_intelligence" in vm
    assert "e2_evidence_interpretation" in vm
    assert "e2_confidence_caveats" in vm["supervisor_summary"]
