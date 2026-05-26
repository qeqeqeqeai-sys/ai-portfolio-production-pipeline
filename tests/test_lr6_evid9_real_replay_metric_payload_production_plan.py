from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def test_public_apis_exist():
    for name in [
        "build_lr6_evid9_production_plan_context",
        "discover_lr6_evid9_replay_metric_sources",
        "build_lr6_evid9_metric_computability_review",
        "build_lr6_evid9_existing_observation_field_inventory",
        "build_lr6_evid9_missing_observation_field_inventory",
        "build_lr6_evid9_replay_path_integration_plan",
        "build_lr6_evid9_evid6_hook_integration_targets",
        "build_lr6_evid9_priority_metric_emission_order",
        "build_lr6_evid9_minimal_real_metric_requirements",
        "build_lr6_evid9_supervisor_review",
        "build_lr6_evid9_markdown_report",
        "certify_lr6_evid9_production_plan_boundary",
    ]:
        assert hasattr(mod, name)


def test_deterministic_output_and_dimension_coverage():
    one = mod.build_lr6_evid9_supervisor_review()
    two = mod.build_lr6_evid9_supervisor_review()
    assert one == two

    review = mod.build_lr6_evid9_metric_computability_review()
    assert len(review) == 7
    assert {row["metric_dimension"] for row in review} == set(mod.EVID_DIMENSIONS)


def test_computability_enums_and_required_structures_exist():
    review = mod.build_lr6_evid9_metric_computability_review()
    valid = set(mod.COMPUTABILITY_STATUSES)
    for row in review:
        assert row["computability"]
        assert set(row["computability"]).issubset(valid)

    assert mod.build_lr6_evid9_missing_observation_field_inventory()
    assert mod.build_lr6_evid9_evid6_hook_integration_targets()
    assert mod.build_lr6_evid9_priority_metric_emission_order()


def test_realism_rules_boundary_and_forbidden_logic_guards():
    context = mod.build_lr6_evid9_production_plan_context()
    realism_text = " | ".join(context["realism_rules"]).lower()
    assert "candidate lists are not observed attribution" in realism_text
    assert "dry-run simulation is not topology drift evidence" in realism_text

    boundary = mod.certify_lr6_evid9_production_plan_boundary()
    assert boundary["planning_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_governed_activation"] is True
    assert boundary["no_interpretation_claims"] is True
    assert boundary["architecture_expansion_frozen"] is True

    review = mod.build_lr6_evid9_supervisor_review()
    assert review["boundary_certification"]["execution_authorized"] is False


def test_report_sections_and_no_execution_authorization_introduced():
    report = mod.build_lr6_evid9_markdown_report().lower()
    for section in [
        "## objective",
        "## inspected replay paths/modules",
        "## replay metric source review",
        "## computability review",
        "## existing observation field inventory",
        "## missing observation field inventory",
        "## evid6 integration targets",
        "## priority emission order",
        "## minimal real metric requirements",
        "## realism warning",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report

    assert "execution_authorized': false" in report
    for forbidden in ["select ", "insert ", "update ", "delete from", "order_book"]:
        assert forbidden not in report
    assert "'no_prediction': true" in report
    assert "'no_trading': true" in report

    file_report = Path("reports/lr6_evid9_real_replay_metric_payload_production_plan.md").read_text(encoding="utf-8").lower()
    assert "## objective" in file_report
