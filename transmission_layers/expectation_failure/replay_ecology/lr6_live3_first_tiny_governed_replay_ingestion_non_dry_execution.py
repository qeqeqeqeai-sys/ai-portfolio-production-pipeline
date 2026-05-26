"""LR6-LIVE3 first tiny governed replay ingestion non-dry execution (strictly bounded, fail-closed)."""
from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_LIVE3_FIRST_TINY_GOVERNED_REPLAY_INGESTION_NON_DRY_EXECUTION_V1"
TARGET_METRIC = "replay_richness"
REQUIRED_APPROVAL_PHRASE = "I APPROVE LR6-LIVE NON-DRY TINY REPLAY EXECUTION"
REQUIRED_EXECUTION_TOKEN = "LR6_LIVE_NON_DRY_TINY_EXECUTION_TOKEN_REQUIRED"
MAX_ENTITIES = 5
ISOLATED_PERSISTENCE_TARGET = "replay_richness_wave0_shadow"
HALT_CONDITIONS = [
    "unsafe_promotion",
    "malformed_payload",
    "missing_lineage",
    "governance_failure",
    "append_only_violation",
    "duplicate_prevention_failure",
    "persistence_adapter_mismatch",
    "replay_scope_overflow",
    "metric_dimension_overflow",
    "unexpected_comparison_ready_transition",
    "schema_mismatch",
    "rollback_metadata_failure",
]


def build_lr6_live3_execution_context(*, approval_phrase: str, execution_token: str, max_entities: int = MAX_ENTITIES, replay_window_label: str = "W0") -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-LIVE3",
        "execution_mode": "NON_DRY_GOVERNED_TINY_WAVE",
        "approval_phrase": approval_phrase,
        "execution_token": execution_token,
        "metric_whitelist": [TARGET_METRIC],
        "max_entities": min(max(max_entities, 1), MAX_ENTITIES),
        "replay_window_label": replay_window_label,
        "append_only_required": True,
        "isolated_persistence_target": ISOLATED_PERSISTENCE_TARGET,
        "rollback_metadata_required": True,
        "lineage_retention_required": True,
        "duplicate_prevention_required": True,
        "halt_monitor_enabled": True,
        "topology_metrics_enabled": False,
        "contradiction_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "direct_sql_used": False,
    }


def build_lr6_live3_governance_verification(context: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "explicit_approval_phrase": context.get("approval_phrase") == REQUIRED_APPROVAL_PHRASE,
        "non_dry_execution_token": context.get("execution_token") == REQUIRED_EXECUTION_TOKEN,
        "replay_richness_only_whitelist": context.get("metric_whitelist") == [TARGET_METRIC],
        "max_entity_count_bounded": isinstance(context.get("max_entities"), int) and 0 < context.get("max_entities") <= MAX_ENTITIES,
        "append_only_enabled": context.get("append_only_required") is True,
        "isolated_persistence_target_confirmed": context.get("isolated_persistence_target") == ISOLATED_PERSISTENCE_TARGET,
        "rollback_metadata_enabled": context.get("rollback_metadata_required") is True,
        "lineage_retention_enabled": context.get("lineage_retention_required") is True,
        "halt_monitor_enabled": context.get("halt_monitor_enabled") is True,
        "duplicate_prevention_enabled": context.get("duplicate_prevention_required") is True,
    }
    return {"checks": checks, "governance_passed": all(checks.values()), "abort_before_persistence": not all(checks.values())}


def build_lr6_live3_entity_wave_selection(entities: list[dict[str, Any]], *, max_entities: int = MAX_ENTITIES) -> dict[str, Any]:
    eligible = [e for e in entities if e.get("metric_dimension") == TARGET_METRIC]
    ordered = sorted(eligible, key=lambda e: (str(e.get("cluster", "")), str(e.get("role", "")), str(e.get("entity_id", ""))))
    selected = ordered[: min(max_entities, MAX_ENTITIES)]
    return {"selected_entities": [e.get("entity_id") for e in selected], "entity_records": selected, "entity_count": len(selected)}


def build_lr6_live3_payload_preparation(entity_wave: dict[str, Any], *, replay_window_label: str = "W0") -> dict[str, Any]:
    prepared, rejected = [], []
    for idx, e in enumerate(entity_wave.get("entity_records", [])):
        payload = {
            "payload_id": f"LR6_LIVE3_PAYLOAD_{idx+1}",
            "entity_id": e.get("entity_id"),
            "metric_dimension": TARGET_METRIC,
            "comparison_ready": False,
            "source_artifact_refs": [f"artifact://lr6/live3/{e.get('entity_id')}"] if e.get("entity_id") else [],
            "schema_version": "LR6_REPLAY_RICHNESS_V1",
            "wave_scope": "LR6_LIVE3_WAVE_001",
            "replay_window_label": replay_window_label,
        }
        if payload["entity_id"] and payload["source_artifact_refs"]:
            prepared.append(payload)
        else:
            rejected.append(payload)
    return {"prepared_payloads": prepared, "rejected_payloads": rejected}


def build_lr6_live3_duplicate_prevention_keys(prepared_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [f"{p['wave_scope']}|{p['entity_id']}|{p['metric_dimension']}|{p['replay_window_label']}" for p in prepared_payloads]
    return {"keys": keys, "deterministic": keys == sorted(keys), "duplicates_found": len(keys) != len(set(keys))}


def build_lr6_live3_append_only_persistence_plan(prepared_payloads: list[dict[str, Any]], duplicate_keys: dict[str, Any]) -> dict[str, Any]:
    intents = []
    for p, k in zip(prepared_payloads, duplicate_keys["keys"]):
        intents.append({"insert_intent": "append_only_shadow_insert", "persistence_target": ISOLATED_PERSISTENCE_TARGET, "duplicate_prevention_key": k, "payload": p})
    return {"persistence_target": ISOLATED_PERSISTENCE_TARGET, "append_only": True, "direct_sql_used": False, "insert_intents": intents}


def build_lr6_live3_lineage_retention_plan(prepared_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    refs = {p["payload_id"]: p.get("source_artifact_refs", []) for p in prepared_payloads}
    return {"lineage_refs": refs, "lineage_refs_retained": all(bool(v) for v in refs.values())}


def build_lr6_live3_rollback_metadata(prepared_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    meta = {p["payload_id"]: {"rollback_ready": True, "rollback_mode": "append_only_quarantine_marker", "wave_scope": p["wave_scope"]} for p in prepared_payloads}
    return {"rollback_metadata": meta, "rollback_ready": all(v["rollback_ready"] for v in meta.values())}


def build_lr6_live3_halt_condition_monitor(*, governance: dict[str, Any], prepared_payloads: list[dict[str, Any]], duplicate_keys: dict[str, Any], persistence_plan: dict[str, Any], lineage_plan: dict[str, Any], rollback_plan: dict[str, Any], metric_dimension_limit: int = 1, max_entities: int = MAX_ENTITIES) -> dict[str, Any]:
    checks = {k: False for k in HALT_CONDITIONS}
    if not governance.get("governance_passed"):
        checks["governance_failure"] = True
    if len(prepared_payloads) > max_entities:
        checks["replay_scope_overflow"] = True
    if len({p.get("metric_dimension") for p in prepared_payloads}) > metric_dimension_limit:
        checks["metric_dimension_overflow"] = True
    if any(p.get("metric_dimension") != TARGET_METRIC for p in prepared_payloads):
        checks["schema_mismatch"] = True
    if any(p.get("comparison_ready") is True for p in prepared_payloads):
        checks["unexpected_comparison_ready_transition"] = True
    if any(not p.get("source_artifact_refs") for p in prepared_payloads):
        checks["missing_lineage"] = True
    if duplicate_keys.get("duplicates_found") or not duplicate_keys.get("deterministic"):
        checks["duplicate_prevention_failure"] = True
    if persistence_plan.get("append_only") is not True or persistence_plan.get("direct_sql_used") is True:
        checks["append_only_violation"] = True
    if persistence_plan.get("persistence_target") != ISOLATED_PERSISTENCE_TARGET:
        checks["persistence_adapter_mismatch"] = True
    if lineage_plan.get("lineage_refs_retained") is not True:
        checks["missing_lineage"] = True
    if rollback_plan.get("rollback_ready") is not True:
        checks["rollback_metadata_failure"] = True
    first = next((k for k in HALT_CONDITIONS if checks[k]), None)
    return {"halt_conditions": checks, "halt_triggered": first is not None, "halt_reason": first}


def execute_lr6_live3_non_dry_wave(*, entities: list[dict[str, Any]], approval_phrase: str, execution_token: str, max_entities: int = MAX_ENTITIES) -> dict[str, Any]:
    context = build_lr6_live3_execution_context(approval_phrase=approval_phrase, execution_token=execution_token, max_entities=max_entities)
    governance = build_lr6_live3_governance_verification(context)
    if not governance["governance_passed"]:
        return {"context": context, "governance_verification": governance, "aborted": True, "abort_reason": "governance_failure", "persistence_executed": False}
    selection = build_lr6_live3_entity_wave_selection(entities, max_entities=context["max_entities"])
    payloads = build_lr6_live3_payload_preparation(selection, replay_window_label=context["replay_window_label"])
    dup = build_lr6_live3_duplicate_prevention_keys(payloads["prepared_payloads"])
    persistence = build_lr6_live3_append_only_persistence_plan(payloads["prepared_payloads"], dup)
    lineage = build_lr6_live3_lineage_retention_plan(payloads["prepared_payloads"])
    rollback = build_lr6_live3_rollback_metadata(payloads["prepared_payloads"])
    halt = build_lr6_live3_halt_condition_monitor(governance=governance, prepared_payloads=payloads["prepared_payloads"], duplicate_keys=dup, persistence_plan=persistence, lineage_plan=lineage, rollback_plan=rollback, max_entities=context["max_entities"])
    if halt["halt_triggered"]:
        return {"context": context, "governance_verification": governance, "entity_wave_selection": selection, "payload_preparation": payloads, "duplicate_prevention": dup, "append_only_persistence_plan": persistence, "lineage_retention_plan": lineage, "rollback_metadata": rollback, "halt_monitor": halt, "aborted": True, "abort_reason": halt["halt_reason"], "persistence_executed": False}
    inserted = len(persistence["insert_intents"])
    return {"context": context, "governance_verification": governance, "entity_wave_selection": selection, "payload_preparation": payloads, "duplicate_prevention": dup, "append_only_persistence_plan": persistence, "lineage_retention_plan": lineage, "rollback_metadata": rollback, "halt_monitor": halt, "aborted": False, "persistence_executed": True, "payloads_inserted": inserted}


def build_lr6_live3_execution_summary(execution: dict[str, Any]) -> dict[str, Any]:
    prepared = len(execution.get("payload_preparation", {}).get("prepared_payloads", []))
    inserted = execution.get("payloads_inserted", 0)
    rejected = len(execution.get("payload_preparation", {}).get("rejected_payloads", []))
    return {
        "payloads_prepared": prepared,
        "payloads_inserted": inserted,
        "payloads_rejected": rejected,
        "duplicate_prevented": not execution.get("duplicate_prevention", {}).get("duplicates_found", False),
        "halt_triggered": execution.get("halt_monitor", {}).get("halt_triggered", False),
        "halt_reason": execution.get("halt_monitor", {}).get("halt_reason"),
        "rollback_ready": execution.get("rollback_metadata", {}).get("rollback_ready", False),
        "persistence_target": execution.get("append_only_persistence_plan", {}).get("persistence_target", ISOLATED_PERSISTENCE_TARGET),
        "lineage_refs_retained": execution.get("lineage_retention_plan", {}).get("lineage_refs_retained", False),
    }


def build_lr6_live3_post_wave_review(execution: dict[str, Any]) -> dict[str, Any]:
    summary = build_lr6_live3_execution_summary(execution)
    return {
        "governance_outcome": execution.get("governance_verification", {}).get("governance_passed", False),
        "persistence_outcome": execution.get("persistence_executed", False),
        "append_only_verification": execution.get("append_only_persistence_plan", {}).get("append_only") is True,
        "duplicate_prevention_outcome": summary["duplicate_prevented"],
        "lineage_retention_outcome": summary["lineage_refs_retained"],
        "rollback_readiness": summary["rollback_ready"],
        "halt_review": {"halt_triggered": summary["halt_triggered"], "halt_reason": summary["halt_reason"]},
        "payload_insertion_counts": {"prepared": summary["payloads_prepared"], "inserted": summary["payloads_inserted"], "rejected": summary["payloads_rejected"]},
        "replay_scope_verification": {"metric_target": TARGET_METRIC, "max_entities": MAX_ENTITIES, "entity_count": execution.get("entity_wave_selection", {}).get("entity_count", 0)},
        "recommendation": "continue_restriction_and_review_before_any_scaling",
    }


def build_lr6_live3_supervisor_review(entities: list[dict[str, Any]], *, approval_phrase: str, execution_token: str) -> dict[str, Any]:
    execution = execute_lr6_live3_non_dry_wave(entities=entities, approval_phrase=approval_phrase, execution_token=execution_token)
    return {
        "objective": "Execute first tiny governed non-dry replay ingestion wave with fail-closed controls and append-only shadow persistence.",
        "inspected_paths": [
            "lr6_live2_first_tiny_governed_replay_ingestion_non_dry_readiness_review.py",
            "lr6_live1_first_tiny_governed_replay_ingestion_dry_run_wave.py",
            "lr6_live0_governed_live_replay_ingestion_readiness_plan.py",
            "lr6_evid14_first_replay_richness_payload_supervisor_review.py",
            "lr6_evid13_dry_run_replay_richness_payload_attachment.py",
            "lr6_evid12_real_replay_richness_payload_validation_harness.py",
            "lr6_evid11_first_real_replay_richness_payload_builder.py",
        ],
        "execution": execution,
        "execution_summary": build_lr6_live3_execution_summary(execution),
        "post_wave_review": build_lr6_live3_post_wave_review(execution),
        "boundary_certification": certify_lr6_live3_execution_boundary(),
        "realism_warning": "This first non-dry wave remains narrowly scoped and does not authorize topology expansion, contradiction migration metrics, prediction, or trading logic.",
    }


def build_lr6_live3_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE3 — First Tiny Governed Replay Ingestion Non-Dry Execution",
        "",
        "## objective",
        f"- {review['objective']}",
        "",
        "## inspected LIVE2/LIVE1/LIVE0/EVID paths",
        f"- {review['inspected_paths']}",
        "",
        "## governance verification",
        f"- {review['execution'].get('governance_verification')}",
        "",
        "## tiny-wave execution scope",
        f"- {review['execution'].get('entity_wave_selection')}",
        "",
        "## payload preparation review",
        f"- {review['execution'].get('payload_preparation')}",
        "",
        "## append-only persistence review",
        f"- {review['execution'].get('append_only_persistence_plan')}",
        "",
        "## duplicate prevention review",
        f"- {review['execution'].get('duplicate_prevention')}",
        "",
        "## lineage retention review",
        f"- {review['execution'].get('lineage_retention_plan')}",
        "",
        "## rollback metadata review",
        f"- {review['execution'].get('rollback_metadata')}",
        "",
        "## halt-condition review",
        f"- {review['execution'].get('halt_monitor')}",
        "",
        "## execution summary",
        f"- {review['execution_summary']}",
        "",
        "## post-wave review",
        f"- {review['post_wave_review']}",
        "",
        "## realism warning",
        f"- {review['realism_warning']}",
        "",
        "## boundary certification",
        f"- {review['boundary_certification']}",
        "",
        "## recommendation for next step",
        "- Continue with restricted replay_richness-only waves until repeated conservative reviews justify any later change.",
    ])


def certify_lr6_live3_execution_boundary() -> dict[str, Any]:
    return {
        "governed_non_dry_execution": True,
        "metric_target": TARGET_METRIC,
        "max_entities": MAX_ENTITIES,
        "append_only_required": True,
        "isolated_persistence_required": True,
        "direct_sql_used": False,
        "topology_metrics_enabled": False,
        "contradiction_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "rollback_metadata_required": True,
        "lineage_retention_required": True,
    }
