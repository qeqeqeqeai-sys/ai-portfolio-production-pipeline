from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    ELIGIBLE_FOR_OPERATOR_REVIEW,
    DEFER_GOVERNANCE_INCOMPLETE,
    DEFER_INSUFFICIENT_DATA,
    DEFER_LOW_MARGINAL_INFORMATION,
    DEFER_SATURATED_OR_REPETITIVE,
    build_cd3_bounded_expansion_plan,
    build_cd3_dashboard_payload,
    build_cd3_expansion_plan_rationale,
    build_cd3_governance_preflight_checklist,
    build_cd3_operator_review_queue,
    build_cd3_replay_expansion_candidate_set,
    certify_cd3_governed_novelty_guided_replay_expansion_plan,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER, build_d7_dashboard_view_model


def _fixtures():
    pool = [
        {"candidate_id": "c1", "replay_window_ref": "w1", "governance_lineage_refs": ["l1"]},
        {"candidate_id": "c2", "replay_window_ref": "w2", "governance_lineage_refs": ["l2"]},
        {"candidate_id": "c3", "replay_window_ref": "w3", "governance_lineage_refs": []},
        {"candidate_id": "c4", "replay_window_ref": "w4", "governance_lineage_refs": ["l4"]},
    ]
    score = [
        {"candidate_id": "c1", "marginal_structural_information_gain": 0.9, "semantic_saturation_penalty": 0.1, "repeated_pattern_penalty": 0.1, "governance_readiness_modifier": 1.0, "missing_dimension_count": 0},
        {"candidate_id": "c2", "marginal_structural_information_gain": 0.5, "semantic_saturation_penalty": 0.1, "repeated_pattern_penalty": 0.1, "governance_readiness_modifier": 1.0, "missing_dimension_count": 0},
        {"candidate_id": "c3", "marginal_structural_information_gain": 0.8, "semantic_saturation_penalty": 0.1, "repeated_pattern_penalty": 0.1, "governance_readiness_modifier": 0.25, "missing_dimension_count": 0},
        {"candidate_id": "c4", "marginal_structural_information_gain": 0.1, "semantic_saturation_penalty": 0.8, "repeated_pattern_penalty": 0.8, "governance_readiness_modifier": 1.0, "missing_dimension_count": 0},
    ]
    buckets = {
        "HIGH_NOVELTY_REPLAY_PRIORITY": ["c1"],
        "BALANCED_DIVERSIFICATION_PRIORITY": ["c2"],
        "GOVERNANCE_INCOMPLETE_CANDIDATE": ["c3"],
        "SATURATED_OR_REPETITIVE_CANDIDATE": ["c4"],
    }
    return pool, score, buckets


def test_cd3_end_to_end_deterministic_and_bounded():
    pool, score, buckets = _fixtures()
    orig = deepcopy((pool, score, buckets))
    candidate_set = build_cd3_replay_expansion_candidate_set(cd2_candidate_pool=pool, cd2_novelty_scorecard=score, cd2_priority_buckets=buckets)
    assert [r["candidate_id"] for r in candidate_set] == ["c1", "c2", "c3", "c4"]
    statuses = {r["candidate_id"]: r["plan_eligibility_status"] for r in candidate_set}
    assert statuses["c1"] == ELIGIBLE_FOR_OPERATOR_REVIEW
    assert statuses["c2"] == ELIGIBLE_FOR_OPERATOR_REVIEW
    assert statuses["c3"] == DEFER_GOVERNANCE_INCOMPLETE
    assert statuses["c4"] == DEFER_SATURATED_OR_REPETITIVE
    plan = build_cd3_bounded_expansion_plan(candidate_set=candidate_set, max_candidate_count=1)
    assert len(plan["selected_candidates"]) == 1
    assert plan["selected_candidates"][0]["candidate_id"] == "c1"
    queue = build_cd3_operator_review_queue(expansion_plan=plan)
    assert queue[0]["recommended_operator_action"] == "REVIEW_FOR_GOVERNED_REPLAY_APPROVAL"
    dashboard = build_cd3_dashboard_payload(expansion_plan=plan, operator_review_queue=queue, rationale=build_cd3_expansion_plan_rationale(expansion_plan=plan))
    assert "Explicit Non-Execution Notice" in dashboard
    assert "Governance Preflight Checklist" in dashboard
    cert = certify_cd3_governed_novelty_guided_replay_expansion_plan(candidate_set=candidate_set, expansion_plan=plan, dashboard_payload=dashboard, operator_review_queue=queue)
    assert cert["no_writes"] and cert["no_direct_sql"] and cert["no_d21_execution"]
    assert (pool, score, buckets) == orig


def test_cd3_degraded_missing_cd2_data_and_checklist():
    candidate_set = build_cd3_replay_expansion_candidate_set(cd2_candidate_pool=[], cd2_novelty_scorecard=[], cd2_priority_buckets={})
    assert candidate_set == []
    checklist = build_cd3_governance_preflight_checklist()
    assert checklist["d8_b4_d21_approval_still_required"] is True


def test_cd3_low_information_and_insufficient_data_deferrals():
    candidate_set = build_cd3_replay_expansion_candidate_set(
        cd2_candidate_pool=[{"candidate_id": "x", "replay_window_ref": "w", "governance_lineage_refs": ["l"]}],
        cd2_novelty_scorecard=[{"candidate_id": "x", "marginal_structural_information_gain": 0.1, "missing_dimension_count": 4, "governance_readiness_modifier": 1.0}],
        cd2_priority_buckets={"LOW_MARGINAL_INFORMATION_PRIORITY": ["x"]},
    )
    assert candidate_set[0]["plan_eligibility_status"] == DEFER_INSUFFICIENT_DATA


def test_d7_cd3_order_and_integration():
    expected = [
        "e6_expectation_executive_summary", "d15_historical_operational_intelligence", "d16_historical_findings_operator_narrative", "d17_historical_confidence_lineage",
        "d18_cross_run_confidence_delta_operator_triage", "d19_triage_explainability_continuity_taxonomy", "h1_historical_density_expansion", "h2_governed_replay_expansion_cycle",
        "cd1_candidate_diversity_strengthening", "h3_cross_replay_structural_transition_intelligence", "cd2_replay_novelty_prioritization", "cd3_governed_novelty_guided_replay_expansion_plan",
    ]
    assert list(D7_RENDER_SECTION_ORDER[:12]) == expected
    vm = build_d7_dashboard_view_model(findings_payload={"rows": [], "row_count": 0}, narratives_payload={"rows": [], "row_count": 0}, evidence_payload={"rows": [], "row_count": 0}, integrity_payload={"manifests": {"rows": []}, "audits": {"rows": []}, "replay": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}})
    assert "cd3_governed_novelty_guided_replay_expansion_plan" in vm
