"""Expectation Failure deterministic contracts and Phase A2/A3 scoring modules."""

from .phase_a1_contracts import (
    build_expectation_failure_evidence_schema,
    build_expectation_failure_explanation_templates,
    build_expectation_failure_invariant_flags,
    build_expectation_failure_score_contracts,
    build_phase_a1_expectation_failure_contract_report,
)

from .phase_a2_valuation_stretch import (
    build_phase_a2_valuation_stretch_report,
    build_valuation_stretch_evidence_summary,
    build_valuation_stretch_subcomponent_contract,
    build_valuation_stretch_thresholds,
    score_valuation_stretch,
)

from .phase_a3_fundamental_support import (
    build_fundamental_support_evidence_summary,
    build_fundamental_support_subcomponent_contract,
    build_fundamental_support_thresholds,
    build_phase_a3_fundamental_support_report,
    score_fundamental_support,
)

from .phase_a4_narrative_saturation import (
    build_narrative_saturation_evidence_summary,
    build_narrative_saturation_subcomponent_contract,
    build_narrative_saturation_thresholds,
    build_phase_a4_narrative_saturation_report,
    score_narrative_saturation,
)


from .phase_a5_certainty_fragility import (
    build_certainty_fragility_evidence_summary,
    build_certainty_fragility_subcomponent_contract,
    build_certainty_fragility_thresholds,
    build_phase_a5_certainty_fragility_report,
    score_certainty_fragility,
)

__all__ = [
    "build_expectation_failure_score_contracts",
    "build_expectation_failure_evidence_schema",
    "build_expectation_failure_explanation_templates",
    "build_expectation_failure_invariant_flags",
    "build_phase_a1_expectation_failure_contract_report",
    "score_valuation_stretch",
    "build_valuation_stretch_thresholds",
    "build_valuation_stretch_subcomponent_contract",
    "build_valuation_stretch_evidence_summary",
    "build_phase_a2_valuation_stretch_report",
    "score_fundamental_support",
    "build_fundamental_support_thresholds",
    "build_fundamental_support_subcomponent_contract",
    "build_fundamental_support_evidence_summary",
    "build_phase_a3_fundamental_support_report",
    "score_narrative_saturation",
    "build_narrative_saturation_thresholds",
    "build_narrative_saturation_subcomponent_contract",
    "build_narrative_saturation_evidence_summary",
    "build_phase_a4_narrative_saturation_report",
    "score_certainty_fragility",
    "build_certainty_fragility_thresholds",
    "build_certainty_fragility_subcomponent_contract",
    "build_certainty_fragility_evidence_summary",
    "build_phase_a5_certainty_fragility_report",
    "score_structural_weakness",
    "build_structural_weakness_thresholds",
    "build_structural_weakness_subcomponent_contract",
    "build_structural_weakness_evidence_summary",
    "build_phase_a6_structural_weakness_report",
    "score_ai_expectation_failure",
    "build_ai_expectation_failure_thresholds",
    "build_ai_expectation_failure_component_contract",
    "build_ai_expectation_failure_interaction_rules",
    "build_ai_expectation_failure_evidence_summary",
    "build_phase_a7_ai_expectation_failure_report",
]



from .phase_a6_structural_weakness import (
    build_phase_a6_structural_weakness_report,
    build_structural_weakness_evidence_summary,
    build_structural_weakness_subcomponent_contract,
    build_structural_weakness_thresholds,
    score_structural_weakness,
)

from .phase_a7_ai_expectation_failure import (
    build_ai_expectation_failure_component_contract,
    build_ai_expectation_failure_evidence_summary,
    build_ai_expectation_failure_interaction_rules,
    build_ai_expectation_failure_thresholds,
    build_phase_a7_ai_expectation_failure_report,
    score_ai_expectation_failure,
)
from .phase_b1_expectation_failure_heatmap import (
    build_expectation_failure_heatmap,
    build_fragility_cluster_summary,
    build_heatmap_evidence_summary,
    build_phase_b1_heatmap_report,
    build_relative_fragility_ranking,
)

__all__.extend([
    "build_expectation_failure_heatmap",
    "build_relative_fragility_ranking",
    "build_fragility_cluster_summary",
    "build_heatmap_evidence_summary",
    "build_phase_b1_heatmap_report",
])


from .phase_b2_asymmetry_interpretation import (
    build_b2_evidence_chain,
    build_cluster_asymmetry_summary,
    build_downside_asymmetry_classification,
    build_expectation_support_mismatch,
    build_long_risk_fragility_interpretation,
    build_phase_b2_asymmetry_report,
    build_ranking_asymmetry_interpretation,
    build_relative_resilience_interpretation,
    build_subsector_asymmetry_summary,
)

__all__.extend([
    "build_downside_asymmetry_classification",
    "build_long_risk_fragility_interpretation",
    "build_expectation_support_mismatch",
    "build_relative_resilience_interpretation",
    "build_ranking_asymmetry_interpretation",
    "build_cluster_asymmetry_summary",
    "build_subsector_asymmetry_summary",
    "build_b2_evidence_chain",
    "build_phase_b2_asymmetry_report",
])

from .phase_b3_benchmark_relative_fragility import (
    build_b3_evidence_chain,
    build_benchmark_context_summary,
    build_benchmark_relative_fragility_label,
    build_benchmark_relative_resilience_interpretation,
    build_peer_relative_fragility_interpretation,
    build_phase_b3_benchmark_relative_report,
    build_relative_fragility_delta,
    build_subsector_relative_fragility_interpretation,
    build_universe_relative_fragility_interpretation,
)

__all__.extend([
    "build_benchmark_context_summary",
    "build_relative_fragility_delta",
    "build_benchmark_relative_fragility_label",
    "build_peer_relative_fragility_interpretation",
    "build_subsector_relative_fragility_interpretation",
    "build_universe_relative_fragility_interpretation",
    "build_benchmark_relative_resilience_interpretation",
    "build_b3_evidence_chain",
    "build_phase_b3_benchmark_relative_report",
])

from .phase_b4_historical_fragility_replay import (
    build_b4_evidence_chain,
    build_entity_replay_interpretation,
    build_fragility_change_delta,
    build_fragility_change_label,
    build_historical_deterioration_interpretation,
    build_historical_improvement_interpretation,
    build_historical_snapshot_summary,
    build_historical_stability_interpretation,
    build_phase_b4_historical_replay_report,
    build_subsector_replay_interpretation,
    build_universe_replay_interpretation,
)

__all__.extend([
    "build_historical_snapshot_summary",
    "build_fragility_change_delta",
    "build_fragility_change_label",
    "build_historical_deterioration_interpretation",
    "build_historical_improvement_interpretation",
    "build_historical_stability_interpretation",
    "build_entity_replay_interpretation",
    "build_subsector_replay_interpretation",
    "build_universe_replay_interpretation",
    "build_b4_evidence_chain",
    "build_phase_b4_historical_replay_report",
])

from .phase_b5_deterioration_alert_interpretation import (
    build_alert_escalation_interpretation,
    build_alert_reason_classification,
    build_alert_severity_label,
    build_alert_trigger_evidence,
    build_b5_evidence_chain,
    build_deterioration_alert_state,
    build_entity_alert_interpretation,
    build_phase_b5_alert_interpretation_report,
    build_subsector_alert_interpretation,
    build_universe_alert_interpretation,
)

__all__.extend([
    "build_alert_trigger_evidence",
    "build_deterioration_alert_state",
    "build_alert_severity_label",
    "build_alert_reason_classification",
    "build_alert_escalation_interpretation",
    "build_entity_alert_interpretation",
    "build_subsector_alert_interpretation",
    "build_universe_alert_interpretation",
    "build_b5_evidence_chain",
    "build_phase_b5_alert_interpretation_report",
])

from .phase_b6_institutional_reporting import (
    build_alert_briefing_section,
    build_asymmetry_briefing_section,
    build_b6_report_context,
    build_benchmark_relative_briefing_section,
    build_entity_briefing_cards,
    build_evidence_appendix,
    build_executive_fragility_summary,
    build_heatmap_briefing_section,
    build_historical_replay_briefing_section,
    build_key_fragility_findings,
    build_limitations_and_disclosures,
    build_phase_b6_institutional_report,
    build_subsector_briefing_cards,
)

__all__.extend([
    "build_b6_report_context",
    "build_executive_fragility_summary",
    "build_key_fragility_findings",
    "build_heatmap_briefing_section",
    "build_asymmetry_briefing_section",
    "build_benchmark_relative_briefing_section",
    "build_historical_replay_briefing_section",
    "build_alert_briefing_section",
    "build_entity_briefing_cards",
    "build_subsector_briefing_cards",
    "build_evidence_appendix",
    "build_limitations_and_disclosures",
    "build_phase_b6_institutional_report",
])


from .phase_b7_system_certification import (
    build_additive_integration_certification,
    build_architecture_constraint_certification,
    build_determinism_certification,
    build_exclusion_preservation_certification,
    build_expectation_failure_subsystem_summary,
    build_explainability_certification,
    build_phase_b7_system_certification_report,
    build_phase_inventory_summary,
    build_public_api_inventory,
    build_replayability_certification,
)

__all__.extend([
    "build_phase_inventory_summary",
    "build_architecture_constraint_certification",
    "build_determinism_certification",
    "build_replayability_certification",
    "build_explainability_certification",
    "build_additive_integration_certification",
    "build_exclusion_preservation_certification",
    "build_public_api_inventory",
    "build_expectation_failure_subsystem_summary",
    "build_phase_b7_system_certification_report",
])

from .dashboard_operationalization import (
    build_dashboard_alert_facts,
    build_dashboard_benchmark_facts,
    build_dashboard_entity_facts,
    build_dashboard_evidence_facts,
    build_dashboard_export_manifest,
    build_dashboard_o1_export_payload,
    build_dashboard_replay_facts,
    build_dashboard_report_metadata,
    build_dashboard_subsector_facts,
)

__all__.extend([
    "build_dashboard_entity_facts",
    "build_dashboard_subsector_facts",
    "build_dashboard_alert_facts",
    "build_dashboard_replay_facts",
    "build_dashboard_benchmark_facts",
    "build_dashboard_evidence_facts",
    "build_dashboard_report_metadata",
    "build_dashboard_export_manifest",
    "build_dashboard_o1_export_payload",
])

from .path2a_cohort_registry_foundation import (
    BLOCKED_COHORT_REGISTRY,
    CERTIFIED_COHORT_REGISTRY,
    DEGRADED_COHORT_REGISTRY,
    build_benchmark_mapping_registry,
    build_cohort_explainability_metadata,
    build_cohort_manifest,
    build_cohort_registry_contracts,
    build_path2a_cohort_registry_report,
    certify_cohort_registry,
    resolve_cohort_membership,
    validate_cohort_integrity,
)

__all__.extend([
    "build_cohort_registry_contracts",
    "build_cohort_manifest",
    "resolve_cohort_membership",
    "build_benchmark_mapping_registry",
    "validate_cohort_integrity",
    "build_cohort_explainability_metadata",
    "certify_cohort_registry",
    "build_path2a_cohort_registry_report",
    "CERTIFIED_COHORT_REGISTRY",
    "DEGRADED_COHORT_REGISTRY",
    "BLOCKED_COHORT_REGISTRY",
])

from .path2b_relative_fragility_scoring import (
    BLOCKED_RELATIVE_FRAGILITY,
    CERTIFIED_RELATIVE_FRAGILITY,
    DEGRADED_RELATIVE_FRAGILITY,
    build_cohort_relative_baselines,
    build_path2b_relative_fragility_report,
    build_relative_deterioration_velocity_comparison,
    build_relative_fragility_driver_summary,
    build_relative_fragility_input_contract,
    build_relative_fragility_score,
    build_relative_persistence_weakness_comparison,
    certify_relative_fragility_scoring,
    compare_peer_fragility_distribution,
)

__all__.extend([
    "build_relative_fragility_input_contract",
    "build_cohort_relative_baselines",
    "compare_peer_fragility_distribution",
    "build_relative_fragility_score",
    "build_relative_deterioration_velocity_comparison",
    "build_relative_persistence_weakness_comparison",
    "build_relative_fragility_driver_summary",
    "certify_relative_fragility_scoring",
    "build_path2b_relative_fragility_report",
    "CERTIFIED_RELATIVE_FRAGILITY",
    "DEGRADED_RELATIVE_FRAGILITY",
    "BLOCKED_RELATIVE_FRAGILITY",
])

from .path2c_percentile_ranking_engine import (
    BLOCKED_RELATIVE_RANKING,
    CERTIFIED_RELATIVE_RANKING,
    DEGRADED_RELATIVE_RANKING,
    assign_percentile_ranking_tiers,
    build_deterministic_cohort_ranking,
    build_path2c_percentile_ranking_report,
    build_percentile_ranking_input_contract,
    build_ranking_explanation_summary,
    calculate_cohort_percentiles,
    certify_percentile_ranking_engine,
    resolve_relative_ranking_ties,
)

__all__.extend([
    "CERTIFIED_RELATIVE_RANKING",
    "DEGRADED_RELATIVE_RANKING",
    "BLOCKED_RELATIVE_RANKING",
    "build_percentile_ranking_input_contract",
    "build_deterministic_cohort_ranking",
    "resolve_relative_ranking_ties",
    "calculate_cohort_percentiles",
    "assign_percentile_ranking_tiers",
    "build_ranking_explanation_summary",
    "certify_percentile_ranking_engine",
    "build_path2c_percentile_ranking_report",
])
