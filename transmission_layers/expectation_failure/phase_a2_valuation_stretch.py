"""Phase A2 deterministic Valuation Stretch scoring module."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from .phase_a1_contracts import SCORE_BANDS, build_expectation_failure_invariant_flags


def build_valuation_stretch_thresholds() -> Dict[str, object]:
    """Return fixed deterministic thresholds/constants for valuation stretch scoring."""
    return {
        "valuation_premium_ratio_bands": (
            {"id": "ratio_lt_1_0", "min": None, "max": 1.0, "score": 10},
            {"id": "ratio_1_0_to_1_49", "min": 1.0, "max": 1.5, "score": 30},
            {"id": "ratio_1_5_to_1_99", "min": 1.5, "max": 2.0, "score": 50},
            {"id": "ratio_2_0_to_2_99", "min": 2.0, "max": 3.0, "score": 70},
            {"id": "ratio_gte_3_0", "min": 3.0, "max": None, "score": 90},
        ),
        "historical_percentile_bands": (
            {"id": "percentile_lt_40", "min": None, "max": 40, "score": 20},
            {"id": "percentile_40_to_59", "min": 40, "max": 60, "score": 40},
            {"id": "percentile_60_to_74", "min": 60, "max": 75, "score": 60},
            {"id": "percentile_75_to_89", "min": 75, "max": 90, "score": 80},
            {"id": "percentile_gte_90", "min": 90, "max": None, "score": 95},
        ),
        "growth_ratio_bands": (
            {"id": "growth_ratio_lt_1_0", "min": None, "max": 1.0, "score": 20},
            {"id": "growth_ratio_1_0_to_1_49", "min": 1.0, "max": 1.5, "score": 40},
            {"id": "growth_ratio_1_5_to_1_99", "min": 1.5, "max": 2.0, "score": 60},
            {"id": "growth_ratio_2_0_to_2_99", "min": 2.0, "max": 3.0, "score": 80},
            {"id": "growth_ratio_gte_3_0", "min": 3.0, "max": None, "score": 95},
        ),
        "fallback_missing_or_invalid_score": 50,
        "weights": {
            "forward_pe_premium_score": 0.25,
            "ev_sales_premium_score": 0.25,
            "ev_ebitda_premium_score": 0.20,
            "historical_percentile_score": 0.20,
            "growth_expectation_intensity_score": 0.10,
        },
    }


def build_valuation_stretch_subcomponent_contract() -> Dict[str, object]:
    return {
        "score_name": "valuation_stretch_score",
        "subcomponents": (
            "forward_pe_premium_score",
            "ev_sales_premium_score",
            "ev_ebitda_premium_score",
            "historical_percentile_score",
            "growth_expectation_intensity_score",
        ),
        "score_range": (0, 100),
        "fixed_weighting": build_valuation_stretch_thresholds()["weights"],
        "band_contract": SCORE_BANDS,
    }


def build_valuation_stretch_evidence_summary() -> Dict[str, Tuple[str, ...]]:
    return {
        "required_input_fields": (
            "ticker",
            "sector",
            "subsector",
            "forward_pe",
            "sector_forward_pe_median",
            "ev_sales",
            "sector_ev_sales_median",
            "ev_ebitda",
            "sector_ev_ebitda_median",
            "historical_valuation_percentile",
            "revenue_growth_expectation",
            "sector_revenue_growth_median",
            "data_quality_flags",
            "raw_evidence_refs",
        ),
        "output_evidence_fields": (
            "subcomponent_scores",
            "thresholds_triggered",
            "missing_inputs",
            "data_quality_flags",
            "raw_evidence_refs",
        ),
    }


def _as_positive_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        val = float(value)
        return val if val > 0 else None
    return None


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _score_ratio(numerator: object, denominator: object, name: str, missing_inputs: List[str]) -> Tuple[int, str]:
    n = _as_positive_float(numerator)
    d = _as_positive_float(denominator)
    if n is None or d is None:
        missing_inputs.append(name)
        return 50, f"{name}:missing_or_invalid"
    ratio = n / d
    if ratio < 1.0:
        return 10, f"{name}:ratio_lt_1_0"
    if ratio < 1.5:
        return 30, f"{name}:ratio_1_0_to_1_49"
    if ratio < 2.0:
        return 50, f"{name}:ratio_1_5_to_1_99"
    if ratio < 3.0:
        return 70, f"{name}:ratio_2_0_to_2_99"
    return 90, f"{name}:ratio_gte_3_0"


def _score_percentile(value: object, missing_inputs: List[str]) -> Tuple[int, str]:
    percentile = _as_float(value)
    if percentile is None or percentile < 0 or percentile > 100:
        missing_inputs.append("historical_valuation_percentile")
        return 50, "historical_valuation_percentile:missing_or_invalid"
    if percentile < 40:
        return 20, "historical_valuation_percentile:percentile_lt_40"
    if percentile < 60:
        return 40, "historical_valuation_percentile:percentile_40_to_59"
    if percentile < 75:
        return 60, "historical_valuation_percentile:percentile_60_to_74"
    if percentile < 90:
        return 80, "historical_valuation_percentile:percentile_75_to_89"
    return 95, "historical_valuation_percentile:percentile_gte_90"


def _score_growth_ratio(growth: object, sector_growth: object, missing_inputs: List[str]) -> Tuple[int, str]:
    g = _as_positive_float(growth)
    s = _as_positive_float(sector_growth)
    if g is None or s is None:
        missing_inputs.append("growth_expectation_intensity_score")
        return 50, "growth_expectation_intensity_score:missing_or_invalid"
    ratio = g / s
    if ratio < 1.0:
        return 20, "growth_expectation_intensity_score:growth_ratio_lt_1_0"
    if ratio < 1.5:
        return 40, "growth_expectation_intensity_score:growth_ratio_1_0_to_1_49"
    if ratio < 2.0:
        return 60, "growth_expectation_intensity_score:growth_ratio_1_5_to_1_99"
    if ratio < 3.0:
        return 80, "growth_expectation_intensity_score:growth_ratio_2_0_to_2_99"
    return 95, "growth_expectation_intensity_score:growth_ratio_gte_3_0"


def _score_band(score: int) -> str:
    for band, (lo, hi) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return band
    return "severe"


def score_valuation_stretch(input_payload: dict) -> dict:
    if not isinstance(input_payload, dict):
        raise TypeError("input_payload must be a dict")

    payload = deepcopy(input_payload)
    missing_inputs: List[str] = []

    fpe_score, fpe_trigger = _score_ratio(payload.get("forward_pe"), payload.get("sector_forward_pe_median"), "forward_pe_premium_score", missing_inputs)
    evs_score, evs_trigger = _score_ratio(payload.get("ev_sales"), payload.get("sector_ev_sales_median"), "ev_sales_premium_score", missing_inputs)
    eve_score, eve_trigger = _score_ratio(payload.get("ev_ebitda"), payload.get("sector_ev_ebitda_median"), "ev_ebitda_premium_score", missing_inputs)
    hist_score, hist_trigger = _score_percentile(payload.get("historical_valuation_percentile"), missing_inputs)
    growth_score, growth_trigger = _score_growth_ratio(payload.get("revenue_growth_expectation"), payload.get("sector_revenue_growth_median"), missing_inputs)

    subcomponent_scores = {
        "forward_pe_premium_score": fpe_score,
        "ev_sales_premium_score": evs_score,
        "ev_ebitda_premium_score": eve_score,
        "historical_percentile_score": hist_score,
        "growth_expectation_intensity_score": growth_score,
    }
    weights = build_valuation_stretch_thresholds()["weights"]
    weighted_score = sum(subcomponent_scores[name] * weight for name, weight in weights.items())
    score_value = int(Decimal(str(weighted_score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    score_value = min(100, max(0, score_value))
    score_band = _score_band(score_value)

    thresholds_triggered = [fpe_trigger, evs_trigger, eve_trigger, hist_trigger, growth_trigger]
    primary_trigger = thresholds_triggered[0]

    if missing_inputs:
        template_id = "template_valuation_stretch_limited_data_v1"
        explanation = (
            "Valuation Stretch is {score_band} with limited data because {trigger_count} "
            "valuation stretch conditions were evaluated, including {primary_trigger}."
        ).format(
            score_band=score_band,
            trigger_count=len(thresholds_triggered),
            primary_trigger=primary_trigger,
        )
    else:
        template_id = "template_valuation_stretch_band_v1"
        explanation = (
            "Valuation Stretch is {score_band} because {trigger_count} valuation stretch "
            "conditions were triggered, including {primary_trigger}."
        ).format(
            score_band=score_band,
            trigger_count=len(thresholds_triggered),
            primary_trigger=primary_trigger,
        )

    return {
        "score_name": "valuation_stretch_score",
        "ticker": payload.get("ticker", "UNKNOWN"),
        "sector": payload.get("sector", "UNKNOWN"),
        "subsector": payload.get("subsector", "UNKNOWN"),
        "score_value": score_value,
        "score_band": score_band,
        "subcomponent_scores": subcomponent_scores,
        "thresholds_triggered": thresholds_triggered,
        "missing_inputs": sorted(set(missing_inputs)),
        "data_quality_flags": list(payload.get("data_quality_flags") or []),
        "raw_evidence_refs": list(payload.get("raw_evidence_refs") or []),
        "explanation_template_id": template_id,
        "explanation": explanation,
        "replay_metadata": {
            "module": "phase_a2_valuation_stretch",
            "version": "v1",
            "deterministic_replay_key_fields": [
                "ticker",
                "sector",
                "subsector",
                "forward_pe",
                "sector_forward_pe_median",
                "ev_sales",
                "sector_ev_sales_median",
                "ev_ebitda",
                "sector_ev_ebitda_median",
                "historical_valuation_percentile",
                "revenue_growth_expectation",
                "sector_revenue_growth_median",
            ],
        },
        "invariant_flags": build_expectation_failure_invariant_flags(),
    }


def build_phase_a2_valuation_stretch_report() -> Dict[str, object]:
    thresholds = build_valuation_stretch_thresholds()
    return {
        "phase": "Phase A2",
        "module": "Valuation Stretch Score Module",
        "status": "complete_deterministic_subcomponent_scoring",
        "public_api": [
            "score_valuation_stretch",
            "build_valuation_stretch_thresholds",
            "build_valuation_stretch_subcomponent_contract",
            "build_valuation_stretch_evidence_summary",
            "build_phase_a2_valuation_stretch_report",
        ],
        "scoring_scope": "valuation_stretch_score_only",
        "subcomponents": list(build_valuation_stretch_subcomponent_contract()["subcomponents"]),
        "thresholds": thresholds,
        "weights": thresholds["weights"],
        "evidence_fields": list(build_valuation_stretch_evidence_summary()["output_evidence_fields"]),
        "invariant_flags": build_expectation_failure_invariant_flags(),
        "implementation_boundaries": [
            "phase_a2_only_no_composite_ai_expectation_failure_score",
            "no_prediction_trading_optimization_agents_or_adaptive_behavior",
            "deterministic_fixed_thresholds_and_templates_only",
        ],
        "supervisor_decision": "APPROVED_FOR_PHASE_A2_PR",
    }
