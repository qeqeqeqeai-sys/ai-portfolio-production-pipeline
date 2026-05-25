from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DETERMINISTIC_VERSION = "LR6_GOV_ACT2_OPERATOR_COMPLETE_REQUEST_V1"
DETERMINISTIC_SEED = "LR6_GOV_ACT2_OPERATOR_COMPLETE_REQUEST_SEED_V1"


def _load_yaml(path: str) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text)
    parsed: dict[str, Any] = {}
    section: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.endswith(":") and indent == 0:
            section = line[:-1]
            parsed[section] = {}
            continue
        key, value = [x.strip() for x in line.split(":", 1)]
        if value.lower() in {"true", "false"}:
            value_obj: Any = value.lower() == "true"
        else:
            try:
                value_obj = float(value) if "." in value else int(value)
            except ValueError:
                value_obj = value
        if section and indent > 0:
            parsed[section][key] = value_obj
        else:
            parsed[key] = value_obj
    return parsed


def load_lr6_gov_act2_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
    lr6_dry2_path: str = "configs/lr6_dry2_expanded_replay_ecology_diagnostic.yaml",
    lr6_dry3_path: str = "configs/lr6_dry3_full_universe_replay_ecology_certification.yaml",
    lr6_dry3r_path: str = "configs/lr6_dry3r_full_universe_refinement.yaml",
    lr6_dry4_path: str = "configs/lr6_dry4_full_universe_saturation_guardrails.yaml",
    lr6_prep_path: str = "configs/lr6_prep_governed_activation_proposal_package.yaml",
    lr6_gov_act1_path: str = "configs/lr6_gov_act1_bounded_activation_review.yaml",
) -> dict[str, Any]:
    return {
        "pruned_universe": _load_yaml(pruned_universe_path),
        "sde1d_readiness": _load_yaml(sde1d_readiness_path),
        "lr6r_readiness": _load_yaml(lr6r_readiness_path),
        "lr6_dry1": _load_yaml(lr6_dry1_path),
        "lr6_dry2": _load_yaml(lr6_dry2_path),
        "lr6_dry3": _load_yaml(lr6_dry3_path),
        "lr6_dry3r": _load_yaml(lr6_dry3r_path),
        "lr6_dry4": _load_yaml(lr6_dry4_path),
        "lr6_prep": _load_yaml(lr6_prep_path),
        "lr6_gov_act1": _load_yaml(lr6_gov_act1_path),
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
            "lr6_dry1": lr6_dry1_path,
            "lr6_dry2": lr6_dry2_path,
            "lr6_dry3": lr6_dry3_path,
            "lr6_dry3r": lr6_dry3r_path,
            "lr6_dry4": lr6_dry4_path,
            "lr6_prep": lr6_prep_path,
            "lr6_gov_act1": lr6_gov_act1_path,
        },
    }


def build_lr6_gov_act2_operator_completion_requirements(inputs: dict[str, Any]) -> dict[str, Any]:
    roles = inputs["lr6_prep"]["operator_approval_requirements"]["required_approver_roles"]
    checklist = [
        "all_required_approvers_confirmed",
        "all_required_approval_phrases_recorded",
        "governance_lock_confirmed",
        "pause_rollback_authority_confirmed",
        "observability_controls_enabled_for_activation_window",
    ]
    return {"required_approver_roles": roles, "activation_request_checklist": checklist}


def build_lr6_gov_act2_approval_phrase_inventory(inputs: dict[str, Any]) -> dict[str, Any]:
    base_phrase = inputs["lr6_prep"]["operator_approval_requirements"]["required_approval_phrase"]
    return {
        "required_primary_phrase": base_phrase,
        "required_secondary_phrases": [
            "APPROVED_LR6_GOV_ACT2_SCOPE_90_ENTITY_30_DAY",
            "CONFIRMED_LR6_GOV_ACT2_MONOCULTURE_WATCH_ACTIVE",
            "CONFIRMED_LR6_GOV_ACT2_SATURATION_WATCH_ACTIVE",
            "CONFIRMED_LR6_GOV_ACT2_PAUSE_AND_ROLLBACK_AUTHORITY_READY",
        ],
    }


def build_lr6_gov_act2_activation_request_scope(inputs: dict[str, Any]) -> dict[str, Any]:
    scope = inputs["lr6_prep"]["bounded_first_activation_scope"]
    return {
        "first_activation_entity_count": scope["proposed_entity_count"],
        "first_activation_window_days": scope["proposed_time_window_days"],
        "min_entities": scope["min_entities"],
        "max_entities": scope["max_entities"],
        "full_universe_size": scope["full_universe_size"],
        "scope_preserved": scope["proposed_entity_count"] == 90 and scope["proposed_time_window_days"] == 30,
        "diagnostic_override_justified": False,
    }


def build_lr6_gov_act2_monoculture_watch_conditions(inputs: dict[str, Any]) -> dict[str, Any]:
    mono = inputs["lr6_prep"]["monoculture_guardrails"]
    return {"watch_status": "active", "conditions": mono}


def build_lr6_gov_act2_saturation_watch_conditions(inputs: dict[str, Any]) -> dict[str, Any]:
    sat = inputs["lr6_prep"]["saturation_guardrails"]
    return {"watch_status": "active", "conditions": sat}


def build_lr6_gov_act2_governance_lock_review(inputs: dict[str, Any]) -> dict[str, Any]:
    prior = inputs["lr6_gov_act1"]
    return {
        "prior_certification_outcome": prior["certification_outcome"],
        "unresolved_governance_risk": "operator_approvals_not_completed",
        "governance_lock_active": True,
        "lock_release_requires_operator_completion": True,
    }


def build_lr6_gov_act2_execution_preconditions(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    return {
        "required_preconditions": [
            "operator_approvals_completed",
            "approval_phrases_recorded",
            "bounded_scope_confirmed",
            "monoculture_watch_active",
            "saturation_watch_active",
            "pause_rollback_controls_armed",
        ]
    }


def build_lr6_gov_act2_pause_rollback_controls(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "pause_conditions": inputs["lr6_prep"]["pause_conditions"],
        "rollback_conditions": inputs["lr6_prep"]["rollback_conditions"],
        "strict_pause_conditions_required": True,
        "strict_rollback_conditions_required": True,
    }


def build_lr6_gov_act2_observability_requirements(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    return {
        "requirements": [
            "activation_scope_boundary_telemetry",
            "monoculture_dominance_watch_telemetry",
            "saturation_watch_telemetry",
            "operator_approval_event_log",
            "pause_and_rollback_event_log",
            "deterministic_reproducibility_payload_hash",
        ]
    }


def build_lr6_gov_act2_residual_risk_register(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    return {
        "residual_risks": [
            "monoculture_dominance_watch_active",
            "operator_approvals_not_completed",
            "bounded_activation_operational_variance",
        ]
    }


def certify_lr6_gov_act2_activation_request_package(inputs: dict[str, Any]) -> dict[str, Any]:
    scope = build_lr6_gov_act2_activation_request_scope(inputs)
    lock = build_lr6_gov_act2_governance_lock_review(inputs)
    return {
        "request_package_certified": True,
        "certification_outcome": "ready_for_operator_decision",
        "ready_for_operator_decision": True,
        "lr6_production_replay_activated": False,
        "package_not_activation": True,
        "bounded_scope_valid": scope["scope_preserved"],
        "governance_lock_active": lock["governance_lock_active"],
    }


def build_lr6_gov_act2_report_payload() -> dict[str, Any]:
    inputs = load_lr6_gov_act2_inputs()
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "Operator-complete governed activation request package preparation without LR6 activation",
        "input_artifact_references": inputs["input_artifact_references"],
        "operator_completion_requirements": build_lr6_gov_act2_operator_completion_requirements(inputs),
        "approval_phrase_inventory": build_lr6_gov_act2_approval_phrase_inventory(inputs),
        "activation_request_scope": build_lr6_gov_act2_activation_request_scope(inputs),
        "monoculture_watch_conditions": build_lr6_gov_act2_monoculture_watch_conditions(inputs),
        "saturation_watch_conditions": build_lr6_gov_act2_saturation_watch_conditions(inputs),
        "governance_lock_review": build_lr6_gov_act2_governance_lock_review(inputs),
        "execution_preconditions": build_lr6_gov_act2_execution_preconditions(inputs),
        "pause_rollback_controls": build_lr6_gov_act2_pause_rollback_controls(inputs),
        "observability_requirements": build_lr6_gov_act2_observability_requirements(inputs),
        "reproducibility_requirements": [
            "deterministic_version_seed_locked",
            "input_artifact_reference_lock",
            "repeatable_operator_request_payload_construction",
        ],
        "residual_risk_register": build_lr6_gov_act2_residual_risk_register(inputs),
        "certification_outcome": certify_lr6_gov_act2_activation_request_package(inputs),
        "governance_certification_metadata": inputs["lr6_prep"]["governance_boundary_inventory"],
        "next_recommended_phase": "LR6-GOV-DEC operator decision on governed activation request package",
        "lr6_production_replay_activated": False,
    }
