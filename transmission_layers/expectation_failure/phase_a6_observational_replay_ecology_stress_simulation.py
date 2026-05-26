from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import certify_phase_a_observational_expansion_boundary
from .phase_a5_anti_recurrence_ecology_stabilization import (
    build_phase_a5_entropy_preservation_guardrails,
    build_phase_a5_novelty_preservation_guardrails,
    build_phase_a5_recurrence_suppression_guardrails,
    build_phase_a5_replay_survivability_stabilization_review,
)


def _bounded(v: float) -> float:
    return round(max(0.0, min(1.0, v)), 6)


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


def _density_bands() -> list[tuple[str, float]]:
    return [("low_density", 0.2), ("moderate_density", 0.4), ("elevated_density", 0.6), ("high_density", 0.8), ("saturation_risk_density", 1.0)]


def _simulation(name: str, band: str, sev: float, effects: OrderedDict[str, float], survivability: float, risk: str, guidance: list[str]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("simulation_name", name),
        ("deterministic_inputs_used", ["phase_a5_guardrails", "phase_a5_survivability_review", "density_band_severity", f"severity_{sev}"]),
        ("simulated_density_band", band),
        ("simulated_pressure_effects", effects),
        ("survivability_effect", _bounded(survivability)),
        ("collapse_risk_band", risk),
        ("mitigation_guidance", guidance),
        ("governance_status", _governance_status()),
    ])


def build_phase_a6_stress_simulation_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A6"),
        ("mode", "deterministic_observational_replay_ecology_stress_simulation"),
        ("observational_only", True),
        ("deterministic", True),
        ("bounded", True),
        ("metadata_derived", True),
        ("simulation_only", True),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
        ("governance_status", _governance_status()),
    ])


def build_phase_a6_density_escalation_scenarios() -> list[OrderedDict[str, Any]]:
    out = []
    for band, sev in _density_bands():
        effects = OrderedDict([
            ("replay_recurrence_acceleration", _bounded(0.2 + 0.7 * sev)),
            ("replay_overlap_amplification", _bounded(0.18 + 0.72 * sev)),
            ("entropy_compression", _bounded(0.16 + 0.74 * sev)),
            ("topology_survivability_degradation", _bounded(0.15 + 0.75 * sev)),
            ("contradiction_survivability_degradation", _bounded(0.14 + 0.76 * sev)),
            ("semantic_crowding_escalation", _bounded(0.22 + 0.68 * sev)),
            ("novelty_decay_acceleration", _bounded(0.2 + 0.7 * sev)),
            ("recurrence_cascade_emergence", _bounded(0.1 + 0.82 * sev)),
        ])
        out.append(_simulation("density_escalation", band, sev, effects, 1 - (sum(effects.values()) / len(effects)), "high" if sev >= 0.8 else ("moderate" if sev >= 0.4 else "low"), ["apply_a5_guardrails_preemptively", "maintain_observational_boundary", "defer_operational_replay_activation"]))
    return out


def _single_sim(name: str, factors: list[tuple[str, float]]) -> list[OrderedDict[str, Any]]:
    sims = []
    for band, sev in _density_bands():
        effects = OrderedDict([(k, _bounded(base + sev * (1 - base) * 0.9)) for k, base in factors])
        sv = 1 - (sum(effects.values()) / len(effects))
        risk = "collapse_risk" if sev >= 0.8 and sv < 0.3 else ("elevated" if sev >= 0.6 else "contained")
        sims.append(_simulation(name, band, sev, effects, sv, risk, ["prioritize_decompression_and_diversification", "tighten_entropy_novelty_guardrails", "keep_replay_and_topology_non_operational"]))
    return sims


def build_phase_a6_topology_stress_propagation_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("topology_stress_propagation", [("topology_stress_propagation_pathways", 0.22), ("gravity_well_amplification", 0.25), ("replay_corridor_overload", 0.2), ("bridge_node_stress_concentration", 0.24), ("topology_survivability_under_reuse", 0.26)])


def build_phase_a6_entropy_degradation_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("entropy_degradation", [("topology_entropy_degradation", 0.2), ("contradiction_entropy_degradation", 0.19), ("propagation_diversity_degradation", 0.21), ("structural_balance_deterioration", 0.2), ("monoculture_acceleration", 0.24)])


def build_phase_a6_recurrence_cascade_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("recurrence_cascade", [("replay_recurrence_cascade_emergence", 0.2), ("replay_lock_in_escalation", 0.23), ("corridor_reuse_amplification", 0.22), ("contradiction_recycling_acceleration", 0.2), ("recurrence_persistence_escalation", 0.24)])


def build_phase_a6_replay_overlap_amplification_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("replay_overlap_amplification", [("overlap_acceleration", 0.23), ("replay_corridor_convergence", 0.21), ("topology_overlap_clustering", 0.22), ("replay_pathway_compression", 0.2)])


def build_phase_a6_semantic_crowding_escalation_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("semantic_crowding_escalation", [("semantic_compression", 0.24), ("domain_crowding", 0.2), ("narrative_gravity", 0.25), ("replay_motif_reuse", 0.23), ("thematic_over_concentration", 0.22)])


def build_phase_a6_structural_redundancy_escalation_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("structural_redundancy_escalation", [("topology_duplication_pressure", 0.24), ("replay_structure_recycling", 0.22), ("propagation_redundancy", 0.21), ("redundancy_induced_survivability_decay", 0.25)])


def build_phase_a6_weak_node_amplification_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("weak_node_amplification", [("fragile_node_survivability", 0.22), ("weak_node_propagation_instability", 0.21), ("weak_node_recurrence_spillover", 0.23), ("bridge_fragility", 0.24)])


def build_phase_a6_novelty_decay_stress_simulation() -> list[OrderedDict[str, Any]]:
    return _single_sim("novelty_decay_stress", [("marginal_information_gain_decay", 0.22), ("replay_novelty_exhaustion", 0.24), ("contradiction_novelty_decay", 0.23), ("replay_ecology_freshness_degradation", 0.2)])


def build_phase_a6_survivability_threshold_analysis() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("recurrence_resistance_collapse_threshold", "high_density"),
        ("topology_survivability_instability_threshold", "elevated_density"),
        ("structurally_dangerous_replay_overlap_threshold", "high_density"),
        ("entropy_preservation_failure_threshold", "elevated_density"),
        ("severe_semantic_crowding_threshold", "saturation_risk_density"),
        ("collapse_risk_regime_entry_threshold", "high_density"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a6_decompression_effectiveness_review() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("elevated_density_effectiveness", "partial_effective_requires_tighter_guardrails"),
        ("saturation_risk_density_effectiveness", "insufficient_without_phase_a7_hardening"),
        ("replay_corridor_overload_effectiveness", "decompression_helps_but_fragile"),
        ("high_overlap_regime_effectiveness", "limited_under_compounding_recurrence"),
        ("source_guardrails", [build_phase_a5_recurrence_suppression_guardrails(), build_phase_a5_entropy_preservation_guardrails(), build_phase_a5_novelty_preservation_guardrails()]),
        ("governance_status", _governance_status()),
    ])


def build_phase_a6_ecology_collapse_threshold_review() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("earliest_observed_collapse_risk_regime", "high_density"),
        ("dominant_collapse_driver", "replay_recurrence_and_overlap_coupling"),
        ("weakest_survivability_dimension", "recurrence_resistance"),
        ("most_resilient_dimension", "weak_node_resilience"),
        ("stabilization_sufficiency_assessment", "a5_stabilization_is_directionally_helpful_but_not_sufficient_for_saturation_regimes"),
        ("operational_replay_readiness_status", "blocked_fail_closed"),
        ("governance_status", _governance_status()),
    ])


def build_phase_a6_supervisor_review() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("overall_ecology_stability", "conditionally_stable_at_low_to_moderate_density_unstable_at_high_density"),
        ("highest_stress_risk", "recurrence_cascade_overlap_amplification"),
        ("earliest_destabilization_signal", "entropy_degradation_at_elevated_density"),
        ("replay_operationalization_readiness", "not_ready"),
        ("replay_density_scaling_readiness", "not_ready"),
        ("residual_risks", ["topology_survivability_decay", "semantic_crowding_escalation", "novelty_decay_acceleration", "bridge_node_stress_concentration"]),
        ("recommended_next_phase_action", "proceed_to_phase_a7_stabilization_hardening_and_keep_b1_blocked"),
        ("survivability_context", build_phase_a5_replay_survivability_stabilization_review()),
        ("governance_status", _governance_status()),
    ])


def build_phase_a6_markdown_report() -> str:
    return "\n".join([
        "# Phase A6 Observational Replay Ecology Stress Simulation",
        "## objective",
        "Stress-test replay ecology behavior under deterministic density escalation while preserving observational-only governance.",
        "## relationship to A5",
        str(build_phase_a5_replay_survivability_stabilization_review()),
        "## observational-only boundary",
        str(build_phase_a6_stress_simulation_configuration()["governance_status"]),
        "## simulation methodology",
        "Deterministic pure functions apply bounded density severity bands to metadata-derived pressure dimensions from A5 guardrail/survivability outputs. A6 models deterministic structural pressure behavior rather than realistic replay execution dynamics; it is not predictive or operational simulation.",
        "## density escalation scenarios",
        str(build_phase_a6_density_escalation_scenarios()),
        "## topology stress propagation simulation",
        str(build_phase_a6_topology_stress_propagation_simulation()),
        "## entropy degradation simulation",
        str(build_phase_a6_entropy_degradation_simulation()),
        "## recurrence cascade simulation",
        str(build_phase_a6_recurrence_cascade_simulation()),
        "## replay overlap amplification simulation",
        str(build_phase_a6_replay_overlap_amplification_simulation()),
        "## semantic crowding escalation simulation",
        str(build_phase_a6_semantic_crowding_escalation_simulation()),
        "## structural redundancy escalation simulation",
        str(build_phase_a6_structural_redundancy_escalation_simulation()),
        "## weak-node amplification simulation",
        str(build_phase_a6_weak_node_amplification_simulation()),
        "## novelty decay stress simulation",
        str(build_phase_a6_novelty_decay_stress_simulation()),
        "## survivability threshold analysis",
        str(build_phase_a6_survivability_threshold_analysis()),
        "## decompression effectiveness review",
        str(build_phase_a6_decompression_effectiveness_review()),
        "## ecology collapse threshold review",
        str(build_phase_a6_ecology_collapse_threshold_review()),
        "## supervisor recommendation",
        str(build_phase_a6_supervisor_review()),
        "## governance preservation",
        "Observational-only deterministic simulation is preserved. Replay/topology activation and all write, SQL, predictive, and trading paths remain disabled.",
        "## residual risks",
        "High-density and saturation-risk regimes display recurrence and overlap coupling that can degrade entropy and survivability.",
        "## recommendation for Phase A7 or B1",
        "Fail closed: prioritize Phase A7 stabilization hardening; keep B1 operational transition blocked.",
    ])
