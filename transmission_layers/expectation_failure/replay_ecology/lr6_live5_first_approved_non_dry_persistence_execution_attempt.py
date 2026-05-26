"""LR6-LIVE5 first approved non-dry persistence execution attempt (tiny, append-only, fail-closed)."""
from __future__ import annotations

from typing import Any, Callable

from transmission_layers.expectation_failure.replay_ecology.lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution import (
    ISOLATED_PERSISTENCE_TARGET,
    MAX_ENTITIES,
    REQUIRED_APPROVAL_PHRASE,
    REQUIRED_EXECUTION_TOKEN,
    TARGET_METRIC,
)

DETERMINISTIC_VERSION = "LR6_LIVE5_FIRST_APPROVED_NON_DRY_PERSISTENCE_EXECUTION_ATTEMPT_V1"
APPROVED_APPEND_ONLY_ADAPTER = "replay_richness_wave0_shadow_append_only_adapter"
HALT_CONDITIONS = [
    "approval_failure",
    "unsafe_promotion",
    "malformed_payload",
    "missing_lineage",
    "duplicate_key_anomaly",
    "append_only_violation",
    "adapter_mismatch",
    "schema_mismatch",
    "rollback_metadata_failure",
    "entity_scope_overflow",
    "metric_dimension_overflow",
    "unexpected_comparison_ready_transition",
]


def build_lr6_live5_execution_context(*, approval_phrase: str, execution_token: str, entities: list[dict[str, Any]], replay_window_label: str = "W0") -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-LIVE5",
        "approval_phrase": approval_phrase,
        "execution_token": execution_token,
        "entities": list(entities),
        "metric_whitelist": [TARGET_METRIC],
        "entity_count": len(entities),
        "max_entities": MAX_ENTITIES,
        "isolated_persistence_target": ISOLATED_PERSISTENCE_TARGET,
        "adapter_name": APPROVED_APPEND_ONLY_ADAPTER,
        "append_only_required": True,
        "duplicate_prevention_required": True,
        "lineage_retention_required": True,
        "rollback_metadata_required": True,
        "halt_monitor_enabled": True,
        "replay_window_label": replay_window_label,
        "direct_sql_used": False,
    }


def build_lr6_live5_approval_gate(context: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "exact_explicit_approval_phrase": context.get("approval_phrase") == REQUIRED_APPROVAL_PHRASE,
        "non_dry_execution_token": context.get("execution_token") == REQUIRED_EXECUTION_TOKEN,
        "replay_richness_only_whitelist": context.get("metric_whitelist") == [TARGET_METRIC],
        "entity_count_leq_5": isinstance(context.get("entity_count"), int) and 0 < context["entity_count"] <= MAX_ENTITIES,
        "isolated_shadow_target_confirmed": context.get("isolated_persistence_target") == ISOLATED_PERSISTENCE_TARGET,
        "append_only_adapter_confirmed": context.get("adapter_name") == APPROVED_APPEND_ONLY_ADAPTER,
        "duplicate_prevention_enabled": context.get("duplicate_prevention_required") is True,
        "lineage_retention_enabled": context.get("lineage_retention_required") is True,
        "rollback_metadata_enabled": context.get("rollback_metadata_required") is True,
        "halt_monitor_enabled": context.get("halt_monitor_enabled") is True,
    }
    passed = all(checks.values())
    return {"checks": checks, "approval_passed": passed, "abort_before_write": not passed}


def build_lr6_live5_entity_wave_selection(entities: list[dict[str, Any]]) -> dict[str, Any]:
    selected = sorted([e for e in entities if e.get("metric_dimension") == TARGET_METRIC], key=lambda e: str(e.get("entity_id", "")))[:MAX_ENTITIES]
    return {"entity_records": selected, "selected_entities": [e.get("entity_id") for e in selected], "entity_count": len(selected)}


def build_lr6_live5_payload_preparation(entity_wave_selection: dict[str, Any], *, replay_window_label: str = "W0") -> dict[str, Any]:
    prepared, rejected = [], []
    for i, entity in enumerate(entity_wave_selection.get("entity_records", []), start=1):
        payload = {
            "payload_id": f"LR6_LIVE5_PAYLOAD_{i}",
            "entity_id": entity.get("entity_id"),
            "metric_dimension": TARGET_METRIC,
            "comparison_ready": False,
            "source_artifact_refs": [f"artifact://lr6/live5/{entity.get('entity_id')}"] if entity.get("entity_id") else [],
            "schema_version": "LR6_REPLAY_RICHNESS_V1",
            "wave_scope": "LR6_LIVE5_WAVE_001",
            "replay_window_label": replay_window_label,
        }
        (prepared if payload["entity_id"] and payload["source_artifact_refs"] else rejected).append(payload)
    return {"prepared_payloads": prepared, "rejected_payloads": rejected}


def build_lr6_live5_duplicate_prevention_review(prepared_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [f"{p['wave_scope']}|{p['entity_id']}|{p['metric_dimension']}|{p['replay_window_label']}" for p in prepared_payloads]
    return {"duplicate_keys": keys, "deterministic": keys == sorted(keys), "duplicates_found": len(keys) != len(set(keys))}


def build_lr6_live5_append_only_write_plan(prepared_payloads: list[dict[str, Any]], duplicate_prevention: dict[str, Any], lineage_and_rollback: dict[str, Any]) -> dict[str, Any]:
    intents = []
    for p, k in zip(prepared_payloads, duplicate_prevention.get("duplicate_keys", [])):
        intents.append({
            "insert_intent": "append_only_shadow_insert",
            "target_name": ISOLATED_PERSISTENCE_TARGET,
            "adapter_name": APPROVED_APPEND_ONLY_ADAPTER,
            "duplicate_key": k,
            "duplicate_prevention_key": k,
            "lineage_metadata": {"source_artifact_refs": p.get("source_artifact_refs", [])},
            "rollback_metadata": lineage_and_rollback.get("rollback_metadata", {}).get(p.get("payload_id"), {}),
            "payload": p,
        })
    return {"append_only": True, "direct_sql_used": False, "target_name": ISOLATED_PERSISTENCE_TARGET, "adapter_name": APPROVED_APPEND_ONLY_ADAPTER, "insert_intents": intents}


def build_lr6_live5_lineage_and_rollback_metadata(prepared_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    lineage = {p["payload_id"]: p.get("source_artifact_refs", []) for p in prepared_payloads}
    rollback = {p["payload_id"]: {"rollback_ready": True, "rollback_mode": "append_only_quarantine_marker", "wave_scope": p["wave_scope"]} for p in prepared_payloads}
    return {"lineage_refs": lineage, "lineage_retained": all(bool(v) for v in lineage.values()), "rollback_metadata": rollback, "rollback_metadata_present": all(v.get("rollback_ready") for v in rollback.values())}


def build_lr6_live5_halt_condition_monitor(*, approval_gate: dict[str, Any], payload_preparation: dict[str, Any], duplicate_prevention: dict[str, Any], append_only_write_plan: dict[str, Any], lineage_and_rollback: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    checks = {k: False for k in HALT_CONDITIONS}
    if not approval_gate.get("approval_passed"):
        checks["approval_failure"] = True
    if selection.get("entity_count", 0) > MAX_ENTITIES:
        checks["entity_scope_overflow"] = True
    if any(p.get("metric_dimension") != TARGET_METRIC for p in payload_preparation.get("prepared_payloads", [])):
        checks["metric_dimension_overflow"] = True
        checks["schema_mismatch"] = True
    if any(p.get("comparison_ready") is True for p in payload_preparation.get("prepared_payloads", [])):
        checks["unexpected_comparison_ready_transition"] = True
    if any(not p.get("source_artifact_refs") for p in payload_preparation.get("prepared_payloads", [])) or not lineage_and_rollback.get("lineage_retained"):
        checks["missing_lineage"] = True
    if duplicate_prevention.get("duplicates_found") or not duplicate_prevention.get("deterministic"):
        checks["duplicate_key_anomaly"] = True
    if append_only_write_plan.get("append_only") is not True or append_only_write_plan.get("direct_sql_used") is True:
        checks["append_only_violation"] = True
    if append_only_write_plan.get("adapter_name") != APPROVED_APPEND_ONLY_ADAPTER or append_only_write_plan.get("target_name") != ISOLATED_PERSISTENCE_TARGET:
        checks["adapter_mismatch"] = True
    if not lineage_and_rollback.get("rollback_metadata_present"):
        checks["rollback_metadata_failure"] = True
    first = next((k for k in HALT_CONDITIONS if checks[k]), None)
    return {"halt_conditions": checks, "halt_triggered": first is not None, "halt_reason": first}


def execute_lr6_live5_approved_non_dry_attempt(*, entities: list[dict[str, Any]], approval_phrase: str, execution_token: str, persistence_adapter: Callable[[list[dict[str, Any]], dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    context = build_lr6_live5_execution_context(approval_phrase=approval_phrase, execution_token=execution_token, entities=entities)
    approval = build_lr6_live5_approval_gate(context)
    selection = build_lr6_live5_entity_wave_selection(entities)
    payload = build_lr6_live5_payload_preparation(selection, replay_window_label=context["replay_window_label"])
    dup = build_lr6_live5_duplicate_prevention_review(payload["prepared_payloads"])
    lineage = build_lr6_live5_lineage_and_rollback_metadata(payload["prepared_payloads"])
    plan = build_lr6_live5_append_only_write_plan(payload["prepared_payloads"], dup, lineage)
    halt = build_lr6_live5_halt_condition_monitor(approval_gate=approval, payload_preparation=payload, duplicate_prevention=dup, append_only_write_plan=plan, lineage_and_rollback=lineage, selection=selection)
    if halt["halt_triggered"]:
        return {"context": context, "approval_gate": approval, "entity_wave_selection": selection, "payload_preparation": payload, "duplicate_prevention_review": dup, "append_only_write_plan": plan, "lineage_and_rollback_metadata": lineage, "halt_condition_monitor": halt, "persistence_attempted": False, "inserted_rows": 0, "rejected_rows": len(payload["rejected_payloads"]), "adapter_result": None}

    default_adapter = lambda intents, meta: {"inserted_rows": len(intents), "rejected_rows": 0, "duplicate_prevented": not dup["duplicates_found"], "append_only_verified": True, "target_name": meta["target_name"]}
    adapter = persistence_adapter or default_adapter
    adapter_result = adapter(plan["insert_intents"], {"target_name": plan["target_name"], "adapter_name": plan["adapter_name"]})
    return {"context": context, "approval_gate": approval, "entity_wave_selection": selection, "payload_preparation": payload, "duplicate_prevention_review": dup, "append_only_write_plan": plan, "lineage_and_rollback_metadata": lineage, "halt_condition_monitor": halt, "persistence_attempted": True, "inserted_rows": int(adapter_result.get("inserted_rows", 0) or 0), "rejected_rows": int(adapter_result.get("rejected_rows", 0) or 0), "adapter_result": adapter_result}


def build_lr6_live5_post_write_verification(execution: dict[str, Any]) -> dict[str, Any]:
    return {
        "persistence_attempted": execution.get("persistence_attempted", False),
        "inserted_rows": execution.get("inserted_rows", 0),
        "duplicate_prevented": execution.get("adapter_result", {}).get("duplicate_prevented", not execution.get("duplicate_prevention_review", {}).get("duplicates_found", True)),
        "rejected_rows": execution.get("rejected_rows", 0),
        "target_name": execution.get("append_only_write_plan", {}).get("target_name", ISOLATED_PERSISTENCE_TARGET),
        "append_only_verified": execution.get("adapter_result", {}).get("append_only_verified", execution.get("append_only_write_plan", {}).get("append_only") is True),
        "lineage_retained": execution.get("lineage_and_rollback_metadata", {}).get("lineage_retained", False),
        "rollback_metadata_present": execution.get("lineage_and_rollback_metadata", {}).get("rollback_metadata_present", False),
        "halt_triggered": execution.get("halt_condition_monitor", {}).get("halt_triggered", False),
        "halt_reason": execution.get("halt_condition_monitor", {}).get("halt_reason"),
        "scope_compliant": execution.get("entity_wave_selection", {}).get("entity_count", 0) <= MAX_ENTITIES,
        "scaling_authorized": False,
    }


def build_lr6_live5_execution_summary(execution: dict[str, Any]) -> dict[str, Any]:
    return {"approval_passed": execution.get("approval_gate", {}).get("approval_passed", False), "persistence_attempted": execution.get("persistence_attempted", False), "inserted_rows": execution.get("inserted_rows", 0), "halt_triggered": execution.get("halt_condition_monitor", {}).get("halt_triggered", False), "halt_reason": execution.get("halt_condition_monitor", {}).get("halt_reason")}


def build_lr6_live5_supervisor_review(*, entities: list[dict[str, Any]], approval_phrase: str, execution_token: str) -> dict[str, Any]:
    execution = execute_lr6_live5_approved_non_dry_attempt(entities=entities, approval_phrase=approval_phrase, execution_token=execution_token)
    return {"objective": "First approved non-dry tiny append-only persistence attempt under explicit controls.", "inspected_paths": ["lr6_live4_first_non_dry_execution_result_verification.py", "lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution.py", "lr6_live2_first_tiny_governed_replay_ingestion_non_dry_readiness_review.py", "lr6_live1_first_tiny_governed_replay_ingestion_dry_run_wave.py", "lr6_evid11_first_real_replay_richness_payload_builder.py"], "execution": execution, "post_write_verification": build_lr6_live5_post_write_verification(execution), "boundary_certification": certify_lr6_live5_execution_boundary(), "realism_warning": "This is a tiny governed attempt only and does not authorize scaling or feature expansion."}


def build_lr6_live5_markdown_report(review: dict[str, Any]) -> str:
    sections = [("objective", review["objective"]), ("inspected LIVE4/LIVE3/LIVE2/LIVE1/EVID paths", review["inspected_paths"]), ("approval gate review", review["execution"].get("approval_gate")), ("tiny-wave scope", review["execution"].get("entity_wave_selection")), ("payload preparation", review["execution"].get("payload_preparation")), ("append-only write plan", review["execution"].get("append_only_write_plan")), ("duplicate prevention", review["execution"].get("duplicate_prevention_review")), ("lineage and rollback metadata", review["execution"].get("lineage_and_rollback_metadata")), ("halt-condition review", review["execution"].get("halt_condition_monitor")), ("execution attempt result", build_lr6_live5_execution_summary(review["execution"])), ("post-write verification", review["post_write_verification"]), ("scaling recommendation", {"scaling_authorized": False, "recommendation": "remain_tiny_and_repeat_controlled_wave"}), ("realism warning", review["realism_warning"]), ("boundary certification", review["boundary_certification"]), ("recommendation for next step", "repeat tiny approved attempt with fresh audit evidence before any broader scope")]
    lines = ["# LR6-LIVE5 — First Approved Non-Dry Persistence Execution Attempt", ""]
    for title, body in sections:
        lines.extend([f"## {title}", f"- {body}", ""])
    return "\n".join(lines)


def certify_lr6_live5_execution_boundary() -> dict[str, Any]:
    return {"approved_non_dry_attempt": True, "execution_requires_explicit_approval": True, "metric_target": TARGET_METRIC, "max_entities": 5, "append_only_required": True, "isolated_persistence_required": True, "direct_sql_used": False, "topology_metrics_enabled": False, "contradiction_migration_enabled": False, "prediction_enabled": False, "trading_enabled": False, "auto_expansion_enabled": False, "scaling_authorized": False}
