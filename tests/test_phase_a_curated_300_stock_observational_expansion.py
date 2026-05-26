from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import (
    DOMAIN_TARGETS,
    REQUIRED_FIELDS,
    build_phase_a_curated_300_stock_universe,
    build_phase_a_curated_observational_expansion_framework,
    build_phase_a_sector_allocation_model,
    certify_phase_a_observational_expansion_boundary,
)


def test_api_existence():
    assert callable(build_phase_a_curated_observational_expansion_framework)
    assert callable(build_phase_a_sector_allocation_model)
    assert callable(build_phase_a_curated_300_stock_universe)
    assert callable(certify_phase_a_observational_expansion_boundary)


def test_deterministic_universe_and_size():
    u1 = build_phase_a_curated_300_stock_universe()
    u2 = build_phase_a_curated_300_stock_universe()
    assert u1 == u2
    assert 290 <= len(u1) <= 310
    assert len(u1) == 300


def test_required_fields_present_and_domain_coverage():
    universe = build_phase_a_curated_300_stock_universe()
    for row in universe:
        for field in REQUIRED_FIELDS:
            assert field in row
    domains = {row["sefi_domain"] for row in universe}
    assert set(DOMAIN_TARGETS.keys()).issubset(domains)


def test_anti_random_and_anti_monoculture_posture():
    framework = build_phase_a_curated_observational_expansion_framework()
    allocation = build_phase_a_sector_allocation_model()
    assert framework["anti_random_scaling"] is True
    assert framework["anti_monoculture"] is True
    total = sum(allocation["sector_allocations"].values())
    largest = max(allocation["sector_allocations"].values())
    assert largest / total <= 0.55


def test_boundary_flags_exact_and_disabled_paths():
    flags = certify_phase_a_observational_expansion_boundary()
    assert flags == {
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
