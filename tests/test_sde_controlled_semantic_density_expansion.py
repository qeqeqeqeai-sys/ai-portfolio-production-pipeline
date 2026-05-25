from transmission_layers.expectation_failure.expectation_intelligence.sde_controlled_semantic_density_expansion import (
    build_sde_ecosystem_readiness_diagnostics,
    build_sde_curated_expansion_plan,
    certify_sde_governance_preservation,
)

ROWS = [
    {"entity_id":"E1","adjacency_cluster":"a","propagation_pathway":"p1","contradiction_topology":"c1","regime_cluster":"r1","linked_entity_refs":["E2"],"topology_relevance":0.9,"contradiction_interaction_potential":0.8,"propagation_pathway_value":0.8,"regime_diversity_value":0.7,"structural_interaction_strength":0.8,"monoculture_penalty":0.1,"information_density":0.9},
    {"entity_id":"E2","adjacency_cluster":"b","propagation_pathway":"p2","contradiction_topology":"c2","regime_cluster":"r2","linked_entity_refs":["E1"],"topology_relevance":0.85,"contradiction_interaction_potential":0.7,"propagation_pathway_value":0.7,"regime_diversity_value":0.9,"structural_interaction_strength":0.7,"monoculture_penalty":0.1,"information_density":0.8},
    {"entity_id":"E3","adjacency_cluster":"a","propagation_pathway":"p1","contradiction_topology":"c1","regime_cluster":"r1","linked_entity_refs":[],"topology_relevance":0.4,"contradiction_interaction_potential":0.4,"propagation_pathway_value":0.4,"regime_diversity_value":0.4,"structural_interaction_strength":0.4,"monoculture_penalty":0.7,"information_density":0.2},
]


def test_sde_diagnostics_deterministic():
    d1 = build_sde_ecosystem_readiness_diagnostics(ecosystem_candidates=ROWS, target_entity_count=300)
    d2 = build_sde_ecosystem_readiness_diagnostics(ecosystem_candidates=ROWS, target_entity_count=300)
    assert d1 == d2
    assert d1["ecosystem_adjacency_diversity"] > 0


def test_sde_curated_plan_filters_and_bounds():
    d = build_sde_ecosystem_readiness_diagnostics(ecosystem_candidates=ROWS)
    plan = build_sde_curated_expansion_plan(ecosystem_candidates=ROWS, diagnostics=d, target_entity_count=300, max_step_size=2)
    selected_ids = [r["entity_id"] for r in plan["selected_entities"]]
    assert len(selected_ids) <= 2
    assert "E3" not in selected_ids
    assert plan["anti_random_scaling_filter"] and plan["anti_monoculture_filter"] and plan["anti_low_information_growth_filter"]
    assert plan["lr6_operationalization_status"] == "deferred_pending_semantic_ecosystem_richness"


def test_sde_governance_and_no_sql_preserved():
    d = build_sde_ecosystem_readiness_diagnostics(ecosystem_candidates=ROWS)
    plan = build_sde_curated_expansion_plan(ecosystem_candidates=ROWS, diagnostics=d)
    cert = certify_sde_governance_preservation(diagnostics=d, plan=plan)
    assert cert["d8_b4_d21_boundary_preserved"]
    assert cert["no_direct_sql"] and cert["no_unauthorized_persistence"] and cert["no_replay_flooding"]
