from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o10_real_data_operationalization_closeout import (
    build_dashboard_o10_closeout_report_payload,
    build_dashboard_o10_closeout_scope,
    build_dashboard_o10_gate_inventory,
    run_dashboard_o10_closeout_certification,
)


def test_public_apis_exist_and_additive_exports():
    for name in [
        "build_dashboard_o10_closeout_scope",
        "build_dashboard_o10_gate_inventory",
        "run_dashboard_o10_closeout_certification",
        "build_dashboard_o10_closeout_report_payload",
    ]:
        assert hasattr(mod, name)


def test_deterministic_repeated_output_and_checksum_stability_and_report_stability():
    kwargs = {
        "o5_result": {"status": "certified"},
        "o8_result": {"status": "verified"},
        "o9_result": {"status": "accepted"},
    }
    first = run_dashboard_o10_closeout_certification(**kwargs)
    second = run_dashboard_o10_closeout_certification(**deepcopy(kwargs))
    assert first == second
    assert first["manifest_checksum"] == second["manifest_checksum"]

    report_a = build_dashboard_o10_closeout_report_payload(first)
    report_b = build_dashboard_o10_closeout_report_payload(deepcopy(second))
    assert report_a == report_b


def test_certified_path():
    result = run_dashboard_o10_closeout_certification(
        o5_result={"status": "certified"},
        o8_result={"status": "verified"},
        o9_result={"status": "accepted"},
    )
    assert result["final_decision"] == "certified"


def test_certified_with_degraded_sections_path():
    result = run_dashboard_o10_closeout_certification(
        o5_result={"status": "certified_with_warnings"},
        o8_result={"status": "degraded"},
        o9_result={"status": "accepted_with_degraded_sections"},
    )
    assert result["final_decision"] == "certified_with_degraded_sections"


def test_provisional_path():
    result = run_dashboard_o10_closeout_certification(
        o5_result={"status": "pending"},
        o8_result={"status": "verified"},
        o9_result={"status": "accepted"},
    )
    assert result["final_decision"] == "provisional"


def test_blocked_path():
    result = run_dashboard_o10_closeout_certification(
        o5_result={"status": "certified"},
        o8_result={"status": "blocked"},
        o9_result={"status": "accepted"},
    )
    assert result["final_decision"] == "blocked"


def test_gate_ordering_and_fixed_count_and_forbidden_operations_and_immutable_input_safety():
    o5 = {"status": "certified"}
    o8 = {"status": "verified"}
    o9 = {"status": "accepted"}
    before = deepcopy((o5, o8, o9))
    result = run_dashboard_o10_closeout_certification(o5_result=o5, o8_result=o8, o9_result=o9)

    assert (o5, o8, o9) == before
    assert len(result["gate_inventory"]) == 25
    assert [g["gate_id"] for g in result["gate_inventory"]] == [f"gate_{i:02d}" for i in range(1, 26)]
    assert [g["gate_id"] for g in result["gate_results"]] == [f"gate_{i:02d}" for i in range(1, 26)]
    for op in ["insert", "update", "delete", "rpc", "raw_sql", "arbitrary_table_access", "unrestricted_column_access", "dashboard_triggered_mutation"]:
        assert op in result["forbidden_operations"]


def test_o4_to_o9_non_regression_smoke():
    from transmission_layers.expectation_failure.dashboard_operationalization import (
        build_dashboard_o4_ui_manifest,
        build_dashboard_o4_view_model,
        build_dashboard_o5_closeout_report,
        build_dashboard_o6_read_adapter_report_payload,
        build_dashboard_o7_runtime_report_payload,
        build_dashboard_o8_deployment_report_payload,
        build_dashboard_o9_acceptance_report_payload,
    )

    assert "schema_version" in build_dashboard_o4_ui_manifest(build_dashboard_o4_view_model({}))
    assert "schema_version" in build_dashboard_o5_closeout_report()
    assert "schema_version" in build_dashboard_o6_read_adapter_report_payload()
    assert "schema_version" in build_dashboard_o7_runtime_report_payload()
    assert "schema_version" in build_dashboard_o8_deployment_report_payload()
    assert "scope" in build_dashboard_o9_acceptance_report_payload()


def test_scope_and_gate_inventory_deterministic():
    assert build_dashboard_o10_closeout_scope() == build_dashboard_o10_closeout_scope()
    assert build_dashboard_o10_gate_inventory() == build_dashboard_o10_gate_inventory()
