from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import (
    build_phase_a1b_real_curated_structural_universe,
    certify_phase_a_observational_expansion_boundary,
)
from .phase_a3_derived_replay_ecology_measurement import (
    build_phase_a3_hub_concentration_measurement,
    build_phase_a3_monoculture_pressure_measurement,
    build_phase_a3_replay_overlap_risk_measurement,
    build_phase_a3_structural_balance_score,
    build_phase_a3_weak_node_amplification_measurement,
)
from .phase_a4_narrative_saturation_replay_recurrence_pressure import (
    build_phase_a4_contradiction_exhaustion_risk_measurement,
    build_phase_a4_contradiction_recurrence_density_measurement,
    build_phase_a4_narrative_saturation_pressure_measurement,
    build_phase_a4_novelty_decay_risk_measurement,
    build_phase_a4_replay_path_repetition_measurement,
    build_phase_a4_replay_recurrence_pressure_measurement,
    build_phase_a4_saturation_recurrence_composite_score,
    build_phase_a4_semantic_crowding_measurement,
    build_phase_a4_structural_redundancy_measurement,
)


def _bounded(v: float) -> float:
    return round(max(0.0, min(1.0, v)), 6)


def _stabilization(name: str, inputs: list[str], pressure: str, actions: list[str], effect: str, risk_if_ignored: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("stabilization_name", name),
        ("deterministic_inputs_used", inputs),
        ("target_pressure", pressure),
        ("stabilization_actions", actions),
        ("expected_effect", effect),
        ("replay_ecology_risk_if_ignored", risk_if_ignored),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def _base_metrics() -> dict[str, float]:
    return {
        "replay_recurrence_pressure": build_phase_a4_replay_recurrence_pressure_measurement()["measurement_value"],
        "replay_path_repetition": build_phase_a4_replay_path_repetition_measurement()["measurement_value"],
        "structural_redundancy": build_phase_a4_structural_redundancy_measurement()["measurement_value"],
        "semantic_crowding": build_phase_a4_semantic_crowding_measurement()["measurement_value"],
        "narrative_saturation_pressure": build_phase_a4_narrative_saturation_pressure_measurement()["measurement_value"],
        "novelty_decay_risk": build_phase_a4_novelty_decay_risk_measurement()["measurement_value"],
        "contradiction_recurrence_density": build_phase_a4_contradiction_recurrence_density_measurement()["measurement_value"],
        "contradiction_exhaustion_risk": build_phase_a4_contradiction_exhaustion_risk_measurement()["measurement_value"],
        "replay_overlap_risk": build_phase_a3_replay_overlap_risk_measurement()["measurement_value"],
        "hub_concentration": build_phase_a3_hub_concentration_measurement()["measurement_value"],
        "monoculture_pressure": build_phase_a3_monoculture_pressure_measurement()["measurement_value"],
        "weak_node_amplification": build_phase_a3_weak_node_amplification_measurement()["measurement_value"],
        "structural_balance_score": build_phase_a3_structural_balance_score()["score"],
    }


def build_phase_a5_anti_recurrence_stabilization_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A5"),
        ("mode", "deterministic_observational_anti_recurrence_stabilization"),
        ("input_source", "phase_a1b_curated_universe_plus_a3_a4_observational_measurements"),
        ("observational_only", True),
        ("bounded", True),
        ("non_predictive", True),
        ("non_trading", True),
        ("pure_function_oriented", True),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def build_phase_a5_replay_corridor_diversification_plan() -> OrderedDict[str, Any]:
    return _stabilization(
        "replay_corridor_diversification_plan",
        ["adjacency_richness_score", "propagation_richness_score", "replay_ecology_richness_score", "replay_overlap_risk", "replay_recurrence_pressure", "replay_path_repetition"],
        "replay_corridor_reuse_and_replay_lock_in",
        ["enforce_max_corridor_reuse_ratio_before_any_replay_density_change", "prioritize_underrepresented_sector_domain_corridors", "require_orthogonal_propagation_mix_for_high_overlap_candidates"],
        "reduces corridor reuse concentration and replay path lock-in under rising density pressure",
        "repeated corridor reuse compounds recurrence pressure and accelerates monoculture topology",
    )


def build_phase_a5_topology_decompression_plan() -> OrderedDict[str, Any]:
    return _stabilization(
        "topology_decompression_plan",
        ["hub_concentration", "structural_redundancy", "semantic_crowding", "structural_balance_score", "monoculture_pressure"],
        "topology_gravity_wells_and_hub_dominance",
        ["cap_hub_dominant_pathway_share", "defer_high_centrality_redundant_paths", "increase_bridge_candidate_rotation_to_raise_topology_entropy"],
        "improves balance and reduces gravity well pull toward over-connected hubs",
        "hub-dominant pathways can create replay monoculture and weak-node spillover",
    )


def build_phase_a5_contradiction_orthogonalization_plan() -> OrderedDict[str, Any]:
    return _stabilization(
        "contradiction_orthogonalization_plan",
        ["contradiction_richness_score", "contradiction_recurrence_density", "contradiction_exhaustion_risk", "weak_node_amplification"],
        "contradiction_recycling_and_exhaustion",
        ["set_max_contradiction_reuse_ratio", "favor_underrepresented_contradiction_buckets", "require_cross_domain_contradiction_pairing_before_reuse"],
        "maintains contradiction novelty and delays contradiction yield exhaustion",
        "recycling identical contradiction frames erodes diversity and weakens replay survivability",
    )


def build_phase_a5_bridge_node_diversification_plan() -> OrderedDict[str, Any]:
    rows = build_phase_a1b_real_curated_structural_universe()
    avg_replay_richness = _bounded(sum(r["replay_ecology_richness_score"] for r in rows) / (10 * len(rows)))
    return _stabilization(
        "bridge_node_diversification_plan",
        ["sector", "sefi_domain", "adjacency_richness_score", "propagation_richness_score", "replay_ecology_richness_score", "weak_node_amplification"],
        "hub_driven_monoculture_and_weak_node_amplification",
        ["prioritize_medium_adjacency_high_propagation_candidates_as_bridges", "enforce_sector_domain_dispersion_for_bridge_selection", f"target_bridge_pool_replay_ecology_richness_at_or_above_{avg_replay_richness}"],
        "improves cross-cluster transmissibility without deepening hub gravity",
        "lack of diversified bridges can trap replay flow in dominant hubs and amplify weak nodes",
    )


def build_phase_a5_recurrence_suppression_guardrails() -> OrderedDict[str, Any]:
    m = _base_metrics()
    return OrderedDict([
        ("max_repeated_replay_corridor_ratio", _bounded(min(0.55, m["replay_recurrence_pressure"] + 0.08))),
        ("max_hub_dominant_pathway_share", _bounded(min(0.52, m["hub_concentration"] + 0.06))),
        ("max_same_domain_wave_concentration", _bounded(min(0.5, m["semantic_crowding"] + 0.05))),
        ("max_contradiction_reuse_ratio", _bounded(min(0.48, m["contradiction_recurrence_density"] + 0.07))),
        ("max_semantic_crowding_pressure", _bounded(min(0.6, m["semantic_crowding"] + 0.08))),
        ("max_replay_path_repetition", _bounded(min(0.58, m["replay_path_repetition"] + 0.08))),
        ("max_structural_redundancy_pressure", _bounded(min(0.58, m["structural_redundancy"] + 0.08))),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def build_phase_a5_entropy_preservation_guardrails() -> OrderedDict[str, Any]:
    m = _base_metrics()
    return OrderedDict([
        ("minimum_topology_entropy", _bounded(max(0.45, 1 - m["hub_concentration"]))),
        ("minimum_contradiction_entropy", _bounded(max(0.46, 1 - m["contradiction_recurrence_density"]))),
        ("minimum_propagation_diversity", 0.5),
        ("minimum_structural_balance_score", _bounded(max(0.52, m["structural_balance_score"]))),
        ("maximum_monoculture_pressure", _bounded(min(0.55, m["monoculture_pressure"] + 0.08))),
        ("maximum_weak_node_amplification", _bounded(min(0.55, m["weak_node_amplification"] + 0.09))),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def build_phase_a5_novelty_preservation_guardrails() -> OrderedDict[str, Any]:
    m = _base_metrics()
    return OrderedDict([
        ("maximum_novelty_decay_risk", _bounded(min(0.45, m["novelty_decay_risk"] + 0.07))),
        ("minimum_high_information_node_share", 0.42),
        ("maximum_low_information_node_share", _bounded(min(0.58, m["novelty_decay_risk"] + 0.21))),
        ("maximum_replay_overlap_risk", _bounded(min(0.55, m["replay_overlap_risk"] + 0.08))),
        ("minimum_orthogonal_propagation_contribution", 0.38),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def build_phase_a5_replay_survivability_stabilization_review() -> OrderedDict[str, Any]:
    m = _base_metrics()
    return OrderedDict([
        ("diversity_survivability", _bounded(1 - ((m["semantic_crowding"] + m["monoculture_pressure"]) / 2))),
        ("contradiction_survivability", _bounded(1 - ((m["contradiction_recurrence_density"] + m["contradiction_exhaustion_risk"]) / 2))),
        ("topology_survivability", _bounded(1 - ((m["hub_concentration"] + m["structural_redundancy"]) / 2))),
        ("novelty_survivability", _bounded(1 - m["novelty_decay_risk"])),
        ("recurrence_resistance", _bounded(1 - ((m["replay_recurrence_pressure"] + m["replay_path_repetition"]) / 2))),
        ("weak_node_resilience", _bounded(1 - m["weak_node_amplification"])),
        ("decompression_readiness", _bounded((build_phase_a3_structural_balance_score()["score"] + (1 - m["hub_concentration"])) / 2)),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def build_phase_a5_stabilization_priority_ranking() -> list[OrderedDict[str, Any]]:
    m = _base_metrics()
    order = [
        "replay_recurrence_pressure",
        "replay_path_repetition",
        "structural_redundancy",
        "semantic_crowding",
        "narrative_saturation_pressure",
        "novelty_decay_risk",
        "contradiction_recurrence_density",
        "contradiction_exhaustion_risk",
    ]
    return [OrderedDict([("priority_rank", i + 1), ("pressure", k), ("pressure_value", m[k]), ("pressure_band", "moderate" if 0.33 <= m[k] < 0.66 else ("high" if m[k] >= 0.66 else "low"))]) for i, k in enumerate(order)]


def build_phase_a5_supervisor_review() -> OrderedDict[str, Any]:
    ranking = build_phase_a5_stabilization_priority_ranking()
    return OrderedDict([
        ("phase", "A5"),
        ("stabilization_status", "deterministic_anti_recurrence_stabilization_ready_observational_only"),
        ("highest_priority_pressure", ranking[0]["pressure"]),
        ("immediate_guardrail_focus", ["max_repeated_replay_corridor_ratio", "max_replay_path_repetition", "max_structural_redundancy_pressure"]),
        ("deferred_focus", ["contradiction_exhaustion_risk", "novelty_decay_risk"]),
        ("residual_risks", ["metadata_only_derivation_limits_latent_drift_visibility", "moderate_recurrence_pressure_requires_strict_pre_activation_guardrails"]),
        ("recommended_next_phase_action", "Proceed only to Phase A6 observational stress simulation; keep replay accumulation and topology activation disabled."),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def build_phase_a5_markdown_report() -> str:
    return "\n".join([
        "# Phase A5 Anti-Recurrence Ecology Stabilization",
        "## objective",
        "Define deterministic anti-recurrence stabilization APIs that constrain recurrence pressure before any replay accumulation or topology activation.",
        "## relationship to A4",
        str(build_phase_a4_saturation_recurrence_composite_score()),
        "## observational-only boundary",
        str(certify_phase_a_observational_expansion_boundary()),
        "## stabilization methodology",
        "Bounded metadata-only pure functions deriving stabilization plans and guardrails from A1/A3/A4 measurements.",
        "## replay corridor diversification plan",
        str(build_phase_a5_replay_corridor_diversification_plan()),
        "## topology decompression plan",
        str(build_phase_a5_topology_decompression_plan()),
        "## contradiction orthogonalization plan",
        str(build_phase_a5_contradiction_orthogonalization_plan()),
        "## bridge-node diversification plan",
        str(build_phase_a5_bridge_node_diversification_plan()),
        "## recurrence suppression guardrails",
        str(build_phase_a5_recurrence_suppression_guardrails()),
        "## entropy preservation guardrails",
        str(build_phase_a5_entropy_preservation_guardrails()),
        "## novelty preservation guardrails",
        str(build_phase_a5_novelty_preservation_guardrails()),
        "## replay survivability stabilization review",
        str(build_phase_a5_replay_survivability_stabilization_review()),
        "## stabilization priority ranking",
        str(build_phase_a5_stabilization_priority_ranking()),
        "## supervisor recommendation",
        str(build_phase_a5_supervisor_review()),
        "## governance preservation",
        "Observational expansion only is preserved. No replay operationalization, topology activation, persistence writes, SQL paths, prediction, or trading are introduced.",
        "## residual risks",
        "Moderate replay recurrence pressure and replay path repetition still require strict guardrail enforcement prior to any future phase promotion.",
        "## recommendation for Phase A6 or B1",
        "A6 should run deterministic observational stress-testing of these guardrails; B1 remains blocked from operational activation.",
    ])
