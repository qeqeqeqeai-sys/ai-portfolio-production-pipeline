from transmission_layers.expectation_failure import replay_ecology as mod


def test_public_apis_exist():
    for name in [
        "build_lr6_evid2_capture_design_context",
        "build_lr6_evid2_evidence_record_schema",
        "build_lr6_evid2_baseline_capture_requirements",
        "build_lr6_evid2_enriched_capture_requirements",
        "build_lr6_evid2_metric_field_definitions",
        "build_lr6_evid2_pre_post_pairing_requirements",
        "build_lr6_evid2_quality_validation_rules",
        "build_lr6_evid2_no_scaffold_as_evidence_rules",
        "build_lr6_evid2_evid1_population_mapping",
        "build_lr6_evid2_supervisor_review",
        "build_lr6_evid2_markdown_report",
        "certify_lr6_evid2_capture_design_boundary",
    ]:
        assert hasattr(mod, name)


def test_deterministic_output():
    assert mod.build_lr6_evid2_supervisor_review() == mod.build_lr6_evid2_supervisor_review()


def test_schema_and_dimensions_coverage():
    schema = mod.build_lr6_evid2_evidence_record_schema()
    required = {
        "evidence_record_id", "replay_phase", "wave_id", "candidate_scope_id", "candidate_count",
        "timestamp_or_snapshot_label", "metric_dimension", "measured_fields", "evidence_status",
        "source_artifact", "source_module", "comparison_ready", "scaffold_only", "notes",
    }
    assert required.issubset(set(schema["required_fields"]))
    dims = {row["metric_dimension"] for row in mod.build_lr6_evid2_metric_field_definitions()}
    assert dims == set(mod.EVID1_DIMENSIONS)


def test_baseline_and_enriched_requirements_exist():
    b = mod.build_lr6_evid2_baseline_capture_requirements()
    e = mod.build_lr6_evid2_enriched_capture_requirements()
    assert len(b) == 7
    assert len(e) == 7


def test_quality_and_no_scaffold_rules_present():
    rules = mod.build_lr6_evid2_quality_validation_rules()
    assert any("scaffold_only=True cannot be comparison_ready=True" in r for r in rules)
    no_scaffold = mod.build_lr6_evid2_no_scaffold_as_evidence_rules()
    assert "no_scaffold_as_evidence_rule" in no_scaffold


def test_population_mapping_boundary_and_report_sections():
    mapping = mod.build_lr6_evid2_evid1_population_mapping()
    assert {row["metric_dimension"] for row in mapping} == set(mod.EVID1_DIMENSIONS)

    boundary = mod.certify_lr6_evid2_capture_design_boundary()
    assert boundary["design_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True

    report = mod.build_lr6_evid2_markdown_report()
    for section in [
        "## objective",
        "## EVID1/EVID1A basis",
        "## evidence record schema",
        "## baseline capture requirements",
        "## enriched capture requirements",
        "## metric field definitions",
        "## pre/post pairing requirements",
        "## quality validation rules",
        "## no-scaffold-as-evidence rules",
        "## EVID1 population mapping",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report


def test_no_execution_sql_persistence_prediction_trading_paths():
    review = mod.build_lr6_evid2_supervisor_review()
    boundary = review["boundary_certification"]
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
