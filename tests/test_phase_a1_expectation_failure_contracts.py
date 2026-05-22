from transmission_layers.expectation_failure import (
    build_expectation_failure_evidence_schema,
    build_expectation_failure_explanation_templates,
    build_expectation_failure_invariant_flags,
    build_expectation_failure_score_contracts,
    build_phase_a1_expectation_failure_contract_report,
)

EXPECTED_SCORES = [
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
]

EXPECTED_BANDS = {
    "low": (0, 19),
    "mild": (20, 39),
    "elevated": (40, 59),
    "high": (60, 79),
    "severe": (80, 100),
}

EXPECTED_EVIDENCE_FIELDS = [
    "score_name",
    "score_value",
    "score_band",
    "subcomponent_scores",
    "raw_evidence_refs",
    "thresholds_triggered",
    "missing_inputs",
    "data_quality_flags",
    "explanation_template_id",
    "confidence_boundary",
    "replay_metadata",
    "checksum_seed_fields",
]


def test_public_api_exports_exist():
    assert callable(build_expectation_failure_score_contracts)
    assert callable(build_expectation_failure_evidence_schema)
    assert callable(build_expectation_failure_explanation_templates)
    assert callable(build_expectation_failure_invariant_flags)
    assert callable(build_phase_a1_expectation_failure_contract_report)


def test_all_five_score_contracts_present_and_bounded():
    contracts = build_expectation_failure_score_contracts()
    assert [c["score_name"] for c in contracts] == EXPECTED_SCORES
    for contract in contracts:
        assert contract["score_range"] == (0, 100)


def test_score_bands_exact_match_required_ranges():
    for contract in build_expectation_failure_score_contracts():
        assert contract["score_bands"] == EXPECTED_BANDS


def test_evidence_schema_includes_all_required_fields():
    schema = build_expectation_failure_evidence_schema()
    assert list(schema.keys()) == EXPECTED_EVIDENCE_FIELDS


def test_explanation_templates_are_fixed_and_deterministic():
    templates_a = build_expectation_failure_explanation_templates()
    templates_b = build_expectation_failure_explanation_templates()
    assert templates_a == templates_b
    assert len(templates_a) == 6
    assert "template_invalid_input_v1" in templates_a
    for template_id, template in templates_a.items():
        assert isinstance(template_id, str)
        assert isinstance(template, str)
        assert "{" in template or template_id == "template_invalid_input_v1"


def test_invariant_flags_are_all_true():
    flags = build_expectation_failure_invariant_flags()
    assert all(flags.values())


def test_report_is_deterministic_across_repeated_calls():
    report_a = build_phase_a1_expectation_failure_contract_report()
    report_b = build_phase_a1_expectation_failure_contract_report()
    assert report_a == report_b


def test_no_scoring_or_composite_output_in_phase_a1():
    report = build_phase_a1_expectation_failure_contract_report()
    boundaries = report["implementation_boundaries"]
    assert "contracts_only_no_score_computation" in boundaries
    assert "no_composite_expectation_failure_scoring" in boundaries


def test_invalid_input_template_exists():
    templates = build_expectation_failure_explanation_templates()
    assert "template_invalid_input_v1" in templates


def test_no_prediction_trading_optimization_or_adaptive_enabled_behavior():
    report = build_phase_a1_expectation_failure_contract_report()
    boundary_text = " ".join(report["implementation_boundaries"])
    assert "no_prediction" in boundary_text
    assert "trading" in boundary_text
    assert "optimization" in boundary_text
    assert "adaptive" in boundary_text


def test_contract_policies_explicitly_disable_prediction():
    for contract in build_expectation_failure_score_contracts():
        assert "no_prediction" in contract["no_prediction_policy"]
