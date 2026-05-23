from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as pkg
from transmission_layers.expectation_failure.dashboard_operationalization.d5_real_dashboard_execution_closeout import (
    BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID,
    CERTIFIED_REAL_DASHBOARD_EXECUTION_COMPLETE,
    DEGRADED_REAL_DASHBOARD_EXECUTION_COMPLETE,
    build_d5_real_dashboard_execution_closeout_payload,
    build_d5_real_dashboard_execution_closeout_report,
)


def _happy_payload():
    return {
        "o9": {"status": "CERTIFIED_DASHBOARD_OPERATIONALIZATION_CLOSEOUT_COMPLETE", "closeout_checksum": "o9c"},
        "d2": {"status": "CERTIFIED_DASHBOARD_SCHEMA_READY", "contract_checksum": "d2c"},
        "d3": {
            "certification_status": "CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY",
            "execution_state": "DRY_RUN_NOT_EXECUTED",
            "summary_checksum": "d3s",
            "handoff_checksum": "d3h",
            "audit_records": [{"record_id": "a1"}],
        },
        "d4": {
            "certification_status": "CERTIFIED_REAL_READBACK_VERIFIED",
            "verification_status": "CERTIFIED_REAL_READBACK_VERIFIED",
            "verification_checksum": "d4v",
            "handoff_checksum": "d4h",
            "summary_checksum": "d4s",
        },
        "replay_metadata": {"replay_id": "R1", "replay_checksum": "rc"},
    }


def test_public_api_presence_and_package_exports_and_import_smoke():
    expected = [
        "build_d5_execution_layer_inventory",
        "build_d5_real_execution_lineage_summary",
        "build_d5_real_execution_invariant_review",
        "build_d5_schema_persistence_readback_review",
        "build_d5_real_execution_checksum_manifest",
        "build_d5_real_dashboard_execution_closeout_payload",
        "certify_d5_real_dashboard_execution_closeout",
        "build_d5_real_dashboard_execution_closeout_report",
        "build_o9_dashboard_operationalization_closeout_report",
        "build_d2_dashboard_supabase_schema_report",
        "build_d3_controlled_dashboard_persistence_execution_report",
        "build_d4_real_persistence_readback_verification_report",
    ]
    for name in expected:
        assert hasattr(pkg, name)


def test_deterministic_checksum_stability_and_input_immutability_happy_path():
    payload = _happy_payload()
    original = deepcopy(payload)
    p1 = build_d5_real_dashboard_execution_closeout_payload(payload)
    p2 = build_d5_real_dashboard_execution_closeout_payload(payload)
    assert p1 == p2
    assert p1["closeout_payload_checksum"] == p2["closeout_payload_checksum"]
    assert payload == original
    assert p1["certification"]["status"] == CERTIFIED_REAL_DASHBOARD_EXECUTION_COMPLETE
    assert [x["layer"] for x in p1["execution_layer_inventory"]["layers"]] == ["O9", "D2", "D3", "D4"]


def test_missing_optional_details_degraded_path_and_review_completeness():
    payload = _happy_payload()
    payload.pop("replay_metadata")
    payload["d3"].pop("handoff_checksum")
    out = build_d5_real_dashboard_execution_closeout_payload(payload)
    assert out["certification"]["status"] == DEGRADED_REAL_DASHBOARD_EXECUTION_COMPLETE
    assert out["schema_persistence_readback_review"]
    assert out["real_execution_invariant_review"]["invariants"]


def test_missing_required_layer_blocked_and_upstream_blocked_and_forbidden_violation_precedence():
    payload = _happy_payload()
    payload.pop("d4")
    out = build_d5_real_dashboard_execution_closeout_payload(payload)
    assert out["certification"]["status"] == BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID

    payload2 = _happy_payload()
    payload2["d3"]["certification_status"] = "BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID"
    out2 = build_d5_real_dashboard_execution_closeout_payload(payload2)
    assert out2["certification"]["status"] == BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID

    payload3 = _happy_payload()
    payload3["database_reads"] = True
    out3 = build_d5_real_dashboard_execution_closeout_payload(payload3)
    assert out3["certification"]["status"] == BLOCKED_REAL_DASHBOARD_EXECUTION_INVALID


def test_lineage_and_manifest_and_report_smoke():
    payload = _happy_payload()
    out = build_d5_real_dashboard_execution_closeout_payload(payload)
    assert out["real_execution_lineage_summary"]["lineage_continuity"]["d3_to_d4_handoff_present"] is True
    assert out["real_execution_checksum_manifest"]["manifest_checksum"]
    report = build_d5_real_dashboard_execution_closeout_report(payload)
    assert report["closeout_payload"]["certification"]["status"] == CERTIFIED_REAL_DASHBOARD_EXECUTION_COMPLETE
