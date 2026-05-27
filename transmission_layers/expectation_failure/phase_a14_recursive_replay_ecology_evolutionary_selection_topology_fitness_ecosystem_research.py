from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import certify_phase_a_observational_expansion_boundary
from .phase_a13_recursive_replay_ecology_mutation_inheritance_adaptive_topology_lineage_research import build_phase_a13_supervisor_review

BASE_INPUTS = ["phase_a13_supervisor_review", "phase_a14_fitness_ecosystem_configuration", "a_series_governance_boundary"]


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


def _model(name: str, objective: str, fitness_signals: list[str], evolution_signals: list[str], selection_effect: str, containment_effect: str, ecosystem_risk: str, reversibility_constraint: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("model_name", name),
        ("research_objective", objective),
        ("deterministic_inputs_used", BASE_INPUTS),
        ("fitness_signals", fitness_signals),
        ("ecosystem_evolution_signals", evolution_signals),
        ("selection_effect", selection_effect),
        ("containment_effect", containment_effect),
        ("ecosystem_risk", ecosystem_risk),
        ("reversibility_constraint", reversibility_constraint),
        ("governance_status", _governance_status()),
    ])


def build_phase_a14_fitness_ecosystem_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A14"),
        ("mode", "recursive_replay_ecology_evolutionary_selection_topology_fitness_ecosystem_research"),
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


def build_phase_a14_topology_fitness_selection_model() -> OrderedDict[str, Any]:
    return _model("topology_fitness_selection", "assess whether recursive replay ecology selects structurally fit topologies favoring fast low-friction attractor-aligned and less reversible structures", ["low_friction_path_survival_bias", "high_velocity_topology_retention"], ["recursive_pressure_selects_fast_structures", "attractor_alignment_compounds_selection"], "selection tilts topology toward brittle efficient propagation structures", "bounded friction reintroduction slows but does not eliminate brittle fitness selection", "fitness selection can compress resilience buffers and shorten intervention windows", "selected topology fitness states become difficult to unwind without structural reset")


def build_phase_a14_lineage_survival_competition_model() -> OrderedDict[str, Any]:
    return _model("lineage_survival_competition", "assess whether inherited topology lineages compete for dominance and whether brittle high-velocity lineages outcompete resilient slower lineages under stress", ["dominance_share_shift_toward_fast_lineages", "resilience_tax_for_slower_lineages"], ["stress_accelerates_brittle_lineage_share", "resilient_lineage_displacement_under_saturation"], "competitive selection favors brittle lineages during recursive stress windows", "lineage diversity quotas preserve partial balance in bounded simulation", "lineage monoculture risk increases collapse susceptibility", "reversing lineage dominance requires prolonged multi-cycle rebalance intervals")


def build_phase_a14_recursive_extinction_replacement_model() -> OrderedDict[str, Any]:
    return _model("recursive_extinction_replacement", "assess whether topology lineages corridors or stabilizers become extinct and are replaced by faster or more attractor-efficient structures", ["legacy_lineage_extinction_frequency", "replacement_velocity_by_attractor_efficiency"], ["extinction_of_slow_corridors", "replacement_by_fast_attractor_aligned_structures"], "extinction-replacement dynamics prune slower resilient structures", "early extinction threshold alarms provide bounded containment lead-time", "replacement cascades can remove fallback structures before detection", "extinct topology functions generally require reset-based reintroduction")


def build_phase_a14_adaptive_mutation_reproduction_model() -> OrderedDict[str, Any]:
    return _model("adaptive_mutation_reproduction", "assess whether successful topology mutations reproduce across related corridors and inherited sub-lineages", ["mutation_replication_rate_across_corridors", "sub_lineage_trait_transfer_success"], ["fit_mutations_propagate_between_adjacent_lineages", "reproduction_bias_strengthens_shared_brittleness"], "successful mutations replicate and amplify common structural biases", "replication throttles constrain deterministic spread under bounded controls", "cross-corridor mutation reproduction can synchronize fragility", "reversibility weakens as replicated mutation depth increases across sub-lineages")


def build_phase_a14_attractor_predation_ecosystem_model() -> OrderedDict[str, Any]:
    return _model("attractor_predation_ecosystem", "assess whether adaptive gravity wells act as predatory attractors consuming weaker corridors lineages or basins", ["weaker_corridor_capture_rate", "predatory_attractor_absorption_depth"], ["multi_attractor_predation_cycles", "basin_absorption_concentration_growth"], "predatory attractors absorb weaker pathways and centralize cascade gravity", "cross-basin dispersion firebreaks limit monocapture concentration", "predation ecosystems can create abrupt systemic capture regimes", "reversal requires sustained deconcentration windows rarely stable at saturation")


def build_phase_a14_stabilization_fitness_collapse_model() -> OrderedDict[str, Any]:
    return _model("stabilization_fitness_collapse", "assess whether stabilization mechanisms lose fitness against evolved topology lineages and become structurally obsolete", ["stabilizer_fitness_decay_rate", "legacy_control_obsolescence_frequency"], ["stabilizer_displacement_by_evolved_lineages", "structural_obsolescence_acceleration"], "stabilization mechanisms lose relative fitness and fail earlier against evolved topology", "rotating bounded stabilizer refresh delays full collapse", "stabilization fitness collapse exposes system to smaller recursive shocks", "recovery often requires structural reset rather than incremental stabilizer tuning")


def build_phase_a14_topology_ecological_succession_model() -> OrderedDict[str, Any]:
    return _model("topology_ecological_succession", "assess whether replay ecology transitions through deterministic succession stages from diversity to selected corridors to attractor dominance and collapse-prone ecology", ["succession_stage_transition_repeatability", "diversity_to_dominance_transition_speed"], ["diverse_topology_to_selected_corridors", "attractor_dominance_to_collapse_prone_state"], "succession narrows ecosystem diversity into higher-risk dominant structures", "stage-gating and diversity preservation rules slow succession convergence", "late-stage succession elevates synchronized failure probability", "late succession states are only partially reversible without broad reset")


def build_phase_a14_recursive_ecosystem_collapse_rebirth_model() -> OrderedDict[str, Any]:
    return _model("recursive_ecosystem_collapse_rebirth", "assess whether collapse resets generate new topology ecosystems that inherit mutation bias and repeat selection cycles", ["post_collapse_bias_retention", "cycle_repetition_similarity"], ["collapse_rebirth_cycle_recurrence", "bias_carryover_into_rebirth_ecosystems"], "rebirth ecosystems reinstantiate prior selection bias and repeat risk cycles", "bounded reset partitions reduce but do not remove inherited rebirth bias", "collapse-rebirth recurrence can normalize unsafe topology traits", "durable reversal needs deep reset plus anti-bias rebuilding windows")


def build_phase_a14_nonlinear_topology_evolutionary_pressure_model() -> OrderedDict[str, Any]:
    return _model("nonlinear_topology_evolutionary_pressure", "assess whether topology evolutionary pressure becomes nonlinear under recursive saturation creating abrupt fitness regime shifts", ["pressure_gradient_convexity", "regime_shift_trigger_density"], ["saturation_induced_phase_transitions", "abrupt_fitness_regime_reordering"], "nonlinear pressure triggers abrupt topology selection regime shifts", "interaction decoupling and pressure ceilings dampen shift amplitude", "abrupt regime shifts can bypass linear containment assumptions", "once shift thresholds are crossed incremental rollback has bounded efficacy")


def build_phase_a14_fitness_reversibility_constraint_model() -> OrderedDict[str, Any]:
    return _model("fitness_reversibility_constraints", "assess whether fitness-selected topology structures become hard to reverse without full structural reset", ["rollback_window_contraction_rate", "partial_reversal_residual_fitness"], ["irreversible_zone_growth_under_selection", "reset_dependency_increase"], "fitness selection contracts reversibility and strengthens structural lock-in", "early bounded resets preserve partial reversibility windows", "lock-in can propagate irreversibility across topology ecosystems", "full restoration frequently requires structural reset and extended de-selection")


def build_phase_a14_fitness_ecosystem_risk_review() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("earliest_fitness_selection_signal", "low_friction_path_survival_bias"),
        ("dominant_evolutionary_amplifier", "nonlinear_pressure_coupled_with_attractor_predation"),
        ("weakest_reversibility_dimension", "fitness_reversibility_strength"),
        ("strongest_containment_dimension", "topology_fitness_selection_containment"),
        ("operational_replay_readiness_status", "not_ready_blocked"),
        ("b1_transition_readiness_status", "blocked"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a14_topology_fitness_scorecard() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("topology_fitness_selection_containment", 0.31),
        ("lineage_survival_balance", 0.28),
        ("extinction_replacement_resistance", 0.24),
        ("mutation_reproduction_resistance", 0.27),
        ("attractor_predation_resistance", 0.23),
        ("stabilization_fitness_resilience", 0.21),
        ("ecological_succession_containment", 0.26),
        ("collapse_rebirth_cycle_resistance", 0.25),
        ("nonlinear_evolutionary_pressure_resistance", 0.20),
        ("fitness_reversibility_strength", 0.19),
        ("overall_topology_fitness_resilience", 0.24),
        ("governance_status", _governance_status()),
    ])


def build_phase_a14_supervisor_review() -> OrderedDict[str, Any]:
    sc = build_phase_a14_topology_fitness_scorecard()
    return OrderedDict([
        ("overall_topology_fitness_resilience", sc["overall_topology_fitness_resilience"]),
        ("dominant_evolutionary_dynamic", "topology_fitness_selection_accelerated_by_nonlinear_pressure_and_attractor_predation"),
        ("strongest_containment_dimension", "topology_fitness_selection_containment"),
        ("weakest_reversibility_dimension", "fitness_reversibility_strength"),
        ("primary_fitness_ecosystem_risk", "selection_for_fast_brittle_topologies_with_stabilization_fitness_collapse_under_saturation"),
        ("replay_operationalization_readiness", "blocked"),
        ("replay_density_scaling_readiness", "blocked"),
        ("b1_transition_readiness", "blocked"),
        ("recommended_next_phase_action", "continue_fail_closed_fitness_ecosystem_research_keep_replay_operationalization_and_b1_blocked"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a14_markdown_report() -> str:
    return "\n".join([
        "## objective",
        "Research deterministic recursive replay ecology evolutionary selection and topology fitness ecosystem behavior under strict observational-only boundaries.",
        "## relationship to A13",
        str(build_phase_a13_supervisor_review()),
        "## observational-only boundary",
        str(build_phase_a14_fitness_ecosystem_configuration()["governance_status"]),
        "## topology fitness research methodology",
        "A14 models deterministic structural topology fitness behavior rather than realistic replay execution dynamics.",
        "## topology fitness selection model",
        str(build_phase_a14_topology_fitness_selection_model()),
        "## lineage survival competition model",
        str(build_phase_a14_lineage_survival_competition_model()),
        "## recursive extinction replacement model",
        str(build_phase_a14_recursive_extinction_replacement_model()),
        "## adaptive mutation reproduction model",
        str(build_phase_a14_adaptive_mutation_reproduction_model()),
        "## attractor predation ecosystem model",
        str(build_phase_a14_attractor_predation_ecosystem_model()),
        "## stabilization fitness collapse model",
        str(build_phase_a14_stabilization_fitness_collapse_model()),
        "## topology ecological succession model",
        str(build_phase_a14_topology_ecological_succession_model()),
        "## recursive ecosystem collapse rebirth model",
        str(build_phase_a14_recursive_ecosystem_collapse_rebirth_model()),
        "## nonlinear topology evolutionary pressure model",
        str(build_phase_a14_nonlinear_topology_evolutionary_pressure_model()),
        "## fitness reversibility constraint model",
        str(build_phase_a14_fitness_reversibility_constraint_model()),
        "## fitness ecosystem risk review",
        str(build_phase_a14_fitness_ecosystem_risk_review()),
        "## topology fitness scorecard",
        str(build_phase_a14_topology_fitness_scorecard()),
        "## supervisor interpretation",
        str(build_phase_a14_supervisor_review()),
        "## governance preservation",
        "Observational-only deterministic simulation remains preserved. No replay execution, replay accumulation, topology activation, persistence expansion, SQL paths, live APIs, prediction, trading, or workflow automation are introduced.",
        "## residual risks",
        "Evolutionary selection can favor fast brittle attractor-aligned topology structures while stabilization fitness collapses, leaving recursive saturation scenarios materially unsafe.",
        "## recommendation regarding B1",
        "Keep replay operationalization, replay density scaling, and B1 blocked unless deterministic evidence becomes overwhelmingly strong.",
    ])
