from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def test_public_apis_exist():
    for name in [
        "build_lr6_evid4_emission_review_context",
        "discover_lr6_evid4_available_payload_sources",
        "build_lr6_evid4_payload_inventory",
        "emit_lr6_evid4_evidence_records_from_available_payloads",
        "build_lr6_evid4_status_summary",
        "build_lr6_evid4_dimension_coverage_review",
        "build_lr6_evid4_scaffold_only_review",
        "build_lr6_evid4_comparison_readiness_review",
        "build_lr6_evid4_evid1_population_readiness",
        "build_lr6_evid4_supervisor_review",
        "build_lr6_evid4_markdown_report",
        "certify_lr6_evid4_emission_review_boundary",
    ]:
        assert hasattr(mod, name)


def test_deterministic_output_and_inventory_exists_if_missing_repo_root():
    one = mod.build_lr6_evid4_payload_inventory("does_not_exist")
    two = mod.build_lr6_evid4_payload_inventory("does_not_exist")
    assert one == two
    assert "sources" in one
    assert one["total_discovered"] == 0


def test_emitted_records_use_evid3_compatible_fields():
    emission = mod.emit_lr6_evid4_evidence_records_from_available_payloads(".")
    records = emission["records"]
    if records:
        row = records[0]
        for key in [
            "evidence_record_id",
            "replay_phase",
            "metric_dimension",
            "measured_fields",
            "evidence_status",
            "source_artifact",
            "source_module",
            "comparison_ready",
            "scaffold_only",
        ]:
            assert key in row


def test_status_summary_has_all_statuses_and_dimension_coverage_complete():
    emission = mod.emit_lr6_evid4_evidence_records_from_available_payloads(".")
    records = emission["records"]
    status = mod.build_lr6_evid4_status_summary(records)
    assert set(status["status_counts"].keys()) == {"MEASURED", "PARTIAL", "MISSING", "NOT_COMPARABLE", "SCAFFOLD_ONLY"}

    dims = mod.build_lr6_evid4_dimension_coverage_review(records)
    assert set(dims.keys()) == set(mod.EVID1_DIMENSIONS)


def test_scaffold_only_not_comparison_ready_and_readiness_enum_valid():
    scaffold_records = mod.emit_lr6_evid4_evidence_records_from_available_payloads(".")["records"]
    for r in scaffold_records:
        if r["scaffold_only"]:
            assert r["comparison_ready"] is False

    readiness = mod.build_lr6_evid4_evid1_population_readiness(scaffold_records)
    assert readiness in {"EVID1_POPULATION_READY", "EVID1_PARTIALLY_POPULATABLE", "EVID1_BLOCKED_SCAFFOLD_ONLY", "EVID1_BLOCKED_MISSING_BASELINE_OR_ENRICHED", "EVID1_BLOCKED_NO_MEASURABLE_RECORDS"}


def test_boundary_and_report_and_no_execution_paths():
    boundary = mod.certify_lr6_evid4_emission_review_boundary()
    assert boundary["emission_review_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True

    report = mod.build_lr6_evid4_markdown_report(".")
    for section in [
        "## objective",
        "## inspected payload sources",
        "## payload inventory",
        "## emitted evidence record summary",
        "## evidence status summary",
        "## dimension coverage review",
        "## scaffold-only review",
        "## comparison readiness review",
        "## EVID1 population readiness",
        "## boundary certification",
        "## recommendation",
    ]:
        assert section in report

    file_report = Path("reports/lr6_evid4_first_real_evidence_record_emission_review.md").read_text(encoding="utf-8")
    assert "## objective" in file_report
