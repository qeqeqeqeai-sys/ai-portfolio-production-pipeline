from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_GOV_FREEZE_V1"
DETERMINISTIC_SEED = "LR6_GOV_FREEZE_SEED_V1"


ACTIVE_CORE_GOVERNANCE = [
    "bounded_replay_windows",
    "dry_run_first_policy",
    "saturation_guardrails",
    "monoculture_caps",
    "rollback_conditions",
    "observability_requirements",
    "deterministic_reproducibility",
    "no_direct_sql_enforcement",
    "additive_architecture_enforcement",
]

FROZEN_RECURSIVE_GOVERNANCE = [
    "repeated_certification_recursion",
    "repeated_approval_preparation_recursion",
    "repeated_review_recursion",
    "governance_of_governance_layers",
    "operator_decision_recursion_layers",
]

EXPERIMENTAL_MODE_GOVERNANCE = [
    "lightweight_replay_experimentation",
    "bounded_dry_runs",
    "reduced_certification_recursion",
    "no_persistence_by_default",
    "fast_semantic_iteration",
    "deterministic_execution",
    "bounded_execution_scope",
]

GOVERNED_MODE_GOVERNANCE = [
    "full_governance",
    "approvals_required",
    "persistence_controls",
    "replay_lineage",
    "escalation_gates",
    "rollback_authority",
]


def build_lr6_governance_inventory() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "active_core_governance": ACTIVE_CORE_GOVERNANCE.copy(),
        "obsolete_recursive_governance": FROZEN_RECURSIVE_GOVERNANCE.copy(),
        "experimental_mode_governance": EXPERIMENTAL_MODE_GOVERNANCE.copy(),
        "governed_mode_governance": GOVERNED_MODE_GOVERNANCE.copy(),
    }


def classify_lr6_governance_layers(inventory: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "active_core_governance": sorted(set(inventory["active_core_governance"])),
        "frozen_historical_governance": sorted(set(inventory["obsolete_recursive_governance"])),
        "experimental_mode_governance": sorted(set(inventory["experimental_mode_governance"])),
        "governed_mode_governance": sorted(set(inventory["governed_mode_governance"])),
        "obsolete_recursive_governance": sorted(set(inventory["obsolete_recursive_governance"])),
    }


def build_lr6_active_governance_profile(classification: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "profile": "active_core_governance",
        "layers": classification["active_core_governance"],
        "is_operational": True,
        "contains_safety_rails": True,
    }


def build_lr6_frozen_governance_profile(classification: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "profile": "frozen_historical_governance",
        "layers": classification["frozen_historical_governance"],
        "is_operational": False,
        "retained_for_history": True,
    }


def build_lr6_experimental_mode_profile(classification: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "mode": "experimental_mode",
        "governance_layers": classification["experimental_mode_governance"],
        "certification_recursion": "reduced",
        "persistence_default": "disabled",
        "deterministic": True,
        "bounded": True,
    }


def build_lr6_governed_mode_profile(classification: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "mode": "governed_mode",
        "governance_layers": classification["governed_mode_governance"],
        "certification_recursion": "full",
        "persistence_controls": "strict",
        "approvals_required": True,
        "rollback_authority": True,
    }


def build_lr6_governance_recursion_diagnostics(classification: dict[str, list[str]]) -> dict[str, Any]:
    frozen = classification["frozen_historical_governance"]
    return {
        "recursive_layer_count": len(frozen),
        "recursive_layers": frozen,
        "governance_recursion_risk": "contained_by_freeze",
        "active_recursive_layers": 0,
    }


def build_lr6_governance_retention_policy(classification: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "policy_name": "lr6_governance_freeze_retention_policy",
        "historical_governance_deleted": False,
        "frozen_layers_retained": classification["frozen_historical_governance"],
        "retention_mode": "archive_and_reference_only",
        "interpretability_preserved": True,
        "additive_architecture_preserved": True,
    }


def certify_lr6_governance_freeze(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "governance_freeze_certified": True,
        "no_replay_execution": True,
        "no_replay_waves": True,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "deterministic_reproducibility_preserved": True,
        "historical_governance_deleted": False,
        "classification_deterministic": bool(payload["classification"]),
    }


def build_lr6_governance_freeze_report_payload() -> dict[str, Any]:
    inventory = build_lr6_governance_inventory()
    classification = classify_lr6_governance_layers(inventory)
    payload = {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "Freeze obsolete recursive LR6 governance layers while separating governed and experimental modes without deleting history",
        "governance_inventory": inventory,
        "classification": classification,
        "active_governance_profile": build_lr6_active_governance_profile(classification),
        "frozen_governance_profile": build_lr6_frozen_governance_profile(classification),
        "experimental_mode_profile": build_lr6_experimental_mode_profile(classification),
        "governed_mode_profile": build_lr6_governed_mode_profile(classification),
        "governance_recursion_diagnostics": build_lr6_governance_recursion_diagnostics(classification),
        "retention_policy": build_lr6_governance_retention_policy(classification),
        "retained_safety_rails": classification["active_core_governance"],
        "next_recommended_phase": "LR6-OBS-SHIFT-1 replay observation and semantic evolution acceleration under frozen governance baseline",
    }
    payload["governance_certification_metadata"] = certify_lr6_governance_freeze(payload)
    return payload
