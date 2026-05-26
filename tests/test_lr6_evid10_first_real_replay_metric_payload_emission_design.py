from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_evid10_design_context,
    identify_lr6_evid10_first_metric_target,
    build_lr6_evid10_replay_richness_payload_contract,
    build_lr6_evid10_existing_field_mapping,
    build_lr6_evid10_payload_derivation_plan,
    build_lr6_evid10_evid6_compatibility_mapping,
    build_lr6_evid10_validation_plan,
    build_lr6_evid10_non_synthetic_readiness_review,
    build_lr6_evid10_integration_boundary_plan,
    build_lr6_evid10_supervisor_review,
    build_lr6_evid10_markdown_report,
    certify_lr6_evid10_design_boundary,
)


def test_public_apis_exist_and_deterministic():
    funcs = [
        build_lr6_evid10_design_context,
        identify_lr6_evid10_first_metric_target,
        build_lr6_evid10_replay_richness_payload_contract,
        build_lr6_evid10_existing_field_mapping,
        build_lr6_evid10_payload_derivation_plan,
        build_lr6_evid10_evid6_compatibility_mapping,
        build_lr6_evid10_validation_plan,
        build_lr6_evid10_non_synthetic_readiness_review,
        build_lr6_evid10_integration_boundary_plan,
        build_lr6_evid10_supervisor_review,
        build_lr6_evid10_markdown_report,
        certify_lr6_evid10_design_boundary,
    ]
    for fn in funcs:
        assert callable(fn)

    assert build_lr6_evid10_supervisor_review() == build_lr6_evid10_supervisor_review()
    assert build_lr6_evid10_markdown_report() == build_lr6_evid10_markdown_report()


def test_first_metric_selection_and_not_all_seven():
    target = identify_lr6_evid10_first_metric_target()
    assert target["selected_metric"] == "replay_richness"
    assert target["all_seven_metrics_implemented"] is False


def test_payload_contract_required_fields_and_narrative_exclusions():
    contract = build_lr6_evid10_replay_richness_payload_contract()
    required = set(contract["required_structured_count_fields"])
    assert {"replay_entity_count", "distinct_candidate_count", "distinct_role_count", "distinct_cluster_count"}.issubset(required)

    optional = contract["field_availability_review"]["optional_field_classification"]
    assert optional["distinct_theme_count"]["availability"] == "narrative_only"
    assert optional["distinct_theme_count"]["excluded_from_first_payload"] is True
    assert optional["distinct_propagation_route_count"]["not_measurement_ready"] is True


def test_evid6_compatibility_and_validation_rules_exist():
    mapping = build_lr6_evid10_evid6_compatibility_mapping()
    assert mapping["metric_dimension"] == "replay_richness"
    assert mapping["no_hook_contract_change_required"] is True

    rules = build_lr6_evid10_validation_plan()["deterministic_rules"]
    assert any("integers >= 0" in rule for rule in rules)
    assert any("scaffold-only input cannot become MEASURED" in rule for rule in rules)


def test_scaffold_and_execution_boundaries_locked_down():
    readiness = build_lr6_evid10_non_synthetic_readiness_review()
    excluded = " ".join(readiness["excluded_from_measured"])
    assert "scaffold-only payloads" in excluded

    boundary = certify_lr6_evid10_design_boundary()
    expected = {
        "planning_only": True,
        "design_only": True,
        "evidence_only": True,
        "execution_authorized": False,
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


def test_report_sections_and_no_forbidden_activation_logic():
    report = build_lr6_evid10_markdown_report()
    required_sections = [
        "## objective",
        "## why replay_richness is first",
        "## inspected EVID9 findings",
        "## inspected replay observation structures",
        "## first real payload contract",
        "## existing field mapping",
        "## excluded narrative/scaffold-only fields",
        "## EVID6 compatibility mapping",
        "## payload derivation plan",
        "## validation plan",
        "## non-synthetic readiness review",
        "## integration boundary plan",
        "## boundary certification",
        "## recommendation for next step",
    ]
    for section in required_sections:
        assert section in report

    review = build_lr6_evid10_supervisor_review()
    review_text = str(review).lower()
    assert "execution_authorized': false" in review_text
    assert "no_direct_sql': true" in review_text
    assert "no_persistence_write': true" in review_text
    assert "no_live_ingestion': true" in review_text
    assert "no_prediction': true" in review_text
    assert "no_trading': true" in review_text


def test_no_execution_or_sql_logic_in_design_mappings():
    mapping_text = str(build_lr6_evid10_existing_field_mapping()).lower()
    integration_text = str(build_lr6_evid10_integration_boundary_plan()).lower()
    assert "insert" not in mapping_text
    assert "update" not in mapping_text
    assert "delete" not in mapping_text
    assert "sql" in integration_text
    assert "no sql" in integration_text

    derivation = build_lr6_evid10_payload_derivation_plan()
    assert len(derivation) > 0
