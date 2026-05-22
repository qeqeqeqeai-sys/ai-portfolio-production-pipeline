"""Phase A4 deterministic Narrative Saturation scoring module."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from .phase_a1_contracts import SCORE_BANDS, build_expectation_failure_invariant_flags


def build_narrative_saturation_thresholds() -> Dict[str, object]:
    return {
        "ai_hype_ratio_bands": (
            {"id": "ratio_lt_1_0", "score": 20},
            {"id": "ratio_1_0_to_1_49", "score": 40},
            {"id": "ratio_1_5_to_1_99", "score": 60},
            {"id": "ratio_2_0_to_2_99", "score": 80},
            {"id": "ratio_gte_3_0", "score": 95},
        ),
        "ai_hype_fallback_bands": (
            {"id": "density_lt_1", "score": 20},
            {"id": "density_1_to_2_99", "score": 40},
            {"id": "density_3_to_5_99", "score": 60},
            {"id": "density_6_to_9_99", "score": 80},
            {"id": "density_gte_10", "score": 95},
        ),
        "news_spike_bands": (
            {"id": "news_lt_1_0", "score": 20}, {"id": "news_1_0_to_1_49", "score": 40}, {"id": "news_1_5_to_1_99", "score": 60}, {"id": "news_2_0_to_2_99", "score": 80}, {"id": "news_gte_3_0", "score": 95},
        ),
        "management_mention_bands": (
            {"id": "mgmt_lt_1", "score": 20}, {"id": "mgmt_1_to_2_99", "score": 40}, {"id": "mgmt_3_to_5_99", "score": 60}, {"id": "mgmt_6_to_9_99", "score": 80}, {"id": "mgmt_gte_10", "score": 95},
        ),
        "sentiment_bands": (
            {"id": "sent_lt_20", "score": 10}, {"id": "sent_20_to_39", "score": 30}, {"id": "sent_40_to_59", "score": 50}, {"id": "sent_60_to_79", "score": 75}, {"id": "sent_gte_80", "score": 95},
        ),
        "thematic_bands": (
            {"id": "theme_lt_20", "score": 10}, {"id": "theme_20_to_39", "score": 30}, {"id": "theme_40_to_59", "score": 50}, {"id": "theme_60_to_79", "score": 75}, {"id": "theme_gte_80", "score": 95},
        ),
        "etf_inclusion_bands": (
            {"id": "etf_eq_0", "score": 10}, {"id": "etf_1_to_2", "score": 30}, {"id": "etf_3_to_5", "score": 55}, {"id": "etf_6_to_10", "score": 75}, {"id": "etf_gt_10", "score": 90},
        ),
        "retail_attention_bands": (
            {"id": "retail_lt_1_0", "score": 15}, {"id": "retail_1_0_to_1_49", "score": 35}, {"id": "retail_1_5_to_1_99", "score": 55}, {"id": "retail_2_0_to_2_99", "score": 75}, {"id": "retail_gte_3_0", "score": 95},
        ),
        "fallback_missing_or_invalid_score": 50,
        "weights": {
            "ai_hype_intensity_score": 0.25,
            "narrative_concentration_score": 0.20,
            "sentiment_overheating_score": 0.20,
            "thematic_crowding_score": 0.20,
            "excessive_optimism_score": 0.15,
        },
    }


def build_narrative_saturation_subcomponent_contract() -> Dict[str, object]:
    return {
        "score_name": "narrative_saturation_score",
        "subcomponents": (
            "ai_hype_intensity_score",
            "narrative_concentration_score",
            "sentiment_overheating_score",
            "thematic_crowding_score",
            "excessive_optimism_score",
        ),
        "score_range": (0, 100),
        "fixed_weighting": build_narrative_saturation_thresholds()["weights"],
        "band_contract": SCORE_BANDS,
    }


def build_narrative_saturation_evidence_summary() -> Dict[str, Tuple[str, ...]]:
    return {
        "required_input_fields": (
            "ticker", "sector", "subsector", "ai_keyword_density", "sector_ai_keyword_density_median", "news_volume_spike",
            "sentiment_overheating", "thematic_crowding", "retail_attention_spike", "management_ai_mention_intensity",
            "etf_theme_inclusion_count", "data_quality_flags", "raw_evidence_refs",
        ),
        "output_evidence_fields": (
            "subcomponent_scores", "thresholds_triggered", "missing_inputs", "data_quality_flags", "raw_evidence_refs",
        ),
    }


def _as_float(v):
    if isinstance(v, bool) or v is None:
        return None
    return float(v) if isinstance(v, (int, float)) else None


def _as_int(v):
    if isinstance(v, bool) or v is None:
        return None
    return int(v) if isinstance(v, int) else None


def _avg(values: List[int]) -> int:
    return int(Decimal(str(sum(values) / len(values))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _band(score):
    for b, (lo, hi) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return b
    return "severe"


def _score_sentiment(v: float) -> Tuple[int, str]:
    if v < 20:
        return 10, "sent_lt_20"
    if v < 40:
        return 30, "sent_20_to_39"
    if v < 60:
        return 50, "sent_40_to_59"
    if v < 80:
        return 75, "sent_60_to_79"
    return 95, "sent_gte_80"


def score_narrative_saturation(input_payload: dict) -> dict:
    if not isinstance(input_payload, dict):
        raise TypeError("input_payload must be a dict")
    payload = deepcopy(input_payload)
    missing_inputs: List[str] = []
    triggers: List[str] = []

    density = _as_float(payload.get("ai_keyword_density"))
    sector_med = _as_float(payload.get("sector_ai_keyword_density_median"))
    if density is None:
        ai_hype = 50; missing_inputs.append("ai_keyword_density"); triggers.append("ai_hype_intensity_score:missing_or_invalid")
    elif sector_med is not None and sector_med > 0:
        ratio = density / sector_med
        if ratio < 1.0: ai_hype,t = 20,"ai_hype_intensity_score:ratio_lt_1_0"
        elif ratio < 1.5: ai_hype,t = 40,"ai_hype_intensity_score:ratio_1_0_to_1_49"
        elif ratio < 2.0: ai_hype,t = 60,"ai_hype_intensity_score:ratio_1_5_to_1_99"
        elif ratio < 3.0: ai_hype,t = 80,"ai_hype_intensity_score:ratio_2_0_to_2_99"
        else: ai_hype,t = 95,"ai_hype_intensity_score:ratio_gte_3_0"
        triggers.append(t)
    else:
        if density < 1: ai_hype,t = 20,"ai_hype_intensity_score:density_lt_1"
        elif density < 3: ai_hype,t = 40,"ai_hype_intensity_score:density_1_to_2_99"
        elif density < 6: ai_hype,t = 60,"ai_hype_intensity_score:density_3_to_5_99"
        elif density < 10: ai_hype,t = 80,"ai_hype_intensity_score:density_6_to_9_99"
        else: ai_hype,t = 95,"ai_hype_intensity_score:density_gte_10"
        triggers.append(t)

    conc_vals=[]
    news = _as_float(payload.get("news_volume_spike"))
    if news is not None:
        if news < 1.0: s,t = 20,"narrative_concentration_score:news_lt_1_0"
        elif news < 1.5: s,t = 40,"narrative_concentration_score:news_1_0_to_1_49"
        elif news < 2.0: s,t = 60,"narrative_concentration_score:news_1_5_to_1_99"
        elif news < 3.0: s,t = 80,"narrative_concentration_score:news_2_0_to_2_99"
        else: s,t = 95,"narrative_concentration_score:news_gte_3_0"
        conc_vals.append(s); triggers.append(t)
    mgmt = _as_float(payload.get("management_ai_mention_intensity"))
    if mgmt is not None:
        if mgmt < 1: s,t = 20,"narrative_concentration_score:mgmt_lt_1"
        elif mgmt < 3: s,t = 40,"narrative_concentration_score:mgmt_1_to_2_99"
        elif mgmt < 6: s,t = 60,"narrative_concentration_score:mgmt_3_to_5_99"
        elif mgmt < 10: s,t = 80,"narrative_concentration_score:mgmt_6_to_9_99"
        else: s,t = 95,"narrative_concentration_score:mgmt_gte_10"
        conc_vals.append(s); triggers.append(t)
    concentration = _avg(conc_vals) if conc_vals else 50
    if not conc_vals: missing_inputs.append("narrative_concentration_score"); triggers.append("narrative_concentration_score:missing_or_invalid")

    sentiment = _as_float(payload.get("sentiment_overheating"))
    if sentiment is None:
        sentiment_score=50; missing_inputs.append("sentiment_overheating"); triggers.append("sentiment_overheating_score:missing_or_invalid")
    else:
        sentiment_score, st = _score_sentiment(sentiment)
        triggers.append(f"sentiment_overheating_score:{st}")

    crowd_vals=[]
    thematic = _as_float(payload.get("thematic_crowding"))
    if thematic is not None:
        s,st = _score_sentiment(thematic)
        crowd_vals.append(s); triggers.append(f"thematic_crowding_score:{st.replace('sent','theme')}")
    etf = _as_int(payload.get("etf_theme_inclusion_count"))
    if etf is not None and etf >= 0:
        if etf == 0: s,t = 10,"thematic_crowding_score:etf_eq_0"
        elif etf <= 2: s,t = 30,"thematic_crowding_score:etf_1_to_2"
        elif etf <= 5: s,t = 55,"thematic_crowding_score:etf_3_to_5"
        elif etf <= 10: s,t = 75,"thematic_crowding_score:etf_6_to_10"
        else: s,t = 90,"thematic_crowding_score:etf_gt_10"
        crowd_vals.append(s); triggers.append(t)
    thematic_score = _avg(crowd_vals) if crowd_vals else 50
    if not crowd_vals: missing_inputs.append("thematic_crowding_score"); triggers.append("thematic_crowding_score:missing_or_invalid")

    optimism_vals=[]
    retail = _as_float(payload.get("retail_attention_spike"))
    if retail is not None:
        if retail < 1.0: s,t = 15,"excessive_optimism_score:retail_lt_1_0"
        elif retail < 1.5: s,t = 35,"excessive_optimism_score:retail_1_0_to_1_49"
        elif retail < 2.0: s,t = 55,"excessive_optimism_score:retail_1_5_to_1_99"
        elif retail < 3.0: s,t = 75,"excessive_optimism_score:retail_2_0_to_2_99"
        else: s,t = 95,"excessive_optimism_score:retail_gte_3_0"
        optimism_vals.append(s); triggers.append(t)
    if sentiment is not None:
        s,st = _score_sentiment(sentiment)
        optimism_vals.append(s); triggers.append(f"excessive_optimism_score:{st}")
    optimism = _avg(optimism_vals) if optimism_vals else 50
    if not optimism_vals: missing_inputs.append("excessive_optimism_score"); triggers.append("excessive_optimism_score:missing_or_invalid")

    sub = {
        "ai_hype_intensity_score": ai_hype,
        "narrative_concentration_score": concentration,
        "sentiment_overheating_score": sentiment_score,
        "thematic_crowding_score": thematic_score,
        "excessive_optimism_score": optimism,
    }
    weights = build_narrative_saturation_thresholds()["weights"]
    raw = sum(sub[k] * w for k, w in weights.items())
    score_value = max(0, min(100, int(Decimal(str(raw)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))
    score_band = _band(score_value)

    limited = bool(missing_inputs)
    template_id = "template_narrative_saturation_limited_data_v1" if limited else "template_narrative_saturation_band_v1"
    explanation = (
        "Narrative Saturation is {score_band} because {trigger_count} narrative overheating conditions were triggered, including {primary_trigger}."
        if not limited else
        "Narrative Saturation is {score_band} with limited data because {trigger_count} narrative overheating conditions were triggered, including {primary_trigger}."
    ).format(score_band=score_band, trigger_count=len(triggers), primary_trigger=triggers[0] if triggers else "none")

    return {
        "score_name": "narrative_saturation_score",
        "ticker": payload.get("ticker", "UNKNOWN"),
        "sector": payload.get("sector", "UNKNOWN"),
        "subsector": payload.get("subsector", "UNKNOWN"),
        "score_value": score_value,
        "score_band": score_band,
        "subcomponent_scores": sub,
        "thresholds_triggered": triggers,
        "missing_inputs": sorted(set(missing_inputs)),
        "data_quality_flags": list(payload.get("data_quality_flags") or []),
        "raw_evidence_refs": list(payload.get("raw_evidence_refs") or []),
        "explanation_template_id": template_id,
        "explanation": explanation,
        "replay_metadata": {"module": "phase_a4_narrative_saturation", "version": "v1", "deterministic_replay_key_fields": list(build_narrative_saturation_evidence_summary()["required_input_fields"] )},
        "invariant_flags": build_expectation_failure_invariant_flags(),
    }


def build_phase_a4_narrative_saturation_report() -> Dict[str, object]:
    thresholds = build_narrative_saturation_thresholds()
    return {
        "phase": "Phase A4",
        "module": "Narrative Saturation Score Module",
        "status": "complete_deterministic_subcomponent_scoring",
        "public_api": [
            "score_narrative_saturation",
            "build_narrative_saturation_thresholds",
            "build_narrative_saturation_subcomponent_contract",
            "build_narrative_saturation_evidence_summary",
            "build_phase_a4_narrative_saturation_report",
        ],
        "scoring_scope": "narrative_saturation_score_only",
        "score_direction": "0_low_narrative_saturation_100_severe_narrative_saturation_high_hype_crowding_risk",
        "subcomponents": list(build_narrative_saturation_subcomponent_contract()["subcomponents"]),
        "thresholds": thresholds,
        "weights": thresholds["weights"],
        "evidence_fields": list(build_narrative_saturation_evidence_summary()["output_evidence_fields"]),
        "invariant_flags": build_expectation_failure_invariant_flags(),
        "implementation_boundaries": [
            "phase_a4_only_no_composite_ai_expectation_failure_score",
            "no_certainty_fragility_structural_weakness_heatmaps_pair_analysis_or_benchmark_comparison",
            "no_prediction_trading_optimization_agents_or_adaptive_behavior",
            "deterministic_fixed_thresholds_and_templates_only",
        ],
        "supervisor_decision": "APPROVED_FOR_PHASE_A4_PR",
    }
