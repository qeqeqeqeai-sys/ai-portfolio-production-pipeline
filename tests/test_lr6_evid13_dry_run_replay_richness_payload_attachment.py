from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def _valid_artifact():
    return {
        "candidate_count": 12,
        "role_count": 5,
        "cluster_count": 4,
        "measurement_basis": "structured_observation",
        "source_artifact_refs": ["artifact://obs7/wave1"],
    }


def test_public_apis_exist_and_deterministic_output():
    for name in [
        "build_lr6_evid13_attachment_context",
        "identify_lr6_evid13_dry_run_attachment_targets",
        "build_lr6_evid13_structured_artifact_adapter",
        "attach_lr6_evid13_replay_richness_payload_dry_run",
        "build_lr6_evid13_attachment_result",
        "build_lr6_evid13_dry_run_emission_preview",
        "build_lr6_evid13_attachment_safety_review",
        "build_lr6_evid13_supervisor_review",
        "build_lr6_evid13_markdown_report",
        "certify_lr6_evid13_attachment_boundary",
    ]:
        assert hasattr(mod, name)

    a = mod.attach_lr6_evid13_replay_richness_payload_dry_run(_valid_artifact())
    b = mod.attach_lr6_evid13_replay_richness_payload_dry_run(_valid_artifact())
    assert a == b


def test_target_and_adapter_mapping():
    targets = mod.identify_lr6_evid13_dry_run_attachment_targets()
    assert len(targets) >= 1
    assert targets[0]["attachment_target"] == "lr6_obs7_simulated_wave_manifest"

    adapted = mod.build_lr6_evid13_structured_artifact_adapter(_valid_artifact())
    assert adapted["replay_entity_count"] == 12
    assert adapted["distinct_candidate_count"] == 12
    assert adapted["distinct_role_count"] == 5
    assert adapted["distinct_cluster_count"] == 4


def test_preview_measured_and_safety_flags():
    preview = mod.build_lr6_evid13_dry_run_emission_preview("lr6_obs7_simulated_wave_manifest", _valid_artifact())
    assert preview["replay_richness_payload"]["evidence_status"] == "MEASURED"
    assert preview["replay_richness_payload"]["comparison_ready"] is False
    assert preview["dry_run_only"] is True
    assert preview["persisted"] is False
    assert preview["live_ingestion"] is False
    assert preview["governed_activation"] is False
    assert preview["evid6_compatible_emission_candidate"]["evid6_contract_compatible"] is True


def test_scaffold_narrative_and_missing_lineage_downgrade():
    scaffold = _valid_artifact() | {"scaffold_only": True}
    narrative = _valid_artifact() | {"measurement_basis": "narrative_only"}
    missing_lineage = _valid_artifact() | {"source_artifact_refs": []}

    assert mod.attach_lr6_evid13_replay_richness_payload_dry_run(scaffold)["preview"]["replay_richness_payload"]["evidence_status"] != "MEASURED"
    assert mod.attach_lr6_evid13_replay_richness_payload_dry_run(narrative)["preview"]["replay_richness_payload"]["evidence_status"] != "MEASURED"
    assert mod.attach_lr6_evid13_replay_richness_payload_dry_run(missing_lineage)["preview"]["replay_richness_payload"]["evidence_status"] != "MEASURED"


def test_boundary_flags_exact_and_report_sections_and_no_forbidden_paths():
    expected = {
        "dry_run_only": True,
        "attachment_only": True,
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
    assert mod.certify_lr6_evid13_attachment_boundary() == expected

    report = mod.build_lr6_evid13_markdown_report().lower()
    for section in [
        "## objective",
        "## inspected evid11/evid12 builder and harness",
        "## inspected dry-run replay observation paths",
        "## attachment targets",
        "## structured artifact adapter",
        "## dry-run emission preview",
        "## scaffold/narrative rejection behavior",
        "## evid6 compatibility",
        "## attachment safety review",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report

    supervisor = str(mod.build_lr6_evid13_supervisor_review()).lower()
    for phrase in ["no_direct_sql", "no_prediction", "no_trading", "no_live_ingestion", "no_persistence_write"]:
        assert phrase in supervisor

    report_file = Path("reports/lr6_evid13_dry_run_replay_richness_payload_attachment.md")
    if report_file.exists():
        text = report_file.read_text(encoding="utf-8").lower()
        assert "## objective" in text
