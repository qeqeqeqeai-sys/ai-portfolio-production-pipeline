from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DETERMINISTIC_VERSION = "LR6_GOV_DEC_OPERATOR_DECISION_RECORD_V1"
DETERMINISTIC_SEED = "LR6_GOV_DEC_OPERATOR_DECISION_RECORD_SEED_V1"



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


def load_lr6_gov_dec_inputs(
    lr6_gov_act2_config_path: str = "configs/lr6_gov_act2_operator_complete_activation_request_package.yaml",
    lr6_gov_act2_report_path: str = "reports/lr6_gov_act2_operator_complete_activation_request_package.md",
    lr6_gov_act1_path: str = "configs/lr6_gov_act1_bounded_activation_review.yaml",
    lr6_dry4_path: str = "configs/lr6_dry4_full_universe_saturation_guardrails.yaml",
) -> dict[str, Any]:
    return {
        "lr6_gov_act2_config": _load_yaml(lr6_gov_act2_config_path),
        "lr6_gov_act2_report_text": Path(lr6_gov_act2_report_path).read_text(encoding="utf-8"),
        "lr6_gov_act1": _load_yaml(lr6_gov_act1_path),
        "lr6_dry4": _load_yaml(lr6_dry4_path),
        "input_artifact_references": {
            "lr6_gov_act2_config": lr6_gov_act2_config_path,
            "lr6_gov_act2_report": lr6_gov_act2_report_path,
            "lr6_gov_act1": lr6_gov_act1_path,
            "lr6_dry4": lr6_dry4_path,
        },
    }


def build_lr6_gov_dec_request_summary(inputs: dict[str, Any]) -> dict[str, Any]:
    act2 = inputs["lr6_gov_act2_config"]
    scope = act2["activation_request_scope"]
    return {
        "source_certification_outcome": act2["certification_outcome"]["certification_outcome"],
        "proposed_bounded_scope": {
            "entity_count": scope["first_activation_entity_count"],
            "window_days": scope["first_activation_window_days"],
        },
        "request_ready_for_operator_decision": act2["certification_outcome"]["ready_for_operator_decision"],
    }


def build_lr6_gov_dec_required_approval_phrases(inputs: dict[str, Any]) -> dict[str, Any]:
    phrases = inputs["lr6_gov_act2_config"]["approval_phrase_inventory"]
    all_required = [phrases["required_primary_phrase"], *phrases["required_secondary_phrases"]]
    return {
        "required_primary_phrase": phrases["required_primary_phrase"],
        "required_secondary_phrases": phrases["required_secondary_phrases"],
        "required_phrase_inventory": all_required,
        "provided_approval_phrase_placeholders": {
            phrase: None for phrase in all_required
        },
    }


def build_lr6_gov_dec_approval_validation(inputs: dict[str, Any]) -> dict[str, Any]:
    phrases = build_lr6_gov_dec_required_approval_phrases(inputs)
    provided = phrases["provided_approval_phrase_placeholders"]
    missing = [k for k, v in provided.items() if v is not True]
    complete = len(missing) == 0
    return {
        "all_required_phrases_explicitly_supplied": complete,
        "missing_required_phrases": missing,
        "approval_inferred_from_artifacts": False,
        "approval_validation_status": "complete" if complete else "incomplete",
    }


def build_lr6_gov_dec_operator_decision_state(inputs: dict[str, Any]) -> dict[str, Any]:
    validation = build_lr6_gov_dec_approval_validation(inputs)
    if validation["all_required_phrases_explicitly_supplied"]:
        state = "operator_approval_recorded"
    elif validation["missing_required_phrases"]:
        state = "pending_operator_decision"
    else:
        state = "approval_incomplete"
    return {
        "decision_state": state,
        "approval_recorded": state == "operator_approval_recorded",
        "default_decision_state": "pending_operator_decision",
        "lr6_production_replay_activated": False,
    }


def build_lr6_gov_dec_rejection_or_deferral_paths(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    return {
        "paths": [
            "defer_for_missing_approval_phrases",
            "reject_due_to_unacknowledged_residual_risk",
            "defer_for_governance_boundary_revalidation",
            "reject_due_to_scope_or_window_mismatch",
        ]
    }


def build_lr6_gov_dec_residual_risk_acknowledgement(inputs: dict[str, Any]) -> dict[str, Any]:
    risks = inputs["lr6_gov_act2_config"]["residual_risk_register"]["residual_risks"]
    return {
        "residual_risk_acknowledgement_required": True,
        "residual_risk_checklist": {risk: False for risk in risks},
    }


def build_lr6_gov_dec_governance_boundary_inventory(inputs: dict[str, Any]) -> dict[str, Any]:
    return dict(inputs["lr6_gov_act2_config"]["governance_certification_metadata"])


def certify_lr6_gov_dec_operator_decision_record(inputs: dict[str, Any]) -> dict[str, Any]:
    validation = build_lr6_gov_dec_approval_validation(inputs)
    decision = build_lr6_gov_dec_operator_decision_state(inputs)
    return {
        "decision_record_certified": True,
        "certification_outcome": "ready_for_operator_decision_recording",
        "operator_decision_state": decision["decision_state"],
        "approval_validation_status": validation["approval_validation_status"],
        "lr6_production_replay_activated": False,
        "no_execution_performed": True,
    }


def build_lr6_gov_dec_report_payload() -> dict[str, Any]:
    inputs = load_lr6_gov_dec_inputs()
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "Deterministic operator decision-record layer for LR6 governed activation request without execution",
        "input_artifact_references": inputs["input_artifact_references"],
        "request_summary": build_lr6_gov_dec_request_summary(inputs),
        "required_approval_phrases": build_lr6_gov_dec_required_approval_phrases(inputs),
        "approval_validation": build_lr6_gov_dec_approval_validation(inputs),
        "decision_state": build_lr6_gov_dec_operator_decision_state(inputs),
        "residual_risk_acknowledgement": build_lr6_gov_dec_residual_risk_acknowledgement(inputs),
        "deferral_rejection_paths": build_lr6_gov_dec_rejection_or_deferral_paths(inputs),
        "governance_boundary_review": build_lr6_gov_dec_governance_boundary_inventory(inputs),
        "certification_outcome": certify_lr6_gov_dec_operator_decision_record(inputs),
        "next_recommended_phase": "LR6-GOV-EXEC-PREP — Governed Execution Preparation",
        "lr6_production_replay_activated": False,
    }
