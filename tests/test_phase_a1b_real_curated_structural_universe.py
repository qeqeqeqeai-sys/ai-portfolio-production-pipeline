import re

from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import (
    REQUIRED_FIELDS,
    build_phase_a1b_contradiction_cluster_map,
    build_phase_a1b_entity_richness_metadata,
    build_phase_a1b_observational_adjacency_map,
    build_phase_a1b_propagation_role_balance,
    build_phase_a1b_real_curated_structural_universe,
    build_phase_a1b_real_universe_supervisor_review,
    build_phase_a1b_structural_domain_map,
    certify_phase_a_observational_expansion_boundary,
)


def test_api_existence():
    assert callable(build_phase_a1b_real_curated_structural_universe)
    assert callable(build_phase_a1b_structural_domain_map)
    assert callable(build_phase_a1b_entity_richness_metadata)
    assert callable(build_phase_a1b_observational_adjacency_map)
    assert callable(build_phase_a1b_contradiction_cluster_map)
    assert callable(build_phase_a1b_propagation_role_balance)
    assert callable(build_phase_a1b_real_universe_supervisor_review)


def test_deterministic_and_size_and_realish_tickers():
    u1 = build_phase_a1b_real_curated_structural_universe()
    u2 = build_phase_a1b_real_curated_structural_universe()
    assert u1 == u2
    assert 290 <= len(u1) <= 310
    assert len({r["ticker"] for r in u1}) == len(u1)
    assert not any(re.match(r"^[A-Z]{4}\d{4}$", r["ticker"]) for r in u1)


def test_required_fields_and_coverage_and_sector_guardrail():
    universe = build_phase_a1b_real_curated_structural_universe()
    for row in universe:
        for field in REQUIRED_FIELDS:
            assert field in row
    domains = {r["sefi_domain"] for r in universe}
    assert len(domains) >= 27
    sectors = {}
    for row in universe:
        sectors[row["sector"]] = sectors.get(row["sector"], 0) + 1
    assert max(sectors.values()) / len(universe) <= 0.70


def test_deterministic_maps_and_richness():
    assert build_phase_a1b_contradiction_cluster_map() == build_phase_a1b_contradiction_cluster_map()
    assert build_phase_a1b_observational_adjacency_map() == build_phase_a1b_observational_adjacency_map()
    assert build_phase_a1b_propagation_role_balance() == build_phase_a1b_propagation_role_balance()
    metadata = build_phase_a1b_entity_richness_metadata()
    sample = next(iter(metadata.values()))
    for field in [
        "contradiction_richness_score",
        "adjacency_richness_score",
        "propagation_richness_score",
        "topology_richness_score",
        "regime_diversity_score",
        "replay_ecology_richness_score",
        "monoculture_risk_score",
        "low_information_growth_risk_score",
    ]:
        assert field in sample


def test_governance_boundary_unchanged_and_no_operational_paths():
    flags = certify_phase_a_observational_expansion_boundary()
    assert flags["observational_expansion_only"] is True
    assert flags["replay_operationalization_enabled"] is False
    assert flags["replay_density_scaling_enabled"] is False
    assert flags["topology_activation_enabled"] is False
    assert flags["prediction_enabled"] is False
    assert flags["trading_enabled"] is False
    assert flags["schema_expansion_enabled"] is False
    assert flags["direct_sql_allowed"] is False
