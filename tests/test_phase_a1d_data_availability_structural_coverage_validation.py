from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import (
    build_phase_a1b_real_curated_structural_universe,
    build_phase_a1d_data_availability_validation_framework,
    build_phase_a1d_required_fmp_coverage_contract,
    build_phase_a1d_entity_data_viability_profiles,
    build_phase_a1d_listing_complexity_review,
    build_phase_a1d_historical_continuity_expectation,
    build_phase_a1d_replay_ecology_data_viability_classification,
    build_phase_a1d_non_viable_entity_candidates,
    build_phase_a1d_data_coverage_gap_review,
    build_phase_a1d_supervisor_review,
    build_phase_a1d_markdown_report,
    certify_phase_a_observational_expansion_boundary,
)


def test_api_existence():
    for fn in [
        build_phase_a1d_data_availability_validation_framework,
        build_phase_a1d_required_fmp_coverage_contract,
        build_phase_a1d_entity_data_viability_profiles,
        build_phase_a1d_listing_complexity_review,
        build_phase_a1d_historical_continuity_expectation,
        build_phase_a1d_replay_ecology_data_viability_classification,
        build_phase_a1d_non_viable_entity_candidates,
        build_phase_a1d_data_coverage_gap_review,
        build_phase_a1d_supervisor_review,
        build_phase_a1d_markdown_report,
    ]:
        assert callable(fn)


def test_framework_deterministic_and_no_live_calls():
    a = build_phase_a1d_data_availability_validation_framework()
    b = build_phase_a1d_data_availability_validation_framework()
    assert a == b
    assert a["network_calls_allowed"] is False
    assert a["fmp_calls_allowed"] is False
    assert a["supabase_writes_allowed"] is False
    assert a["schema_expansion_allowed"] is False


def test_fmp_coverage_contract_completeness_and_status():
    c = build_phase_a1d_required_fmp_coverage_contract()
    required = {
        "profile","quote","historical_price_daily","market_cap","key_metrics","ratios","enterprise_values",
        "income_statement","balance_sheet_statement","cash_flow_statement","financial_growth",
        "analyst_estimates_optional","earnings_calendar_optional",
    }
    assert set(c.keys()) == required
    for v in c.values():
        assert v["validation_status"] == "CONTRACT_ONLY_NOT_PROBED"


def test_entity_profiles_deterministic_and_cover_universe():
    p1 = build_phase_a1d_entity_data_viability_profiles()
    p2 = build_phase_a1d_entity_data_viability_profiles()
    assert p1 == p2
    u = build_phase_a1b_real_curated_structural_universe()
    assert len(p1) == len(u)
    assert {x["ticker"] for x in p1} == {x["ticker"] for x in u}


def test_reviews_and_classification_deterministic():
    assert build_phase_a1d_listing_complexity_review() == build_phase_a1d_listing_complexity_review()
    assert build_phase_a1d_historical_continuity_expectation() == build_phase_a1d_historical_continuity_expectation()
    assert build_phase_a1d_replay_ecology_data_viability_classification() == build_phase_a1d_replay_ecology_data_viability_classification()
    assert build_phase_a1d_non_viable_entity_candidates() == build_phase_a1d_non_viable_entity_candidates()
    assert build_phase_a1d_data_coverage_gap_review() == build_phase_a1d_data_coverage_gap_review()


def test_governance_boundary_unchanged_and_controls_off():
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
    assert flags == expected


def test_supervisor_and_markdown_shape():
    s = build_phase_a1d_supervisor_review()
    assert "coverage_gap_review" in s
    md = build_phase_a1d_markdown_report()
    assert "# Phase A1D Data Availability & Structural Coverage Validation" in md
    assert "CONTRACT_ONLY_NOT_PROBED" in md
