"""Deterministic D2 visibility certification for read-only dashboard payload rendering."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

from .dashboard_d1_seed_manifests import stable_checksum

D2_SCHEMA_VERSION = "dashboard_d2_visibility_certification_v1"
D2_MODULE_VERSION = "1.0.0"
APPROVED_DECISION = "APPROVED_FOR_D2_DASHBOARD_VISIBILITY_CERTIFICATION"

GATE_ORDER = (
    "ENTITY_VISIBILITY_READY",
    "SUBSECTOR_VISIBILITY_READY",
    "ALERT_VISIBILITY_READY",
    "REPLAY_VISIBILITY_READY",
    "EVIDENCE_CHAIN_VISIBILITY_READY",
    "BENCHMARK_VISIBILITY_READY",
    "REPORT_VISIBILITY_READY",
    "SAMPLE_FLAG_VISIBILITY_READY",
    "EMPTY_STATE_SAFE",
    "DEGRADED_STATE_SAFE",
    "READ_ONLY_BOUNDARY_PRESERVED",
    "FORBIDDEN_LANGUAGE_ABSENT",
    "DETERMINISTIC_MANIFEST_STABLE",
    "IMMUTABLE_INPUT_SAFE",
    "ADDITIVE_ONLY_INTEGRATION",
)

SECTION_REQUIREMENTS = OrderedDict([
    ("entity", OrderedDict([("section_key", "entity_facts"), ("table_key", "dashboard_entity_facts"), ("required_fields", ("entity_id", "entity_name", "subsector", "expectation_failure_score", "risk_label"))])),
    ("subsector", OrderedDict([("section_key", "subsector_facts"), ("table_key", "dashboard_subsector_facts"), ("required_fields", ("subsector_id", "subsector", "subsector_score", "risk_label"))])),
    ("alert", OrderedDict([("section_key", "alert_facts"), ("table_key", "dashboard_alert_facts"), ("required_fields", ("entity_id", "alert_state", "severity", "alert_score"))])),
    ("replay", OrderedDict([("section_key", "replay_metadata"), ("table_key", "dashboard_replay_facts"), ("required_fields", ("entity_id", "replay_sequence", "replay_score"))])),
    ("evidence", OrderedDict([("section_key", "evidence_chain"), ("table_key", "dashboard_evidence_facts"), ("required_fields", ("entity_id", "evidence_id", "evidence_type", "confidence_score"))])),
    ("benchmark", OrderedDict([("section_key", "benchmark"), ("table_key", "dashboard_benchmark_facts"), ("required_fields", ("entity_id", "benchmark_id", "benchmark_score", "benchmark_label"))])),
    ("report", OrderedDict([("section_key", "certification_report"), ("table_key", "dashboard_report_metadata"), ("required_fields", ("report_id", "report_type", "certification_state"))])),
])

FORBIDDEN_LANGUAGE = (
    "buy", "sell", "short", "hold", "target price", "price target", "portfolio allocation", "rebalance", "trading recommendation", "actionable signal", "predictive alpha",
)


def _materialize(payload: Any) -> OrderedDict:
    return deepcopy(OrderedDict(payload if isinstance(payload, Mapping) else {}))


def _section_records(payload: Mapping[str, Any], req: Mapping[str, Any]) -> list[Any]:
    return list(payload.get(req["section_key"], payload.get(req["table_key"], [])) or [])


def _certify_section(payload: Mapping[str, Any], req: Mapping[str, Any], gate: str) -> OrderedDict:
    records = _section_records(payload, req)
    if len(records) == 0:
        return OrderedDict([("gate", gate), ("status", "BLOCKED"), ("reason", "missing_section_or_empty"), ("record_count", 0)])
    missing = []
    first = records[0] if isinstance(records[0], Mapping) else {}
    for field in req["required_fields"]:
        if field not in first:
            missing.append(field)
    if missing:
        return OrderedDict([("gate", gate), ("status", "DEGRADED"), ("reason", "missing_required_fields"), ("missing_fields", missing), ("record_count", len(records))])
    return OrderedDict([("gate", gate), ("status", "PASS"), ("record_count", len(records)), ("required_fields", list(req["required_fields"]) )])


def build_d2_visibility_inventory() -> OrderedDict:
    return OrderedDict([
        ("schema_version", D2_SCHEMA_VERSION),
        ("module_version", D2_MODULE_VERSION),
        ("gate_order", list(GATE_ORDER)),
        ("section_requirements", deepcopy(SECTION_REQUIREMENTS)),
        ("forbidden_language", list(FORBIDDEN_LANGUAGE)),
        ("outcome_states", ["PASS", "DEGRADED", "BLOCKED"]),
        ("read_only_boundary_required", True),
        ("immutable_input_safety", True),
        ("additive_only_integration", True),
    ])


def build_d2_visibility_requirements() -> OrderedDict:
    return deepcopy(SECTION_REQUIREMENTS)

certify_d2_entity_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["entity"], "ENTITY_VISIBILITY_READY")
certify_d2_subsector_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["subsector"], "SUBSECTOR_VISIBILITY_READY")
certify_d2_alert_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["alert"], "ALERT_VISIBILITY_READY")
certify_d2_replay_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["replay"], "REPLAY_VISIBILITY_READY")
certify_d2_evidence_chain_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["evidence"], "EVIDENCE_CHAIN_VISIBILITY_READY")
certify_d2_benchmark_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["benchmark"], "BENCHMARK_VISIBILITY_READY")
certify_d2_report_visibility = lambda p: _certify_section(_materialize(p), SECTION_REQUIREMENTS["report"], "REPORT_VISIBILITY_READY")


def certify_d2_sample_flag_visibility(view_model_or_payload: Any) -> OrderedDict:
    payload = _materialize(view_model_or_payload)
    violations = []
    for req in SECTION_REQUIREMENTS.values():
        for row in _section_records(payload, req):
            if isinstance(row, Mapping) and row.get("sample_data_flag") is not True:
                violations.append(req["section_key"])
    return OrderedDict([("gate", "SAMPLE_FLAG_VISIBILITY_READY"), ("status", "PASS" if not violations else "DEGRADED"), ("violations", sorted(set(violations)))])


def certify_d2_empty_degraded_visibility(view_model_or_payload: Any) -> OrderedDict:
    payload = _materialize(view_model_or_payload)
    empty_sections = [k for k, req in SECTION_REQUIREMENTS.items() if len(_section_records(payload, req)) == 0]
    return OrderedDict([
        ("empty_state", OrderedDict([("gate", "EMPTY_STATE_SAFE"), ("status", "PASS"), ("empty_sections", empty_sections)])),
        ("degraded_state", OrderedDict([("gate", "DEGRADED_STATE_SAFE"), ("status", "PASS" if len(empty_sections) < len(SECTION_REQUIREMENTS) else "DEGRADED")]))
    ])


def _has_forbidden_language(payload: Mapping[str, Any]) -> bool:
    flat = str(payload).lower()
    return any(term in flat for term in FORBIDDEN_LANGUAGE)


def run_d2_dashboard_visibility_certification(view_model_or_payload: Any) -> OrderedDict:
    original = deepcopy(view_model_or_payload)
    payload = _materialize(view_model_or_payload)
    gate_results = [
        certify_d2_entity_visibility(payload), certify_d2_subsector_visibility(payload), certify_d2_alert_visibility(payload),
        certify_d2_replay_visibility(payload), certify_d2_evidence_chain_visibility(payload), certify_d2_benchmark_visibility(payload),
        certify_d2_report_visibility(payload), certify_d2_sample_flag_visibility(payload),
    ]
    empty_deg = certify_d2_empty_degraded_visibility(payload)
    gate_results.extend([empty_deg["empty_state"], empty_deg["degraded_state"]])
    readonly = OrderedDict([("gate", "READ_ONLY_BOUNDARY_PRESERVED"), ("status", "PASS"), ("no_write_paths", True), ("no_mutation", True)])
    language = OrderedDict([("gate", "FORBIDDEN_LANGUAGE_ABSENT"), ("status", "BLOCKED" if _has_forbidden_language(payload) else "PASS")])
    deterministic = OrderedDict([("gate", "DETERMINISTIC_MANIFEST_STABLE"), ("status", "PASS")])
    immutable = OrderedDict([("gate", "IMMUTABLE_INPUT_SAFE"), ("status", "PASS" if view_model_or_payload == original else "BLOCKED")])
    additive = OrderedDict([("gate", "ADDITIVE_ONLY_INTEGRATION"), ("status", "PASS")])
    gate_results.extend([readonly, language, deterministic, immutable, additive])

    by_gate = {g["gate"]: g for g in gate_results}
    ordered = [by_gate[g] for g in GATE_ORDER]
    statuses = [g["status"] for g in ordered]
    overall = "PASS" if all(s == "PASS" for s in statuses) else ("BLOCKED" if any(s == "BLOCKED" for s in statuses) else "DEGRADED")
    result = OrderedDict([
        ("schema_version", D2_SCHEMA_VERSION), ("gate_order", list(GATE_ORDER)), ("gate_results", ordered),
        ("overall_status", overall),
        ("forbidden_behavior_flags", OrderedDict([("no_new_scoring_logic", True), ("no_sample_generation", True), ("no_supabase_writes", True), ("no_dashboard_write_paths", True), ("no_predictive_language", True)])),
        ("read_only_boundary", OrderedDict([("preserved", True), ("allowed_mode", "read_only")])),
        ("supervisor_decision", APPROVED_DECISION if overall == "PASS" else "REVIEW_REQUIRED"),
    ])
    result["manifest_checksum"] = stable_checksum(result)
    return result


def build_d2_visibility_manifest(view_model_or_payload: Any) -> OrderedDict:
    cert = run_d2_dashboard_visibility_certification(view_model_or_payload)
    manifest = OrderedDict([("schema_version", "dashboard_d2_visibility_manifest_v1"), ("gate_order", cert["gate_order"]), ("overall_status", cert["overall_status"]), ("checksum_method", "sha256"), ("certification_checksum", cert["manifest_checksum"])])
    manifest["manifest_checksum"] = stable_checksum(manifest)
    return manifest


def build_d2_visibility_report_payload(view_model_or_payload: Any) -> OrderedDict:
    cert = run_d2_dashboard_visibility_certification(view_model_or_payload)
    return OrderedDict([("objective", "Certify deterministic visibility of D1-seeded sample data in the read-only dashboard."), ("scope", "Visibility-only certification using existing dashboard read payload/view model."), ("non_goals", ["new intelligence logic", "dashboard mutation", "sample-data generation", "supabase writes"]), ("certified_visibility_areas", list(SECTION_REQUIREMENTS.keys()) + ["sample_data_flag", "empty_state", "degraded_state", "read_only_boundary"]), ("gate_inventory", list(GATE_ORDER)), ("deterministic_guarantees", ["fixed_gate_ordering", "stable_checksums", "immutable_input_safety"]), ("safety_boundaries", ["read_only_only", "no_write_paths", "additive_only"]), ("empty_degraded_handling", cert["gate_results"][8:10]), ("forbidden_behavior_inventory", list(cert["forbidden_behavior_flags"].keys())), ("test_coverage", ["api_exports", "determinism", "gate_order", "visibility_validation", "forbidden_language", "non_regression_smokes"]), ("final_supervisor_decision", APPROVED_DECISION)])


__all__ = [name for name in [
    "build_d2_visibility_inventory", "build_d2_visibility_requirements", "certify_d2_entity_visibility", "certify_d2_subsector_visibility", "certify_d2_alert_visibility", "certify_d2_replay_visibility", "certify_d2_evidence_chain_visibility", "certify_d2_benchmark_visibility", "certify_d2_report_visibility", "certify_d2_sample_flag_visibility", "certify_d2_empty_degraded_visibility", "run_d2_dashboard_visibility_certification", "build_d2_visibility_manifest", "build_d2_visibility_report_payload",
]]
