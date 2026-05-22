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
