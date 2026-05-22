"""Phase A7 deterministic AI Expectation Failure composite scoring module."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from .phase_a1_contracts import SCORE_BANDS, build_expectation_failure_invariant_flags


REQUIRED_INPUT_FIELDS: Tuple[str, ...] = (
    "ticker",
    "sector",
    "subsector",
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
    "data_quality_flags",
    "raw_evidence_refs",
)

_COMPONENTS: Tuple[str, ...] = (
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
)



def build_ai_expectation_failure_thresholds() -> Dict[str, object]:
    return {
        "fallback_missing_or_invalid_score": 50,
        "component_triggers": {
            "elevated_trigger_min": 40,
            "high_trigger_min": 60,
            "severe_trigger_min": 80,
        },
        "interaction_trigger": "any_interaction_flag_true",
        "interaction_penalty_cap": 20,
        "score_bands": SCORE_BANDS,
    }


def build_ai_expectation_failure_component_contract() -> Dict[str, object]:
    return {
        "score_name": "ai_expectation_failure_score",
        "component_scores": _COMPONENTS,
        "score_range": (0, 100),
        "weights": {
            "valuation_stretch_score": 0.25,
            "fundamental_support_score": 0.20,
            "narrative_saturation_score": 0.20,
            "certainty_fragility_score": 0.20,
            "structural_weakness_score": 0.15,
        },
        "band_contract": SCORE_BANDS,
    }


def build_ai_expectation_failure_interaction_rules() -> Dict[str, object]:
    return {
        "unsupported_valuation_flag": {
            "condition": "valuation_stretch_score>=75 and fundamental_support_score>=65",
            "penalty": 5,
        },
        "crowded_expectation_flag": {
            "condition": "valuation_stretch_score>=75 and narrative_saturation_score>=65",
            "penalty": 5,
        },
        "certainty_mismatch_flag": {
            "condition": "valuation_stretch_score>=70 and certainty_fragility_score>=70",
            "penalty": 5,
        },
        "structural_confirmation_flag": {
            "condition": "structural_weakness_score>=70 and any_two_other_components>=65",
            "penalty": 5,
        },
        "severe_failure_cluster_flag": {
            "condition": "at_least_four_components>=75",
            "penalty": 10,
        },
    }


def build_ai_expectation_failure_evidence_summary() -> Dict[str, Tuple[str, ...]]:
    return {
        "required_input_fields": REQUIRED_INPUT_FIELDS,
        "output_evidence_fields": (
            "component_scores",
            "component_weights",
            "interaction_flags",
            "thresholds_triggered",
            "missing_inputs",
            "data_quality_flags",
            "raw_evidence_refs",
        ),
    }


def _as_float(value):
    if isinstance(value, bool) or value is None:
        return None
    return float(value) if isinstance(value, (int, float)) else None


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _score_band(score_value: int) -> str:
    for band, (low, high) in SCORE_BANDS.items():
        if low <= score_value <= high:
            return band
    return "severe"


def _bound_or_fallback(payload: dict, field: str, missing: List[str], flags: List[str]) -> int:
    value = _as_float(payload.get(field))
    if value is None:
        missing.append(field)
        return 50
    if value < 0:
        flags.append(f"clamped_low:{field}")
        return 0
    if value > 100:
        flags.append(f"clamped_high:{field}")
        return 100
    return _round_half_up(value)


def _build_invariant_flags() -> Dict[str, bool]:
    flags = dict(build_expectation_failure_invariant_flags())
    flags.update(
        {
            "immutable_input_safe": True,
            "fixed_weights_used": True,
            "fixed_interaction_rules_used": True,
            "additive_only_architecture": True,
            "no_runtime_mutation": True,
            "no_optimization_loop": True,
            "no_adaptive_control": True,
            "no_component_recomputation": True,
        }
    )
    return flags


def score_ai_expectation_failure(input_payload: dict) -> dict:
    if not isinstance(input_payload, dict):
        raise TypeError("input_payload must be a dict")

    payload = deepcopy(input_payload)
    component_contract = build_ai_expectation_failure_component_contract()
    thresholds = build_ai_expectation_failure_thresholds()
    interaction_rules = build_ai_expectation_failure_interaction_rules()

    missing_inputs: List[str] = []
    added_quality_flags: List[str] = []
    component_scores = {
        component: _bound_or_fallback(payload, component, missing_inputs, added_quality_flags) for component in component_contract["component_scores"]
    }

    base_score_raw = sum(component_scores[name] * weight for name, weight in component_contract["weights"].items())
    base_score = max(0, min(100, _round_half_up(base_score_raw)))

    interaction_flags = {
        "unsupported_valuation_flag": component_scores["valuation_stretch_score"] >= 75 and component_scores["fundamental_support_score"] >= 65,
        "crowded_expectation_flag": component_scores["valuation_stretch_score"] >= 75 and component_scores["narrative_saturation_score"] >= 65,
        "certainty_mismatch_flag": component_scores["valuation_stretch_score"] >= 70 and component_scores["certainty_fragility_score"] >= 70,
        "structural_confirmation_flag": component_scores["structural_weakness_score"] >= 70 and sum(
            component_scores[name] >= 65
            for name in ("valuation_stretch_score", "fundamental_support_score", "narrative_saturation_score", "certainty_fragility_score")
        )
        >= 2,
        "severe_failure_cluster_flag": sum(score >= 75 for score in component_scores.values()) >= 4,
    }

    interaction_penalty_raw = sum(
        interaction_rules[flag]["penalty"] for flag, enabled in interaction_flags.items() if enabled
    )
    interaction_penalty = min(thresholds["interaction_penalty_cap"], interaction_penalty_raw)
    score_value = min(100, _round_half_up(base_score + interaction_penalty))
    score_band = _score_band(score_value)

    thresholds_triggered: List[str] = []
    for name, score in component_scores.items():
        if score >= thresholds["component_triggers"]["elevated_trigger_min"]:
            thresholds_triggered.append(f"{name}:component_elevated_trigger")
        if score >= thresholds["component_triggers"]["high_trigger_min"]:
            thresholds_triggered.append(f"{name}:component_high_trigger")
        if score >= thresholds["component_triggers"]["severe_trigger_min"]:
            thresholds_triggered.append(f"{name}:component_severe_trigger")
    if any(interaction_flags.values()):
        thresholds_triggered.append("interaction_trigger")

    limited_data = bool(missing_inputs)
    explanation_template_id = (
        "template_ai_expectation_failure_limited_data_v1" if limited_data else "template_ai_expectation_failure_band_v1"
    )
    primary_trigger = thresholds_triggered[0] if thresholds_triggered else "none"
    if limited_data:
        explanation = (
            "AI Expectation Failure risk is {score_band} with limited data because {trigger_count} expectation-failure conditions were triggered, "
            "including {primary_trigger}. Interaction penalty applied: {interaction_penalty}."
        ).format(
            score_band=score_band,
            trigger_count=len(thresholds_triggered),
            primary_trigger=primary_trigger,
            interaction_penalty=interaction_penalty,
        )
    else:
        explanation = (
            "AI Expectation Failure risk is {score_band} because {trigger_count} expectation-failure conditions were triggered, including "
            "{primary_trigger}. Interaction penalty applied: {interaction_penalty}."
        ).format(
            score_band=score_band,
            trigger_count=len(thresholds_triggered),
            primary_trigger=primary_trigger,
            interaction_penalty=interaction_penalty,
        )

    return {
        "score_name": "ai_expectation_failure_score",
        "ticker": payload.get("ticker", "UNKNOWN"),
        "sector": payload.get("sector", "UNKNOWN"),
        "subsector": payload.get("subsector", "UNKNOWN"),
        "score_value": score_value,
        "base_score": base_score,
        "interaction_penalty": interaction_penalty,
        "score_band": score_band,
        "component_scores": component_scores,
        "component_weights": component_contract["weights"],
        "interaction_flags": interaction_flags,
        "thresholds_triggered": thresholds_triggered,
        "missing_inputs": sorted(set(missing_inputs)),
        "data_quality_flags": list(payload.get("data_quality_flags") or []) + added_quality_flags,
        "raw_evidence_refs": list(payload.get("raw_evidence_refs") or []),
        "explanation_template_id": explanation_template_id,
        "explanation": explanation,
        "replay_metadata": {
            "module": "phase_a7_ai_expectation_failure",
            "version": "v1",
            "deterministic_replay_key_fields": list(build_ai_expectation_failure_evidence_summary()["required_input_fields"]),
        },
        "invariant_flags": _build_invariant_flags(),
    }


def build_phase_a7_ai_expectation_failure_report() -> Dict[str, object]:
    return {
        "phase": "Phase A7",
        "module": "AI Expectation Failure Composite Score Module",
        "status": "complete_deterministic_composite_scoring",
        "public_api": [
            "score_ai_expectation_failure",
            "build_ai_expectation_failure_thresholds",
            "build_ai_expectation_failure_component_contract",
            "build_ai_expectation_failure_interaction_rules",
            "build_ai_expectation_failure_evidence_summary",
            "build_phase_a7_ai_expectation_failure_report",
        ],
        "scoring_scope": "ai_expectation_failure_score_only",
        "score_direction": "0_low_expectation_failure_risk_100_severe_expectation_failure_risk",
        "component_scores": list(_COMPONENTS),
        "component_weights": build_ai_expectation_failure_component_contract()["weights"],
        "interaction_rules": build_ai_expectation_failure_interaction_rules(),
        "interaction_penalty_cap": build_ai_expectation_failure_thresholds()["interaction_penalty_cap"],
        "thresholds": build_ai_expectation_failure_thresholds(),
        "evidence_fields": list(build_ai_expectation_failure_evidence_summary()["output_evidence_fields"]),
        "invariant_flags": _build_invariant_flags(),
        "implementation_boundaries": [
            "phase_a7_only_additive_composite_scoring",
            "no_heatmaps_pair_analysis_benchmark_comparison_or_portfolio_construction",
            "no_trading_signals_target_prices_or_autonomous_agents",
            "no_prediction_engine_optimization_or_adaptive_control",
            "no_component_recomputation_phase_a2_to_phase_a6",
        ],
        "supervisor_decision": "ready_for_phase_a7_review",
    }
