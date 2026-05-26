from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def test_public_apis_exist():
    for name in [
        "build_lr6_evid5_hook_design_context",
        "build_lr6_evid5_minimal_metric_contract",
        "build_lr6_evid5_replay_time_emission_hook_spec",
        "build_lr6_evid5_metric_computation_guidelines",
        "build_lr6_evid5_evid2_field_mapping",
        "build_lr6_evid5_evid3_adapter_compatibility_review",
        "build_lr6_evid5_integration_points",
        "build_lr6_evid5_validation_rules",
        "build_lr6_evid5_non_persistence_emission_policy",
        "build_lr6_evid5_supervisor_review",
        "build_lr6_evid5_markdown_report",
        "certify_lr6_evid5_hook_design_boundary",
    ]:
        assert hasattr(mod, name)


def test_deterministic_output_and_contract_coverage():
    one = mod.build_lr6_evid5_supervisor_review()
    two = mod.build_lr6_evid5_supervisor_review()
    assert one == two
    contract = mod.build_lr6_evid5_minimal_metric_contract()
    assert len(contract) == 7
    assert {r["metric_dimension"] for r in contract} == set(mod.EVID1_DIMENSIONS)
    assert all(len(r["required_emitted_fields"]) == 5 for r in contract)


def test_hook_spec_mapping_compatibility_validation_and_policy():
    hook = mod.build_lr6_evid5_replay_time_emission_hook_spec()
    assert hook["function_name"] == "emit_lr6_replay_metric_evidence"
    assert hook["io_policy"] == "pure_function_only"
    forbidden = set(hook["forbidden_operations"])
    assert "database_writes" in forbidden
    assert "sql_execution" in forbidden

    mapping = mod.build_lr6_evid5_evid2_field_mapping()
    for key in [
        "replay_phase",
        "wave_id",
        "candidate_scope_id",
        "candidate_count",
        "metric_dimension",
        "measured_fields",
        "evidence_status",
        "source_artifact",
        "source_module",
        "comparison_ready",
        "scaffold_only",
    ]:
        assert key in mapping

    compat = mod.build_lr6_evid5_evid3_adapter_compatibility_review()
    assert compat["adapter_transformation_required"] is False
    assert "measured" in compat["measured_status_rule"].lower()

    rules = mod.build_lr6_evid5_validation_rules()
    all_rules = " | ".join(rules).lower()
    assert "non-negative integers" in all_rules
    assert "bounded" in all_rules
    assert "narrative-only" in all_rules

    policy = mod.build_lr6_evid5_non_persistence_emission_policy()
    assert policy["no_writes"] is True
    assert policy["no_supabase"] is True
    assert policy["no_sql"] is True


def test_boundary_report_sections_and_no_execution_paths():
    boundary = mod.certify_lr6_evid5_hook_design_boundary()
    assert boundary["design_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["hook_design_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True

    review = mod.build_lr6_evid5_supervisor_review()
    assert review["boundary_certification"]["execution_authorized"] is False

    report = mod.build_lr6_evid5_markdown_report()
    for section in [
        "## objective",
        "## EVID4 basis",
        "## minimal metric contract",
        "## replay-time emission hook spec",
        "## metric computation guidelines",
        "## EVID2 field mapping",
        "## EVID3 compatibility review",
        "## integration points",
        "## validation rules",
        "## non-persistence policy",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report

    file_report = Path("reports/lr6_evid5_replay_metrics_emission_hook_design.md").read_text(encoding="utf-8")
    assert "## objective" in file_report
