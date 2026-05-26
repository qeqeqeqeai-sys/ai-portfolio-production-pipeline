"""LR6-OBS9 deterministic post-execution review framework (review-only, non-executing)."""
from __future__ import annotations

from typing import Any, Callable

from transmission_layers.expectation_failure.replay_ecology.lr6_obs6_first_enriched_replay_wave_design import (
    build_lr6_obs6_first_wave_candidates,
    build_lr6_obs6_observation_questions,
    build_lr6_obs6_stop_conditions,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_obs7_dry_run_enriched_replay_observation_simulation import (
    build_lr6_obs7_contradiction_stress_review,
    build_lr6_obs7_propagation_stress_review,
    build_lr6_obs7_simulated_observation_routes,
    build_lr6_obs7_stop_condition_simulation,
    build_lr6_obs7_weak_signal_stress_review,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_obs8_governed_enriched_replay_observation_proposal import (
    build_lr6_obs8_expected_execution_artifacts,
    build_lr6_obs8_fail_closed_conditions,
    build_lr6_obs8_governance_requirements,
    build_lr6_obs8_supervisor_review as build_obs8_supervisor,
    build_lr6_obs8_verification_requirements,
)

DETERMINISTIC_VERSION = "LR6_OBS9_EXECUTION_REVIEW_FRAMEWORK_V1"
SOURCE_PHASE = "LR6-OBS9"


def _safe_list(builder: Callable[[], Any]) -> list[Any]:
    try:
        out = builder()
    except Exception:
        out = []
    return out if isinstance(out, list) else []


def _safe_dict(builder: Callable[[], Any]) -> dict[str, Any]:
    try:
        out = builder()
    except Exception:
        out = {}
    return out if isinstance(out, dict) else {}


def build_lr6_obs9_review_framework_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = lr6_artifacts if isinstance(lr6_artifacts, dict) else {}
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "framework_mode": "post_execution_review_framework_only",
        "inspected_obs6_outputs": bool(artifacts.get("lr6_obs6_first_enriched_replay_wave_design", True)),
        "inspected_obs7_outputs": bool(artifacts.get("lr6_obs7_dry_run_enriched_replay_observation_simulation", True)),
        "inspected_obs8_outputs": bool(artifacts.get("lr6_obs8_governed_enriched_replay_observation_proposal", True)),
        "execution_authorized": False,
        "review_framework_only": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs9_success_criteria() -> list[str]:
    return [
        "Contradiction findings become structurally meaningful via persistent or migrating tensions.",
        "Weak-signal entities appear materially in attribution and bridge roles.",
        "Propagation pathways become less obvious and show non-trivial rewiring.",
        "Replay topology diversifies through secondary attractors and indirect bridges.",
        "Replay richness improves longitudinally without monoculture reinforcement.",
        "Semantic gravity becomes less megacap-dominated.",
        "Topology drift becomes visible across repeated observation slices.",
        "Enriched replay outputs are distinguishable from baseline replay outputs.",
    ]


def build_lr6_obs9_failure_criteria() -> list[str]:
    return [
        "Replay remains megacap-centered with no meaningful gravity relief.",
        "Contradiction ecology remains generic, static, or narratively recycled.",
        "Weak-signal entities remain absent from meaningful attribution.",
        "Propagation remains repetitive and obvious.",
        "Enrichment does not materially change replay outputs.",
        "Saturation increases without diversification gain.",
        "Topology drift remains weak, isolated, or absent.",
        "Enriched replay remains indistinguishable from pre-enrichment replay.",
    ]


def build_lr6_obs9_replay_delta_interpretation_rules() -> list[str]:
    return [
        "Do not overinterpret minor semantic wording changes as structural replay improvement.",
        "Do not infer emergence from isolated examples without recurrence.",
        "Separate structural persistence from random variation using repeated slices.",
        "Differentiate topology diversification from simple category expansion.",
        "Treat contradiction migration as meaningful only when cross-cluster persistence exists.",
        "Differentiate replay richness from reporting sophistication or narrative verbosity.",
    ]


def build_lr6_obs9_contradiction_usefulness_criteria() -> list[str]:
    return [
        "persistence", "migration", "cross_cluster_spread", "replay_tension_maintenance",
        "topology_interaction", "asymmetry_creation", "non_trivial_structural_recurrence",
    ]


def build_lr6_obs9_topology_diversification_criteria() -> list[str]:
    return [
        "indirect_bridges", "non_obvious_propagation", "cross_role_contamination",
        "infrastructure_linked_propagation", "peripheral_to_core_bridge_emergence",
        "weakening_of_megacap_gravity", "secondary_replay_attractors",
    ]


def build_lr6_obs9_weak_signal_success_criteria() -> list[str]:
    return [
        "appears_in_attribution", "influences_propagation_structure", "alters_replay_topology",
        "increases_replay_diversity", "creates_interpretable_drift", "bridges_disconnected_clusters",
    ]


def build_lr6_obs9_fail_closed_review_thresholds() -> list[str]:
    return [
        "Trivial replay changes across the wave.",
        "Repetitive topology with no meaningful rewiring.",
        "Absent weak-signal effects in attribution and pathways.",
        "Worsening megacap monoculture.",
        "No meaningful contradiction evolution.",
        "No distinguishable replay richness improvement.",
        "Observation outputs collapse into narrative restatement.",
    ]


def build_lr6_obs9_continuation_vs_termination_logic() -> dict[str, list[str]]:
    return {
        "CONTINUE_ONLY_IF": [
            "Replay ecology measurably diversifies.",
            "Contradiction ecology deepens structurally.",
            "Topology drift is observable and recurring.",
            "Weak-signal entities matter in attribution and propagation.",
            "Replay outputs differ materially from baseline.",
        ],
        "TERMINATE_OR_PAUSE_IF": [
            "Replay remains structurally repetitive.",
            "Enrichment yields cosmetic changes only.",
            "Propagation pathways remain obvious.",
            "Architecture complexity exceeds ecological value.",
        ],
    }


def build_lr6_obs9_confirmation_bias_safeguards() -> list[str]:
    return [
        "Maintain explicit anti-self-congratulation posture.",
        "No emergent-intelligence claims without repeated evidence.",
        "No novelty claims from isolated examples.",
        "Do not confuse procedural sophistication with ecological richness.",
        "Do not assign topology significance without longitudinal persistence.",
        "Do not treat narrative complexity as replay intelligence.",
    ]


def certify_lr6_obs9_review_framework_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "review_framework_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs9_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "context": build_lr6_obs9_review_framework_context(lr6_artifacts),
        "inspected_obs6_inputs": {
            "first_wave_candidates": _safe_list(build_lr6_obs6_first_wave_candidates),
            "observation_questions": _safe_list(build_lr6_obs6_observation_questions),
            "stop_conditions": _safe_list(build_lr6_obs6_stop_conditions),
        },
        "inspected_obs7_inputs": {
            "simulated_observation_routes": _safe_list(build_lr6_obs7_simulated_observation_routes),
            "contradiction_stress_review": _safe_dict(build_lr6_obs7_contradiction_stress_review),
            "propagation_stress_review": _safe_dict(build_lr6_obs7_propagation_stress_review),
            "weak_signal_stress_review": _safe_dict(build_lr6_obs7_weak_signal_stress_review),
            "stop_condition_simulation": _safe_list(build_lr6_obs7_stop_condition_simulation),
        },
        "inspected_obs8_inputs": {
            "governance_requirements": _safe_list(build_lr6_obs8_governance_requirements),
            "verification_requirements": _safe_list(build_lr6_obs8_verification_requirements),
            "fail_closed_conditions": _safe_list(build_lr6_obs8_fail_closed_conditions),
            "expected_execution_artifacts": _safe_list(build_lr6_obs8_expected_execution_artifacts),
            "obs8_supervisor_review": _safe_dict(lambda: build_obs8_supervisor(lr6_artifacts)),
        },
        "success_criteria": build_lr6_obs9_success_criteria(),
        "failure_criteria": build_lr6_obs9_failure_criteria(),
        "replay_delta_interpretation_rules": build_lr6_obs9_replay_delta_interpretation_rules(),
        "contradiction_usefulness_criteria": build_lr6_obs9_contradiction_usefulness_criteria(),
        "topology_diversification_criteria": build_lr6_obs9_topology_diversification_criteria(),
        "weak_signal_success_criteria": build_lr6_obs9_weak_signal_success_criteria(),
        "fail_closed_review_thresholds": build_lr6_obs9_fail_closed_review_thresholds(),
        "continuation_vs_termination_logic": build_lr6_obs9_continuation_vs_termination_logic(),
        "confirmation_bias_safeguards": build_lr6_obs9_confirmation_bias_safeguards(),
        "boundary_certification": certify_lr6_obs9_review_framework_boundary(),
        "explicit_non_authorization_notice": "OBS9 is review-framework-only; no execution is authorized.",
        "architectural_overengineering_warning": "Do not expand architecture for cosmetic complexity; ecological usefulness must lead.",
        "recommendation_for_next_phase": "If a governed first wave is ever executed later, apply this framework before any continuation decision.",
    }


def build_lr6_obs9_markdown_report(review: dict[str, Any]) -> str:
    lines = [
        "# LR6-OBS9 Execution Review Framework",
        "",
        "## Objective",
        "Define deterministic post-execution review criteria for a hypothetical future governed first-wave enriched replay observation.",
        "",
        "## Inspected OBS6/OBS7/OBS8 Inputs",
        f"- OBS6 first-wave candidates: {len(review['inspected_obs6_inputs']['first_wave_candidates'])}",
        f"- OBS7 simulated routes: {len(review['inspected_obs7_inputs']['simulated_observation_routes'])}",
        f"- OBS8 expected artifacts: {len(review['inspected_obs8_inputs']['expected_execution_artifacts'])}",
        "",
        "## Success Criteria",
    ]
    lines.extend([f"- {x}" for x in review["success_criteria"]])
    lines.extend(["", "## Failure Criteria"])
    lines.extend([f"- {x}" for x in review["failure_criteria"]])
    lines.extend(["", "## Replay Delta Interpretation Rules"])
    lines.extend([f"- {x}" for x in review["replay_delta_interpretation_rules"]])
    lines.extend(["", "## Contradiction Usefulness Criteria"])
    lines.extend([f"- {x}" for x in review["contradiction_usefulness_criteria"]])
    lines.extend(["", "## Topology Diversification Criteria"])
    lines.extend([f"- {x}" for x in review["topology_diversification_criteria"]])
    lines.extend(["", "## Weak-Signal Success Criteria"])
    lines.extend([f"- {x}" for x in review["weak_signal_success_criteria"]])
    lines.extend(["", "## Fail-Closed Review Thresholds"])
    lines.extend([f"- {x}" for x in review["fail_closed_review_thresholds"]])
    lines.extend(["", "## Continuation vs Termination Logic"])
    lines.extend([f"- CONTINUE_ONLY_IF: {x}" for x in review["continuation_vs_termination_logic"]["CONTINUE_ONLY_IF"]])
    lines.extend([f"- TERMINATE_OR_PAUSE_IF: {x}" for x in review["continuation_vs_termination_logic"]["TERMINATE_OR_PAUSE_IF"]])
    lines.extend(["", "## Confirmation Bias Safeguards"])
    lines.extend([f"- {x}" for x in review["confirmation_bias_safeguards"]])
    lines.extend([
        "",
        "## Explicit Non-Authorization Notice",
        f"- {review['explicit_non_authorization_notice']}",
        "",
        "## Architectural Overengineering Warning",
        f"- {review['architectural_overengineering_warning']}",
        "",
        "## Recommendation for Next Phase",
        f"- {review['recommendation_for_next_phase']}",
    ])
    return "\n".join(lines)
