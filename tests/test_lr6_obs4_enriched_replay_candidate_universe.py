from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_obs4_candidate_universe,
    build_lr6_obs4_candidate_universe_context,
    build_lr6_obs4_contradiction_enrichment_entities,
    build_lr6_obs4_density_gap_priorities,
    build_lr6_obs4_ecological_role_taxonomy,
    build_lr6_obs4_markdown_report,
    build_lr6_obs4_megacap_concentration_assessment,
    build_lr6_obs4_propagation_diversity_entities,
    build_lr6_obs4_supervisor_review,
    build_lr6_obs4_weak_signal_bridge_entities,
    certify_lr6_obs4_design_boundary,
)


def test_apis_exist_and_deterministic():
    context_a = build_lr6_obs4_candidate_universe_context()
    context_b = build_lr6_obs4_candidate_universe_context()
    assert context_a == context_b
    assert isinstance(build_lr6_obs4_density_gap_priorities(), list)
    assert isinstance(build_lr6_obs4_ecological_role_taxonomy(), list)


def test_candidate_count_and_megacap_mix():
    universe = build_lr6_obs4_candidate_universe()
    assert 50 <= len(universe) <= 75
    assessment = build_lr6_obs4_megacap_concentration_assessment()
    assert assessment["guardrail_pass"] is True
    assert assessment["megacap_count"] < 5


def test_coverage_completeness_and_bridges():
    roles = {r["role"] for r in build_lr6_obs4_ecological_role_taxonomy()}
    assert len(roles) == 18
    weak = build_lr6_obs4_weak_signal_bridge_entities()
    contradiction = build_lr6_obs4_contradiction_enrichment_entities()
    propagation = build_lr6_obs4_propagation_diversity_entities()
    assert len(weak) >= 8
    assert len(contradiction) >= 8
    assert len(propagation) >= 12


def test_boundary_certification_correctness():
    boundary = certify_lr6_obs4_design_boundary()
    assert boundary == {
        "observation_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def test_no_sql_or_executional_language_in_report():
    review = build_lr6_obs4_supervisor_review()
    markdown = build_lr6_obs4_markdown_report(review).lower()
    forbidden = ["select ", "insert ", "update ", "delete from", "supabase", "persist", "buy ", "sell ", "trade signal", "forecast"]
    for token in forbidden:
        assert token not in markdown
    assert review["supervisor_assessment"]["architecture_expansion_should_remain_frozen"] is True
