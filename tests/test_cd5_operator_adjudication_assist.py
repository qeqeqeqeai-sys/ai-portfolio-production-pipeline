from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    BLOCKED_OPERATOR_ADJUDICATION_ASSIST,
    CERTIFIED_OPERATOR_ADJUDICATION_ASSIST,
    DEGRADED_OPERATOR_ADJUDICATION_ASSIST,
    build_cd5_dashboard_payload,
    build_cd5_decision_audit_preview,
    build_cd5_decision_rationale_previews,
    build_cd5_governance_consistency_analysis,
    build_cd5_operator_attention_summary,
    build_cd5_operator_decision_guidance,
    build_cd5_operator_review_checklists,
    build_cd5_report_markdown,
    build_cd5_report_payload,
    certify_cd5_operator_adjudication_assist,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER, build_d7_dashboard_view_model


def _sample_candidates():
    return [
        {"candidate_id": "c2", "novelty_score": 65, "candidate_diversity_score": 55, "governance_complete": True},
        {"candidate_id": "c1", "novelty_score": 25, "candidate_diversity_score": 25, "governance_complete": False},
    ]


def test_cd5_api_and_determinism_and_notices():
    candidates = _sample_candidates()
    before = deepcopy(candidates)
    checks = build_cd5_operator_review_checklists(replay_candidates=candidates)
    rationale = build_cd5_decision_rationale_previews(replay_candidates=candidates)
    guidance = build_cd5_operator_decision_guidance(operator_review_checklists=checks, decision_rationale_previews=rationale)
    consistency = build_cd5_governance_consistency_analysis(operator_review_checklists=checks, operator_decision_guidance=guidance, decision_rationale_previews=rationale)
    audit = build_cd5_decision_audit_preview(operator_review_checklists=checks, decision_rationale_previews=rationale, operator_decision_guidance=guidance)
    attention = build_cd5_operator_attention_summary(operator_decision_guidance=guidance, decision_rationale_previews=rationale)
    payload = build_cd5_dashboard_payload(operator_review_checklists=checks, decision_rationale_previews=rationale, operator_decision_guidance=guidance, governance_consistency_analysis=consistency, decision_audit_preview=audit, operator_attention_summary=attention)
    cert = certify_cd5_operator_adjudication_assist(dashboard_payload=payload)
    report = build_cd5_report_payload(dashboard_payload=payload, certification=cert)
    md = build_cd5_report_markdown(report_payload=report)

    assert [r["candidate_id"] for r in checks] == ["c1", "c2"]
    assert candidates == before
    assert "non-execution" in payload["Explicit Non-Execution Notice"].lower()
    assert "separate" in payload["Decision Audit Preview"]["approval_separation_notice"].lower()
    assert cert["status"] in {CERTIFIED_OPERATOR_ADJUDICATION_ASSIST, DEGRADED_OPERATOR_ADJUDICATION_ASSIST}
    assert "CD5" in md


def test_cd5_degraded_and_blocked_paths():
    candidates = [{"candidate_id": "c1", "novelty_score": 10, "governance_complete": False}]
    checks = build_cd5_operator_review_checklists(replay_candidates=candidates)
    rationale = build_cd5_decision_rationale_previews(replay_candidates=candidates)
    guidance = build_cd5_operator_decision_guidance(operator_review_checklists=checks, decision_rationale_previews=rationale)
    consistency = build_cd5_governance_consistency_analysis(operator_review_checklists=checks, operator_decision_guidance=guidance, decision_rationale_previews=rationale)
    audit = build_cd5_decision_audit_preview(operator_review_checklists=checks, decision_rationale_previews=rationale, operator_decision_guidance=guidance)
    attention = build_cd5_operator_attention_summary(operator_decision_guidance=guidance, decision_rationale_previews=rationale)
    payload = build_cd5_dashboard_payload(operator_review_checklists=checks, decision_rationale_previews=rationale, operator_decision_guidance=guidance, governance_consistency_analysis=consistency, decision_audit_preview=audit, operator_attention_summary=attention)
    degraded = certify_cd5_operator_adjudication_assist(dashboard_payload={k: v for k, v in payload.items() if k != "Explicit Non-Execution Notice"})
    blocked_payload = deepcopy(payload)
    blocked_payload["Governance/Boundary Constraints"]["no_writes"] = False
    blocked = certify_cd5_operator_adjudication_assist(dashboard_payload=blocked_payload)
    assert degraded["status"] == DEGRADED_OPERATOR_ADJUDICATION_ASSIST
    assert blocked["status"] == BLOCKED_OPERATOR_ADJUDICATION_ASSIST


def test_cd5_d7_integration_and_ordering():
    assert "cd5_operator_adjudication_assist" in D7_RENDER_SECTION_ORDER
    assert D7_RENDER_SECTION_ORDER.index("cd4_expectation_drift_and_replay_saturation_intelligence") < D7_RENDER_SECTION_ORDER.index("cd5_operator_adjudication_assist")
    vm = build_d7_dashboard_view_model(findings_payload={"rows": []}, narratives_payload={"rows": []}, evidence_payload={"rows": []}, integrity_payload={"manifests": {"rows": []}, "audits": {"rows": []}, "replay": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}}, historical_runs_payloads=[])
    assert "cd5_operator_adjudication_assist" in vm
