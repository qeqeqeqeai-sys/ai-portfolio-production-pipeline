from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import *


def test_api_existence():
    for fn in [
        build_phase_a1c_real_company_name_map,
        build_phase_a1c_structural_adjacency_classes,
        build_phase_a1c_structural_adjacency_map,
        build_phase_a1c_contradiction_taxonomy,
        build_phase_a1c_entity_contradiction_profiles,
        build_phase_a1c_propagation_taxonomy,
        build_phase_a1c_entity_propagation_profiles,
        build_phase_a1c_monoculture_review,
        build_phase_a1c_low_information_node_review,
        build_phase_a1c_universe_replacement_review,
        build_phase_a1c_supervisor_review,
        build_phase_a1c_markdown_report,
    ]:
        assert callable(fn)


def test_company_name_hardening_deterministic_no_placeholder():
    a = build_phase_a1c_real_company_name_map()
    b = build_phase_a1c_real_company_name_map()
    assert a == b
    for row in a:
        assert set(row.keys()) == {"ticker", "company_name", "company_name_review_status", "name_source"}
        assert row["company_name"] != f"{row['ticker']} Corp"


def test_adjacency_determinism_and_fields():
    classes = build_phase_a1c_structural_adjacency_classes()
    assert classes == build_phase_a1c_structural_adjacency_classes()
    m1 = build_phase_a1c_structural_adjacency_map()
    m2 = build_phase_a1c_structural_adjacency_map()
    assert m1 == m2
    assert m1
    for link in m1:
        assert set(link.keys()) == {"source_ticker", "target_ticker", "adjacency_class", "linkage_rationale", "activation_status"}
        assert "index" not in link["linkage_rationale"].lower()
        assert link["activation_status"] == "observational_only"


def test_taxonomies_and_profiles_deterministic():
    c = build_phase_a1c_contradiction_taxonomy()
    p = build_phase_a1c_propagation_taxonomy()
    assert len(c) == 20
    assert len(p) == 15
    assert c == build_phase_a1c_contradiction_taxonomy()
    assert p == build_phase_a1c_propagation_taxonomy()
    assert build_phase_a1c_entity_contradiction_profiles() == build_phase_a1c_entity_contradiction_profiles()
    assert build_phase_a1c_entity_propagation_profiles() == build_phase_a1c_entity_propagation_profiles()


def test_reviews_and_governance_and_no_ops_expansion():
    assert build_phase_a1c_monoculture_review() == build_phase_a1c_monoculture_review()
    assert build_phase_a1c_low_information_node_review() == build_phase_a1c_low_information_node_review()
    assert build_phase_a1c_universe_replacement_review() == build_phase_a1c_universe_replacement_review()

    flags = certify_phase_a_observational_expansion_boundary()
    expected = {
        "observational_expansion_only": True,
        "replay_operationalization_enabled": False,
        "replay_density_scaling_enabled": False,
        "topology_activation_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "autonomous_replay_activation_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "write_path_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "direct_sql_allowed": False,
        "append_only_required": True,
        "deterministic_governance_required": True,
    }
    assert dict(flags) == expected

    src = open("transmission_layers/expectation_failure/phase_a1_curated_observational_expansion.py", "r", encoding="utf-8").read().lower()
    banned = ["requests.", "http://", "https://", "supabase", "insert into", "alter table", "create table", "fmp"]
    for token in banned:
        assert token not in src
