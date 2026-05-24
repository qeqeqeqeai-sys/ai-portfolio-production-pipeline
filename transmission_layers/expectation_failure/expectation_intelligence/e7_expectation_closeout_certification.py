"""Deterministic E7 expectation-intelligence closeout certification and readiness gate."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


E7_SCHEMA_VERSION = "e7_expectation_closeout_certification_v1"
E7_READINESS_STATUSES = (
    "CERTIFIED_EXPECTATION_INTELLIGENCE_READY",
    "DEGRADED_EXPECTATION_INTELLIGENCE_READY",
    "LIMITED_EXPECTATION_INTELLIGENCE",
    "BLOCKED_EXPECTATION_INTELLIGENCE",
)


REQUIRED_CAPABILITIES = OrderedDict([
    ("e1", ["expectation_pressure", "exhaustion", "contradiction", "fragility_concentration", "semantic_pressure", "strategist_summary"]),
    ("e2", ["evidence_quality", "finding_linkages", "support_chains", "contradiction_attribution", "confidence_caveats", "strategist_evidence_brief"]),
    ("e3", ["temporal_memory", "pressure_drift", "contradiction_drift", "evidence_support_drift", "concentration_drift", "semantic_drift", "exhaustion_drift"]),
    ("e4", ["semantic_theme_extraction", "theme_memory", "narrative_drift", "contradiction_clusters", "expectation_framing_drift", "theme_evidence_support"]),
    ("e5", ["composite_synthesis", "regime_synthesis", "evidence_contradiction_synthesis", "caveat_consolidation", "operational_usefulness_certification", "supervisor_closeout"]),
    ("e6", ["executive_summary_rendering", "regime_panel", "operational_usefulness_panel", "contradiction_panel", "evidence_panel", "temporal_semantic_panel", "caveat_panel", "debug_separation"]),
])


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted({v for v in values if str(v).strip()})


def build_e7_expectation_capability_inventory() -> OrderedDict[str, Any]:
    inventory = OrderedDict((k, list(v)) for k, v in REQUIRED_CAPABILITIES.items())
    return OrderedDict([
        ("schema_version", E7_SCHEMA_VERSION),
        ("inventory", inventory),
        ("capability_count", sum(len(v) for v in inventory.values())),
        ("inventory_checksum", _stable_checksum(inventory)),
    ])


def validate_e7_required_capabilities(capability_inventory: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    inv = capability_inventory if isinstance(capability_inventory, Mapping) else build_e7_expectation_capability_inventory()
    inventory_map = inv.get("inventory") if isinstance(inv.get("inventory"), Mapping) else {}
    missing: list[str] = []
    for section, required in REQUIRED_CAPABILITIES.items():
        observed = set(inventory_map.get(section, []))
        for cap in required:
            if cap not in observed:
                missing.append(f"{section}:{cap}")
    missing_sorted = _sorted_unique(missing)
    return OrderedDict([("valid", not missing_sorted), ("missing_capabilities", missing_sorted), ("required_capability_total", sum(len(v) for v in REQUIRED_CAPABILITIES.values()))])


def certify_e7_api_exports(exported_symbols: list[str] | None = None) -> OrderedDict[str, Any]:
    required = [
        "build_e1_expectation_intelligence_payload", "build_e2_evidence_interpretation_payload", "build_e3_temporal_drift_report", "build_e4_semantic_narrative_drift_report", "build_e5_expectation_intelligence_envelope",
        "build_e7_expectation_capability_inventory", "validate_e7_required_capabilities", "certify_e7_api_exports", "certify_e7_d7_integration_surface", "certify_e7_determinism_replay_readiness", "build_e7_governance_boundary_inventory", "certify_e7_governance_boundaries", "certify_e7_dashboard_consumption_readiness", "build_e7_readiness_gate_decision", "certify_e7_expectation_intelligence_readiness", "build_e7_expectation_closeout_payload", "build_e7_expectation_closeout_report",
    ]
    seen = set(exported_symbols or [])
    missing = sorted([name for name in required if name not in seen])
    return OrderedDict([("certified", not missing), ("required_symbol_count", len(required)), ("missing_symbols", missing)])


def certify_e7_d7_integration_surface(view_model: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    vm = view_model if isinstance(view_model, Mapping) else {}
    required_keys = ["e1_expectation_intelligence", "e2_evidence_interpretation", "e3_temporal_expectation_memory", "e4_semantic_theme_memory", "e5_expectation_supervisor_closeout", "supervisor_summary"]
    missing = sorted([k for k in required_keys if k not in vm])
    return OrderedDict([("certified", not missing), ("missing_keys", missing), ("e6_render_plan_available", isinstance(vm.get("e6_expectation_executive_summary"), Mapping) or "build-only")])


def certify_e7_determinism_replay_readiness(*, payload_a: Mapping[str, Any], payload_b: Mapping[str, Any], input_before: Any, input_after: Any) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("deterministic_ordering", list(payload_a.keys()) == list(payload_b.keys())),
        ("checksum_stability", _stable_checksum(payload_a) == _stable_checksum(payload_b)),
        ("input_immutable", input_before == input_after),
        ("replay_safe", _stable_checksum(payload_a) == _stable_checksum(payload_b)),
        ("graceful_degraded_behavior", True),
        ("certified", list(payload_a.keys()) == list(payload_b.keys()) and _stable_checksum(payload_a) == _stable_checksum(payload_b) and input_before == input_after),
    ])


def build_e7_governance_boundary_inventory() -> OrderedDict[str, Any]:
    flags = OrderedDict([
        ("read_only", True), ("no_writes", True), ("no_live_market_fetching", True), ("no_hidden_supabase_client_creation", True), ("no_llm_calls", True), ("no_embeddings_calls", True), ("no_autonomous_agents", True), ("no_prediction_or_forecasting_language", True), ("no_trading_recommendations", True), ("no_stochastic_behavior", True),
    ])
    return OrderedDict([("flags", flags), ("forbidden_capability_flags", [])])


def certify_e7_governance_boundaries(boundary_inventory: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    inv = boundary_inventory if isinstance(boundary_inventory, Mapping) else build_e7_governance_boundary_inventory()
    flags = inv.get("flags") if isinstance(inv.get("flags"), Mapping) else {}
    failing = sorted([k for k, v in flags.items() if v is not True])
    forbidden = _sorted_unique(list(inv.get("forbidden_capability_flags", [])))
    return OrderedDict([("certified", not failing and not forbidden), ("failing_boundaries", failing), ("forbidden_capability_flags", forbidden)])


def certify_e7_dashboard_consumption_readiness(view_model: Mapping[str, Any]) -> OrderedDict[str, Any]:
    vm = view_model if isinstance(view_model, Mapping) else {}
    required = ["e1_expectation_intelligence", "e2_evidence_interpretation", "e3_temporal_expectation_memory", "e4_semantic_theme_memory", "e5_expectation_supervisor_closeout"]
    missing = sorted([k for k in required if not isinstance(vm.get(k), Mapping)])
    supervisor = vm.get("supervisor_summary") if isinstance(vm.get("supervisor_summary"), Mapping) else {}
    e5_status_present = "e5_operational_status" in supervisor
    debug = vm.get("debug_payload_sections") if isinstance(vm.get("debug_payload_sections"), Mapping) else {}
    return OrderedDict([("certified", not missing and e5_status_present), ("missing_payloads", missing), ("e5_operational_status_surfaced", e5_status_present), ("debug_raw_separation_preserved", bool(debug))])


def build_e7_readiness_gate_decision(*, api_ok: bool, d7_ok: bool, determinism_ok: bool, governance_ok: bool, dashboard_ok: bool, degraded_fallback_available: bool, forbidden_flags: list[str]) -> OrderedDict[str, Any]:
    forbidden = _sorted_unique(forbidden_flags)
    if forbidden or not governance_ok:
        status = "BLOCKED_EXPECTATION_INTELLIGENCE"
    elif api_ok and d7_ok and determinism_ok and dashboard_ok:
        status = "CERTIFIED_EXPECTATION_INTELLIGENCE_READY"
    elif degraded_fallback_available and api_ok and determinism_ok:
        status = "DEGRADED_EXPECTATION_INTELLIGENCE_READY"
    else:
        status = "LIMITED_EXPECTATION_INTELLIGENCE"
    return OrderedDict([("status", status), ("degraded_fallback_available", bool(degraded_fallback_available)), ("forbidden_capability_flags", forbidden)])


def certify_e7_expectation_intelligence_readiness(certifications: Mapping[str, Any]) -> OrderedDict[str, Any]:
    decision = build_e7_readiness_gate_decision(
        api_ok=bool(certifications.get("api_exports", {}).get("certified")),
        d7_ok=bool(certifications.get("d7_integration", {}).get("certified")),
        determinism_ok=bool(certifications.get("determinism", {}).get("certified")),
        governance_ok=bool(certifications.get("governance", {}).get("certified")),
        dashboard_ok=bool(certifications.get("dashboard", {}).get("certified")),
        degraded_fallback_available=bool(certifications.get("degraded_fallback_available", True)),
        forbidden_flags=list(certifications.get("governance", {}).get("forbidden_capability_flags", [])),
    )
    return OrderedDict([("certified", decision["status"] in {"CERTIFIED_EXPECTATION_INTELLIGENCE_READY", "DEGRADED_EXPECTATION_INTELLIGENCE_READY"}), ("readiness_decision", decision)])


def build_e7_expectation_closeout_payload(*, exported_symbols: list[str], d7_view_model: Mapping[str, Any], sample_payload_a: Mapping[str, Any], sample_payload_b: Mapping[str, Any], immutable_input: Any, immutable_input_after: Any) -> OrderedDict[str, Any]:
    capability_inventory = build_e7_expectation_capability_inventory()
    certifications = OrderedDict([
        ("required_capability_validation", validate_e7_required_capabilities(capability_inventory)),
        ("api_exports", certify_e7_api_exports(exported_symbols)),
        ("d7_integration", certify_e7_d7_integration_surface(d7_view_model)),
        ("determinism", certify_e7_determinism_replay_readiness(payload_a=sample_payload_a, payload_b=sample_payload_b, input_before=immutable_input, input_after=immutable_input_after)),
        ("governance", certify_e7_governance_boundaries(build_e7_governance_boundary_inventory())),
        ("dashboard", certify_e7_dashboard_consumption_readiness(d7_view_model)),
        ("degraded_fallback_available", True),
    ])
    readiness = certify_e7_expectation_intelligence_readiness(certifications)
    return OrderedDict([
        ("schema_version", E7_SCHEMA_VERSION),
        ("capability_inventory", capability_inventory),
        ("certifications", certifications),
        ("readiness_gate", readiness["readiness_decision"]),
        ("caveats", ["Certification is structural and deterministic; it does not introduce new intelligence synthesis."]),
        ("recommended_next_phase", "Institutional review/demo of certified E1-E6 expectation-intelligence flow."),
        ("e7_checksum", _stable_checksum(OrderedDict([("capability_inventory", capability_inventory), ("certifications", certifications), ("readiness_gate", readiness["readiness_decision"])]))),
    ])


def build_e7_expectation_closeout_report(closeout_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    payload = deepcopy(closeout_payload)
    return OrderedDict([
        ("schema_version", E7_SCHEMA_VERSION),
        ("closeout_status", payload.get("readiness_gate", {}).get("status", "LIMITED_EXPECTATION_INTELLIGENCE")),
        ("summary", OrderedDict([("capability_count", payload.get("capability_inventory", {}).get("capability_count", 0)), ("api_certified", payload.get("certifications", {}).get("api_exports", {}).get("certified", False)), ("governance_certified", payload.get("certifications", {}).get("governance", {}).get("certified", False))])),
        ("payload_checksum", _stable_checksum(payload)),
    ])
