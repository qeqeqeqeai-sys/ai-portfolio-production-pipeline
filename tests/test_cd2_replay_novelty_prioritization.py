from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_cd2_replay_candidate_pool,
    build_cd2_novelty_scorecard,
    build_cd2_candidate_priority_buckets,
    build_cd2_replay_selection_rationale,
    build_cd2_prioritization_summary,
    build_cd2_operator_guardrails,
    build_cd2_dashboard_payload,
    certify_cd2_replay_novelty_prioritization,
    CERTIFIED_REPLAY_NOVELTY_PRIORITIZATION,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _sample():
    return [
        {"candidate_id": "c2", "regime_state": "risk_on", "contradiction_state": "divergent", "continuity_state": "stable", "confidence_state": "converging", "semantic_theme_family": "liquidity", "pattern_family": "pf_a", "prior_recurrence_count": 0, "transition_signature": "t1", "governance_lineage_refs": ["l1"]},
        {"candidate_id": "c1", "regime_state": "risk_off", "contradiction_state": "aligned", "continuity_state": "fragmented", "confidence_state": "diverging", "semantic_theme_family": "credit", "pattern_family": "pf_a", "prior_recurrence_count": 2, "transition_signature": "t2", "governance_lineage_refs": []},
    ]


def test_cd2_deterministic_and_bounded_and_immutable():
    rows = _sample()
    frozen = deepcopy(rows)
    pool = build_cd2_replay_candidate_pool(replay_windows=rows)
    assert [r["candidate_id"] for r in pool] == ["c1", "c2"]
    score1 = build_cd2_novelty_scorecard(candidate_pool=pool)
    score2 = build_cd2_novelty_scorecard(candidate_pool=pool)
    assert score1 == score2
    for row in score1:
        for k, v in row.items():
            if k.endswith(("novelty", "rarity", "gain", "penalty", "modifier")):
                assert 0.0 <= float(v) <= 1.0
    assert rows == frozen


def test_cd2_buckets_rationale_guardrails_and_certification():
    pool = build_cd2_replay_candidate_pool(replay_windows=_sample())
    score = build_cd2_novelty_scorecard(candidate_pool=pool)
    buckets1 = build_cd2_candidate_priority_buckets(candidate_pool=pool, novelty_scorecard=score)
    buckets2 = build_cd2_candidate_priority_buckets(candidate_pool=pool, novelty_scorecard=score)
    assert buckets1 == buckets2
    rationale1 = build_cd2_replay_selection_rationale(candidate_pool=pool, novelty_scorecard=score, priority_buckets=buckets1)
    rationale2 = build_cd2_replay_selection_rationale(candidate_pool=pool, novelty_scorecard=score, priority_buckets=buckets1)
    assert rationale1 == rationale2
    guards = build_cd2_operator_guardrails()
    assert all(guards.values())
    summary = build_cd2_prioritization_summary(candidate_pool=pool, novelty_scorecard=score, priority_buckets=buckets1)
    dashboard = build_cd2_dashboard_payload(candidate_pool=pool, novelty_scorecard=score, priority_buckets=buckets1, selection_rationale=rationale1, prioritization_summary=summary, operator_guardrails=guards)
    cert = certify_cd2_replay_novelty_prioritization(candidate_pool=pool, novelty_scorecard=score, dashboard_payload=dashboard, operator_guardrails=guards)
    assert cert["status"] in {CERTIFIED_REPLAY_NOVELTY_PRIORITIZATION, "DEGRADED_REPLAY_NOVELTY_PRIORITIZATION"}


def test_cd2_degraded_missing_and_governance_incomplete_behavior_and_d7_integration():
    pool = build_cd2_replay_candidate_pool(replay_windows=[{"candidate_id": "x"}])
    score = build_cd2_novelty_scorecard(candidate_pool=pool)
    buckets = build_cd2_candidate_priority_buckets(candidate_pool=pool, novelty_scorecard=score)
    assert "x" in buckets["INSUFFICIENT_DATA_CANDIDATE"] or "x" in buckets["GOVERNANCE_INCOMPLETE_CANDIDATE"]
    vm = build_d7_dashboard_view_model(findings_payload={"rows": []}, narratives_payload={"rows": []}, evidence_payload={"rows": []}, integrity_payload={"manifests": {"rows": []}, "audits": {"rows": []}, "replay": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}})
    assert "cd2_replay_novelty_prioritization" in vm
    text = str(vm["cd2_replay_novelty_prioritization"]).lower()
    assert "select " not in text and "insert " not in text and "update " not in text
    assert "recommendation_only" in text and "d21 command" not in text
