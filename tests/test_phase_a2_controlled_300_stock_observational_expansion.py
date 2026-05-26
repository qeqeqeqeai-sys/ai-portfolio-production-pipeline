from transmission_layers.expectation_failure import (
    build_phase_a2_observational_expansion_configuration,
    build_phase_a2_curated_ingestion_safe_subset,
    build_phase_a2_replay_density_guardrails,
    build_phase_a2_topology_saturation_review,
    build_phase_a2_contradiction_density_review,
    build_phase_a2_propagation_diversity_review,
    build_phase_a2_monoculture_resistance_review,
    build_phase_a2_replay_quality_preservation_review,
    build_phase_a2_longitudinal_continuity_review,
    build_phase_a2_structural_balance_review,
    build_phase_a2_observational_wave_plan,
    build_phase_a2_supervisor_review,
    build_phase_a2_markdown_report,
    certify_phase_a_observational_expansion_boundary,
)


def test_api_existence():
    for fn in [
        build_phase_a2_observational_expansion_configuration,
        build_phase_a2_curated_ingestion_safe_subset,
        build_phase_a2_replay_density_guardrails,
        build_phase_a2_topology_saturation_review,
        build_phase_a2_contradiction_density_review,
        build_phase_a2_propagation_diversity_review,
        build_phase_a2_monoculture_resistance_review,
        build_phase_a2_replay_quality_preservation_review,
        build_phase_a2_longitudinal_continuity_review,
        build_phase_a2_structural_balance_review,
        build_phase_a2_observational_wave_plan,
        build_phase_a2_supervisor_review,
        build_phase_a2_markdown_report,
    ]:
        assert callable(fn)


def test_a2_deterministic_outputs_and_boundary_controls():
    assert build_phase_a2_observational_expansion_configuration() == build_phase_a2_observational_expansion_configuration()
    assert build_phase_a2_curated_ingestion_safe_subset() == build_phase_a2_curated_ingestion_safe_subset()
    assert build_phase_a2_replay_density_guardrails() == build_phase_a2_replay_density_guardrails()
    assert build_phase_a2_topology_saturation_review() == build_phase_a2_topology_saturation_review()
    assert build_phase_a2_contradiction_density_review() == build_phase_a2_contradiction_density_review()
    assert build_phase_a2_propagation_diversity_review() == build_phase_a2_propagation_diversity_review()
    assert build_phase_a2_monoculture_resistance_review() == build_phase_a2_monoculture_resistance_review()
    assert build_phase_a2_replay_quality_preservation_review() == build_phase_a2_replay_quality_preservation_review()
    assert build_phase_a2_longitudinal_continuity_review() == build_phase_a2_longitudinal_continuity_review()
    assert build_phase_a2_observational_wave_plan() == build_phase_a2_observational_wave_plan()

    flags = certify_phase_a_observational_expansion_boundary()
    assert flags["observational_expansion_only"] is True
    assert flags["replay_operationalization_enabled"] is False
    assert flags["replay_density_scaling_enabled"] is False
    assert flags["topology_activation_enabled"] is False
    assert flags["prediction_enabled"] is False
    assert flags["trading_enabled"] is False
    assert flags["write_path_expansion_enabled"] is False
    assert flags["schema_expansion_enabled"] is False
    assert flags["direct_sql_allowed"] is False


def test_supervisor_review_shape_and_report_sections():
    review = build_phase_a2_supervisor_review()
    assert "configuration" in review
    assert "ingestion_safe_subset_findings" in review
    assert "deferred_review_required_findings" in review
    assert "replay_density_guardrails" in review

    md = build_phase_a2_markdown_report(review)
    for header in [
        "## objective",
        "## relationship to A1E",
        "## observational-only boundary",
        "## ingestion-safe subset findings",
        "## deferred/review-required findings",
        "## replay density guardrails",
        "## topology saturation findings",
        "## contradiction density findings",
        "## propagation diversity findings",
        "## monoculture resistance findings",
        "## replay quality preservation findings",
        "## longitudinal continuity findings",
        "## observational wave plan",
        "## governance preservation",
        "## residual risks",
        "## recommendation for Phase B1",
    ]:
        assert header in md
