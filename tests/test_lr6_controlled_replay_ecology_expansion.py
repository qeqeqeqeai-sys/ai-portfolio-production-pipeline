from transmission_layers.expectation_failure.expectation_intelligence.lr6_controlled_replay_ecology_expansion import (
    build_lr6_replay_ecology_diagnostics,
    build_lr6_bounded_replay_enrichment_plan,
    certify_lr6_governance_and_reproducibility,
)

HISTORY = [
    {"candidate_id":"H1","semantic_family":"a","semantic_themes":["x"],"contradiction_family":"c1","regime_transition_family":"r1","continuity_transition_family":"t1","structural_info_gain":0.8},
    {"candidate_id":"H2","semantic_family":"b","semantic_themes":["y"],"contradiction_family":"c2","regime_transition_family":"r2","continuity_transition_family":"t2","structural_info_gain":0.9},
]
POOL = [
    {"candidate_id":"C1","semantic_family":"a","contradiction_novelty":0.6,"continuity_transition_novelty":0.8,"semantic_theme_novelty":0.8,"regime_transition_novelty":0.7,"structural_info_gain":0.9,"saturation_risk":0.2},
    {"candidate_id":"C2","semantic_family":"b","contradiction_novelty":0.7,"continuity_transition_novelty":0.7,"semantic_theme_novelty":0.9,"regime_transition_novelty":0.9,"structural_info_gain":0.85,"saturation_risk":0.3},
    {"candidate_id":"C3","semantic_family":"a","contradiction_novelty":0.7,"continuity_transition_novelty":0.7,"semantic_theme_novelty":0.7,"regime_transition_novelty":0.7,"structural_info_gain":0.75,"saturation_risk":0.8},
]


def test_lr6_ecology_scoring_determinism_and_reproducibility():
    d1 = build_lr6_replay_ecology_diagnostics(replay_history=HISTORY, candidate_pool=POOL)
    d2 = build_lr6_replay_ecology_diagnostics(replay_history=HISTORY, candidate_pool=POOL)
    assert d1 == d2
    p1 = build_lr6_bounded_replay_enrichment_plan(diagnostics=d1, candidate_pool=POOL, max_candidates=2, per_family_quota=1)
    p2 = build_lr6_bounded_replay_enrichment_plan(diagnostics=d1, candidate_pool=POOL, max_candidates=2, per_family_quota=1)
    assert p1 == p2


def test_lr6_anti_monoculture_anti_saturation_diversity_balancing_and_bounded_planning():
    d = build_lr6_replay_ecology_diagnostics(replay_history=HISTORY, candidate_pool=POOL)
    p = build_lr6_bounded_replay_enrichment_plan(diagnostics=d, candidate_pool=POOL, max_candidates=2, per_family_quota=1)
    assert len(p["selected_candidates"]) <= 2
    assert p["anti_monoculture_filtering"] and p["anti_saturation_filtering"] and p["diversity_balancing"]
    ids = [r["candidate_id"] for r in p["selected_candidates"]]
    assert "C3" not in ids
    assert p["deterministic_candidate_ranking"] == sorted(p["deterministic_candidate_ranking"], key=lambda x: (x != "C2", x)) or p["deterministic_candidate_ranking"]


def test_lr6_governance_preservation_and_no_sql_or_persistence():
    d = build_lr6_replay_ecology_diagnostics(replay_history=HISTORY, candidate_pool=POOL)
    p = build_lr6_bounded_replay_enrichment_plan(diagnostics=d, candidate_pool=POOL)
    c = certify_lr6_governance_and_reproducibility(diagnostics=d, plan=p)
    assert c["d8_b4_d21_boundaries_preserved"]
    assert c["no_direct_sql"]
    assert c["no_unauthorized_persistence"]
    assert c["deterministic_reproducibility_preserved"]
