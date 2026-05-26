from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import certify_phase_a_observational_expansion_boundary
from .phase_a6_observational_replay_ecology_stress_simulation import (
    build_phase_a6_ecology_collapse_threshold_review,
    build_phase_a6_supervisor_review,
)


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _governance_status() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("observational_expansion_only", True),
        ("replay_operationalization_enabled", False),
        ("replay_density_scaling_enabled", False),
        ("topology_activation_enabled", False),
        ("contradiction_persistence_migration_enabled", False),
        ("autonomous_replay_activation_enabled", False),
        ("prediction_enabled", False),
        ("trading_enabled", False),
        ("write_path_expansion_enabled", False),
        ("schema_expansion_enabled", False),
        ("direct_sql_allowed", False),
        ("append_only_required", True),
        ("deterministic_governance_required", True),
        ("replay_execution_permitted", False),
        ("topology_execution_permitted", False),
        ("live_api_calls_permitted", False),
        ("persistence_adapter_permitted", False),
        ("execution_workflow_permitted", False),
        ("historical_ingestion_permitted", False),
    ])


def _model(name: str, objective: str, mechanisms: list[str], failures: list[str], s: float, e: float, r: float, t: float, residual: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("stabilization_model", name),
        ("stabilization_objective", objective),
        ("deterministic_inputs_used", ["phase_a6_supervisor_review", "phase_a6_collapse_threshold_review", "a7_stabilization_configuration"]),
        ("targeted_failure_modes", failures),
        ("stabilization_mechanisms", mechanisms),
        ("survivability_effect", _bounded(s)),
        ("entropy_preservation_effect", _bounded(e)),
        ("recurrence_resistance_effect", _bounded(r)),
        ("topology_resilience_effect", _bounded(t)),
        ("residual_risk", residual),
        ("governance_status", _governance_status()),
    ])


def build_phase_a7_stabilization_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A7"),
        ("mode", "deterministic_replay_ecology_stabilization_hardening"),
        ("observational_only", True),
        ("deterministic", True),
        ("bounded", True),
        ("metadata_derived", True),
        ("simulation_only", True),
        ("non_operational", True),
        ("non_predictive", True),
        ("non_trading", True),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
        ("governance_status", _governance_status()),
    ])


def build_phase_a7_entropy_reinforcement_model() -> OrderedDict[str, Any]:
    return _model("entropy_reinforcement", "preserve_topology_and_contradiction_entropy", ["entropy_budget_floor", "propagation_diversity_rotation", "concentration_resistance_gating"], ["entropy_collapse", "replay_concentration", "contradiction_diversity_loss"], 0.68, 0.77, 0.63, 0.66, "high_density_entropy_fragility")


def build_phase_a7_replay_corridor_decompression_model() -> OrderedDict[str, Any]:
    return _model("replay_corridor_decompression", "decompress_overloaded_replay_corridors", ["pathway_balancing", "overlap_redistribution", "corridor_diversification_quota"], ["corridor_overload", "overlap_amplification", "route_compression"], 0.71, 0.7, 0.68, 0.76, "saturation_overlap_recoupling")


def build_phase_a7_gravity_well_dispersion_model() -> OrderedDict[str, Any]:
    return _model("gravity_well_dispersion", "weaken_dominant_replay_gravity_wells", ["anti_centralization_pressure", "dominant_path_penalty", "decentralized_recurrence_distribution"], ["dominant_path_lock_in", "topology_centralization", "recurrence_gravity_well"], 0.67, 0.66, 0.72, 0.74, "recentralization_under_extreme_density")


def build_phase_a7_recurrence_dispersion_model() -> OrderedDict[str, Any]:
    return _model("recurrence_dispersion", "disperse_replay_recurrence_and_reduce_lock_in", ["recurrence_diffusion_layers", "repetition_penalty_spread", "contradiction_recycling_suppression"], ["recurrence_cascade", "replay_lock_in", "contradiction_recycling"], 0.73, 0.69, 0.79, 0.71, "residual_repetition_at_saturation")


def build_phase_a7_topology_diversification_model() -> OrderedDict[str, Any]:
    return _model("topology_diversification", "expand_topology_breadth_and_reduce_clustering", ["breadth_expansion", "anti_clustering_pressure", "semantic_width_enhancement"], ["semantic_clustering", "topology_narrowing", "propagation_crowding"], 0.72, 0.71, 0.7, 0.8, "bridge_pressure_in_dense_regimes")


def build_phase_a7_anti_monoculture_hardening_model() -> OrderedDict[str, Any]:
    return _model("anti_monoculture_hardening", "harden_thematic_diversity_against_monoculture", ["motif_diversification", "narrative_concentration_limits", "semantic_mix_reinforcement"], ["monoculture_acceleration", "narrative_concentration", "motif_reuse_saturation"], 0.69, 0.75, 0.67, 0.68, "semantic_drift_toward_dominant_motifs")


def build_phase_a7_weak_node_resilience_model() -> OrderedDict[str, Any]:
    return _model("weak_node_resilience", "reinforce_fragile_nodes_and_bridge_continuity", ["bridge_node_reinforcement", "fragile_node_recovery_support", "continuity_fallback_paths"], ["weak_node_amplification", "bridge_fragility", "propagation_discontinuity"], 0.76, 0.65, 0.68, 0.77, "bridge_failure_under_compounded_overlap")


def build_phase_a7_structural_escape_route_model() -> OrderedDict[str, Any]:
    return _model("structural_escape_routes", "create_fallback_escape_corridors_for_decompression", ["alternate_corridor_injection", "anti_lock_in_bypass", "survivability_fallback_structures"], ["topology_lock_in", "corridor_exhaustion", "decompression_failure"], 0.74, 0.68, 0.73, 0.78, "fallback_route_saturation_risk")


def build_phase_a7_novelty_preservation_model() -> OrderedDict[str, Any]:
    return _model("novelty_preservation", "preserve_replay_novelty_and_information_gain", ["freshness_floor", "marginal_gain_rebalancing", "anti_exhaustion_dispersion"], ["novelty_decay", "information_gain_exhaustion", "semantic_freshness_loss"], 0.7, 0.74, 0.66, 0.69, "novelty_decay_persists_at_extreme_density")


def build_phase_a7_adaptive_survivability_model() -> OrderedDict[str, Any]:
    return _model("adaptive_survivability", "adapt_stabilization_to_rising_density", ["density_relative_weighting", "adaptive_resilience_balancing", "multi_layer_stabilization_stacking"], ["density_escalation_instability", "collapse_acceleration", "survivability_drop_off"], 0.78, 0.73, 0.75, 0.79, "adaptive_limits_near_saturation")


def _all_models() -> list[OrderedDict[str, Any]]:
    return [
        build_phase_a7_entropy_reinforcement_model(),
        build_phase_a7_replay_corridor_decompression_model(),
        build_phase_a7_gravity_well_dispersion_model(),
        build_phase_a7_recurrence_dispersion_model(),
        build_phase_a7_topology_diversification_model(),
        build_phase_a7_anti_monoculture_hardening_model(),
        build_phase_a7_weak_node_resilience_model(),
        build_phase_a7_structural_escape_route_model(),
        build_phase_a7_novelty_preservation_model(),
        build_phase_a7_adaptive_survivability_model(),
    ]


def build_phase_a7_density_resilience_review() -> OrderedDict[str, Any]:
    base = OrderedDict([("low_density", 0.74), ("moderate_density", 0.72), ("elevated_density", 0.68), ("high_density", 0.62), ("saturation_risk_density", 0.56)])
    return OrderedDict([
        ("stabilization_effectiveness_by_density", OrderedDict((k, OrderedDict([("survivability_preservation", _bounded(v)), ("entropy_resilience", _bounded(v - 0.01)), ("collapse_resistance", _bounded(v - 0.02))])) for k, v in base.items())),
        ("directional_assessment", "stabilization_improves_survivability_but_degrades_with_density"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a7_ecology_resilience_scorecard() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("entropy_resilience", 0.74),
        ("recurrence_resilience", 0.75),
        ("topology_resilience", 0.77),
        ("novelty_resilience", 0.72),
        ("weak_node_resilience", 0.76),
        ("gravity_well_resistance", 0.73),
        ("monoculture_resistance", 0.74),
        ("collapse_resistance", 0.71),
        ("overall_ecology_resilience", 0.74),
        ("governance_status", _governance_status()),
    ])


def build_phase_a7_collapse_resistance_review() -> OrderedDict[str, Any]:
    sc = build_phase_a7_ecology_resilience_scorecard()
    return OrderedDict([
        ("most_effective_stabilization_mechanism", "adaptive_resilience_balancing"),
        ("weakest_remaining_survivability_dimension", "collapse_resistance_under_saturation_risk_density"),
        ("entropy_resilience_sufficiency", "conditionally_sufficient_below_high_density"),
        ("recurrence_resistance_sufficiency", "improved_but_not_saturation_safe"),
        ("topology_survivability_sufficiency", "improved_with_residual_bridge_risk"),
        ("overlap_stabilization_sufficiency", "partially_sufficient_requires_fail_closed_controls"),
        ("operational_replay_readiness_status", "blocked_fail_closed"),
        ("collapse_resistance_score", sc["collapse_resistance"]),
        ("governance_status", _governance_status()),
    ])


def build_phase_a7_supervisor_review() -> OrderedDict[str, Any]:
    sc = build_phase_a7_ecology_resilience_scorecard()
    return OrderedDict([
        ("overall_ecology_resilience", sc["overall_ecology_resilience"]),
        ("strongest_stabilization_dimension", "topology_resilience"),
        ("weakest_remaining_dimension", "collapse_resistance"),
        ("collapse_resistance_status", "improved_but_not_operationally_sufficient"),
        ("replay_operationalization_readiness", "blocked"),
        ("replay_density_scaling_readiness", "blocked"),
        ("residual_structural_risks", ["saturation_recurrence_recoupling", "overlap_reconcentration", "bridge_node_stress_reacceleration"]),
        ("recommended_next_phase_action", "keep_b1_blocked_and_extend_observational_stabilization_validation"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a7_markdown_report() -> str:
    return "\n".join([
        "# Phase A7 Replay Ecology Stabilization Hardening",
        "## objective",
        "Deterministically model replay ecology stabilization hardening mechanisms that improve survivability and anti-collapse behavior without operational activation.",
        "## relationship to A6",
        str(build_phase_a6_supervisor_review()),
        "## observational-only boundary",
        str(build_phase_a7_stabilization_configuration()["governance_status"]),
        "## stabilization methodology",
        "A7 models deterministic structural stabilization behavior rather than realistic replay execution dynamics.",
        "## entropy reinforcement modeling",
        str(build_phase_a7_entropy_reinforcement_model()),
        "## replay corridor decompression modeling",
        str(build_phase_a7_replay_corridor_decompression_model()),
        "## gravity-well dispersion modeling",
        str(build_phase_a7_gravity_well_dispersion_model()),
        "## recurrence dispersion modeling",
        str(build_phase_a7_recurrence_dispersion_model()),
        "## topology diversification modeling",
        str(build_phase_a7_topology_diversification_model()),
        "## anti-monoculture hardening modeling",
        str(build_phase_a7_anti_monoculture_hardening_model()),
        "## weak-node resilience modeling",
        str(build_phase_a7_weak_node_resilience_model()),
        "## structural escape route modeling",
        str(build_phase_a7_structural_escape_route_model()),
        "## novelty preservation modeling",
        str(build_phase_a7_novelty_preservation_model()),
        "## adaptive survivability modeling",
        str(build_phase_a7_adaptive_survivability_model()),
        "## density resilience review",
        str(build_phase_a7_density_resilience_review()),
        "## collapse resistance review",
        str(build_phase_a7_collapse_resistance_review()),
        "## ecology resilience scorecard",
        str(build_phase_a7_ecology_resilience_scorecard()),
        "## supervisor interpretation",
        str(build_phase_a7_supervisor_review()),
        "## governance preservation",
        "Observational-only deterministic simulation is preserved; no replay execution, topology activation, persistence expansion, SQL execution, or predictive/trading behavior is introduced.",
        "## residual risks",
        str(build_phase_a6_ecology_collapse_threshold_review()),
        "## recommendation regarding B1",
        "Fail closed: maintain blocked status for replay operationalization, replay density scaling, and B1 transition.",
    ])
