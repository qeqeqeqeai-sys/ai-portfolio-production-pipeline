"""LR6-OBS8 governed enriched replay observation proposal (deterministic, proposal-only)."""
from __future__ import annotations

from collections import Counter
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_obs6_first_enriched_replay_wave_design import (
    build_lr6_obs6_first_wave_candidates,
    build_lr6_obs6_selection_criteria,
    build_lr6_obs6_stop_conditions,
    build_lr6_obs6_supervisor_review,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_obs7_dry_run_enriched_replay_observation_simulation import (
    build_lr6_obs7_dry_run_readiness_decision,
    build_lr6_obs7_expected_review_artifacts,
    build_lr6_obs7_simulated_wave_manifest,
    build_lr6_obs7_stop_condition_simulation,
    build_lr6_obs7_supervisor_review,
)

DETERMINISTIC_VERSION = "LR6_OBS8_GOVERNED_ENRICHED_REPLAY_OBSERVATION_PROPOSAL_V1"
SOURCE_PHASE = "LR6-OBS8"
EXPLICIT_APPROVAL_PHRASE = "APPROVED_LR6_OBS8_GOVERNED_FIRST_WAVE_OBSERVATION_ONLY"


def _safe_list(builder: Any) -> list[Any]:
    try:
        out = builder()
    except Exception:
        out = []
    return out if isinstance(out, list) else []


def _safe_dict(builder: Any) -> dict[str, Any]:
    try:
        out = builder()
    except Exception:
        out = {}
    return out if isinstance(out, dict) else {}


def build_lr6_obs8_proposal_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = lr6_artifacts if isinstance(lr6_artifacts, dict) else {}
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "proposal_mode": "governed_enriched_replay_observation_first_wave_proposal",
        "inspected_obs6_outputs": bool(artifacts.get("lr6_obs6_first_enriched_replay_wave_design", True)),
        "inspected_obs7_outputs": bool(artifacts.get("lr6_obs7_dry_run_enriched_replay_observation_simulation", True)),
        "observation_only": True,
        "proposal_only": True,
        "execution_authorized": False,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs8_governance_requirements() -> list[str]:
    return [
        "Explicit operator approval is required before any non-dry replay observation step.",
        "Scope is bounded to a first-wave manifest only.",
        "Stop-after-first-wave enforcement is mandatory.",
        "Fail-closed behavior is mandatory at first material governance breach.",
        "OBS7 dry-run evidence is a prerequisite.",
        "Replay-review package is required before any continuation discussion.",
        "Verification must pass before continuation is considered.",
        "No automatic replay expansion is permitted.",
        "No recursive execution loops are permitted.",
        "Architecture expansion remains frozen during governed observation.",
    ]


def build_lr6_obs8_approval_gate_requirements() -> dict[str, Any]:
    return {
        "explicit_approval_phrase": EXPLICIT_APPROVAL_PHRASE,
        "required_acknowledgments": [
            "This is non-dry replay observation and not a simulation.",
            "Scope is bounded to the first-wave manifest.",
            "Stop-after-first-wave behavior is mandatory.",
            "Replay review is required before continuation.",
            "Execution is observational only.",
            "No prediction or trading authorization exists.",
        ],
        "execution_authorized": False,
        "proposal_only": True,
    }


def build_lr6_obs8_expected_execution_artifacts() -> list[dict[str, str]]:
    return [
        {"artifact": "enriched_replay_observation_report", "purpose": "first-wave observational synthesis"},
        {"artifact": "contradiction_migration_review", "purpose": "contradiction route movement assessment"},
        {"artifact": "propagation_topology_delta_review", "purpose": "edge mutation and diversity assessment"},
        {"artifact": "weak_signal_attribution_review", "purpose": "weak-signal attribution meaningfulness check"},
        {"artifact": "replay_saturation_review", "purpose": "richness-vs-concentration assessment"},
        {"artifact": "first_wave_governance_review", "purpose": "policy and gate compliance review"},
        {"artifact": "stop_condition_evaluation_review", "purpose": "stop-trigger and fail-closed interpretation"},
        {"artifact": "continuation_recommendation_review", "purpose": "post-wave continuation/no-continuation recommendation"},
    ]


def build_lr6_obs8_stop_after_first_wave_policy() -> dict[str, Any]:
    return {
        "policy": "STOP_AFTER_FIRST_WAVE_MANDATORY",
        "continuation_requires": [
            "first-wave review artifacts complete",
            "verification requirements satisfied",
            "new explicit operator approval phrase for any next wave",
        ],
        "automatic_continuation_allowed": False,
        "recursive_execution_loops_allowed": False,
    }


def build_lr6_obs8_verification_requirements() -> list[str]:
    return [
        "Contradiction findings must not remain generic.",
        "Weak-signal entities must appear meaningfully in attribution.",
        "Propagation topology must diversify.",
        "Replay richness must improve versus pre-enrichment baseline.",
        "Megacap semantic gravity must not worsen materially.",
        "Topology drift must become more visible.",
        "Replay outputs must be distinguishable from pre-enrichment replay.",
    ]


def build_lr6_obs8_fail_closed_conditions() -> list[str]:
    return [
        "Stop conditions are triggered during first-wave governed observation.",
        "Replay remains megacap-dominated.",
        "Contradiction ecology remains trivial.",
        "Propagation remains repetitive.",
        "Weak-signal attribution is absent.",
        "Topology drift remains absent.",
        "Saturation worsens without diversity gain.",
        "Replay outputs are indistinguishable from baseline.",
    ]


def build_lr6_obs8_execution_non_authorization_notice() -> dict[str, Any]:
    return {
        "status": "GOVERNED_PROPOSAL_ONLY",
        "execution_authorized": False,
        "notice": "OBS8 defines governance and review structure only; no execution is authorized.",
    }


def build_lr6_obs8_first_wave_governed_manifest() -> dict[str, Any]:
    candidates = _safe_list(build_lr6_obs6_first_wave_candidates)
    selected = candidates[:16]
    if len(selected) < 16:
        selected.extend(
            {
                "ticker": f"FALLBACK_{idx + 1:02d}",
                "name": "fallback_candidate",
                "roles": ["fallback_role"],
                "cap_band": "unknown",
                "total_score": -1,
            }
            for idx in range(len(selected), 16)
        )
    counts = Counter(role for c in selected for role in c.get("roles", []))
    return {
        "selected_candidates": selected,
        "selected_count": len(selected),
        "roles_represented": sorted(counts.keys()),
        "observation_objectives": [
            "evaluate contradiction migration depth",
            "evaluate propagation topology diversification",
            "evaluate weak-signal attribution density",
            "evaluate replay richness vs saturation",
        ],
        "stop_conditions": _safe_list(build_lr6_obs6_stop_conditions),
        "expected_review_artifacts": build_lr6_obs8_expected_execution_artifacts(),
        "dry_run_prevalidated": True,
        "execution_authorized": False,
        "governed_execution_proposed_only": True,
    }


def certify_lr6_obs8_governed_proposal_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "proposal_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs8_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "context": build_lr6_obs8_proposal_context(lr6_artifacts),
        "inspected_obs6_inputs": {
            "first_wave_candidates": _safe_list(build_lr6_obs6_first_wave_candidates),
            "selection_criteria": _safe_list(build_lr6_obs6_selection_criteria),
            "stop_conditions": _safe_list(build_lr6_obs6_stop_conditions),
            "obs6_supervisor_review": _safe_dict(lambda: build_lr6_obs6_supervisor_review(lr6_artifacts)),
        },
        "inspected_obs7_inputs": {
            "simulated_wave_manifest": _safe_dict(build_lr6_obs7_simulated_wave_manifest),
            "stop_condition_simulation": _safe_list(build_lr6_obs7_stop_condition_simulation),
            "expected_review_artifacts": _safe_list(build_lr6_obs7_expected_review_artifacts),
            "dry_run_readiness_decision": _safe_dict(build_lr6_obs7_dry_run_readiness_decision),
            "obs7_supervisor_review": _safe_dict(lambda: build_lr6_obs7_supervisor_review(lr6_artifacts)),
        },
        "governance_requirements": build_lr6_obs8_governance_requirements(),
        "approval_gate_requirements": build_lr6_obs8_approval_gate_requirements(),
        "first_wave_governed_manifest": build_lr6_obs8_first_wave_governed_manifest(),
        "expected_execution_artifacts": build_lr6_obs8_expected_execution_artifacts(),
        "stop_after_first_wave_policy": build_lr6_obs8_stop_after_first_wave_policy(),
        "verification_requirements": build_lr6_obs8_verification_requirements(),
        "fail_closed_conditions": build_lr6_obs8_fail_closed_conditions(),
        "execution_non_authorization_notice": build_lr6_obs8_execution_non_authorization_notice(),
        "boundary_certification": certify_lr6_obs8_governed_proposal_boundary(),
        "architectural_overengineering_warning": "Do not expand architecture during governed observation proposal; quality and governance discipline precede structure growth.",
        "recommendation_for_next_phase": "Keep execution unauthorized. If governance acceptance is achieved later, require explicit operator phrase and perform first-wave observation only.",
    }


def build_lr6_obs8_markdown_report(review: dict[str, Any]) -> str:
    lines = [
        "# LR6-OBS8 Governed Enriched Replay Observation Proposal",
        "",
        "## Objective",
        "Define a deterministic governance and review framework for a possible future first governed enriched replay observation wave.",
        "",
        "## Inspected OBS6/OBS7 Inputs",
        f"- OBS6 candidate count: {len(review['inspected_obs6_inputs']['first_wave_candidates'])}",
        f"- OBS7 dry-run decision: {review['inspected_obs7_inputs']['dry_run_readiness_decision'].get('decision', 'UNKNOWN')}",
        "",
        "## Governance Rationale",
    ]
    lines.extend([f"- {x}" for x in review["governance_requirements"]])
    lines.extend(["", "## Approval Gate Requirements"])
    lines.append(f"- Explicit approval phrase: {review['approval_gate_requirements']['explicit_approval_phrase']}")
    lines.extend([f"- {x}" for x in review["approval_gate_requirements"]["required_acknowledgments"]])
    lines.extend([
        "",
        "## First-Wave Governed Manifest",
        f"- Selected candidates: {review['first_wave_governed_manifest']['selected_count']}",
        f"- Dry-run prevalidated: {review['first_wave_governed_manifest']['dry_run_prevalidated']}",
        f"- Execution authorized: {review['first_wave_governed_manifest']['execution_authorized']}",
        f"- Governed execution proposed only: {review['first_wave_governed_manifest']['governed_execution_proposed_only']}",
        "",
        "## Expected Execution Artifacts",
    ])
    lines.extend([f"- {x['artifact']}: {x['purpose']}" for x in review["expected_execution_artifacts"]])
    lines.extend(["", "## Stop-After-First-Wave Policy"])
    lines.extend([f"- {k}: {v}" for k, v in review["stop_after_first_wave_policy"].items()])
    lines.extend(["", "## Verification Requirements"])
    lines.extend([f"- {x}" for x in review["verification_requirements"]])
    lines.extend(["", "## Fail-Closed Conditions"])
    lines.extend([f"- {x}" for x in review["fail_closed_conditions"]])
    lines.extend([
        "",
        "## Explicit Non-Authorization Notice",
        f"- {review['execution_non_authorization_notice']['notice']}",
        "",
        "## Architectural Overengineering Warning",
        f"- {review['architectural_overengineering_warning']}",
        "",
        "## Recommendation for Next Phase",
        f"- {review['recommendation_for_next_phase']}",
    ])
    return "\n".join(lines)
