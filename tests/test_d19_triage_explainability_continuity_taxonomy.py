from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence.d19_triage_explainability_continuity_taxonomy import *
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model, D7_RENDER_SECTION_ORDER


def _sample_triage():
    return [{"priority_band":"high","priority_rank":1,"finding_or_cluster_ref":"F1","confidence_delta_direction":"weakened","limiting_constraints":["SPARSE_REPLAY"],"compressed_lineage_refs":["L1"],"review_reason":"Weakened confidence"}]


def _sample_inv():
    return [{"stable_key":"F1","delta_direction":"weakened","continuity_status":"FRAGMENTED","replay_depth_status":"INSUFFICIENT","lineage_refs":["L1"]}]


def test_api_presence_and_determinism_and_immutability():
    triage=_sample_triage(); snap=deepcopy(triage)
    inv=build_d19_triage_explainability_inventory(d18_triage_queue=triage, d18_cross_run_confidence_inventory=_sample_inv(), d17_confidence_overlays={"compressed_lineage_checksum":"CHK"}, d16_dashboard_payload={"what_changed":[{"current_regime":"R2"}]})
    assert triage==snap
    assert inv and inv[0]["rank_change_direction"] in {"increased_priority","decreased_priority","unchanged_priority","newly_ranked","removed_from_queue","unavailable"}
    assert build_d19_triage_explainability_inventory(d18_triage_queue=triage, d18_cross_run_confidence_inventory=_sample_inv(), d17_confidence_overlays={"compressed_lineage_checksum":"CHK"}, d16_dashboard_payload={"what_changed":[{"current_regime":"R2"}]}) == inv


def test_taxonomy_constraint_regime_notes_and_certification():
    inv=build_d19_triage_explainability_inventory(d18_triage_queue=_sample_triage(), d18_cross_run_confidence_inventory=_sample_inv())
    rat=build_d19_rank_change_rationale(triage_explainability_inventory=inv, max_chars=180)
    tax=build_d19_continuity_degradation_taxonomy(triage_explainability_inventory=inv, d18_cross_run_confidence_inventory=_sample_inv())
    con=build_d19_constraint_escalation_summary(triage_explainability_inventory=inv, continuity_taxonomy=tax)
    reg=build_d19_regime_transition_impact_explanations(triage_explainability_inventory=inv, d18_regime_transition_confidence_delta=[])
    notes=build_d19_operator_adjudication_notes(triage_explainability_inventory=inv, continuity_taxonomy=tax)
    payload=build_d19_dashboard_payload(triage_explainability_inventory=inv, rank_change_rationales=rat, continuity_taxonomy=tax, constraint_escalation_summary=con, regime_transition_impact_explanations=reg, operator_adjudication_notes=notes)
    cert=certify_d19_triage_explainability(triage_explainability_inventory=inv, rank_change_rationales=rat, continuity_taxonomy=tax, dashboard_payload=payload)
    assert cert["certification_status"] in {CERTIFIED_TRIAGE_EXPLAINABILITY, BLOCKED_TRIAGE_EXPLAINABILITY, DEGRADED_TRIAGE_EXPLAINABILITY}
    assert all(len(x["rank_change_rationale"]) <= 181 for x in rat)
    assert all(n["note_type"] in {"review_lineage","inspect_constraint_history","compare_regime_transition","review_continuity_gap","acknowledge_stable_high_confidence","no_action_required"} for n in notes)
    assert "d19" not in str(payload).lower() or "trade" not in str(payload).lower()


def test_d7_integration_and_order():
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]}, narratives_payload={"rows":[]}, evidence_payload={"rows":[]}, integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}})
    assert "d19_triage_explainability_continuity_taxonomy" in vm
    assert D7_RENDER_SECTION_ORDER.index("d18_cross_run_confidence_delta_operator_triage") < D7_RENDER_SECTION_ORDER.index("d19_triage_explainability_continuity_taxonomy")
