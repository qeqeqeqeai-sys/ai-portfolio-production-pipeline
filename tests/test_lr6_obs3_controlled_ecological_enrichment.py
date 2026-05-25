from transmission_layers.expectation_failure.replay_ecology.lr6_obs3_controlled_ecological_enrichment import (
    build_lr6_obs3_contradiction_migration_watchlist,
    build_lr6_obs3_density_gap_assessment,
    build_lr6_obs3_ecological_enrichment_context,
    build_lr6_obs3_markdown_report,
    build_lr6_obs3_propagation_mutation_watchlist,
    build_lr6_obs3_replay_stress_observation_plan,
    build_lr6_obs3_semantic_gravity_assessment,
    build_lr6_obs3_supervisor_review,
    build_lr6_obs3_weak_signal_bridge_candidates,
    certify_lr6_obs3_observation_boundary,
)

REQUIRED_SECTIONS = {
    "## Objective",
    "## Inspected LR6 Inputs",
    "## Ecological Enrichment Rationale",
    "## Strongest Density Gaps",
    "## Weak-Signal Bridge Opportunities",
    "## Contradiction Migration Watchlist",
    "## Propagation Mutation Watchlist",
    "## Semantic Gravity / Monoculture Assessment",
    "## Replay Stress Observation Plan",
    "## Architectural Overengineering Warning",
    "## Recommendation for Next Observation Cycle",
}
BANNED = {"predict", "prediction", "trade", "trading", "buy", "sell", "select ", "insert ", "update "}


def _walk(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from _walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from _walk(x)
    elif isinstance(v, str):
        yield v


def test_obs3_required_apis_determinism_and_fallbacks():
    context_a = build_lr6_obs3_ecological_enrichment_context(None)
    context_b = build_lr6_obs3_ecological_enrichment_context({})
    assert context_a == context_b
    assert context_a["coverage_summary"]["fallback_mode_engaged"] is True

    density = build_lr6_obs3_density_gap_assessment(context_a)
    weak = build_lr6_obs3_weak_signal_bridge_candidates(context_a, max_candidates=9)
    contradiction = build_lr6_obs3_contradiction_migration_watchlist(context_a)
    propagation = build_lr6_obs3_propagation_mutation_watchlist(context_a)
    gravity = build_lr6_obs3_semantic_gravity_assessment(context_a, weak)
    stress = build_lr6_obs3_replay_stress_observation_plan(context_a)

    assert density["density_gap_count"] > 0
    assert len(weak) == 9
    assert len(contradiction) > 0
    assert len(propagation) > 0
    assert "semantic_gravity_score" in gravity
    assert "stress_design" in stress


def test_obs3_supervisor_review_markdown_and_boundary_flags():
    first = build_lr6_obs3_supervisor_review({})
    second = build_lr6_obs3_supervisor_review({})
    assert first == second

    cert = certify_lr6_obs3_observation_boundary()
    assert cert == {
        "observation_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }
    assert first["observation_dimensions"]["architecture_expansion_should_remain_frozen"] is True

    report = build_lr6_obs3_markdown_report(first)
    for section in REQUIRED_SECTIONS:
        assert section in report


def test_obs3_non_prediction_non_trading_non_sql_and_non_megacap_only():
    review = build_lr6_obs3_supervisor_review({})
    text = " ".join(s.lower() for s in _walk(review))
    for banned in BANNED:
        assert banned not in text

    bridge_categories = {x["bridge_category"] for x in review["weak_signal_bridge_candidates"]}
    assert any("non_megacap" in c or "weak_signal" in c for c in bridge_categories)
    assert len(review["weak_signal_bridge_candidates"]) <= 20
