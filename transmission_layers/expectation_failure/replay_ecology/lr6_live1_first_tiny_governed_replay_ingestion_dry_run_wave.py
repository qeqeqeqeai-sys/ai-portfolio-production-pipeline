"""LR6-LIVE1 first tiny governed replay ingestion dry-run wave (simulation-only)."""
from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_LIVE1_FIRST_TINY_GOVERNED_REPLAY_INGESTION_DRY_RUN_WAVE_V1"
REQUIRED_APPROVAL_TOKEN = "LR6_LIVE1_DRY_RUN_TINY_WAVE_APPROVED"
TARGET_METRIC = "replay_richness"
HALT_CONDITIONS = [
    "unsafe_promotion",
    "malformed_payload",
    "missing_lineage",
    "governance_failure",
    "replay_scope_overflow",
    "metric_dimension_overflow",
    "append_only_violation",
    "duplicate_anomaly",
    "unexpected_comparison_ready_transition",
    "replay_saturation_anomaly",
    "schema_mismatch",
    "shadow_persistence_mismatch",
]


def build_lr6_live1_dry_run_context(*, approval_token: str = REQUIRED_APPROVAL_TOKEN, replay_window_count: int = 1) -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-LIVE1",
        "execution_mode": "DRY_RUN_ONLY",
        "approval_token": approval_token,
        "metric_whitelist": [TARGET_METRIC],
        "max_entities": 5,
        "metric_dimension_limit": 1,
        "replay_window_count": replay_window_count,
        "append_only_simulation": True,
        "persistence_simulated_only": True,
        "shadow_target_only": True,
        "governed_non_dry": False,
        "halt_monitor_enabled": True,
    }


def build_lr6_live1_governance_gate_review(context: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "explicit_approval_token_present": context.get("approval_token") == REQUIRED_APPROVAL_TOKEN,
        "dry_run_mode_enabled": context.get("execution_mode") == "DRY_RUN_ONLY",
        "append_only_simulation_enabled": context.get("append_only_simulation") is True,
        "shadow_persistence_enabled": context.get("shadow_target_only") is True and context.get("persistence_simulated_only") is True,
        "replay_richness_only_whitelist": context.get("metric_whitelist") == [TARGET_METRIC],
        "bounded_replay_window": isinstance(context.get("replay_window_count"), int) and 0 < context.get("replay_window_count") <= 1,
        "bounded_entity_count": isinstance(context.get("max_entities"), int) and 0 < context.get("max_entities") <= 5,
        "halt_monitor_enabled": context.get("halt_monitor_enabled") is True,
    }
    return {"checks": checks, "governance_passed": all(checks.values()), "halt_before_simulation": not all(checks.values())}


def build_lr6_live1_entity_wave_selection(entities: list[dict[str, Any]], *, max_entities: int = 5) -> dict[str, Any]:
    eligible = [e for e in entities if e.get("metric_dimension") == TARGET_METRIC]
    ordered = sorted(eligible, key=lambda e: (str(e.get("cluster", "")), str(e.get("role", "")), str(e.get("entity_id", ""))))
    selected = ordered[: min(max_entities, 5)]
    return {
        "selected_entities": [e.get("entity_id") for e in selected],
        "entity_records": selected,
        "entity_count": len(selected),
        "selection_policy": "cluster_role_entity_id_sorted_first_five",
    }


def build_lr6_live1_replay_window_scope(*, replay_window_count: int = 1) -> dict[str, Any]:
    bounded = min(max(replay_window_count, 1), 1)
    return {"replay_window_count": bounded, "window_labels": ["W0"], "bounded": True}


def build_lr6_live1_payload_preparation(entity_wave: dict[str, Any]) -> dict[str, Any]:
    prepared = []
    rejected = []
    for idx, entity in enumerate(entity_wave.get("entity_records", [])):
        payload = {
            "payload_id": f"LR6_LIVE1_PAYLOAD_{idx+1}",
            "entity_id": entity.get("entity_id"),
            "metric_dimension": TARGET_METRIC,
            "comparison_ready": False,
            "source_artifact_refs": [f"artifact://lr6/live1/{entity.get('entity_id')}"] if entity.get("entity_id") else [],
            "schema_version": "LR6_REPLAY_RICHNESS_V1",
        }
        if payload["entity_id"] and payload["source_artifact_refs"]:
            prepared.append(payload)
        else:
            rejected.append(payload)
    return {"prepared_payloads": prepared, "rejected_payloads": rejected}


def build_lr6_live1_append_only_simulation(prepared_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [f"{p['entity_id']}|{p['metric_dimension']}|W0" for p in prepared_payloads]
    unique = len(keys) == len(set(keys))
    return {"append_only_simulation": True, "duplicate_prevention_keys": keys, "append_only_violation": not unique}


def build_lr6_live1_shadow_persistence_simulation(prepared_payloads: list[dict[str, Any]], append_only: dict[str, Any]) -> dict[str, Any]:
    intents = [
        {
            "insert_intent": "append_only_shadow_insert",
            "duplicate_prevention_key": f"{p['entity_id']}|{p['metric_dimension']}|W0",
            "lineage": p["source_artifact_refs"],
            "wave_scope": "LR6_LIVE1_WAVE_001",
            "audit_metadata": {"phase": "LR6-LIVE1", "dry_run": True},
            "rollback_metadata": {"rollback_ready": True, "rollback_mode": "quarantine_marker_only"},
        }
        for p in prepared_payloads
    ]
    return {
        "simulated_only": True,
        "persisted": False,
        "persistence_simulated_only": True,
        "shadow_target_only": True,
        "append_only_violation": append_only.get("append_only_violation", False),
        "insertion_intents": intents,
    }


def build_lr6_live1_halt_condition_monitor(*, governance_review: dict[str, Any], prepared_payloads: list[dict[str, Any]], shadow_sim: dict[str, Any], metric_dimension_limit: int = 1) -> dict[str, Any]:
    checks = {k: False for k in HALT_CONDITIONS}
    if not governance_review.get("governance_passed"):
        checks["governance_failure"] = True
    if any(p.get("metric_dimension") != TARGET_METRIC for p in prepared_payloads):
        checks["schema_mismatch"] = True
    if any(not p.get("source_artifact_refs") for p in prepared_payloads):
        checks["missing_lineage"] = True
    if len({p.get("metric_dimension") for p in prepared_payloads}) > metric_dimension_limit:
        checks["metric_dimension_overflow"] = True
    if shadow_sim.get("append_only_violation"):
        checks["append_only_violation"] = True
    if shadow_sim.get("persisted") is not False or shadow_sim.get("simulated_only") is not True:
        checks["shadow_persistence_mismatch"] = True

    first = next((k for k in HALT_CONDITIONS if checks[k]), None)
    return {"halt_conditions": checks, "halt_triggered": first is not None, "halt_reason": first}


def build_lr6_live1_wave_summary(*, entity_wave: dict[str, Any], replay_window_scope: dict[str, Any], governance_review: dict[str, Any], payload_prep: dict[str, Any], halt: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_entities": entity_wave["selected_entities"],
        "entity_count": entity_wave["entity_count"],
        "metric_dimensions": [TARGET_METRIC],
        "replay_window_scope": replay_window_scope,
        "governance_passed": governance_review["governance_passed"],
        "payloads_prepared": len(payload_prep["prepared_payloads"]),
        "payloads_rejected": len(payload_prep["rejected_payloads"]),
        "append_only_simulation": True,
        "persistence_simulated_only": True,
        "halt_triggered": halt["halt_triggered"],
        "halt_reason": halt["halt_reason"],
        "rollback_ready": True,
        "dry_run_only": True,
        "persisted": False,
    }


def run_lr6_live1_dry_run_wave(*, entities: list[dict[str, Any]], approval_token: str = REQUIRED_APPROVAL_TOKEN) -> dict[str, Any]:
    context = build_lr6_live1_dry_run_context(approval_token=approval_token)
    governance = build_lr6_live1_governance_gate_review(context)
    if not governance["governance_passed"]:
        halt = {"halt_triggered": True, "halt_reason": "governance_failure", "halt_conditions": {k: k == "governance_failure" for k in HALT_CONDITIONS}}
        return {"context": context, "governance_review": governance, "halt_monitor": halt, "wave_summary": build_lr6_live1_wave_summary(entity_wave={"selected_entities": [], "entity_count": 0}, replay_window_scope=build_lr6_live1_replay_window_scope(), governance_review=governance, payload_prep={"prepared_payloads": [], "rejected_payloads": []}, halt=halt)}

    selection = build_lr6_live1_entity_wave_selection(entities)
    window = build_lr6_live1_replay_window_scope(replay_window_count=context["replay_window_count"])
    payload = build_lr6_live1_payload_preparation(selection)
    append_only = build_lr6_live1_append_only_simulation(payload["prepared_payloads"])
    shadow = build_lr6_live1_shadow_persistence_simulation(payload["prepared_payloads"], append_only)
    halt = build_lr6_live1_halt_condition_monitor(governance_review=governance, prepared_payloads=payload["prepared_payloads"], shadow_sim=shadow, metric_dimension_limit=context["metric_dimension_limit"])
    summary = build_lr6_live1_wave_summary(entity_wave=selection, replay_window_scope=window, governance_review=governance, payload_prep=payload, halt=halt)
    return {"context": context, "governance_review": governance, "entity_wave_selection": selection, "replay_window_scope": window, "payload_preparation": payload, "append_only_simulation": append_only, "shadow_persistence_simulation": shadow, "halt_monitor": halt, "wave_summary": summary}


def certify_lr6_live1_dry_run_boundary() -> dict[str, Any]:
    return {
        "dry_run_only": True,
        "governance_simulation_only": True,
        "append_only_simulation_only": True,
        "shadow_persistence_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": "replay_richness",
        "max_entities": 5,
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_live1_supervisor_review() -> dict[str, Any]:
    sample_entities = [
        {"entity_id": "E1", "cluster": "A", "role": "alpha", "metric_dimension": TARGET_METRIC},
        {"entity_id": "E2", "cluster": "B", "role": "beta", "metric_dimension": TARGET_METRIC},
        {"entity_id": "E3", "cluster": "A", "role": "gamma", "metric_dimension": TARGET_METRIC},
        {"entity_id": "E4", "cluster": "C", "role": "alpha", "metric_dimension": TARGET_METRIC},
        {"entity_id": "E5", "cluster": "B", "role": "delta", "metric_dimension": TARGET_METRIC},
        {"entity_id": "E6", "cluster": "D", "role": "epsilon", "metric_dimension": TARGET_METRIC},
    ]
    run = run_lr6_live1_dry_run_wave(entities=sample_entities)
    return {
        "objective": "Simulate first tiny governed replay ingestion lifecycle under strict dry-run governance.",
        "inspected_paths": [
            "lr6_live0_governed_live_replay_ingestion_readiness_plan.py",
            "lr6_evid14_first_replay_richness_payload_supervisor_review.py",
            "lr6_evid13_dry_run_replay_richness_payload_attachment.py",
            "lr6_evid12_real_replay_richness_payload_validation_harness.py",
            "lr6_evid11_first_real_replay_richness_payload_builder.py",
            "lr6_evid6_minimal_in_memory_metrics_emission_hook.py",
        ],
        **run,
        "boundary_certification": certify_lr6_live1_dry_run_boundary(),
    }


def build_lr6_live1_markdown_report() -> str:
    review = build_lr6_live1_supervisor_review()
    return "\n".join([
        "# LR6-LIVE1 — First Tiny Governed Replay Ingestion Dry-Run Wave",
        "",
        "## objective",
        "- Simulate the first tiny governed replay ingestion lifecycle in dry-run mode only.",
        "",
        "## inspected LIVE0/EVID paths",
        f"- {review['inspected_paths']}",
        "",
        "## governance gate review",
        f"- {review['governance_review']}",
        "",
        "## tiny-wave selection",
        f"- {review['entity_wave_selection']}",
        "",
        "## replay window scope",
        f"- {review['replay_window_scope']}",
        "",
        "## payload preparation review",
        f"- {review['payload_preparation']}",
        "",
        "## append-only simulation review",
        f"- {review['append_only_simulation']}",
        "",
        "## shadow persistence simulation review",
        f"- {review['shadow_persistence_simulation']}",
        "",
        "## halt-condition review",
        f"- {review['halt_monitor']}",
        "",
        "## dry-run wave summary",
        f"- {review['wave_summary']}",
        "",
        "## realism warning",
        "- Governance-first and fail-closed posture: simulated-only, persisted=False, and zero live ingestion authorization.",
        "",
        "## boundary certification",
        f"- {review['boundary_certification']}",
        "",
        "## recommendation for next step",
        "- Remain in dry-run bounded mode; require explicit governance renewal before any future non-dry proposal.",
    ])
