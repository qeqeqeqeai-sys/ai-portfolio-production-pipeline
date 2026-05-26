from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def _valid_artifact():
    return {
        "replay_entity_count": 12,
        "distinct_candidate_count": 8,
        "distinct_role_count": 5,
        "distinct_cluster_count": 4,
        "source_artifact_refs": ["artifact://wave/W1"],
        "measurement_basis": "observed_structured_fields",
    }


def test_public_apis_exist_and_deterministic():
    for name in [
        "build_lr6_evid11_builder_context",
        "extract_lr6_evid11_structured_richness_fields",
        "validate_lr6_evid11_richness_source_artifact",
        "build_lr6_evid11_replay_richness_payload",
        "build_lr6_evid11_evid6_emission_candidate",
        "build_lr6_evid11_payload_validation_result",
        "build_lr6_evid11_scaffold_rejection_result",
        "build_lr6_evid11_supervisor_review",
        "build_lr6_evid11_markdown_report",
        "certify_lr6_evid11_builder_boundary",
    ]:
        assert hasattr(mod, name)

    assert mod.build_lr6_evid11_replay_richness_payload(_valid_artifact()) == mod.build_lr6_evid11_replay_richness_payload(_valid_artifact())


def test_only_replay_richness_metric_target_and_measured_when_valid():
    payload = mod.build_lr6_evid11_replay_richness_payload(_valid_artifact())
    assert payload["metric_dimension"] == "replay_richness"
    assert payload["evidence_status"] == "MEASURED"
    assert payload["comparison_ready"] is False


def test_scaffold_only_and_narrative_only_cannot_be_measured():
    scaffold = _valid_artifact() | {"scaffold_only": True}
    narrative = _valid_artifact() | {"measurement_basis": "narrative_only"}
    assert mod.build_lr6_evid11_replay_richness_payload(scaffold)["evidence_status"] != "MEASURED"
    assert mod.build_lr6_evid11_replay_richness_payload(narrative)["evidence_status"] != "MEASURED"


def test_missing_negative_non_integer_counts_downgraded_or_rejected():
    missing = {"measurement_basis": "observed_structured_fields", "source_artifact_refs": ["a"]}
    assert mod.build_lr6_evid11_replay_richness_payload(missing)["evidence_status"] == "NOT_COMPARABLE"

    negative = _valid_artifact() | {"distinct_role_count": -1}
    assert mod.build_lr6_evid11_replay_richness_payload(negative)["evidence_status"] == "PARTIAL"

    non_integer = _valid_artifact() | {"distinct_cluster_count": "4"}
    assert mod.build_lr6_evid11_replay_richness_payload(non_integer)["evidence_status"] == "PARTIAL"


def test_evid6_candidate_compatibility_and_no_forbidden_paths():
    candidate = mod.build_lr6_evid11_evid6_emission_candidate(_valid_artifact())
    record = candidate["evid6_record"]
    assert candidate["metric_target"] == "replay_richness"
    assert candidate["evid6_contract_compatible"] is True
    assert record["metric_dimension"] == "replay_richness"

    as_text = str(mod.build_lr6_evid11_supervisor_review()).lower()
    for phrase in [
        "execution_authorized': false",
        "no_persistence_write': true",
        "no_direct_sql': true",
        "no_live_ingestion': true",
        "no_prediction': true",
        "no_trading': true",
    ]:
        assert phrase in as_text


def test_boundary_flags_exact_and_report_sections_exist():
    expected = {
        "planning_only": False,
        "builder_only": True,
        "evidence_only": True,
        "in_memory_only": True,
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
    assert mod.certify_lr6_evid11_builder_boundary() == expected

    report = mod.build_lr6_evid11_markdown_report()
    for section in [
        "## objective",
        "## inspected prior EVID9/EVID10 design",
        "## structured source artifact assumptions",
        "## payload extraction logic",
        "## validation logic",
        "## scaffold/narrative rejection logic",
        "## EVID6 compatibility",
        "## sample valid in-memory payload",
        "## sample rejected scaffold payload",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report

    file_report = Path("reports/lr6_evid11_first_real_replay_richness_payload_builder.md").read_text(encoding="utf-8")
    assert "## objective" in file_report
