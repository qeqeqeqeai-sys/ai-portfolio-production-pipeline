from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_additive_integration_certification,
    build_architecture_constraint_certification,
    build_determinism_certification,
    build_exclusion_preservation_certification,
    build_expectation_failure_subsystem_summary,
    build_explainability_certification,
    build_phase_b7_system_certification_report,
    build_phase_inventory_summary,
    build_public_api_inventory,
    build_replayability_certification,
)

import transmission_layers.expectation_failure.phase_b6_institutional_reporting as b6
import transmission_layers.expectation_failure.phase_b5_deterioration_alert_interpretation as b5


def _sample_reports():
    return {
        f"phase_{pid.lower()}": {"phase_id": pid, "replay_metadata": {"phase_id": pid, "output_checksum": "x"}}
        for pid in ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "B1", "B2", "B3", "B4", "B5", "B6"]
    }


def _sample_modules():
    return {
        "transmission_layers.expectation_failure.phase_b6_institutional_reporting": b6,
        "transmission_layers.expectation_failure.phase_b5_deterioration_alert_interpretation": b5,
    }


def test_public_api_presence_and_exports():
    report = build_phase_b7_system_certification_report({}, {}, {})
    assert report["phase_id"] == "B7"


def test_deterministic_repeated_output_and_checksum_stability():
    r1 = build_phase_b7_system_certification_report(_sample_reports(), _sample_modules(), {})
    r2 = build_phase_b7_system_certification_report(_sample_reports(), _sample_modules(), {})
    assert r1 == r2
    assert r1["replay_metadata"]["output_checksum"] == r2["replay_metadata"]["output_checksum"]


def test_input_immutability():
    reports = _sample_reports()
    modules = _sample_modules()
    reports_before = deepcopy(reports)
    _ = build_phase_b7_system_certification_report(reports, modules, {"evidence_chain_references": ["x"]})
    assert reports == reports_before


def test_phase_inventory_ordering_and_missing_phase_handling():
    inv = build_phase_inventory_summary({"phase_a1": {"phase_id": "A1"}}, None)
    assert inv["phase_inventory"] == ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "B1", "B2", "B3", "B4", "B5", "B6"]
    assert "A2" in inv["missing_expected_phases"]


def test_certification_builders():
    reports = _sample_reports()
    modules = _sample_modules()
    assert build_architecture_constraint_certification(reports, modules, {})["certification_status"] == "FULLY_CERTIFIED"
    assert build_determinism_certification(reports, modules, {})["certification_status"] == "FULLY_CERTIFIED"
    assert build_replayability_certification(reports, modules, {})["replayability_status"] == "REPLAYABILITY_CERTIFIED"
    assert build_explainability_certification(reports, modules, {})["explainability_status"] == "EXPLAINABILITY_CERTIFIED"
    assert build_additive_integration_certification(reports, modules, {})["additive_status"] == "ADDITIVE_INTEGRATION_CERTIFIED"
    assert build_exclusion_preservation_certification(reports, modules, {})["exclusion_status"] == "EXCLUSION_PRESERVATION_CERTIFIED"


def test_public_api_inventory_ordering():
    inv = build_public_api_inventory(_sample_modules())
    for row in inv["public_api_inventory"]:
        assert row["public_api_names"] == sorted(row["public_api_names"])


def test_subsystem_summary_and_findings_and_decision_precedence():
    summary = build_expectation_failure_subsystem_summary(_sample_reports(), _sample_modules(), {})
    assert summary["subsystem_identity"] == "deterministic institutional expectation-fragility intelligence"
    partial = build_phase_b7_system_certification_report({"phase_a1": {"phase_id": "A1"}}, {}, {})
    assert partial["final_certification_decision"] == "EXPECTATION_FAILURE_SUBSYSTEM_PARTIALLY_CERTIFIED"
    assert [f["finding_id"] for f in partial["certification_findings"]] == sorted([f["finding_id"] for f in partial["certification_findings"]])


def test_replay_metadata_and_template_versions_and_language_boundaries():
    report = build_phase_b7_system_certification_report(_sample_reports(), _sample_modules(), {})
    replay = report["replay_metadata"]
    assert replay["phase_id"] == "B7"
    assert replay["certification_template_version"] == "b7_certification_templates_v1"
    serialized = str(report).lower()
    banned = ["buy this", "sell this", "short this", "execute trade", "portfolio allocation recommendation"]
    for token in banned:
        assert token not in serialized
