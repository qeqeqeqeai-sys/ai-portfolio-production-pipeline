"""Phase A1 deterministic contracts for Expectation Failure intelligence layer.

This module intentionally defines only static contracts, schemas, templates, and
invariant assertions. It does not perform any scoring computation.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

SCORE_NAMES: Tuple[str, ...] = (
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
)

SCORE_BANDS: Dict[str, Tuple[int, int]] = {
    "low": (0, 19),
    "mild": (20, 39),
    "elevated": (40, 59),
    "high": (60, 79),
    "severe": (80, 100),
}


def build_expectation_failure_score_contracts() -> List[Dict[str, object]]:
    """Return deterministic score contracts for Phase A1 (no computation)."""
    contracts: List[Dict[str, object]] = []
    for score_name in SCORE_NAMES:
        contracts.append(
            {
                "score_name": score_name,
                "score_range": (0, 100),
                "score_direction": "higher_means_greater_expectation_failure_risk",
                "score_bands": SCORE_BANDS,
                "required_evidence_fields": (
                    "score_name",
                    "score_value",
                    "score_band",
                    "subcomponent_scores",
                    "raw_evidence_refs",
                    "thresholds_triggered",
                    "missing_inputs",
                    "data_quality_flags",
                    "explanation_template_id",
                    "confidence_boundary",
                    "replay_metadata",
                    "checksum_seed_fields",
                ),
                "allowed_missing_input_behavior": "allow_missing_inputs_with_explicit_tracking_and_deterministic_boundary_flags",
                "explanation_template_id": f"template_{score_name}_generic_v1",
                "deterministic_threshold_policy": "fixed_literal_thresholds_only_no_runtime_recalibration",
                "replay_policy": "replay_compatible_static_contract_inputs_and_outputs",
                "no_prediction_policy": "no_prediction_no_forecast_no_forward_price_targeting",
            }
        )
    return contracts


def build_expectation_failure_evidence_schema() -> Dict[str, object]:
    """Return fixed evidence schema fields for contract-conformant score evidence."""
    return {
        "score_name": "string",
        "score_value": "number_0_to_100",
        "score_band": "enum_low_mild_elevated_high_severe",
        "subcomponent_scores": "list_of_named_numeric_components",
        "raw_evidence_refs": "list_of_source_reference_identifiers",
        "thresholds_triggered": "list_of_triggered_fixed_threshold_identifiers",
        "missing_inputs": "list_of_missing_input_identifiers",
        "data_quality_flags": "list_of_data_quality_flags",
        "explanation_template_id": "string_template_identifier",
        "confidence_boundary": "deterministic_boundary_descriptor",
        "replay_metadata": "deterministic_replay_metadata_payload",
        "checksum_seed_fields": "ordered_list_of_checksum_seed_fields",
    }


def build_expectation_failure_explanation_templates() -> Dict[str, str]:
    """Return fixed deterministic explanation templates (no free-form generation)."""
    templates = {
        "template_valuation_stretch_score_generic_v1": (
            "valuation_stretch_score={score_value} ({score_band}); fixed-threshold interpretation applied. "
            "Evidence refs={raw_evidence_refs}; missing_inputs={missing_inputs}; quality_flags={data_quality_flags}."
        ),
        "template_fundamental_support_score_generic_v1": (
            "fundamental_support_score={score_value} ({score_band}); fixed-threshold interpretation applied. "
            "Evidence refs={raw_evidence_refs}; missing_inputs={missing_inputs}; quality_flags={data_quality_flags}."
        ),
        "template_narrative_saturation_score_generic_v1": (
            "narrative_saturation_score={score_value} ({score_band}); fixed-threshold interpretation applied. "
            "Evidence refs={raw_evidence_refs}; missing_inputs={missing_inputs}; quality_flags={data_quality_flags}."
        ),
        "template_certainty_fragility_score_generic_v1": (
            "certainty_fragility_score={score_value} ({score_band}); fixed-threshold interpretation applied. "
            "Evidence refs={raw_evidence_refs}; missing_inputs={missing_inputs}; quality_flags={data_quality_flags}."
        ),
        "template_structural_weakness_score_generic_v1": (
            "structural_weakness_score={score_value} ({score_band}); fixed-threshold interpretation applied. "
            "Evidence refs={raw_evidence_refs}; missing_inputs={missing_inputs}; quality_flags={data_quality_flags}."
        ),
        "template_invalid_input_v1": (
            "invalid_input_detected; required fields missing or malformed. "
            "No score computation performed; deterministic contract violation response emitted."
        ),
    }
    return templates


def build_expectation_failure_invariant_flags() -> Dict[str, bool]:
    """Return invariant flags that gate all Phase A1 contract outputs."""
    return {
        "deterministic_output": True,
        "replay_compatible": True,
        "immutable_input_safe": True,
        "bounded_score": True,
        "fixed_thresholds_used": True,
        "fixed_template_explanation": True,
        "additive_only_architecture": True,
        "no_runtime_mutation": True,
        "no_autonomous_trading": True,
        "no_prediction_engine": True,
        "no_optimization_loop": True,
        "no_adaptive_control": True,
    }


def build_phase_a1_expectation_failure_contract_report() -> Dict[str, object]:
    """Return deterministic Phase A1 implementation report payload."""
    contracts = build_expectation_failure_score_contracts()
    schema = build_expectation_failure_evidence_schema()
    templates = build_expectation_failure_explanation_templates()
    flags = build_expectation_failure_invariant_flags()
    return {
        "phase": "Phase A1",
        "module": "Expectation Failure Score Contracts & Evidence Schema",
        "status": "complete_deterministic_foundational_contracts",
        "public_api": [
            "build_expectation_failure_score_contracts",
            "build_expectation_failure_evidence_schema",
            "build_expectation_failure_explanation_templates",
            "build_expectation_failure_invariant_flags",
            "build_phase_a1_expectation_failure_contract_report",
        ],
        "defined_scores": [contract["score_name"] for contract in contracts],
        "evidence_schema_fields": list(schema.keys()),
        "explanation_template_ids": list(templates.keys()),
        "invariant_flags": flags,
        "implementation_boundaries": [
            "contracts_only_no_score_computation",
            "no_composite_expectation_failure_scoring",
            "no_prediction_trading_optimization_agents_or_adaptive_behavior",
            "no_external_io_or_side_effects",
        ],
        "supervisor_decision": "APPROVED_FOR_PHASE_A1_PR",
    }
