from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_cd4_replay_drift_profile, build_cd4_semantic_saturation_analysis, build_cd4_expectation_decay_analysis,
    build_cd4_replay_freshness_scoring, build_cd4_replay_half_life_estimation, build_cd4_concentration_instability_analysis,
    build_cd4_operator_attention_queue, build_cd4_dashboard_payload, certify_cd4_expectation_drift_and_replay_saturation_intelligence,
    build_cd4_report_payload, build_cd4_report_markdown,
    FRESH, ACTIVE, AGING, STALE, SATURATED,
)


def _rows():
    return [
        {"candidate_id":"A","semantic_theme_family":"ai","prior_recurrence_count":0,"contradiction_state":"contradiction_rising","continuity_state":"stable","regime_state":"stable"},
        {"candidate_id":"B","semantic_theme_family":"ai","prior_recurrence_count":3,"contradiction_state":"none","continuity_state":"disrupted","regime_state":"transition"},
        {"candidate_id":"C","semantic_theme_family":"energy","prior_recurrence_count":1,"contradiction_state":"none","continuity_state":"stable","regime_state":"stable"},
    ]


def test_cd4_api_and_determinism_bounds_and_buckets():
    rows=_rows(); frozen=deepcopy(rows)
    d1=build_cd4_replay_drift_profile(replay_candidates=rows)
    s1=build_cd4_semantic_saturation_analysis(replay_drift_profile=d1)
    e1=build_cd4_expectation_decay_analysis(replay_drift_profile=d1, semantic_saturation_analysis=s1)
    f1=build_cd4_replay_freshness_scoring(expectation_decay_analysis=e1, semantic_saturation_analysis=s1)
    h1=build_cd4_replay_half_life_estimation(expectation_decay_analysis=e1, semantic_saturation_analysis=s1)
    c1=build_cd4_concentration_instability_analysis(replay_candidates=rows, semantic_saturation_analysis=s1)
    q1=build_cd4_operator_attention_queue(replay_freshness_scoring=f1, expectation_decay_analysis=e1, concentration_instability_analysis=c1)
    dash=build_cd4_dashboard_payload(replay_drift_profile=d1, semantic_saturation_analysis=s1, expectation_decay_analysis=e1, replay_freshness_scoring=f1, replay_half_life_estimation=h1, concentration_instability_analysis=c1, operator_attention_queue=q1)
    cert=certify_cd4_expectation_drift_and_replay_saturation_intelligence(dashboard_payload=dash)
    rpt=build_cd4_report_payload(dashboard_payload=dash, certification=cert)
    md=build_cd4_report_markdown(report_payload=rpt)

    assert rows == frozen
    assert build_cd4_replay_freshness_scoring(expectation_decay_analysis=e1, semantic_saturation_analysis=s1) == f1
    assert all(0 <= x["freshness_score"] <= 100 for x in f1)
    assert all(x["freshness_bucket"] in {FRESH,ACTIVE,AGING,STALE,SATURATED} for x in f1)
    assert [r["candidate_id"] for r in f1] == sorted([r["candidate_id"] for r in f1], key=lambda cid: (-next(v["freshness_score"] for v in f1 if v["candidate_id"]==cid), cid))
    assert all("half_life_bucket" in x for x in h1)
    assert cert["recommendation_only"] is True
    assert "Non-execution" in md
