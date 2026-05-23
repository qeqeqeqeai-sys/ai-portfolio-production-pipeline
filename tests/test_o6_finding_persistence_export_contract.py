from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o5_finding_generation_payload,
    build_o6_dashboard_export_bundle,
    build_o6_evidence_map_records,
    build_o6_finding_export_inventory,
    build_o6_finding_persistence_export_contract_report,
    build_o6_finding_records,
    build_o6_narrative_records,
    build_o6_supervisor_panel_records,
    certify_o6_finding_persistence_export_contract,
)


def _o4_sample_payload():
    return {
        "integration_version": "o4_test",
        "expectation_fragility_kpis": [{"kpi_id": "top_entity_composite_pressure", "value": 74}],
        "semantic_alerts": [
            {"severity": "HIGH", "semantic_category": "EARNINGS", "symbol": "AAA", "metric_name": "m1", "evidence_quality": "GOOD"},
            {"severity": "MODERATE", "semantic_category": "GUIDANCE", "symbol": "BBB", "metric_name": "m2", "evidence_quality": "DEGRADED_PARTIAL"},
        ],
        "governance_status_panel": {"forbidden_capability_inventory": {"database_writes": True}},
        "replay_metadata_panel": {"o3_lineage_checksum": "l1", "o4_checksum": "l2"},
        "certification": {"checksum": "c1"},
    }


def test_public_api_presence_and_non_regression_smoke_imports():
    import transmission_layers.expectation_failure.dashboard_operationalization as m

    assert hasattr(m, "build_o1_operational_visibility_report")
    assert hasattr(m, "build_o2_replay_timeline")
    assert hasattr(m, "build_o3_dashboard_view_model")
    assert hasattr(m, "build_o4_dashboard_integration_payload")
    assert hasattr(m, "build_o5_finding_generation_payload")
    assert hasattr(m, "build_o6_dashboard_export_bundle")


def test_o6_happy_path_deterministic_and_checksum_stable_and_shape():
    payload = build_o5_finding_generation_payload(_o4_sample_payload())
    a = build_o6_dashboard_export_bundle(payload)
    b = build_o6_dashboard_export_bundle(payload)
    assert a == b
    assert a["o6_checksum"] == b["o6_checksum"]
    assert a["finding_records"] == sorted(a["finding_records"], key=lambda x: (x["finding_id"], x["record_id"]))
    fr = a["finding_records"][0]
    expected = {
        "record_id", "record_type", "finding_id", "finding_type", "finding_title", "finding_severity",
        "finding_direction", "confidence_label", "finding_summary", "supporting_evidence_refs",
        "semantic_category_refs", "kpi_refs", "alert_refs", "lineage_refs", "source_payload_checksum", "export_checksum",
    }
    assert set(fr.keys()) == expected


def test_input_immutability_and_id_reference_preservation():
    payload = build_o5_finding_generation_payload(_o4_sample_payload())
    payload_copy = deepcopy(payload)
    bundle = build_o6_dashboard_export_bundle(payload)
    assert payload == payload_copy
    finding_ids = {f["finding_id"] for f in payload["semantic_findings"]}
    exported_ids = {r["finding_id"] for r in bundle["finding_records"]}
    assert finding_ids == exported_ids
    assert any(r["supporting_evidence_refs"] for r in bundle["evidence_map_records"])
    assert all(r["lineage_refs"] for r in bundle["finding_records"])


def test_degraded_missing_partial_payload():
    degraded_payload = {
        "semantic_findings": [],
        "dashboard_insight_narratives": {},
        "finding_evidence_map": {},
        "supervisor_interpretation_panel": {},
        "certification": {},
    }
    cert = certify_o6_finding_persistence_export_contract(degraded_payload)
    assert cert["certification_status"] == "DEGRADED_FINDING_EXPORT_READY"
    assert cert["degraded_reasons"]


def test_blocked_structurally_invalid_payload():
    invalid_payload = {"semantic_findings": "not-a-list", "dashboard_insight_narratives": [], "finding_evidence_map": []}
    cert = certify_o6_finding_persistence_export_contract(invalid_payload)
    assert cert["certification_status"] == "BLOCKED_FINDING_EXPORT_INVALID"
    assert cert["blocking_reasons"]


def test_record_ids_deterministic_and_order_fixed_and_package_exports_present():
    payload = build_o5_finding_generation_payload(_o4_sample_payload())
    r1 = build_o6_finding_records(payload)
    r2 = build_o6_finding_records(payload)
    assert [x["record_id"] for x in r1] == [x["record_id"] for x in r2]
    import transmission_layers.expectation_failure.dashboard_operationalization as m

    for name in [
        "build_o6_finding_export_inventory",
        "build_o6_finding_records",
        "build_o6_narrative_records",
        "build_o6_evidence_map_records",
        "build_o6_supervisor_panel_records",
        "build_o6_dashboard_export_bundle",
        "certify_o6_finding_persistence_export_contract",
        "build_o6_finding_persistence_export_contract_report",
    ]:
        assert hasattr(m, name)


def test_governance_inventory_forbidden_capabilities_and_report_smoke():
    payload = build_o5_finding_generation_payload(_o4_sample_payload())
    cert = certify_o6_finding_persistence_export_contract(payload)
    inv = cert["forbidden_capability_inventory"]
    assert inv["database_writes"] and inv["network_calls"] and inv["llm_calls"]
    report = build_o6_finding_persistence_export_contract_report(payload)
    assert "O6 Finding Persistence Export Contract Report" in report


def test_individual_record_builders_smoke():
    payload = build_o5_finding_generation_payload(_o4_sample_payload())
    assert build_o6_finding_export_inventory(payload)["finding_count"] >= 1
    assert build_o6_finding_records(payload)
    assert build_o6_narrative_records(payload)
    assert build_o6_evidence_map_records(payload)
    assert build_o6_supervisor_panel_records(payload)
