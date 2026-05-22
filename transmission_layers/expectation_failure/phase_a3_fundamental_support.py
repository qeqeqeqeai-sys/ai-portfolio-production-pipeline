"""Phase A3 deterministic Fundamental Support scoring module."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from .phase_a1_contracts import SCORE_BANDS, build_expectation_failure_invariant_flags


def build_fundamental_support_thresholds() -> Dict[str, object]:
    return {
        "fcf_quality_relative_bands": (
            {"id": "fcf_margin_lt_0", "score": 90},
            {"id": "fcf_margin_lt_0_5x_sector", "score": 75},
            {"id": "fcf_margin_lt_1_0x_sector", "score": 55},
            {"id": "fcf_margin_lt_1_5x_sector", "score": 30},
            {"id": "fcf_margin_gte_1_5x_sector", "score": 15},
        ),
        "fcf_quality_fallback_bands": (
            {"id": "fcf_margin_lt_0", "score": 90},
            {"id": "fcf_margin_0_to_4_99", "score": 70},
            {"id": "fcf_margin_5_to_9_99", "score": 50},
            {"id": "fcf_margin_10_to_19_99", "score": 30},
            {"id": "fcf_margin_gte_20", "score": 15},
        ),
        "margin_change_bands": (
            {"id": "change_lte_neg_10", "score": 90},
            {"id": "change_neg_10_to_neg_5", "score": 75},
            {"id": "change_neg_5_to_0", "score": 60},
            {"id": "change_0_to_4_99", "score": 30},
            {"id": "change_gte_5", "score": 15},
        ),
        "roic_relative_bands": (
            {"id": "roic_lt_0", "score": 90},
            {"id": "roic_lt_0_5x_sector", "score": 75},
            {"id": "roic_lt_1_0x_sector", "score": 55},
            {"id": "roic_lt_1_5x_sector", "score": 30},
            {"id": "roic_gte_1_5x_sector", "score": 15},
        ),
        "roic_fallback_bands": (
            {"id": "roic_lt_0", "score": 90},
            {"id": "roic_0_to_4_99", "score": 70},
            {"id": "roic_5_to_9_99", "score": 50},
            {"id": "roic_10_to_19_99", "score": 30},
            {"id": "roic_gte_20", "score": 15},
        ),
        "net_debt_to_ebitda_bands": (
            {"id": "ndebt_ebitda_lt_0", "score": 15},
            {"id": "ndebt_ebitda_0_to_0_99", "score": 25},
            {"id": "ndebt_ebitda_1_to_1_99", "score": 40},
            {"id": "ndebt_ebitda_2_to_2_99", "score": 60},
            {"id": "ndebt_ebitda_3_to_3_99", "score": 75},
            {"id": "ndebt_ebitda_gte_4", "score": 90},
        ),
        "cash_to_debt_bands": (
            {"id": "cash_debt_gte_2", "score": 15},
            {"id": "cash_debt_1_to_1_99", "score": 30},
            {"id": "cash_debt_0_5_to_0_99", "score": 55},
            {"id": "cash_debt_0_25_to_0_49", "score": 75},
            {"id": "cash_debt_lt_0_25", "score": 90},
        ),
        "share_dilution_bands": (
            {"id": "dilution_lt_0", "score": 15},
            {"id": "dilution_0_to_1_99", "score": 25},
            {"id": "dilution_2_to_4_99", "score": 45},
            {"id": "dilution_5_to_9_99", "score": 70},
            {"id": "dilution_gte_10", "score": 90},
        ),
        "cash_burn_bands": (
            {"id": "burn_lte_0", "score": 15},
            {"id": "burn_0_01_to_9_99", "score": 30},
            {"id": "burn_10_to_24_99", "score": 55},
            {"id": "burn_25_to_49_99", "score": 75},
            {"id": "burn_gte_50", "score": 90},
        ),
        "fallback_missing_or_invalid_score": 50,
        "weights": {
            "fcf_quality_risk_score": 0.25,
            "margin_durability_risk_score": 0.20,
            "capital_efficiency_risk_score": 0.20,
            "balance_sheet_risk_score": 0.20,
            "dilution_cash_burn_risk_score": 0.15,
        },
    }


def build_fundamental_support_subcomponent_contract() -> Dict[str, object]:
    return {
        "score_name": "fundamental_support_score",
        "subcomponents": (
            "fcf_quality_risk_score",
            "margin_durability_risk_score",
            "capital_efficiency_risk_score",
            "balance_sheet_risk_score",
            "dilution_cash_burn_risk_score",
        ),
        "score_range": (0, 100),
        "fixed_weighting": build_fundamental_support_thresholds()["weights"],
        "band_contract": SCORE_BANDS,
    }


def build_fundamental_support_evidence_summary() -> Dict[str, Tuple[str, ...]]:
    return {
        "required_input_fields": (
            "ticker", "sector", "subsector", "fcf_margin", "sector_fcf_margin_median",
            "gross_margin_change", "operating_margin_change", "roic", "sector_roic_median",
            "net_debt_to_ebitda", "cash_to_debt", "share_dilution_rate", "cash_burn_rate",
            "data_quality_flags", "raw_evidence_refs",
        ),
        "output_evidence_fields": (
            "subcomponent_scores", "thresholds_triggered", "missing_inputs", "data_quality_flags", "raw_evidence_refs",
        ),
    }

def _as_float(v):
    if isinstance(v, bool) or v is None:
        return None
    return float(v) if isinstance(v, (int, float)) else None

def _band(score):
    for b,(lo,hi) in SCORE_BANDS.items():
        if lo<=score<=hi:
            return b
    return "severe"

def _avg(values: List[int]) -> int:
    return int(Decimal(str(sum(values)/len(values))).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def score_fundamental_support(input_payload: dict) -> dict:
    if not isinstance(input_payload, dict):
        raise TypeError("input_payload must be a dict")
    payload = deepcopy(input_payload)
    missing_inputs: List[str] = []
    triggers: List[str] = []

    fcf = _as_float(payload.get("fcf_margin")); fcf_med = _as_float(payload.get("sector_fcf_margin_median"))
    if fcf is None:
        fcf_score = 50; missing_inputs.append("fcf_margin"); triggers.append("fcf_quality_risk_score:missing_or_invalid")
    elif fcf_med is None or fcf_med <= 0:
        if fcf < 0: fcf_score, trig = 90, "fcf_quality_risk_score:fcf_margin_lt_0"
        elif fcf < 5: fcf_score, trig = 70, "fcf_quality_risk_score:fcf_margin_0_to_4_99"
        elif fcf < 10: fcf_score, trig = 50, "fcf_quality_risk_score:fcf_margin_5_to_9_99"
        elif fcf < 20: fcf_score, trig = 30, "fcf_quality_risk_score:fcf_margin_10_to_19_99"
        else: fcf_score, trig = 15, "fcf_quality_risk_score:fcf_margin_gte_20"
        triggers.append(trig)
    else:
        if fcf < 0: fcf_score, trig = 90, "fcf_quality_risk_score:fcf_margin_lt_0"
        elif fcf < 0.5 * fcf_med: fcf_score, trig = 75, "fcf_quality_risk_score:fcf_margin_lt_0_5x_sector"
        elif fcf < fcf_med: fcf_score, trig = 55, "fcf_quality_risk_score:fcf_margin_lt_1_0x_sector"
        elif fcf < 1.5 * fcf_med: fcf_score, trig = 30, "fcf_quality_risk_score:fcf_margin_lt_1_5x_sector"
        else: fcf_score, trig = 15, "fcf_quality_risk_score:fcf_margin_gte_1_5x_sector"
        triggers.append(trig)

    margin_scores=[]
    for field,label in (("gross_margin_change","gross_margin_change"),("operating_margin_change","operating_margin_change")):
        v=_as_float(payload.get(field))
        if v is None: continue
        if v <= -10: s,t=90,f"margin_durability_risk_score:{label}:change_lte_neg_10"
        elif v <= -5: s,t=75,f"margin_durability_risk_score:{label}:change_neg_10_to_neg_5"
        elif v < 0: s,t=60,f"margin_durability_risk_score:{label}:change_neg_5_to_0"
        elif v < 5: s,t=30,f"margin_durability_risk_score:{label}:change_0_to_4_99"
        else: s,t=15,f"margin_durability_risk_score:{label}:change_gte_5"
        margin_scores.append(s); triggers.append(t)
    if margin_scores:
        margin_score=_avg(margin_scores)
    else:
        margin_score=50; missing_inputs.append("margin_durability_risk_score"); triggers.append("margin_durability_risk_score:missing_or_invalid")

    roic=_as_float(payload.get("roic")); roic_med=_as_float(payload.get("sector_roic_median"))
    if roic is None:
        roic_score=50; missing_inputs.append("roic"); triggers.append("capital_efficiency_risk_score:missing_or_invalid")
    elif roic_med is None or roic_med <= 0:
        if roic < 0: roic_score,trig=90,"capital_efficiency_risk_score:roic_lt_0"
        elif roic < 5: roic_score,trig=70,"capital_efficiency_risk_score:roic_0_to_4_99"
        elif roic < 10: roic_score,trig=50,"capital_efficiency_risk_score:roic_5_to_9_99"
        elif roic < 20: roic_score,trig=30,"capital_efficiency_risk_score:roic_10_to_19_99"
        else: roic_score,trig=15,"capital_efficiency_risk_score:roic_gte_20"
        triggers.append(trig)
    else:
        if roic < 0: roic_score,trig=90,"capital_efficiency_risk_score:roic_lt_0"
        elif roic < 0.5*roic_med: roic_score,trig=75,"capital_efficiency_risk_score:roic_lt_0_5x_sector"
        elif roic < roic_med: roic_score,trig=55,"capital_efficiency_risk_score:roic_lt_1_0x_sector"
        elif roic < 1.5*roic_med: roic_score,trig=30,"capital_efficiency_risk_score:roic_lt_1_5x_sector"
        else: roic_score,trig=15,"capital_efficiency_risk_score:roic_gte_1_5x_sector"
        triggers.append(trig)

    bs=[]
    ndebt=_as_float(payload.get("net_debt_to_ebitda"))
    if ndebt is not None:
        if ndebt < 0: s,t=15,"balance_sheet_risk_score:ndebt_ebitda_lt_0"
        elif ndebt < 1: s,t=25,"balance_sheet_risk_score:ndebt_ebitda_0_to_0_99"
        elif ndebt < 2: s,t=40,"balance_sheet_risk_score:ndebt_ebitda_1_to_1_99"
        elif ndebt < 3: s,t=60,"balance_sheet_risk_score:ndebt_ebitda_2_to_2_99"
        elif ndebt < 4: s,t=75,"balance_sheet_risk_score:ndebt_ebitda_3_to_3_99"
        else: s,t=90,"balance_sheet_risk_score:ndebt_ebitda_gte_4"
        bs.append(s); triggers.append(t)
    c2d=_as_float(payload.get("cash_to_debt"))
    if c2d is not None:
        if c2d >= 2: s,t=15,"balance_sheet_risk_score:cash_debt_gte_2"
        elif c2d >= 1: s,t=30,"balance_sheet_risk_score:cash_debt_1_to_1_99"
        elif c2d >= 0.5: s,t=55,"balance_sheet_risk_score:cash_debt_0_5_to_0_99"
        elif c2d >= 0.25: s,t=75,"balance_sheet_risk_score:cash_debt_0_25_to_0_49"
        else: s,t=90,"balance_sheet_risk_score:cash_debt_lt_0_25"
        bs.append(s); triggers.append(t)
    balance_score=_avg(bs) if bs else 50
    if not bs: missing_inputs.append("balance_sheet_risk_score"); triggers.append("balance_sheet_risk_score:missing_or_invalid")

    dc=[]
    dil=_as_float(payload.get("share_dilution_rate"))
    if dil is not None:
        if dil < 0: s,t=15,"dilution_cash_burn_risk_score:dilution_lt_0"
        elif dil < 2: s,t=25,"dilution_cash_burn_risk_score:dilution_0_to_1_99"
        elif dil < 5: s,t=45,"dilution_cash_burn_risk_score:dilution_2_to_4_99"
        elif dil < 10: s,t=70,"dilution_cash_burn_risk_score:dilution_5_to_9_99"
        else: s,t=90,"dilution_cash_burn_risk_score:dilution_gte_10"
        dc.append(s); triggers.append(t)
    burn=_as_float(payload.get("cash_burn_rate"))
    if burn is not None:
        if burn <= 0: s,t=15,"dilution_cash_burn_risk_score:burn_lte_0"
        elif burn < 10: s,t=30,"dilution_cash_burn_risk_score:burn_0_01_to_9_99"
        elif burn < 25: s,t=55,"dilution_cash_burn_risk_score:burn_10_to_24_99"
        elif burn < 50: s,t=75,"dilution_cash_burn_risk_score:burn_25_to_49_99"
        else: s,t=90,"dilution_cash_burn_risk_score:burn_gte_50"
        dc.append(s); triggers.append(t)
    dilution_score=_avg(dc) if dc else 50
    if not dc: missing_inputs.append("dilution_cash_burn_risk_score"); triggers.append("dilution_cash_burn_risk_score:missing_or_invalid")

    sub = {"fcf_quality_risk_score":fcf_score,"margin_durability_risk_score":margin_score,"capital_efficiency_risk_score":roic_score,"balance_sheet_risk_score":balance_score,"dilution_cash_burn_risk_score":dilution_score}
    weights=build_fundamental_support_thresholds()["weights"]
    raw=sum(sub[k]*w for k,w in weights.items())
    score_value=max(0,min(100,int(Decimal(str(raw)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))))
    score_band=_band(score_value)
    template_id = "template_fundamental_support_limited_data_v1" if missing_inputs else "template_fundamental_support_band_v1"
    explanation=("Fundamental Support risk is {score_band} because {trigger_count} fundamental weakness conditions were triggered, including {primary_trigger}." if not missing_inputs else "Fundamental Support risk is {score_band} with limited data because {trigger_count} fundamental weakness conditions were triggered, including {primary_trigger}.").format(score_band=score_band,trigger_count=len(triggers),primary_trigger=triggers[0] if triggers else "none")

    return {
        "score_name":"fundamental_support_score",
        "ticker":payload.get("ticker","UNKNOWN"),
        "sector":payload.get("sector","UNKNOWN"),
        "subsector":payload.get("subsector","UNKNOWN"),
        "score_value":score_value,
        "score_band":score_band,
        "subcomponent_scores":sub,
        "thresholds_triggered":triggers,
        "missing_inputs":sorted(set(missing_inputs)),
        "data_quality_flags":list(payload.get("data_quality_flags") or []),
        "raw_evidence_refs":list(payload.get("raw_evidence_refs") or []),
        "explanation_template_id":template_id,
        "explanation":explanation,
        "replay_metadata":{"module":"phase_a3_fundamental_support","version":"v1","deterministic_replay_key_fields":list(build_fundamental_support_evidence_summary()["required_input_fields"])},
        "invariant_flags":build_expectation_failure_invariant_flags(),
    }


def build_phase_a3_fundamental_support_report() -> Dict[str, object]:
    thresholds = build_fundamental_support_thresholds()
    return {
        "phase": "Phase A3",
        "module": "Fundamental Support Score Module",
        "status": "complete_deterministic_subcomponent_scoring",
        "public_api": [
            "score_fundamental_support",
            "build_fundamental_support_thresholds",
            "build_fundamental_support_subcomponent_contract",
            "build_fundamental_support_evidence_summary",
            "build_phase_a3_fundamental_support_report",
        ],
        "scoring_scope": "fundamental_support_score_only",
        "score_direction": "0_strong_support_100_weak_support_high_expectation_failure_risk",
        "subcomponents": list(build_fundamental_support_subcomponent_contract()["subcomponents"]),
        "thresholds": thresholds,
        "weights": thresholds["weights"],
        "evidence_fields": list(build_fundamental_support_evidence_summary()["output_evidence_fields"]),
        "invariant_flags": build_expectation_failure_invariant_flags(),
        "implementation_boundaries": [
            "phase_a3_only_no_composite_ai_expectation_failure_score",
            "no_narrative_saturation_certainty_fragility_structural_weakness_heatmaps_pair_analysis_or_benchmark_comparison",
            "no_prediction_trading_optimization_agents_or_adaptive_behavior",
            "deterministic_fixed_thresholds_and_templates_only",
        ],
        "supervisor_decision": "APPROVED_FOR_PHASE_A3_PR",
    }
