from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_e7_expectation_capability_inventory,
    validate_e7_required_capabilities,
    certify_e7_api_exports,
    certify_e7_d7_integration_surface,
    certify_e7_determinism_replay_readiness,
    build_e7_governance_boundary_inventory,
    certify_e7_governance_boundaries,
    certify_e7_dashboard_consumption_readiness,
    build_e7_readiness_gate_decision,
    certify_e7_expectation_intelligence_readiness,
    build_e7_expectation_closeout_payload,
    build_e7_expectation_closeout_report,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model
import transmission_layers.expectation_failure.expectation_intelligence as eapi


def _vm():
    return build_d7_dashboard_view_model(findings_payload={"rows":[]}, narratives_payload={"rows":[]}, evidence_payload={"rows":[]}, integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}}, historical_runs_payloads=[])


def test_e7_inventory_validation_and_export_presence():
    inv = build_e7_expectation_capability_inventory()
    assert inv["capability_count"] >= 35
    val = validate_e7_required_capabilities(inv)
    assert val["valid"] is True
    api = certify_e7_api_exports(list(getattr(eapi, "__all__", [])))
    assert api["certified"] is True


def test_e7_d7_determinism_governance_dashboard_and_readiness_statuses():
    vm = _vm()
    d7 = certify_e7_d7_integration_surface(vm)
    assert d7["certified"] is True
    a = {"x":1,"y":[2,3]}
    b = deepcopy(a)
    before = {"a":[1,2]}
    after = deepcopy(before)
    det = certify_e7_determinism_replay_readiness(payload_a=a, payload_b=b, input_before=before, input_after=after)
    assert det["certified"] is True
    gov = certify_e7_governance_boundaries(build_e7_governance_boundary_inventory())
    assert gov["certified"] is True
    dash = certify_e7_dashboard_consumption_readiness(vm)
    assert dash["certified"] is True
    dec = build_e7_readiness_gate_decision(api_ok=True, d7_ok=True, determinism_ok=True, governance_ok=True, dashboard_ok=True, degraded_fallback_available=True, forbidden_flags=[])
    assert dec["status"] == "CERTIFIED_EXPECTATION_INTELLIGENCE_READY"
    blocked = build_e7_readiness_gate_decision(api_ok=True, d7_ok=True, determinism_ok=True, governance_ok=False, dashboard_ok=True, degraded_fallback_available=True, forbidden_flags=["no_llm_calls"])
    assert blocked["status"] == "BLOCKED_EXPECTATION_INTELLIGENCE"


def test_e7_closeout_payload_report_and_degraded_paths():
    vm = _vm()
    x = {"k": "v"}
    payload = build_e7_expectation_closeout_payload(exported_symbols=list(getattr(eapi, "__all__", [])), d7_view_model=vm, sample_payload_a=x, sample_payload_b=deepcopy(x), immutable_input=[1], immutable_input_after=[1])
    assert payload["readiness_gate"]["status"] in {"CERTIFIED_EXPECTATION_INTELLIGENCE_READY", "DEGRADED_EXPECTATION_INTELLIGENCE_READY"}
    report = build_e7_expectation_closeout_report(payload)
    assert report["closeout_status"] in {"CERTIFIED_EXPECTATION_INTELLIGENCE_READY", "DEGRADED_EXPECTATION_INTELLIGENCE_READY", "LIMITED_EXPECTATION_INTELLIGENCE", "BLOCKED_EXPECTATION_INTELLIGENCE"}
    ready = certify_e7_expectation_intelligence_readiness(payload["certifications"])
    assert "readiness_decision" in ready
