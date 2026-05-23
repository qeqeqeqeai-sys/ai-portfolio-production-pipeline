from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o3_dashboard_view_model,
    build_o4_dashboard_integration_payload,
    build_o4_dashboard_kpi_panels,
    build_o4_market_context_sections,
    build_o4_real_market_semantic_dashboard_integration_report,
    build_o4_semantic_alert_panels,
    build_o4_semantic_dashboard_inventory,
    certify_o4_real_market_semantic_dashboard_integration,
)


OBS = [
    {"observation_id": "1", "as_of_date": "2026-05-01", "symbol": "AAA", "entity_name": "A", "sector": "Tech", "subsector": "Soft", "metric_name": "pe", "metric_category": "valuation_proxy", "percentile": 90, "source_name": "src", "checksum": "x"},
    {"observation_id": "2", "as_of_date": "2026-05-01", "symbol": "BBB", "entity_name": "B", "sector": "Fin", "subsector": "Bank", "metric_name": "vix", "metric_category": "stress", "percentile": 70, "source_name": "src", "checksum": "y"},
    {"observation_id": "3", "as_of_date": "2026-05-01", "symbol": "BBB", "entity_name": "B", "sector": "Fin", "subsector": "Bank", "metric_name": "expectation_fragility_score", "metric_category": "score", "percentile": 95, "source_name": "src", "checksum": "z"},
]


def test_public_api_presence_and_exports():
    vm = build_o3_dashboard_view_model(OBS)
    assert isinstance(build_o4_semantic_dashboard_inventory(vm), dict)
    assert isinstance(build_o4_dashboard_kpi_panels(vm), list)
    assert isinstance(build_o4_semantic_alert_panels(vm), list)
    assert isinstance(build_o4_market_context_sections(vm), dict)
    assert isinstance(build_o4_dashboard_integration_payload(vm), dict)
    assert isinstance(certify_o4_real_market_semantic_dashboard_integration(vm), dict)
    assert isinstance(build_o4_real_market_semantic_dashboard_integration_report(vm), str)


def test_deterministic_output_and_checksum_stability_and_immutability():
    vm = build_o3_dashboard_view_model(OBS)
    vm_copy = deepcopy(vm)
    p1 = build_o4_dashboard_integration_payload(vm)
    p2 = build_o4_dashboard_integration_payload(vm)
    assert p1 == p2
    assert p1["certification"]["checksum"] == p2["certification"]["checksum"]
    assert vm == vm_copy


def test_happy_path_o3_compatible():
    vm = build_o3_dashboard_view_model(OBS)
    cert = certify_o4_real_market_semantic_dashboard_integration(vm)
    assert cert["certification_status"] == "CERTIFIED_SEMANTIC_DASHBOARD_READY"


def test_missing_partial_o3_degraded_path():
    cert = certify_o4_real_market_semantic_dashboard_integration({"semantic_evidence_records": []})
    assert cert["certification_status"] == "DEGRADED_SEMANTIC_DASHBOARD_READY"
    assert cert["degraded_reasons"]


def test_structurally_invalid_blocked_path():
    cert = certify_o4_real_market_semantic_dashboard_integration({"semantic_evidence_records": "bad"})
    assert cert["certification_status"] == "BLOCKED_SEMANTIC_DASHBOARD_INVALID"


def test_fixed_panel_ordering_and_kpi_bounds_and_alert_tiebreak():
    vm = build_o3_dashboard_view_model(OBS)
    inv = build_o4_semantic_dashboard_inventory(vm)
    assert inv["semantic_panel_ids"] == ["executive_semantic_summary", "evidence_cards", "category_summary_panels", "market_context_panels", "governance_status_panel", "replay_metadata_panel"]
    kpis = build_o4_dashboard_kpi_panels(vm)
    pressure = [k for k in kpis if k["kpi_id"] == "top_entity_composite_pressure"][0]
    assert 0 <= pressure["value"] <= 100
    alerts = build_o4_semantic_alert_panels(vm)
    assert alerts == sorted(alerts, key=lambda x: (["SEVERE", "HIGH", "ELEVATED", "MODERATE", "LOW"].index(x["severity"]) if x["severity"] in ["SEVERE", "HIGH", "ELEVATED", "MODERATE", "LOW"] else 99, -x["score"], x["symbol"], x["metric_name"], x["semantic_category"]))


def test_lineage_and_governance_and_forbidden_capabilities_and_report_smoke():
    vm = build_o3_dashboard_view_model(OBS)
    vm["lineage"] = {"o3_checksum": vm["certification_summary"]["checksum"]}
    payload = build_o4_dashboard_integration_payload(vm)
    assert payload["replay_metadata_panel"]["o3_lineage_checksum"]
    cert = payload["certification"]
    assert cert["forbidden_capability_inventory"]["network_calls"] is True
    report = build_o4_real_market_semantic_dashboard_integration_report(vm)
    assert "O4 Real Market Semantic Dashboard Integration Report" in report


def test_o1_o2_o3_non_regression_import_smoke():
    from transmission_layers.expectation_failure.dashboard_operationalization import (
        build_o1_operational_visibility_report,
        build_o2_replay_operationalization_report,
        build_o3_real_market_semantic_inputs_report,
    )

    assert callable(build_o1_operational_visibility_report)
    assert callable(build_o2_replay_operationalization_report)
    assert callable(build_o3_real_market_semantic_inputs_report)
