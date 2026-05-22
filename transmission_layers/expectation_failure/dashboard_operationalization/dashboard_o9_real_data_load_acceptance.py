"""Dashboard O9 deterministic real-data load acceptance (read-only supervisor review layer)."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION = "dashboard_o9_real_data_load_acceptance_v1"
MODULE_VERSION = "1.0.0"

_REQUIRED_SECTIONS = (
    "entity_facts",
    "subsector_facts",
    "alert_facts",
    "benchmark_facts",
    "replay_facts",
    "evidence_facts",
    "certification_metadata",
)

_ALLOWED_STATUSES = (
    "accepted",
    "accepted_with_degraded_sections",
    "provisional",
    "blocked",
    "invalid_client",
)


def build_dashboard_o9_acceptance_scope() -> OrderedDict:
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", "Deterministic supervisor acceptance review for first real Supabase dashboard read trial via certified runtime/read paths."),
        ("read_path", ["dashboard_o7_streamlit_supabase_runtime", "dashboard_o6_supabase_read_adapter", "dashboard_o8_supabase_deployment_verification"]),
        ("required_sections", list(_REQUIRED_SECTIONS)),
        ("status_values", list(_ALLOWED_STATUSES)),
        ("forbidden_operations", ["insert", "update", "delete", "upsert", "rpc", "raw_sql", "arbitrary_table_access", "unrestricted_column_access", "dashboard_triggered_mutation"]),
    ])


def evaluate_dashboard_real_data_presence(snapshot) -> OrderedDict:
    materialized = deepcopy(dict(snapshot or {})) if isinstance(snapshot, Mapping) else {}
    populated = []
    for section in _REQUIRED_SECTIONS:
        part = materialized.get(section) or {}
        rows = part.get("rows", []) if isinstance(part, Mapping) else []
        if isinstance(rows, list) and len(rows) > 0:
            populated.append(section)
    return OrderedDict([("has_real_data", len(populated) > 0), ("populated_sections", populated)])


def evaluate_dashboard_section_population(snapshot) -> OrderedDict:
    materialized = deepcopy(dict(snapshot or {})) if isinstance(snapshot, Mapping) else {}
    populated_sections, empty_sections = [], []
    for section in _REQUIRED_SECTIONS:
        part = materialized.get(section) or {}
        rows = part.get("rows", []) if isinstance(part, Mapping) else []
        if isinstance(rows, list) and len(rows) > 0:
            populated_sections.append(section)
        else:
            empty_sections.append(section)
    return OrderedDict([("checked_sections", list(_REQUIRED_SECTIONS)), ("populated_sections", populated_sections), ("empty_sections", empty_sections)])


def evaluate_dashboard_degraded_sections(snapshot) -> list[str]:
    materialized = deepcopy(dict(snapshot or {})) if isinstance(snapshot, Mapping) else {}
    degraded = []
    for section in _REQUIRED_SECTIONS:
        part = materialized.get(section) or {}
        status = part.get("status") if isinstance(part, Mapping) else None
        if status == "degraded":
            degraded.append(section)
    return degraded


def evaluate_dashboard_o8_verification_visibility(o8_result) -> OrderedDict:
    payload = deepcopy(dict(o8_result or {})) if isinstance(o8_result, Mapping) else {}
    status = str(payload.get("status") or "not_provided")
    visible = "status" in payload
    return OrderedDict([("o8_verification_status", status), ("o8_status_visible", visible)])


def run_dashboard_o9_real_data_load_acceptance(client=None, config_or_secrets=None, snapshot=None, o8_result=None):
    scope = build_dashboard_o9_acceptance_scope()
    snap = deepcopy(dict(snapshot or {})) if isinstance(snapshot, Mapping) else None
    if snap is None and (client is not None or isinstance(config_or_secrets, Mapping)):
        from .dashboard_o7_streamlit_supabase_runtime import build_streamlit_supabase_runtime_config, load_streamlit_dashboard_snapshot

        cfg = build_streamlit_supabase_runtime_config(
            supabase_url=(config_or_secrets or {}).get("supabase_url") if isinstance(config_or_secrets, Mapping) else None,
            supabase_key=((config_or_secrets or {}).get("supabase_key") or (config_or_secrets or {}).get("supabase_anon_key")) if isinstance(config_or_secrets, Mapping) else None,
            run_id=(config_or_secrets or {}).get("run_id") if isinstance(config_or_secrets, Mapping) else None,
            as_of_date=(config_or_secrets or {}).get("as_of_date") if isinstance(config_or_secrets, Mapping) else None,
        )
        loaded = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=OrderedDict(), client=client)
        snap = deepcopy(dict(loaded.get("snapshot") or {}))

    if snap is None:
        snap = {}

    if client is not None and not hasattr(client, "table"):
        status = "invalid_client"
    else:
        section_eval = evaluate_dashboard_section_population(snap)
        degraded = evaluate_dashboard_degraded_sections(snap)
        populated_count = len(section_eval["populated_sections"])
        if populated_count == 0:
            status = "provisional" if len(degraded) == 0 else "blocked"
        elif len(degraded) > 0:
            status = "accepted_with_degraded_sections"
        else:
            status = "accepted"

    section_eval = evaluate_dashboard_section_population(snap)
    degraded = evaluate_dashboard_degraded_sections(snap)
    real_presence = evaluate_dashboard_real_data_presence(snap)
    o8_vis = evaluate_dashboard_o8_verification_visibility(o8_result)

    findings = OrderedDict([
        ("real_data_present", real_presence["has_real_data"]),
        ("populated_section_count", len(section_eval["populated_sections"])),
        ("empty_section_count", len(section_eval["empty_sections"])),
        ("degraded_section_count", len(degraded)),
        ("o8_verification_visible", o8_vis["o8_status_visible"]),
    ])

    return OrderedDict([
        ("objective", scope["objective"]),
        ("scope", scope),
        ("read_path", scope["read_path"]),
        ("checked_sections", section_eval["checked_sections"]),
        ("populated_sections", section_eval["populated_sections"]),
        ("empty_sections", section_eval["empty_sections"]),
        ("degraded_sections", degraded),
        ("o8_verification_status", o8_vis["o8_verification_status"]),
        ("forbidden_operations", scope["forbidden_operations"]),
        ("findings", findings),
        ("invariants", OrderedDict([("read_only_acceptance_review_only", True), ("injected_client_only", True), ("no_writes", True), ("no_rpc", True), ("no_raw_sql", True), ("bounded_sample_load_checks_only", True), ("deterministic_output_shape", True), ("immutable_input_safe", True), ("additive_only", True)])),
        ("status", status),
        ("final_decision", "supervisor_acceptance_granted" if status in {"accepted", "accepted_with_degraded_sections"} else "supervisor_follow_up_required"),
    ])


def build_dashboard_o9_acceptance_report_payload(result=None):
    materialized = run_dashboard_o9_real_data_load_acceptance() if result is None else deepcopy(result)
    return OrderedDict([
        ("objective", materialized["objective"]),
        ("scope", materialized["scope"]),
        ("read_path", materialized["read_path"]),
        ("checked_sections", materialized["checked_sections"]),
        ("populated_sections", materialized["populated_sections"]),
        ("empty_sections", materialized["empty_sections"]),
        ("degraded_sections", materialized["degraded_sections"]),
        ("o8_verification_status", materialized["o8_verification_status"]),
        ("forbidden_operations", materialized["forbidden_operations"]),
        ("findings", materialized["findings"]),
        ("invariants", materialized["invariants"]),
        ("final_decision", materialized["final_decision"]),
    ])


__all__ = [
    "build_dashboard_o9_acceptance_scope",
    "evaluate_dashboard_real_data_presence",
    "evaluate_dashboard_section_population",
    "evaluate_dashboard_degraded_sections",
    "evaluate_dashboard_o8_verification_visibility",
    "run_dashboard_o9_real_data_load_acceptance",
    "build_dashboard_o9_acceptance_report_payload",
]
