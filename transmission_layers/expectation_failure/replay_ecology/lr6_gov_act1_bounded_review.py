from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DETERMINISTIC_VERSION = "LR6_GOV_ACT1_BOUNDED_REVIEW_V1"
DETERMINISTIC_SEED = "LR6_GOV_ACT1_BOUNDED_REVIEW_SEED_V1"


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


def load_lr6_gov_act1_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
    lr6_dry2_path: str = "configs/lr6_dry2_expanded_replay_ecology_diagnostic.yaml",
    lr6_dry3_path: str = "configs/lr6_dry3_full_universe_replay_ecology_certification.yaml",
    lr6_dry3r_path: str = "configs/lr6_dry3r_full_universe_refinement.yaml",
    lr6_dry4_path: str = "configs/lr6_dry4_full_universe_saturation_guardrails.yaml",
    lr6_prep_path: str = "configs/lr6_prep_governed_activation_proposal_package.yaml",
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
        },
    }


def build_lr6_gov_act1_activation_scope_review(inputs: dict[str, Any]) -> dict[str, Any]:
    scope = inputs["lr6_prep"]["bounded_first_activation_scope"]
    valid = scope["min_entities"] <= scope["proposed_entity_count"] <= scope["max_entities"]
    return {
        "reviewed_scope": scope,
        "scope_bounds_preserved": valid,
        "bounded_vs_full_universe": scope["proposed_entity_count"] < scope["full_universe_size"],
    }


def build_lr6_gov_act1_governance_gate_review(inputs: dict[str, Any]) -> dict[str, Any]:
    gates = inputs["lr6_prep"]["activation_gates"]
    return {
        "gates": gates,
        "non_operator_gates_cleared": all(v for k, v in gates.items() if k != "gate_operator_approvals_complete"),
        "operator_gate_pending": not bool(gates["gate_operator_approvals_complete"]),
    }


def build_lr6_gov_act1_operator_approval_review(inputs: dict[str, Any]) -> dict[str, Any]:
    approvals = inputs["lr6_prep"]["operator_approval_requirements"]
    return {
        "approval_requirements": approvals,
        "approval_roles_present": len(approvals["required_approver_roles"]) >= 2,
        "approval_phrase_defined": bool(approvals["required_approval_phrase"]),
        "approval_status": "pending",
    }


def build_lr6_gov_act1_saturation_guardrail_review(inputs: dict[str, Any]) -> dict[str, Any]:
    sat = inputs["lr6_prep"]["saturation_guardrails"]
    return {
        "saturation_guardrails": sat,
        "severe_breach_detected": sat["current_saturation_risk_score"] >= sat["severe_threshold"],
        "warning_band": sat["current_saturation_risk_score"] >= sat["warning_threshold"],
    }


def build_lr6_gov_act1_monoculture_guardrail_review(inputs: dict[str, Any]) -> dict[str, Any]:
    mono = inputs["lr6_prep"]["monoculture_guardrails"]
    return {
        "monoculture_guardrails": mono,
        "severe_breach_detected": mono["current_monoculture_risk_score"] >= mono["severe_threshold"],
        "dominance_watch_triggered": mono["current_monoculture_risk_score"] >= mono["dominance_watch_threshold"],
    }


def build_lr6_gov_act1_pause_rollback_review(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "pause_conditions": inputs["lr6_prep"]["pause_conditions"],
        "rollback_conditions": inputs["lr6_prep"]["rollback_conditions"],
        "pause_and_rollback_defined": True,
    }


def build_lr6_gov_act1_observability_review(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    required = [
        "post_activation_readiness_score_tracking",
        "saturation_monoculture_tracking",
        "approval_event_logging",
        "governance_boundary_violation_logging",
    ]
    return {"required_observability_controls": required, "observability_requirements_defined": True}


def build_lr6_gov_act1_reproducibility_review(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    checks = [
        "deterministic_version_seed_locked",
        "input_artifact_reference_lock",
        "repeatable_review_payload_construction",
    ]
    return {"required_reproducibility_checks": checks, "reproducibility_requirements_defined": True}


def build_lr6_gov_act1_activation_risk_review(inputs: dict[str, Any]) -> dict[str, Any]:
    sat = build_lr6_gov_act1_saturation_guardrail_review(inputs)
    mono = build_lr6_gov_act1_monoculture_guardrail_review(inputs)
    op = build_lr6_gov_act1_operator_approval_review(inputs)
    unresolved_activation_risks = []
    unresolved_governance_risks = []
    if op["approval_status"] != "complete":
        unresolved_governance_risks.append("operator_approvals_not_completed")
    if mono["dominance_watch_triggered"]:
        unresolved_activation_risks.append("monoculture_dominance_watch_active")
    return {
        "unresolved_activation_risks": unresolved_activation_risks,
        "unresolved_governance_risks": unresolved_governance_risks,
        "escalation_requirements": inputs["lr6_prep"]["escalation_requirements"],
    }


def certify_lr6_gov_act1_review(inputs: dict[str, Any]) -> dict[str, Any]:
    scope = build_lr6_gov_act1_activation_scope_review(inputs)
    gates = build_lr6_gov_act1_governance_gate_review(inputs)
    op = build_lr6_gov_act1_operator_approval_review(inputs)
    risks = build_lr6_gov_act1_activation_risk_review(inputs)
    eligible = scope["scope_bounds_preserved"] and gates["non_operator_gates_cleared"] and op["approval_phrase_defined"]
    additional = bool(risks["unresolved_governance_risks"])
    recommendation = "additional_review_required" if additional else "ready_for_future_governed_activation_request_preparation"
    return {
        "review_certified": eligible,
        "certification_outcome": recommendation,
        "may_prepare_future_governed_activation_request": recommendation == "ready_for_future_governed_activation_request_preparation",
        "lr6_production_replay_activated": False,
    }


def build_lr6_gov_act1_report_payload() -> dict[str, Any]:
    inputs = load_lr6_gov_act1_inputs()
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "Final bounded governed activation review before any future non-dry LR6 activation request preparation",
        "input_artifact_references": inputs["input_artifact_references"],
        "activation_scope_review": build_lr6_gov_act1_activation_scope_review(inputs),
        "governance_gate_review": build_lr6_gov_act1_governance_gate_review(inputs),
        "operator_approval_review": build_lr6_gov_act1_operator_approval_review(inputs),
        "saturation_guardrail_review": build_lr6_gov_act1_saturation_guardrail_review(inputs),
        "monoculture_guardrail_review": build_lr6_gov_act1_monoculture_guardrail_review(inputs),
        "pause_rollback_review": build_lr6_gov_act1_pause_rollback_review(inputs),
        "observability_review": build_lr6_gov_act1_observability_review(inputs),
        "reproducibility_review": build_lr6_gov_act1_reproducibility_review(inputs),
        "activation_risk_review": build_lr6_gov_act1_activation_risk_review(inputs),
        "certification_outcome": certify_lr6_gov_act1_review(inputs),
        "governance_certification_metadata": inputs["lr6_prep"]["governance_boundary_inventory"],
        "next_recommended_phase": "LR6-GOV-ACT-2 operator-complete governed activation request package preparation",
        "lr6_production_replay_activated": False,
    }
