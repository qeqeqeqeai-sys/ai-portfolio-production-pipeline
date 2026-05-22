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
]
