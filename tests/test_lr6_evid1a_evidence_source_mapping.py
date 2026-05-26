from transmission_layers.expectation_failure.replay_ecology import (
    EVID1_DIMENSIONS,
    build_lr6_evid1a_baseline_source_inventory,
    build_lr6_evid1a_enriched_source_inventory,
    build_lr6_evid1a_evid1_population_plan,
    build_lr6_evid1a_markdown_report,
    build_lr6_evid1a_metric_source_map,
    build_lr6_evid1a_minimum_evidence_requirements,
    build_lr6_evid1a_missing_metric_inventory,
    build_lr6_evid1a_run1_output_measurability_review,
    build_lr6_evid1a_source_mapping_context,
    build_lr6_evid1a_supervisor_review,
    certify_lr6_evid1a_mapping_boundary,
)


def test_public_apis_exist_and_deterministic_output():
    c1 = build_lr6_evid1a_source_mapping_context()
    c2 = build_lr6_evid1a_source_mapping_context()
    assert c1 == c2
    assert callable(build_lr6_evid1a_baseline_source_inventory)
    assert callable(build_lr6_evid1a_enriched_source_inventory)
    assert callable(build_lr6_evid1a_metric_source_map)
    assert callable(build_lr6_evid1a_missing_metric_inventory)
    assert callable(build_lr6_evid1a_minimum_evidence_requirements)
    assert callable(build_lr6_evid1a_run1_output_measurability_review)
    assert callable(build_lr6_evid1a_evid1_population_plan)
    assert callable(build_lr6_evid1a_supervisor_review)
    assert callable(build_lr6_evid1a_markdown_report)
    assert callable(certify_lr6_evid1a_mapping_boundary)


def test_inventories_and_metric_map_coverage():
    baseline = build_lr6_evid1a_baseline_source_inventory()
    enriched = build_lr6_evid1a_enriched_source_inventory()
    assert baseline
    assert enriched
    metric_map = build_lr6_evid1a_metric_source_map()
    assert {row["metric"] for row in metric_map} == set(EVID1_DIMENSIONS)


def test_missing_inventory_and_run1_enum_and_scaffold_not_ready():
    metric_map = build_lr6_evid1a_metric_source_map()
    missing = build_lr6_evid1a_missing_metric_inventory(metric_map)
    assert missing
    run1 = build_lr6_evid1a_run1_output_measurability_review()
    assert run1["decision"] in {
        "RUN1_MEASURABLE_EVIDENCE_AVAILABLE",
        "RUN1_PARTIAL_EVIDENCE_AVAILABLE",
        "RUN1_SCAFFOLD_ONLY",
        "RUN1_EVIDENCE_MISSING",
    }
    assert all(row["population_status"] != "READY" for row in metric_map if row["population_status"] == "BLOCKED_SCAFFOLD_ONLY")


def test_population_plan_rules_and_boundary_and_report_sections():
    plan = build_lr6_evid1a_evid1_population_plan()
    rules = plan["rules"]
    assert "no_imputation_rule" in rules
    assert "no_scaffold_as_evidence_rule" in rules
    assert "evidence_before_narrative_rule" in rules

    boundary = certify_lr6_evid1a_mapping_boundary()
    assert boundary["mapping_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True

    report = build_lr6_evid1a_markdown_report()
    for section in [
        "## objective",
        "## inspected artifacts/modules",
        "## baseline source inventory",
        "## enriched source inventory",
        "## metric source map",
        "## missing metric inventory",
        "## RUN1 measurability review",
        "## minimum evidence requirements",
        "## EVID1 population plan",
        "## mapping boundary",
        "## recommendation",
    ]:
        assert section in report


def test_no_execution_or_sql_or_trading_paths_introduced():
    review = build_lr6_evid1a_supervisor_review()
    boundary = review["mapping_boundary"]
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
