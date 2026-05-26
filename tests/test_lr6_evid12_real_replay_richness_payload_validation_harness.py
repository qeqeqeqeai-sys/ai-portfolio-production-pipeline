from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_evid12_comparison_readiness_review,
    build_lr6_evid12_markdown_report,
    build_lr6_evid12_rejection_safety_review,
    build_lr6_evid12_status_transition_review,
    build_lr6_evid12_supervisor_review,
    build_lr6_evid12_validation_context,
    build_lr6_evid12_validation_matrix,
    build_lr6_evid12_validation_scenarios,
    certify_lr6_evid12_validation_boundary,
    run_lr6_evid12_validation_harness,
    run_lr6_evid12_validation_scenario,
)


def test_public_apis_exist():
    assert callable(build_lr6_evid12_validation_context)
    assert callable(build_lr6_evid12_validation_scenarios)
    assert callable(run_lr6_evid12_validation_scenario)
    assert callable(run_lr6_evid12_validation_harness)
    assert callable(build_lr6_evid12_validation_matrix)
    assert callable(build_lr6_evid12_status_transition_review)
    assert callable(build_lr6_evid12_rejection_safety_review)
    assert callable(build_lr6_evid12_comparison_readiness_review)
    assert callable(build_lr6_evid12_supervisor_review)
    assert callable(build_lr6_evid12_markdown_report)
    assert callable(certify_lr6_evid12_validation_boundary)


def test_deterministic_output_and_required_scenarios():
    result_a = run_lr6_evid12_validation_harness()
    result_b = run_lr6_evid12_validation_harness()
    assert result_a == result_b

    ids = {s["scenario_id"] for s in build_lr6_evid12_validation_scenarios()}
    required = {
        "valid_structured_artifact",
        "partial_structured_artifact",
        "scaffold_only_artifact",
        "narrative_only_artifact",
        "malformed_counts_artifact",
        "missing_lineage_artifact",
        "dry_run_structured_artifact",
        "baseline_comparison_artifact",
        "baseline_missing_artifact",
    }
    assert required.issubset(ids)


def test_safety_and_status_guards():
    by_id = {r["scenario_id"]: r for r in run_lr6_evid12_validation_harness()["scenario_results"]}
    assert by_id["valid_structured_artifact"]["observed_status"] == "MEASURED"
    assert by_id["scaffold_only_artifact"]["observed_status"] != "MEASURED"
    assert by_id["narrative_only_artifact"]["observed_status"] != "MEASURED"
    assert by_id["malformed_counts_artifact"]["observed_status"] != "MEASURED"
    assert by_id["missing_lineage_artifact"]["observed_status"] != "MEASURED"
    assert by_id["baseline_missing_artifact"]["comparison_ready"] is False
    assert by_id["baseline_comparison_artifact"]["comparison_ready"] is True


def test_summary_and_unsafe_promotion_count():
    harness = run_lr6_evid12_validation_harness()
    summary = harness["aggregate_summary"]
    assert summary["total_scenarios"] == 9
    assert summary["passed"] + summary["failed"] == 9
    assert summary["unsafe_promotion_count"] == 0
    assert summary["comparison_ready_count"] == 1


def test_boundary_flags_exact_and_report_sections_present():
    boundary = certify_lr6_evid12_validation_boundary()
    expected = {
        "validation_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": "replay_richness",
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "no_interpretation_claims": True,
        "architecture_expansion_frozen": True,
    }
    assert boundary == expected

    report = build_lr6_evid12_markdown_report().lower()
    for section in [
        "## objective",
        "## inspected evid11 builder",
        "## validation scenario matrix",
        "## status transition review",
        "## rejection safety review",
        "## comparison readiness review",
        "## aggregate validation result",
        "## unsafe promotion review",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report
