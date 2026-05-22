"""Phase B2 deterministic long / short asymmetry interpretation layer."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Dict, Iterable, List, Tuple

SCORE_FIELDS: Tuple[str, ...] = (
    "ai_expectation_failure_score",
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
)

EXPLANATION_TEMPLATE_ID = "template_phase_b2_asymmetry_v1"
CLASSIFICATION_RULE_VERSION = "b2_rules_v1"
THRESHOLD_VERSION = "b2_thresholds_v1"
EXPLANATION_TEMPLATE_VERSION = "b2_templates_v1"


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _stable_checksum(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_score(entity: dict, field: str, flags: List[str]) -> int:
    raw = entity.get(field)
    if raw is None:
        flags.append(f"missing_{field}")
        return 50
    if isinstance(raw, bool):
        flags.append(f"invalid_{field}")
        return 50
    if not isinstance(raw, (int, float)):
        flags.append(f"invalid_{field}")
        return 50
    val = float(raw)
    if val < 0:
        flags.append(f"clamped_{field}")
        return 0
    if val > 100:
        flags.append(f"clamped_{field}")
        return 100
    return _round_half_up(val)


def _bands(score: int) -> str:
    if score >= 80:
        return "severe"
    if score >= 60:
        return "high"
    if score >= 40:
        return "elevated"
    if score >= 20:
        return "mild"
    return "low"


def _normalize_entity(entity: dict) -> Tuple[Dict[str, int], List[str]]:
    flags: List[str] = []
    return {f: _normalize_score(entity, f, flags) for f in SCORE_FIELDS}, sorted(set(flags))


def build_expectation_support_mismatch(entity: dict) -> dict:
    scores, flags = _normalize_entity(entity)
    invalid_or_missing = sum(1 for f in flags if f.startswith("missing_") or f.startswith("invalid_"))
    if invalid_or_missing >= 4:
        return {"expectation_support_mismatch_label": "INSUFFICIENT_EVIDENCE", "mismatch_score": 50, "evidence_quality_flags": flags}
    burden = (scores["valuation_stretch_score"] + scores["narrative_saturation_score"] + scores["certainty_fragility_score"]) / 3
    support_gap = 100 - scores["fundamental_support_score"]
    mismatch_score = _round_half_up((burden + support_gap) / 2)
    if mismatch_score >= 80:
        label = "SEVERE_EXPECTATION_SUPPORT_MISMATCH"
    elif mismatch_score >= 70:
        label = "HIGH_EXPECTATION_SUPPORT_MISMATCH"
    elif mismatch_score >= 55:
        label = "MODERATE_EXPECTATION_SUPPORT_MISMATCH"
    elif mismatch_score >= 40:
        label = "LOW_EXPECTATION_SUPPORT_MISMATCH"
    else:
        label = "EXPECTATIONS_REASONABLY_SUPPORTED"
    return {"expectation_support_mismatch_label": label, "mismatch_score": mismatch_score, "evidence_quality_flags": flags}


def build_downside_asymmetry_classification(entity: dict) -> dict:
    scores, flags = _normalize_entity(entity)
    mismatch = build_expectation_support_mismatch(entity)
    missing_count = sum(1 for f in flags if f.startswith("missing_") or f.startswith("invalid_"))
    if missing_count >= 4:
        label = "INSUFFICIENT_EVIDENCE"
    elif scores["ai_expectation_failure_score"] >= 80 and scores["valuation_stretch_score"] >= 75 and scores["fundamental_support_score"] <= 40 and scores["certainty_fragility_score"] >= 65:
        label = "EXTREME_DOWNSIDE_ASYMMETRY"
    elif scores["ai_expectation_failure_score"] >= 70 and scores["valuation_stretch_score"] >= 65 and scores["fundamental_support_score"] <= 50:
        label = "HIGH_DOWNSIDE_ASYMMETRY"
    elif scores["ai_expectation_failure_score"] >= 60 or mismatch["expectation_support_mismatch_label"] in {"SEVERE_EXPECTATION_SUPPORT_MISMATCH", "HIGH_EXPECTATION_SUPPORT_MISMATCH"}:
        label = "MODERATE_DOWNSIDE_ASYMMETRY"
    elif scores["ai_expectation_failure_score"] >= 45:
        label = "LOW_DOWNSIDE_ASYMMETRY"
    else:
        label = "NO_CLEAR_DOWNSIDE_ASYMMETRY"
    return {"downside_asymmetry_label": label, "normalized_scores": scores, "evidence_quality_flags": sorted(set(flags + mismatch["evidence_quality_flags"]))}


def build_long_risk_fragility_interpretation(entity: dict) -> dict:
    downside = build_downside_asymmetry_classification(entity)
    scores = downside["normalized_scores"]
    if downside["downside_asymmetry_label"] == "INSUFFICIENT_EVIDENCE":
        label = "INSUFFICIENT_EVIDENCE"
    elif downside["downside_asymmetry_label"] == "EXTREME_DOWNSIDE_ASYMMETRY" or (downside["downside_asymmetry_label"] == "HIGH_DOWNSIDE_ASYMMETRY" and scores["fundamental_support_score"] <= 40):
        label = "VERY_FRAGILE_LONG_EXPOSURE"
    elif scores["ai_expectation_failure_score"] >= 65 and scores["structural_weakness_score"] >= 60:
        label = "FRAGILE_LONG_EXPOSURE"
    elif max(scores["certainty_fragility_score"], scores["valuation_stretch_score"], scores["narrative_saturation_score"]) >= 60:
        label = "WATCHLIST_LONG_EXPOSURE"
    elif scores["fundamental_support_score"] >= 60 and scores["structural_weakness_score"] <= 50:
        label = "SUPPORTED_LONG_EXPOSURE"
    else:
        label = "RESILIENT_LONG_EXPOSURE"
    return {"long_risk_fragility_label": label, "evidence_quality_flags": downside["evidence_quality_flags"]}


def build_relative_resilience_interpretation(entity: dict) -> dict:
    scores, flags = _normalize_entity(entity)
    missing = sum(1 for f in flags if f.startswith("missing_") or f.startswith("invalid_"))
    if missing >= 4:
        return {"relative_resilience_label": "INSUFFICIENT_EVIDENCE", "resilience_score": 50, "evidence_quality_flags": flags}
    resilience_score = _round_half_up((scores["fundamental_support_score"] + (100 - scores["structural_weakness_score"]) + (100 - scores["certainty_fragility_score"]) + (100 - scores["ai_expectation_failure_score"])) / 4)
    if resilience_score >= 75:
        label = "HIGH_RELATIVE_RESILIENCE"
    elif resilience_score >= 60:
        label = "MODERATE_RELATIVE_RESILIENCE"
    elif resilience_score >= 45:
        label = "NEUTRAL_RELATIVE_RESILIENCE"
    elif resilience_score >= 30:
        label = "LOW_RELATIVE_RESILIENCE"
    else:
        label = "STRUCTURALLY_FRAGILE_RELATIVE_OUTLIER"
    return {"relative_resilience_label": label, "resilience_score": resilience_score, "evidence_quality_flags": flags}


def build_ranking_asymmetry_interpretation(entity: dict, b1_rankings: List[dict] | None = None) -> dict:
    if not b1_rankings:
        return {"ranking_interpretation_label": "INSUFFICIENT_RANKING_CONTEXT"}
    sorted_rows = sorted(b1_rankings, key=lambda r: (r.get("rank", 10**9), str(r.get("entity_id") or r.get("ticker") or r.get("entity_name") or "")))
    ids = [str(r.get("entity_id") or r.get("ticker") or r.get("entity_name") or "") for r in sorted_rows]
    key = str(entity.get("entity_id") or entity.get("ticker") or entity.get("entity_name") or "")
    if key not in ids:
        return {"ranking_interpretation_label": "INSUFFICIENT_RANKING_CONTEXT"}
    rank = ids.index(key) + 1
    total = len(sorted_rows)
    top10 = max(1, (total + 9) // 10)
    top25 = max(top10, (total + 3) // 4)
    bottom10_start = total - max(1, (total + 9) // 10) + 1
    bottom25_start = total - ((total + 3) // 4) + 1
    resilience = build_relative_resilience_interpretation(entity)["relative_resilience_label"]
    if rank <= top10:
        label = "TOP_FRAGILITY_CANDIDATE"
    elif rank <= top25:
        label = "HIGH_FRAGILITY_CANDIDATE"
    elif rank >= bottom10_start and resilience in {"HIGH_RELATIVE_RESILIENCE", "MODERATE_RELATIVE_RESILIENCE"}:
        label = "RELATIVE_RESILIENCE_CANDIDATE"
    elif rank >= bottom25_start:
        label = "LOW_FRAGILITY_CANDIDATE"
    else:
        label = "MID_FRAGILITY_CANDIDATE"
    return {"ranking_interpretation_label": label, "rank": rank, "universe_size": total}


def build_cluster_asymmetry_summary(cluster_id: str, members: List[dict]) -> dict:
    if not members:
        return {"cluster_id": cluster_id, "cluster_label": "INSUFFICIENT_CLUSTER_EVIDENCE", "member_count": 0}
    normalized = [ _normalize_entity(m)[0] for m in members ]
    avg = {f: _round_half_up(sum(r[f] for r in normalized)/len(normalized)) for f in SCORE_FIELDS}
    unsupported = avg["valuation_stretch_score"] >= 70 and avg["fundamental_support_score"] <= 45
    crowded = avg["valuation_stretch_score"] >= 70 and avg["narrative_saturation_score"] >= 70
    certainty = avg["certainty_fragility_score"] >= 70
    structural = avg["structural_weakness_score"] >= 70
    composite = avg["ai_expectation_failure_score"] >= 70
    resilience = avg["fundamental_support_score"] >= 70 and avg["ai_expectation_failure_score"] <= 40
    if unsupported:
        label, driver = "UNSUPPORTED_VALUATION_CLUSTER", "unsupported_valuation"
    elif crowded:
        label, driver = "CROWDED_EXPECTATION_CLUSTER", "crowded_expectation"
    elif certainty:
        label, driver = "CERTAINTY_FRAGILITY_CLUSTER", "certainty_fragility"
    elif structural:
        label, driver = "STRUCTURAL_WEAKNESS_CLUSTER", "structural_weakness"
    elif composite:
        label, driver = "ASYMMETRIC_DOWNSIDE_CLUSTER", "composite_downside"
    elif resilience:
        label, driver = "RESILIENT_OUTLIER_CLUSTER", "resilience"
    else:
        label, driver = "MIXED_FRAGILITY_CLUSTER", "mixed"
    rep = sorted([m.get("ticker") or m.get("entity_name") or m.get("entity_id") or "UNKNOWN" for m in members])[:3]
    return {"cluster_id": cluster_id, "cluster_label": label, "member_count": len(members), "dominant_asymmetry_driver": driver, "average_expectation_failure_score": avg["ai_expectation_failure_score"], "average_valuation_stretch_score": avg["valuation_stretch_score"], "average_fundamental_support_score": avg["fundamental_support_score"], "average_narrative_saturation_score": avg["narrative_saturation_score"], "average_certainty_fragility_score": avg["certainty_fragility_score"], "average_structural_weakness_score": avg["structural_weakness_score"], "representative_entities": rep, "evidence_quality_flags": [], "interpretation_summary": f"Cluster {cluster_id} classified as {label} with dominant driver {driver}."}


def build_subsector_asymmetry_summary(subsector_name: str, members: List[dict], b1_rankings: List[dict] | None = None) -> dict:
    if not members:
        return {"subsector_name": subsector_name, "subsector_asymmetry_label": "INSUFFICIENT_SUBSECTOR_EVIDENCE"}
    downs = [build_downside_asymmetry_classification(m)["downside_asymmetry_label"] for m in members]
    mm = [build_expectation_support_mismatch(m)["mismatch_score"] for m in members]
    fs = [_normalize_entity(m)[0]["ai_expectation_failure_score"] for m in members]
    fragile = sum(d in {"EXTREME_DOWNSIDE_ASYMMETRY", "HIGH_DOWNSIDE_ASYMMETRY"} for d in downs)
    resilient = sum(build_relative_resilience_interpretation(m)["relative_resilience_label"] == "HIGH_RELATIVE_RESILIENCE" for m in members)
    avg_failure, avg_mismatch = _round_half_up(sum(fs)/len(fs)), _round_half_up(sum(mm)/len(mm))
    if fragile / len(members) >= 0.5 and avg_failure >= 75:
        label, driver = "SUBSECTOR_EXTREME_ASYMMETRY", "composite_downside"
    elif fragile / len(members) >= 0.35:
        label, driver = "SUBSECTOR_HIGH_ASYMMETRY", "expectation_support_gap"
    elif resilient / len(members) >= 0.5 and avg_failure <= 45:
        label, driver = "SUBSECTOR_RELATIVE_RESILIENCE", "resilience"
    elif resilient / len(members) >= 0.3:
        label, driver = "SUBSECTOR_MODERATE_RESILIENCE", "mixed_resilience"
    else:
        label, driver = "SUBSECTOR_MIXED_ASYMMETRY", "mixed"
    tops = sorted([m.get("ticker") or m.get("entity_id") or "UNKNOWN" for m in members])[:3]
    return {"subsector_name": subsector_name, "subsector_asymmetry_label": label, "dominant_driver": driver, "average_failure_score": avg_failure, "average_mismatch_score": avg_mismatch, "fragile_member_count": fragile, "resilient_member_count": resilient, "top_fragility_candidates": tops, "resilient_outliers": tops, "evidence_quality_flags": [], "interpretation_summary": f"Subsector {subsector_name} classified as {label} with dominant driver {driver}."}


def build_b2_evidence_chain(entity: dict, b1_rankings: List[dict] | None = None, evidence_context: dict | None = None) -> dict:
    safe = deepcopy(entity)
    scores, flags = _normalize_entity(safe)
    downside = build_downside_asymmetry_classification(safe)
    mismatch = build_expectation_support_mismatch(safe)
    long_risk = build_long_risk_fragility_interpretation(safe)
    resilience = build_relative_resilience_interpretation(safe)
    ranking = build_ranking_asymmetry_interpretation(safe, b1_rankings)
    label = downside["downside_asymmetry_label"]
    summary = f"{safe.get('entity_name') or safe.get('ticker') or safe.get('entity_id') or 'UNKNOWN'} is classified as {label} because expectation-failure risk is {_bands(scores['ai_expectation_failure_score'])}, valuation stretch is {_bands(scores['valuation_stretch_score'])}, fundamental support is {_bands(100-scores['fundamental_support_score'])}, narrative saturation is {_bands(scores['narrative_saturation_score'])}, certainty fragility is {_bands(scores['certainty_fragility_score'])}, and structural weakness is {_bands(scores['structural_weakness_score'])}. This is an expectation-risk interpretation, not a trading recommendation."
    replay = {"phase_id": "B2", "phase_name": "Long / Short Asymmetry Interpretation Layer", "classification_rule_version": CLASSIFICATION_RULE_VERSION, "threshold_version": THRESHOLD_VERSION, "explanation_template_version": EXPLANATION_TEMPLATE_VERSION, "deterministic_sort_order": "entity_id_or_ticker_asc", "tie_breaker_policy": "entity_id_then_ticker_then_name", "missing_data_policy": "fallback_50", "clamping_policy": "clamp_0_100", "architecture_constraints": ["deterministic_only", "bounded_labels", "replayable", "explainable", "additive_only", "no_trading_logic"]}
    out = {"entity_id": safe.get("entity_id"), "entity_name": safe.get("entity_name") or safe.get("ticker"), "downside_asymmetry_label": label, "long_risk_fragility_label": long_risk["long_risk_fragility_label"], "expectation_support_mismatch_label": mismatch["expectation_support_mismatch_label"], "relative_resilience_label": resilience["relative_resilience_label"], "ranking_interpretation_label": ranking["ranking_interpretation_label"], "primary_driver": "ai_expectation_failure_score", "secondary_driver": "valuation_stretch_score", "offsetting_support_factor": "fundamental_support_score", "normalized_scores": scores, "b1_context_used": {"ranking": ranking, "evidence_context": evidence_context or {}}, "evidence_quality_flags": sorted(set(flags + downside["evidence_quality_flags"])), "classification_rule_id": "b2_entity_chain_v1", "explanation_template_id": EXPLANATION_TEMPLATE_ID, "interpretation_summary": summary, "replay_metadata": replay}
    out["replay_metadata"]["input_checksum"] = _stable_checksum(safe)
    out["replay_metadata"]["output_checksum"] = _stable_checksum({k: v for k, v in out.items() if k != "replay_metadata"})
    return out


def build_phase_b2_asymmetry_report(entities: Iterable[dict], b1_rankings=None, b1_clusters=None, b1_subsector_summaries=None, evidence_context=None) -> dict:
    items = [deepcopy(e) for e in entities]
    ordered = sorted(items, key=lambda e: str(e.get("entity_id") or e.get("ticker") or e.get("entity_name") or ""))
    chains = [build_b2_evidence_chain(e, b1_rankings=b1_rankings, evidence_context=evidence_context) for e in ordered]
    cluster_groups: Dict[str, List[dict]] = {}
    for e in ordered:
        cid = str(e.get("cluster_id") or "UNCLUSTERED")
        cluster_groups.setdefault(cid, []).append(e)
    clusters = [build_cluster_asymmetry_summary(cid, members) for cid, members in sorted(cluster_groups.items())]
    subsector_groups: Dict[str, List[dict]] = {}
    for e in ordered:
        sec = str(e.get("subsector") or "UNKNOWN")
        subsector_groups.setdefault(sec, []).append(e)
    subsectors = [build_subsector_asymmetry_summary(sec, members, b1_rankings=b1_rankings) for sec, members in sorted(subsector_groups.items())]
    out = {"phase_id": "B2", "phase_name": "Long / Short Asymmetry Interpretation Layer", "entity_count": len(ordered), "entity_evidence_chains": chains, "cluster_asymmetry_summaries": clusters, "subsector_asymmetry_summaries": subsectors, "b1_context": {"rankings": b1_rankings or [], "clusters": b1_clusters or [], "subsector_summaries": b1_subsector_summaries or []}, "replay_metadata": {"phase_id": "B2", "phase_name": "Long / Short Asymmetry Interpretation Layer", "classification_rule_version": CLASSIFICATION_RULE_VERSION, "threshold_version": THRESHOLD_VERSION, "explanation_template_version": EXPLANATION_TEMPLATE_VERSION, "deterministic_sort_order": "entity_id_or_ticker_asc", "tie_breaker_policy": "entity_id_then_ticker_then_name", "missing_data_policy": "fallback_50", "clamping_policy": "clamp_0_100", "architecture_constraints": ["deterministic_only", "bounded_labels", "replayable", "explainable", "immutable_input_safe", "additive_only", "no_trading_logic"]}}
    out["replay_metadata"]["input_checksum"] = _stable_checksum(ordered)
    out["replay_metadata"]["output_checksum"] = _stable_checksum({k: v for k, v in out.items() if k != "replay_metadata"})
    return out
