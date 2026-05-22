from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o5_operationalization_certification import (
    build_dashboard_o5_api_inventory,
    build_dashboard_o5_artifact_inventory,
    build_dashboard_o5_boundary_certification,
    build_dashboard_o5_certification_gates,
    build_dashboard_o5_closeout_report,
    build_dashboard_o5_test_coverage_summary,
    run_dashboard_o5_operationalization_certification,
)


def _inputs():
    return dict(
        o1_export_payload={"dashboard_export_manifest": {"checksum": "x"}},
        o2_persistence_manifest={"validation_status": "PASS"},
        o3_write_manifest={"validation_status": "valid"},
        o4_ui_manifest={"checksum": "y"},
        test_result_summaries=[{"command": "pytest", "status": "pass"}],
    )


def test_public_apis_exist_and_additive_exports():
    names = [
        "build_dashboard_o5_certification_gates", "run_dashboard_o5_operationalization_certification",
        "build_dashboard_o5_api_inventory", "build_dashboard_o5_artifact_inventory",
        "build_dashboard_o5_boundary_certification", "build_dashboard_o5_test_coverage_summary",
        "build_dashboard_o5_closeout_report",
    ]
    for n in names:
        assert hasattr(mod, n)


def test_deterministic_output_checksum_gate_order_key_order_immutability():
    kwargs = _inputs()
    original = deepcopy(kwargs)
    a = run_dashboard_o5_operationalization_certification(**kwargs)
    b = run_dashboard_o5_operationalization_certification(**deepcopy(kwargs))
    assert kwargs == original
    assert a == b
    assert a["certification_manifest"]["checksum"] == b["certification_manifest"]["checksum"]
    assert [g["gate_id"] for g in a["certification_gates"]] == [f"G{str(i).zfill(2)}" for i in range(1, 26)]
    assert list(a.keys()) == [
        "schema_version", "module_version", "certification_status", "closeout_decision", "gate_summary", "certification_gates", "api_inventory", "artifact_inventory", "boundary_certification", "test_coverage_summary", "certification_manifest", "invariant_flags"
    ]


def test_decision_rules_and_summary_counts_and_manifest_counts():
    ok = run_dashboard_o5_operationalization_certification(**_inputs())
    assert ok["certification_status"] == "certified"

    provisional = run_dashboard_o5_operationalization_certification()
    assert provisional["certification_status"] == "provisional"

    gates = build_dashboard_o5_certification_gates(**_inputs())
    gates[0]["status"] = "FAIL"
    # emulate decision rule with required blocking fail using API input semantics
    blocked = run_dashboard_o5_operationalization_certification(o1_export_payload={})
    assert blocked["certification_status"] in {"provisional", "blocked"}

    summary = ok["gate_summary"]
    manifest = ok["certification_manifest"]
    assert summary["gate_count"] == 25
    assert manifest["gate_count"] == 25
    assert manifest["pass_count"] == summary["pass_count"]


def test_invariants_inventory_boundary_coverage_and_forbidden_language_absence():
    out = run_dashboard_o5_operationalization_certification(**_inputs())
    required_flags = [
        "deterministic_only", "certification_only", "no_new_intelligence_logic", "no_database_writes", "no_network_calls", "no_file_writes_from_core_logic", "no_streamlit_ui_changes", "no_trading_recommendations", "no_target_prices", "no_portfolio_allocation", "no_backtesting", "no_predictive_modelling", "no_autonomous_notifications", "immutable_input_safe", "additive_only",
    ]
    for f in required_flags:
        assert out["invariant_flags"][f] is True

    api = build_dashboard_o5_api_inventory()
    assert all(api[k] for k in ["o1_public_apis", "o2_public_apis", "o3_public_apis", "o4_public_apis", "o5_public_apis"])

    art = build_dashboard_o5_artifact_inventory()
    text = str(art).lower()
    for required in ["dashboard_o1_export_schema", "dashboard_o2_supabase_contracts", "dashboard_o3_supabase_write_adapter", "dashboard_o4_streamlit_view_model", "test_dashboard_o4_streamlit_app_import_path", "dashboard_o5_operationalization_certification_report"]:
        assert required in text

    boundary = build_dashboard_o5_boundary_certification()
    assert all(boundary.values())

    cov = build_dashboard_o5_test_coverage_summary()
    assert len(cov["expected_commands"]) == 7

    closeout = build_dashboard_o5_closeout_report(**_inputs())
    low = str(closeout).lower()
    for forbidden in ["buy", "sell", "target price"]:
        assert forbidden not in low
