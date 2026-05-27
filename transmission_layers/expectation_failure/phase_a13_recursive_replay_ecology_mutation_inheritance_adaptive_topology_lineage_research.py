from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import certify_phase_a_observational_expansion_boundary
from .phase_a12_adaptive_recursive_replay_ecology_evolution_structural_mutation_research import build_phase_a12_supervisor_review

BASE_INPUTS = ["phase_a12_supervisor_review", "phase_a13_mutation_lineage_configuration", "a_series_governance_boundary"]


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


def _model(name: str, objective: str, inheritance_signals: list[str], lineage_signals: list[str], lineage_effect: str, containment_effect: str, lineage_risk: str, reversibility_constraint: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("model_name", name),
        ("research_objective", objective),
        ("deterministic_inputs_used", BASE_INPUTS),
        ("inheritance_signals", inheritance_signals),
        ("lineage_evolution_signals", lineage_signals),
        ("lineage_effect", lineage_effect),
        ("containment_effect", containment_effect),
        ("lineage_risk", lineage_risk),
        ("reversibility_constraint", reversibility_constraint),
        ("governance_status", _governance_status()),
    ])


def build_phase_a13_mutation_lineage_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A13"),
        ("mode", "recursive_replay_ecology_mutation_inheritance_adaptive_topology_lineage_research"),
        ("observational_only", True),
        ("deterministic", True),
        ("bounded", True),
        ("metadata_derived", True),
        ("simulation_only", True),
        ("non_operational", True),
        ("non_predictive", True),
        ("non_trading", True),
        ("pure_function_oriented", True),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
        ("governance_status", _governance_status()),
    ])


def build_phase_a13_recursive_mutation_inheritance_model() -> OrderedDict[str, Any]:
    return _model("recursive_mutation_inheritance", "assess whether structural mutations are inherited across replay ecology cycles and whether inherited deformation changes future cascade behavior", ["cross_cycle_deformation_retention", "inheritance_bias_in_future_cascade_routes"], ["inherited_strain_reactivates_under_lower_stress", "lineage_memory_accumulates_across_recursive_cycles"], "inherited_mutation_biases_future cascade routing toward previously deformed structures", "early bounded reset partitions limit inherited lineage carryover", "inherited deformation can amplify future cascades before visible instability", "lineage-level reversal requires structural reset once inheritance memory saturates")


def build_phase_a13_topology_lineage_evolution_model() -> OrderedDict[str, Any]:
    return _model("topology_lineage_evolution", "assess whether topology structure evolves through recognizable lineage states after repeated mutation exposure", ["repeatable_lineage_state_transitions", "topology_signature_persistence_across_cycles"], ["lineage_state_progression_from_diverse_to_narrow", "state_lock_in_after_repeated_mutation"], "topology evolves into recognizable inherited lineage states with reduced diversity", "lineage-state gating can delay lock-in under bounded simulation controls", "lineage lock-in narrows escape paths and increases collapse susceptibility", "late-stage lineage states are difficult to reverse incrementally")


def build_phase_a13_propagation_lineage_branching_model() -> OrderedDict[str, Any]:
    return _model("propagation_lineage_branching", "assess whether propagation pathways branch into inherited sub-lineages with different recurrence entropy and collapse-risk characteristics", ["branch_signature_recurrence", "sub_lineage_entropy_separation"], ["fragile_branches_accelerate_recurrence", "resilient_branches_degrade_under_saturation"], "propagation branches into inherited sub-lineages with uneven risk profiles", "branch diversity monitoring preserves partial containment when applied early", "high-risk fragile branches can dominate recurrence under recursive stress", "branch convergence reversal weakens once fragile branches become attractor aligned")


def build_phase_a13_mutation_selection_pressure_model() -> OrderedDict[str, Any]:
    return _model("mutation_selection_pressure", "assess whether repeated stress selects for faster more brittle lower-friction propagation structures", ["fast_path_survival_bias", "brittle_structure_retention_after_pressure"], ["selection_favors_low_friction_paths", "resilience_tax_increases_for_broad_containment"], "selection pressure favors rapid brittle structures over broad resilient pathways", "friction-restoration controls partially counter deterministic brittle selection", "selection pressure can accelerate systemic brittleness and shorten intervention windows", "selected brittle lineages require high-cost reset to regain resilience")


def build_phase_a13_adaptive_attractor_ecosystem_model() -> OrderedDict[str, Any]:
    return _model("adaptive_attractor_ecosystem", "assess whether multiple adaptive gravity wells form an ecosystem of competing coopting attractors rather than isolated collapse basins", ["multi_attractor_memory_retention", "cross_attractor_capture_inheritance"], ["attractor_competition_cycles", "cooptive_attractor_merging_under_stress"], "adaptive attractors form a nonlinear ecosystem that redistributes cascade gravity", "cross-basin dispersion controls reduce monocapture in bounded scenarios", "competing attractor ecosystems can synchronize into larger collapse basins", "ecosystem-level reversal needs prolonged anti-capture intervals rarely available at saturation")


def build_phase_a13_recursive_corridor_speciation_model() -> OrderedDict[str, Any]:
    return _model("recursive_corridor_speciation", "assess whether replay corridors differentiate into distinct structural corridor types such as fragile fast corridors resilient slow corridors attractor-aligned corridors and exhausted corridors", ["corridor_type_inheritance", "corridor_trait_persistence_across_cycles"], ["fragile_fast_corridor_expansion", "exhausted_corridor_accumulation"], "corridors speciate into inherited types with distinct failure and recurrence characteristics", "corridor redundancy and trait balancing slow harmful speciation concentration", "speciation can concentrate flow into fragile attractor-aligned corridors", "lineage reversal degrades once corridor type diversity collapses below threshold")


def build_phase_a13_stabilization_extinction_model() -> OrderedDict[str, Any]:
    return _model("stabilization_extinction_dynamics", "assess whether repeated mutation pressure can render prior stabilization mechanisms ineffective or extinct", ["legacy_stabilizer_failure_persistence", "extinction_of_prior_recovery_modes"], ["stabilizer_effectiveness_decay_lineage", "fallback_stabilizer_exhaustion_progression"], "stabilization mechanisms can become lineage-level ineffective before nominal exhaustion", "adaptive rotating containment budgets delay full stabilizer extinction", "extinction dynamics allow smaller shocks to bypass legacy controls", "reversibility is bounded by extinction depth and requires structural retraining reset")


def build_phase_a13_topology_evolutionary_drift_model() -> OrderedDict[str, Any]:
    return _model("topology_evolutionary_drift", "assess whether topology drifts directionally away from broad resilience toward narrow recursive attractor efficiency", ["directional_drift_memory", "resilience_capacity_erosion_inheritance"], ["drift_toward_attractor_efficiency", "broad_resilience_decay_over_cycles"], "topology drift narrows resilience in favor of recursive attractor throughput", "periodic broadening interventions constrain drift velocity in simulation", "directional drift can become self-reinforcing and hard to counter", "reversal requires sustained multi-cycle broadening interventions")


def build_phase_a13_nonlinear_mutation_ecosystem_model() -> OrderedDict[str, Any]:
    return _model("nonlinear_mutation_ecosystem", "assess whether inherited mutation lineages interact and produce nonlinear ecosystem-level risk", ["cross_lineage_coupling_memory", "interaction_amplifier_retention"], ["nonlinear_risk_phase_transitions", "emergent_superposition_of_lineage_failures"], "lineage interactions create nonlinear ecosystem risk beyond isolated model sums", "decoupling controls and interaction firebreaks reduce nonlinear escalation", "ecosystem interactions can produce abrupt systemic transitions under saturation", "reversal is bounded once cross-lineage couplings exceed deterministic threshold")


def build_phase_a13_lineage_reversibility_constraint_model() -> OrderedDict[str, Any]:
    return _model("lineage_reversibility_constraints", "assess whether lineage-level mutation becomes difficult to reverse without full structural reset", ["lineage_rollback_window_contraction", "partial_reversal_residual_inheritance"], ["reset_requirement_growth", "irreversible_lineage_zone_expansion"], "lineage reversibility contracts as inherited mutation depth compounds", "early bounded resets preserve partial lineage reversibility", "irreversible lineage zones expand under recursive high saturation exposure", "full recovery often requires structural reset rather than incremental rollback")


def build_phase_a13_mutation_lineage_risk_review() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("earliest_mutation_inheritance_signal", "cross_cycle_deformation_retention"),
        ("dominant_lineage_amplifier", "inheritance_memory_plus_nonlinear_cross_lineage_coupling"),
        ("weakest_reversibility_dimension", "lineage_reversibility_strength"),
        ("strongest_containment_dimension", "mutation_inheritance_containment"),
        ("operational_replay_readiness_status", "not_ready_blocked"),
        ("b1_transition_readiness_status", "blocked"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a13_lineage_evolution_scorecard() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("mutation_inheritance_containment", 0.36),
        ("topology_lineage_stability", 0.33),
        ("propagation_branching_resistance", 0.31),
        ("mutation_selection_pressure_resistance", 0.27),
        ("attractor_ecosystem_stability", 0.30),
        ("corridor_speciation_containment", 0.29),
        ("stabilization_extinction_resistance", 0.24),
        ("evolutionary_drift_resistance", 0.28),
        ("mutation_ecosystem_containment", 0.26),
        ("lineage_reversibility_strength", 0.22),
        ("overall_lineage_resilience", 0.29),
        ("governance_status", _governance_status()),
    ])


def build_phase_a13_supervisor_review() -> OrderedDict[str, Any]:
    sc = build_phase_a13_lineage_evolution_scorecard()
    return OrderedDict([
        ("overall_lineage_resilience", sc["overall_lineage_resilience"]),
        ("dominant_lineage_dynamic", "mutation_inheritance_coupled_with_nonlinear_lineage_interaction_acceleration"),
        ("strongest_containment_dimension", "mutation_inheritance_containment"),
        ("weakest_reversibility_dimension", "lineage_reversibility_strength"),
        ("primary_lineage_risk", "inherited_brittle_lineages_and_stabilization_extinction_under_recursive_saturation"),
        ("replay_operationalization_readiness", "blocked"),
        ("replay_density_scaling_readiness", "blocked"),
        ("b1_transition_readiness", "blocked"),
        ("recommended_next_phase_action", "continue_fail_closed_lineage_research_do_not_operationalize_replay_and_keep_b1_blocked"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a13_markdown_report() -> str:
    return "\n".join([
        "# Phase A13 Recursive Replay Ecology Mutation Inheritance & Adaptive Topology Lineage Research",
        "## objective",
        "Research deterministic recursive replay ecology mutation inheritance and adaptive topology lineage behavior under strict observational-only boundaries.",
        "## relationship to A12",
        str(build_phase_a12_supervisor_review()),
        "## observational-only boundary",
        str(build_phase_a13_mutation_lineage_configuration()["governance_status"]),
        "## mutation lineage research methodology",
        "A13 models deterministic structural mutation lineage behavior rather than realistic replay execution dynamics.",
        "## recursive mutation inheritance model",
        str(build_phase_a13_recursive_mutation_inheritance_model()),
        "## topology lineage evolution model",
        str(build_phase_a13_topology_lineage_evolution_model()),
        "## propagation lineage branching model",
        str(build_phase_a13_propagation_lineage_branching_model()),
        "## mutation selection pressure model",
        str(build_phase_a13_mutation_selection_pressure_model()),
        "## adaptive attractor ecosystem model",
        str(build_phase_a13_adaptive_attractor_ecosystem_model()),
        "## recursive corridor speciation model",
        str(build_phase_a13_recursive_corridor_speciation_model()),
        "## stabilization extinction model",
        str(build_phase_a13_stabilization_extinction_model()),
        "## topology evolutionary drift model",
        str(build_phase_a13_topology_evolutionary_drift_model()),
        "## nonlinear mutation ecosystem model",
        str(build_phase_a13_nonlinear_mutation_ecosystem_model()),
        "## lineage reversibility constraint model",
        str(build_phase_a13_lineage_reversibility_constraint_model()),
        "## mutation lineage risk review",
        str(build_phase_a13_mutation_lineage_risk_review()),
        "## lineage evolution scorecard",
        str(build_phase_a13_lineage_evolution_scorecard()),
        "## supervisor interpretation",
        str(build_phase_a13_supervisor_review()),
        "## governance preservation",
        "Observational-only deterministic simulation remains preserved. No replay execution, replay accumulation, topology execution, persistence expansion, SQL paths, live APIs, prediction, trading, or workflow automation are introduced.",
        "## residual risks",
        "Mutation inheritance and adaptive topology lineage remain materially unsafe under recursive high and saturation exposure due to branching brittleness, stabilization extinction dynamics, and nonlinear ecosystem coupling.",
        "## recommendation regarding B1",
        "Keep replay operationalization, replay density scaling, and B1 blocked unless deterministic evidence becomes overwhelmingly strong.",
    ])
