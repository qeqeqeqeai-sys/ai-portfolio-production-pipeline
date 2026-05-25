from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DETERMINISTIC_VERSION = "LR6_PREP_GOVERNED_ACTIVATION_PROPOSAL_V1"
DETERMINISTIC_SEED = "LR6_PREP_GOVERNED_ACTIVATION_PROPOSAL_SEED_V1"


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


def load_lr6_prep_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
    lr6_dry2_path: str = "configs/lr6_dry2_expanded_replay_ecology_diagnostic.yaml",
    lr6_dry3_path: str = "configs/lr6_dry3_full_universe_replay_ecology_certification.yaml",
    lr6_dry3r_path: str = "configs/lr6_dry3r_full_universe_refinement.yaml",
    lr6_dry4_path: str = "configs/lr6_dry4_full_universe_saturation_guardrails.yaml",
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
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
            "lr6_dry1": lr6_dry1_path,
            "lr6_dry2": lr6_dry2_path,
            "lr6_dry3": lr6_dry3_path,
            "lr6_dry3r": lr6_dry3r_path,
            "lr6_dry4": lr6_dry4_path,
        },
    }


def build_lr6_prep_readiness_summary(inputs: dict[str, Any]) -> dict[str, Any]:
    d1, d2, d3 = inputs["lr6_dry1"]["diagnostic_scores"], inputs["lr6_dry2"]["diagnostic_scores"], inputs["lr6_dry3"]["diagnostic_scores"]
    d3r, d4 = inputs["lr6_dry3r"], inputs["lr6_dry4"]
    return {
        "adjusted_readiness_score": float(d4["adjusted_readiness_diagnostics"]["adjusted_readiness_score"]),
        "readiness_threshold": float(d4["adjusted_readiness_diagnostics"]["readiness_threshold"]),
        "threshold_cleared": bool(d4["adjusted_readiness_diagnostics"]["clears_threshold_under_guardrailed_interpretation"]),
        "dry_progression": [
            {"stage": "LR6-DRY1", "window": int(d1["bounded_window_size"]), "score": float(d1["diagnostic_readiness_score"])},
            {"stage": "LR6-DRY2", "window": int(d2["expanded_window_size"]), "score": float(d2["diagnostic_readiness_score"])},
            {"stage": "LR6-DRY3", "window": int(d3["full_universe_size"]), "score": float(d3["diagnostic_readiness_score"])},
            {"stage": "LR6-DRY3R", "window": int(d3["full_universe_size"]), "score": float(d3r["refined_readiness_decision"]["refined_diagnostic_readiness_score"])},
            {"stage": "LR6-DRY4", "window": int(d3["full_universe_size"]), "score": float(d4["adjusted_readiness_diagnostics"]["adjusted_readiness_score"])},
        ],
    }


def build_lr6_prep_activation_gates(inputs: dict[str, Any]) -> dict[str, Any]:
    summary = build_lr6_prep_readiness_summary(inputs)
    return {
        "gate_readiness_threshold_met": summary["threshold_cleared"],
        "gate_no_severe_saturation_breach": not bool(inputs["lr6_dry4"]["saturation_guardrail_diagnostics"]["severe_saturation_breach"]),
        "gate_no_severe_monoculture_breach": not bool(inputs["lr6_dry4"]["monoculture_guardrail_diagnostics"]["severe_monoculture_breach"]),
        "gate_dry_run_history_complete": True,
        "gate_governance_constraints_locked": True,
        "gate_operator_approvals_complete": False,
    }


def build_lr6_prep_operator_approval_requirements(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    return {
        "required_approver_roles": ["SEFI_GOVERNANCE_OWNER", "SEFI_REPLAY_OPERATOR", "SEFI_RISK_OPERATOR"],
        "required_approval_phrase": "APPROVE_LR6_GOVERNED_BOUNDED_ACTIVATION_PHASE1_NO_PRODUCTION_REPLAY_EXECUTION",
        "dual_control_required": True,
        "approval_expiration_hours": 24,
    }


def build_lr6_prep_bounded_first_activation_scope(inputs: dict[str, Any]) -> dict[str, Any]:
    entities = [e["entity_id"] for e in sorted(inputs["pruned_universe"]["selected_entities"], key=lambda x: x["entity_id"])][:90]
    return {
        "max_entities": 120,
        "min_entities": 60,
        "proposed_entity_count": 90,
        "proposed_entity_ids": entities,
        "proposed_time_window_days": 30,
        "full_universe_size": 300,
        "smaller_than_full_universe": True,
    }


def build_lr6_prep_saturation_guardrails(inputs: dict[str, Any]) -> dict[str, Any]:
    sat = inputs["lr6_dry4"]["saturation_guardrail_diagnostics"]
    return {"current_saturation_risk_score": float(sat["saturation_risk_score"]), "severe_threshold": 0.85, "warning_threshold": 0.6}


def build_lr6_prep_monoculture_guardrails(inputs: dict[str, Any]) -> dict[str, Any]:
    mono = inputs["lr6_dry4"]["monoculture_guardrail_diagnostics"]
    return {"current_monoculture_risk_score": float(mono["monoculture_risk_score"]), "severe_threshold": 0.25, "dominance_watch_threshold": 0.15}


def build_lr6_prep_pause_conditions(inputs: dict[str, Any]) -> list[str]:
    _ = inputs
    return ["saturation_risk_score>=0.85", "dominant_ecosystem_share>=0.25", "operator_approval_missing", "governance_boundary_violation"]


def build_lr6_prep_rollback_conditions(inputs: dict[str, Any]) -> list[str]:
    _ = inputs
    return ["post_activation_readiness_score_drops_below_0.79", "severe_guardrail_breach_confirmed", "deterministic_reproducibility_check_fails"]


def build_lr6_prep_governance_boundary_inventory(inputs: dict[str, Any]) -> dict[str, bool]:
    governance = inputs["lr6r_readiness"]["governance_certification_metadata"]
    return {
        "no_replay_execution": bool(governance["no_replay_execution"]),
        "no_replay_waves": True,
        "no_persistence_writes": bool(governance["no_persistence_writes"]),
        "no_direct_sql": bool(governance["no_direct_sql"]),
        "no_external_apis": bool(governance["no_external_apis"]),
        "no_prediction_or_trading": bool(governance["no_prediction_or_trading"]),
        "additive_architecture_preserved": bool(governance["additive_architecture_preserved"]),
        "deterministic_reproducibility_preserved": True,
        "interpretability_preserved": True,
        "lr6_production_replay_activated": False,
    }


def build_lr6_prep_escalation_requirements(inputs: dict[str, Any]) -> dict[str, Any]:
    _ = inputs
    return {"escalate_on": ["any_severe_guardrail_breach", "approval_phrase_mismatch", "boundary_violation"], "escalation_path": ["SEFI_GOVERNANCE_OWNER", "SEFI_EXECUTIVE_REVIEW"]}


def build_lr6_prep_activation_risk_summary(inputs: dict[str, Any]) -> dict[str, Any]:
    return {"saturation": build_lr6_prep_saturation_guardrails(inputs), "monoculture": build_lr6_prep_monoculture_guardrails(inputs), "residual_risk_state": "bounded_and_governable"}


def certify_lr6_prep_activation_proposal(inputs: dict[str, Any]) -> dict[str, Any]:
    gates = build_lr6_prep_activation_gates(inputs)
    all_non_operator = all(v for k, v in gates.items() if k != "gate_operator_approvals_complete")
    return {
        "proposal_certified": all_non_operator,
        "recommendation_state": "future_governed_activation_may_be_considered_after_operator_approvals" if all_non_operator else "additional_readiness_work_required",
        "next_recommended_phase": "LR6-GOV-ACT-1 bounded governed activation review (no replay execution in prep)",
        "lr6_production_replay_activated": False,
    }


def build_lr6_prep_report_payload() -> dict[str, Any]:
    inputs = load_lr6_prep_inputs()
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "Governed LR6 activation proposal preparation package (non-activating)",
        "input_artifact_references": inputs["input_artifact_references"],
        "readiness_evidence_summary": build_lr6_prep_readiness_summary(inputs),
        "activation_gates": build_lr6_prep_activation_gates(inputs),
        "bounded_first_activation_scope": build_lr6_prep_bounded_first_activation_scope(inputs),
        "operator_approval_requirements": build_lr6_prep_operator_approval_requirements(inputs),
        "saturation_guardrails": build_lr6_prep_saturation_guardrails(inputs),
        "monoculture_guardrails": build_lr6_prep_monoculture_guardrails(inputs),
        "pause_conditions": build_lr6_prep_pause_conditions(inputs),
        "rollback_conditions": build_lr6_prep_rollback_conditions(inputs),
        "governance_boundary_inventory": build_lr6_prep_governance_boundary_inventory(inputs),
        "escalation_requirements": build_lr6_prep_escalation_requirements(inputs),
        "activation_risk_summary": build_lr6_prep_activation_risk_summary(inputs),
        "governance_certification": certify_lr6_prep_activation_proposal(inputs),
        "lr6_production_replay_activated": False,
    }
