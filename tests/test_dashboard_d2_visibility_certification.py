from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_guardrail_contracts import build_d1_guardrail_certification
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import build_d1_seed_payload
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d2_visibility_certification import (
    APPROVED_DECISION,
    build_d2_visibility_inventory,
    build_d2_visibility_manifest,
    build_d2_visibility_report_payload,
    build_d2_visibility_requirements,
    certify_d2_alert_visibility,
    certify_d2_benchmark_visibility,
    certify_d2_empty_degraded_visibility,
    certify_d2_entity_visibility,
    certify_d2_evidence_chain_visibility,
    certify_d2_replay_visibility,
    certify_d2_report_visibility,
    certify_d2_sample_flag_visibility,
    certify_d2_subsector_visibility,
    run_d2_dashboard_visibility_certification,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o10_real_data_operationalization_closeout import run_dashboard_o10_closeout_certification


def _payload():
    return build_d1_seed_payload()


def test_public_api_export_presence_and_additive_behavior():
    for name in [
        "build_d2_visibility_inventory", "build_d2_visibility_requirements", "certify_d2_entity_visibility", "certify_d2_subsector_visibility",
        "certify_d2_alert_visibility", "certify_d2_replay_visibility", "certify_d2_evidence_chain_visibility", "certify_d2_benchmark_visibility",
        "certify_d2_report_visibility", "certify_d2_sample_flag_visibility", "certify_d2_empty_degraded_visibility",
        "run_d2_dashboard_visibility_certification", "build_d2_visibility_manifest", "build_d2_visibility_report_payload",
    ]:
        assert hasattr(mod, name)


def test_deterministic_repeated_output_checksum_stability_and_fixed_gate_ordering():
    a = run_d2_dashboard_visibility_certification(_payload())
    b = run_d2_dashboard_visibility_certification(_payload())
    assert a == b
    assert a["manifest_checksum"] == b["manifest_checksum"]
    assert [g["gate"] for g in a["gate_results"]] == build_d2_visibility_inventory()["gate_order"]


def test_certified_all_visible_case_and_report_decision_value():
    result = run_d2_dashboard_visibility_certification(_payload())
    assert result["overall_status"] == "PASS"
    assert result["supervisor_decision"] == APPROVED_DECISION
    assert build_d2_visibility_report_payload(_payload())["final_supervisor_decision"] == APPROVED_DECISION


def test_degraded_partial_visibility_case():
    payload = _payload()
    payload["dashboard_subsector_facts"][0].pop("risk_label")
    result = run_d2_dashboard_visibility_certification(payload)
    assert result["overall_status"] == "DEGRADED"


def test_blocked_missing_critical_section_case():
    payload = _payload()
    payload["dashboard_entity_facts"] = []
    result = run_d2_dashboard_visibility_certification(payload)
    assert result["overall_status"] == "BLOCKED"


def test_section_visibility_validations():
    p = _payload()
    assert certify_d2_entity_visibility(p)["status"] == "PASS"
    assert certify_d2_subsector_visibility(p)["status"] == "PASS"
    assert certify_d2_alert_visibility(p)["status"] == "PASS"
    assert certify_d2_replay_visibility(p)["status"] == "PASS"
    assert certify_d2_evidence_chain_visibility(p)["status"] == "PASS"
    assert certify_d2_benchmark_visibility(p)["status"] == "PASS"
    assert certify_d2_report_visibility(p)["status"] == "PASS"


def test_sample_data_flag_visibility_validation():
    payload = _payload()
    payload["dashboard_alert_facts"][0]["sample_data_flag"] = False
    assert certify_d2_sample_flag_visibility(payload)["status"] == "DEGRADED"


def test_empty_and_degraded_table_safety():
    payload = _payload()
    payload["dashboard_alert_facts"] = []
    out = certify_d2_empty_degraded_visibility(payload)
    assert out["empty_state"]["status"] == "PASS"
    assert out["degraded_state"]["status"] == "PASS"


def test_forbidden_language_rejection():
    payload = _payload()
    payload["dashboard_entity_facts"][0]["entity_name"] = "buy now"
    result = run_d2_dashboard_visibility_certification(payload)
    gate = [g for g in result["gate_results"] if g["gate"] == "FORBIDDEN_LANGUAGE_ABSENT"][0]
    assert gate["status"] == "BLOCKED"


def test_immutable_input_safety_read_only_boundary_manifest_stability_and_requirements_stability():
    payload = _payload()
    before = deepcopy(payload)
    result = run_d2_dashboard_visibility_certification(payload)
    manifest_a = build_d2_visibility_manifest(payload)
    manifest_b = build_d2_visibility_manifest(deepcopy(payload))
    assert payload == before
    assert result["read_only_boundary"]["preserved"] is True
    assert manifest_a == manifest_b
    assert build_d2_visibility_requirements() == build_d2_visibility_requirements()


def test_d1_d1g_o10_smokes():
    assert build_d1_guardrail_certification()["status"] == "certified"
    assert build_d1_seed_payload()["run_id"].startswith("D1-RUN-")
    out = run_dashboard_o10_closeout_certification(o5_result={"status": "certified"}, o8_result={"status": "verified"}, o9_result={"status": "accepted"})
    assert out["final_decision"] == "certified"
