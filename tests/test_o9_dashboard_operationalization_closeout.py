from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o9_dashboard_operationalization_closeout_payload,
    build_o9_dashboard_operationalization_closeout_report,
    build_o9_end_to_end_invariant_review,
    build_o9_end_to_end_lineage_summary,
    build_o9_governance_boundary_review,
    build_o9_operationalization_layer_inventory,
    build_o9_replay_checksum_manifest,
    certify_o9_dashboard_operationalization_closeout,
)


def _upstream(omit=None):
    omit = set(omit or [])
    payload = {f"o{i}": {"status": "certified", "checksum": f"c{i}", "lineage_references": [f"o{i-1}"] if i > 1 else ["root"]} for i in range(1, 9) if f"o{i}" not in omit}
    payload["replay_metadata"] = {"run_id": "r1"}
    return payload


def test_public_api_presence():
    for fn in [
        build_o9_operationalization_layer_inventory,
        build_o9_end_to_end_lineage_summary,
        build_o9_end_to_end_invariant_review,
        build_o9_governance_boundary_review,
        build_o9_replay_checksum_manifest,
        build_o9_dashboard_operationalization_closeout_payload,
        certify_o9_dashboard_operationalization_closeout,
        build_o9_dashboard_operationalization_closeout_report,
    ]:
        assert callable(fn)


def test_deterministic_and_checksum_stable_and_input_immutable():
    src = _upstream()
    before = deepcopy(src)
    a = build_o9_dashboard_operationalization_closeout_payload(src)
    b = build_o9_dashboard_operationalization_closeout_payload(src)
    assert a == b
    assert a["replay_checksum_manifest"] == b["replay_checksum_manifest"]
    assert src == before


def test_happy_path_certified():
    out = build_o9_dashboard_operationalization_closeout_payload(_upstream())
    assert out["certification"]["certification_status"] == "CERTIFIED_DASHBOARD_OPERATIONALIZATION_COMPLETE"


def test_missing_optional_details_degraded():
    p = _upstream()
    p["o2"].pop("lineage_references")
    out = build_o9_dashboard_operationalization_closeout_payload(p)
    assert out["certification"]["certification_status"] == "DEGRADED_DASHBOARD_OPERATIONALIZATION_COMPLETE"


def test_missing_required_layer_blocked_and_upstream_blocked_propagation():
    out = build_o9_dashboard_operationalization_closeout_payload(_upstream(omit=["o3"]))
    assert out["certification"]["certification_status"] == "BLOCKED_DASHBOARD_OPERATIONALIZATION_INVALID"
    p = _upstream()
    p["o4"]["status"] = "blocked"
    out2 = build_o9_dashboard_operationalization_closeout_payload(p)
    assert out2["certification"]["certification_status"] == "BLOCKED_DASHBOARD_OPERATIONALIZATION_INVALID"


def test_forbidden_capability_violation_blocked_and_precedence():
    p = _upstream()
    p["forbidden_capabilities"] = ["llm_calls"]
    out = build_o9_dashboard_operationalization_closeout_payload(p)
    assert out["certification"]["certification_status"] == "BLOCKED_DASHBOARD_OPERATIONALIZATION_INVALID"


def test_fixed_order_lineage_manifest_and_review_completeness():
    out = build_o9_dashboard_operationalization_closeout_payload(_upstream())
    assert [x["layer"] for x in out["layer_inventory"]] == [f"O{i}" for i in range(1, 9)]
    assert "lineage_continuity" in out["end_to_end_lineage_summary"]
    assert "governance_boundary_compliant" in out["governance_boundary_review"]
    assert "deterministic_payload_shape" in out["end_to_end_invariant_review"]
    m1 = out["replay_checksum_manifest"]
    m2 = build_o9_dashboard_operationalization_closeout_payload(_upstream())["replay_checksum_manifest"]
    assert m1 == m2


def test_report_smoke_and_package_export_and_non_regression_import_smoke():
    report = build_o9_dashboard_operationalization_closeout_report(_upstream())
    assert "certification" in report
    import transmission_layers.expectation_failure.dashboard_operationalization as m

    assert hasattr(m, "build_o1_operational_visibility_report")
    assert hasattr(m, "build_o2_replay_operationalization_report")
    assert hasattr(m, "build_o3_real_market_semantic_inputs_report")
    assert hasattr(m, "build_o4_real_market_semantic_dashboard_integration_report")
    assert hasattr(m, "build_o5_semantic_finding_generation_report")
    assert hasattr(m, "build_o6_finding_persistence_export_contract_report")
    assert hasattr(m, "build_o7_dashboard_persistence_adapter_report")
    assert hasattr(m, "build_o8_dashboard_persistence_readback_verification_report")
    assert hasattr(m, "build_o9_dashboard_operationalization_closeout_report")
