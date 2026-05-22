from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_guardrail_contracts import (
    APPROVED_DECISION,
    build_d1_guardrail_certification,
    build_d1_guardrail_contract,
    build_d1_guardrail_inventory,
    build_d1_guardrail_manifest,
    build_d1_guardrail_report_payload,
    validate_d1_seed_payload_against_guardrails,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_d1_sample_data_seed import (
    FIXED_TIMESTAMP,
    build_d1_seed_payload,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o10_real_data_operationalization_closeout import (
    run_dashboard_o10_closeout_certification,
)


def test_public_api_export_presence_and_additive_behavior():
    for name in [
        "build_d1_guardrail_inventory",
        "build_d1_guardrail_contract",
        "validate_d1_seed_payload_against_guardrails",
        "build_d1_guardrail_manifest",
        "build_d1_guardrail_certification",
        "build_d1_guardrail_report_payload",
        "build_d1_seed_payload",
    ]:
        assert hasattr(mod, name)


def test_deterministic_repeated_outputs_checksum_stability_and_ordering():
    a = build_d1_guardrail_contract()
    b = build_d1_guardrail_contract()
    assert a == b
    assert a["contract_checksum"] == b["contract_checksum"]
    assert list(build_d1_guardrail_inventory().keys()) == [
        "fixed_timestamp", "id_namespace_prefixes", "manifest_schema", "checksum_method", "table_inventory_expectations",
        "bounded_score_range", "allowed_labels", "required_sample_data_flag", "forbidden_language_inventory",
        "dry_run_default_policy", "explicit_execution_confirmation_policy", "o3_only_controlled_persistence_policy",
        "no_dashboard_write_path_expansion", "no_predictive_actionable_synthetic_behavior", "immutable_input_safety",
    ]


def test_fixed_timestamp_and_id_namespace_contracts_and_manifest_schema_stability():
    inv = build_d1_guardrail_inventory()
    assert inv["fixed_timestamp"] == FIXED_TIMESTAMP
    assert inv["manifest_schema"] == "dashboard_d1_seed_manifest_v1"
    assert inv["id_namespace_prefixes"][0] == "D1-RUN-"


def test_validation_passes_for_d1_seed_and_input_immutable():
    payload = build_d1_seed_payload()
    before = deepcopy(payload)
    result = validate_d1_seed_payload_against_guardrails(payload)
    assert payload == before
    assert result["valid"] is True


def test_validation_fails_for_bounds_labels_sample_flag_namespace_timestamp_and_forbidden_language():
    payload = build_d1_seed_payload()
    payload["dashboard_entity_facts"][0]["expectation_failure_score"] = 101
    payload["dashboard_entity_facts"][0]["risk_label"] = "critical"
    payload["dashboard_entity_facts"][0]["sample_data_flag"] = False
    payload["dashboard_entity_facts"][0]["entity_id"] = "ENTITY-001"
    payload["dashboard_entity_facts"][0]["as_of_sgt"] = "2026-01-02T00:00:00+08:00"
    payload["dashboard_entity_facts"][0]["entity_name"] = "buy now"
    result = validate_d1_seed_payload_against_guardrails(payload)
    assert result["valid"] is False
    assert any("score_out_of_range" in v for v in result["violations"])
    assert any("label_not_allowed" in v for v in result["violations"])
    assert any("sample_data_flag_missing" in v for v in result["violations"])
    assert any("id_namespace_violation" in v for v in result["violations"])
    assert any("timestamp_mismatch" in v for v in result["violations"])
    assert any("forbidden_language" in v for v in result["violations"])


def test_manifest_and_policies_and_certification_decision():
    manifest = build_d1_guardrail_manifest()
    contract = build_d1_guardrail_contract()
    cert = build_d1_guardrail_certification()
    assert manifest["checksum_method"] == "sha256"
    assert contract["guardrail_inventory"]["dry_run_default_policy"] is True
    assert contract["guardrail_inventory"]["o3_only_controlled_persistence_policy"] is True
    assert cert["supervisor_decision"] == APPROVED_DECISION


def test_d1_non_regression_smoke_and_o10_closeout_smoke():
    assert build_d1_seed_payload()["fixed_timestamp"] == FIXED_TIMESTAMP
    out = run_dashboard_o10_closeout_certification(
        o5_result={"status": "certified"},
        o8_result={"status": "verified"},
        o9_result={"status": "accepted"},
    )
    assert out["final_decision"] == "certified"


def test_report_payload_stability():
    assert build_d1_guardrail_report_payload() == build_d1_guardrail_report_payload()
