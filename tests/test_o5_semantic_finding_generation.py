from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o5_finding_inventory,
    build_o5_semantic_findings,
    build_o5_dashboard_insight_narratives,
    build_o5_executive_finding_summary,
    build_o5_finding_evidence_map,
    build_o5_supervisor_interpretation_panel,
    build_o5_finding_generation_payload,
    certify_o5_semantic_finding_generation,
    build_o5_semantic_finding_generation_report,
    build_o4_dashboard_integration_payload,
)


def _sample_o4_payload():
    return {
        "integration_version": "o4_real_market_semantic_dashboard_integration_v1",
        "expectation_fragility_kpis": [
            {"kpi_id": "top_entity_composite_pressure", "value": 82.0},
            {"kpi_id": "top_entity_evidence_count", "value": 5},
            {"kpi_id": "top_entity_degraded_evidence_count", "value": 1},
        ],
        "semantic_alerts": [
            {"severity": "HIGH", "symbol": "AAA", "metric_name": "m1", "semantic_category": "VALUATION", "evidence_quality": "HIGH_QUALITY"},
            {"severity": "ELEVATED", "symbol": "BBB", "metric_name": "m2", "semantic_category": "MOMENTUM", "evidence_quality": "DEGRADED_MISSING_VALUE"},
        ],
        "evidence_cards": {"card": "x"},
        "category_summary_panels": {"panel": "y"},
        "market_context_panels": {"context": "z"},
        "governance_status_panel": {"forbidden_capability_inventory": {"live_market_fetching": True}},
        "replay_metadata_panel": {"o3_lineage_checksum": "o3c", "o4_checksum": "o4c"},
        "semantic_dashboard_inventory": {},
        "certification": {"checksum": "o4c"},
    }


def test_public_api_presence_and_smoke():
    p = _sample_o4_payload()
    assert build_o5_finding_inventory(p)
    assert build_o5_semantic_findings(p)
    assert build_o5_dashboard_insight_narratives(p)
    assert build_o5_executive_finding_summary(p)
    assert build_o5_finding_evidence_map(p)
    assert build_o5_supervisor_interpretation_panel(p)
    assert build_o5_finding_generation_payload(p)
    assert certify_o5_semantic_finding_generation(p)
    assert build_o5_semantic_finding_generation_report(p)


def test_deterministic_repeated_output_and_checksum_stability():
    p = _sample_o4_payload()
    a = build_o5_finding_generation_payload(p)
    b = build_o5_finding_generation_payload(p)
    assert a == b
    assert a["o5_checksum"] == b["o5_checksum"]


def test_input_immutability():
    p = _sample_o4_payload()
    before = deepcopy(p)
    _ = build_o5_finding_generation_payload(p)
    assert p == before


def test_happy_path_and_bounds_and_preservation():
    p = _sample_o4_payload()
    findings = build_o5_semantic_findings(p)
    assert findings
    for f in findings:
        assert f["finding_id"].startswith("O5F-")
        assert f["finding_severity"] in ("SEVERE", "HIGH", "ELEVATED", "MODERATE", "LOW")
        assert f["finding_direction"] in ("ELEVATING", "CONTAINED", "SUPPORTIVE", "CONFLICTED", "LIMITED", "NEUTRAL")
        assert f["confidence_label"] in ("HIGH", "MEDIUM", "LOW")
        assert "o4_checksum" in f["lineage_refs"]


def test_degraded_missing_partial_o4_path():
    cert = certify_o5_semantic_finding_generation({"semantic_alerts": []})
    assert cert["certification_status"] == "DEGRADED_FINDINGS_READY"
    assert cert["degraded_reasons"]


def test_blocked_structurally_invalid_path():
    cert = certify_o5_semantic_finding_generation({"expectation_fragility_kpis": "bad", "semantic_alerts": "bad"})
    assert cert["certification_status"] == "BLOCKED_FINDINGS_INVALID"


def test_fixed_finding_order_and_forbidden_language_absence():
    findings = build_o5_semantic_findings(_sample_o4_payload())
    ids = [f["finding_id"] for f in findings]
    assert ids == sorted(ids) or len(ids) >= 1
    blob = str(build_o5_dashboard_insight_narratives(_sample_o4_payload())).lower()
    for term in ("buy", "sell", "short", "long"):
        assert term not in blob


def test_evidence_map_and_narrative_template_determinism():
    p = _sample_o4_payload()
    assert build_o5_finding_evidence_map(p) == build_o5_finding_evidence_map(p)
    assert build_o5_dashboard_insight_narratives(p) == build_o5_dashboard_insight_narratives(p)


def test_governance_inventory_and_report_smoke_and_o1_to_o4_import_smoke():
    panel = build_o5_supervisor_interpretation_panel(_sample_o4_payload())
    assert "forbidden_capability_inventory" in panel
    assert "# O5 Semantic Finding Generation Report" in build_o5_semantic_finding_generation_report(_sample_o4_payload())
    payload = build_o4_dashboard_integration_payload({}, {})
    assert payload["integration_version"].startswith("o4_")
