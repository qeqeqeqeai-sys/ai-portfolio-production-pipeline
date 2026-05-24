from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence.d18_cross_run_confidence_delta_operator_triage import *
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model, D7_RENDER_SECTION_ORDER


def _sample_d17(cur_band="moderate"):
    return {"Historical Finding Confidence":[{"cluster_id":"C1","finding":"f1","confidence_band":cur_band,"strongest_limiting_constraints":["sparse_replay"],"continuity_strength":"FRAGMENTED","replay_sufficiency":"INSUFFICIENT"}]}


def test_api_presence_and_determinism():
    inv = build_d18_cross_run_confidence_inventory(current_run_payload=_sample_d17("high"), prior_run_payload=_sample_d17("low"), d17_confidence_overlays={"compressed_lineage_checksum":"CHK"}, d17_operator_drilldowns={"strongest_constraints":["A"]})
    assert inv and inv[0]["delta_direction"] == "strengthened"
    assert build_d18_cross_run_confidence_inventory(current_run_payload=_sample_d17("high"), prior_run_payload=_sample_d17("low"), d17_confidence_overlays={"compressed_lineage_checksum":"CHK"}, d17_operator_drilldowns={"strongest_constraints":["A"]}) == inv


def test_immutability_and_fallback_key_and_triage_priority():
    cur={"Historical Finding Confidence":[{"finding":"x","confidence_band":"degraded","strongest_limiting_constraints":["c"]}]}
    prv={"Historical Finding Confidence":[{"finding":"x","confidence_band":"high","strongest_limiting_constraints":["c"]}]}
    snap=deepcopy(cur)
    inv=build_d18_cross_run_confidence_inventory(current_run_payload=cur, prior_run_payload=prv, d17_confidence_overlays={}, d17_operator_drilldowns={})
    assert cur==snap
    assert inv[0]["stable_key"].startswith("FBK:")
    cps=build_d18_constraint_persistence_summary(comparison_inventory=inv)
    triage=build_d18_operator_triage_queue(comparison_inventory=inv, constraint_persistence_summary=cps, regime_transition_confidence_delta=[])
    assert triage[0]["priority_band"] in {"high","medium"}


def test_payload_certification_and_guardrails():
    inv=build_d18_cross_run_confidence_inventory(current_run_payload=_sample_d17("moderate"), prior_run_payload=None, d17_confidence_overlays={"compressed_lineage_checksum":"CHK"}, d17_operator_drilldowns={"strongest_constraints":["A"]})
    ds=build_d18_confidence_delta_summary(comparison_inventory=inv)
    cps=build_d18_constraint_persistence_summary(comparison_inventory=inv)
    reg=build_d18_regime_transition_confidence_delta(comparison_inventory=inv, d16_dashboard_payload={"what_changed":[{"previous_regime":"R1","current_regime":"R2"}]})
    tq=build_d18_operator_triage_queue(comparison_inventory=inv, constraint_persistence_summary=cps, regime_transition_confidence_delta=reg)
    cards=build_d18_priority_drilldown_cards(triage_queue=tq)
    payload=build_d18_dashboard_payload(comparison_inventory=inv, delta_summary=ds, constraint_persistence_summary=cps, regime_transition_confidence_delta=reg, operator_triage_queue=tq, priority_drilldown_cards=cards)
    cert=certify_d18_cross_run_triage(comparison_inventory=inv, delta_summary=ds, triage_queue=tq, dashboard_payload=payload)
    assert cert["certification_status"] in {CERTIFIED_CROSS_RUN_TRIAGE, DEGRADED_CROSS_RUN_TRIAGE}
    text=str(payload).lower()
    for token in ("buy", "sell", "trade", "predict"):
        assert token not in text


def test_d7_integration_and_ordering_smoke():
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]}, narratives_payload={"rows":[]}, evidence_payload={"rows":[]}, integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}})
    assert "d18_cross_run_confidence_delta_operator_triage" in vm
    assert D7_RENDER_SECTION_ORDER.index("d15_historical_operational_intelligence") < D7_RENDER_SECTION_ORDER.index("d16_historical_findings_operator_narrative") < D7_RENDER_SECTION_ORDER.index("d17_historical_confidence_lineage") < D7_RENDER_SECTION_ORDER.index("d18_cross_run_confidence_delta_operator_triage")
