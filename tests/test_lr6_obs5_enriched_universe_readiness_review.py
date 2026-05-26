from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_obs5_candidate_adjustment_recommendations,
    build_lr6_obs5_contradiction_potential_assessment,
    build_lr6_obs5_first_wave_readiness_decision,
    build_lr6_obs5_markdown_report,
    build_lr6_obs5_overconcentration_risk_assessment,
    build_lr6_obs5_propagation_diversity_assessment,
    build_lr6_obs5_readiness_context,
    build_lr6_obs5_redundancy_and_sparse_category_review,
    build_lr6_obs5_role_balance_assessment,
    build_lr6_obs5_supervisor_review,
    build_lr6_obs5_weak_signal_usefulness_assessment,
    certify_lr6_obs5_readiness_boundary,
)


def test_public_apis_exist_and_are_deterministic():
    a = build_lr6_obs5_supervisor_review()
    b = build_lr6_obs5_supervisor_review()
    assert a == b
    assert isinstance(build_lr6_obs5_readiness_context(), dict)
    assert isinstance(build_lr6_obs5_candidate_adjustment_recommendations(), list)


def test_fallback_behavior_when_obs4_inputs_missing():
    review = build_lr6_obs5_supervisor_review({"lr6_obs4_enriched_replay_candidate_universe": False})
    assert "role_balance_assessment" in review
    assert len(review["role_balance_assessment"]["role_count_map"]) == 18


def test_assessment_presence_and_role_coverage():
    rb = build_lr6_obs5_role_balance_assessment()
    assert len(rb["role_count_map"]) == 18
    assert isinstance(build_lr6_obs5_weak_signal_usefulness_assessment(), dict)
    assert isinstance(build_lr6_obs5_contradiction_potential_assessment(), dict)
    assert isinstance(build_lr6_obs5_propagation_diversity_assessment(), dict)
    assert isinstance(build_lr6_obs5_overconcentration_risk_assessment(), dict)
    assert isinstance(build_lr6_obs5_redundancy_and_sparse_category_review(), dict)


def test_readiness_decision_and_boundary_flags():
    decision = build_lr6_obs5_first_wave_readiness_decision()["decision"]
    assert decision in {
        "READY_FOR_BOUNDED_OBSERVATION_WAVE",
        "CONDITIONALLY_READY_NEEDS_MINOR_REBALANCE",
        "NOT_READY_REQUIRES_REDESIGN",
    }
    boundary = certify_lr6_obs5_readiness_boundary()
    assert boundary["observation_only"] is True
    assert boundary["review_only"] is True
    assert boundary["architecture_expansion_frozen"] is True


def test_markdown_required_sections_and_language_guards():
    markdown = build_lr6_obs5_markdown_report(build_lr6_obs5_supervisor_review()).lower()
    required_sections = [
        "objective",
        "inspected obs4 inputs",
        "role balance assessment",
        "weak-signal usefulness assessment",
        "contradiction potential assessment",
        "propagation diversity assessment",
        "overconcentration risk assessment",
        "redundancy review",
        "sparse category review",
        "candidate adjustment recommendations",
        "first-wave readiness decision",
        "architectural overengineering warning",
        "recommendation for next phase",
    ]
    for section in required_sections:
        assert section in markdown

    forbidden = ["select ", "insert ", "update ", "delete from", "persist to", "execute trade", "buy ", "sell ", "prediction", "forecast"]
    for token in forbidden:
        assert token not in markdown
