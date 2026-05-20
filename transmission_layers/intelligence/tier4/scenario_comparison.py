from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .scenario_metrics import compute_scenario_response_metrics
from .scenario_semantics import normalize_structural_scenario


def _checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _factors(metrics: Dict[str, float]) -> List[str]:
    return [k for k, _ in sorted(((k, v) for k, v in metrics.items() if k.endswith("_delta")), key=lambda kv: (-kv[1], kv[0]))[:3]]


def compute_scenario_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = sorted(set(a.keys()) & set(b.keys()))
    if not keys:
        return 1.0
    gap = sum(abs(float(a[k]) - float(b[k])) for k in keys) / len(keys)
    return max(0.0, min(1.0, round(1.0 - gap, 6)))


def compare_scenario_outcomes(baseline_scenario: Dict[str, Any], candidate_scenario: Dict[str, Any], baseline_result: Dict[str, Any], candidate_result: Dict[str, Any]) -> Dict[str, Any]:
    b = normalize_structural_scenario(baseline_scenario)
    c = normalize_structural_scenario(candidate_scenario)
    bm = compute_scenario_response_metrics(baseline_result, baseline_result)
    cm = compute_scenario_response_metrics(baseline_result, candidate_result)
    dominant = _factors(cm)
    expl = "scenario comparison favored higher impact due to greater overload and fragmentation deltas." if cm["scenario_impact_score"] >= bm["scenario_impact_score"] else "scenario response remained regime-stable with limited structural impact."
    out = {
        "baseline_scenario": b["scenario_id"],
        "candidate_scenario": c["scenario_id"],
        "impact_score_delta": round(cm["scenario_impact_score"] - bm["scenario_impact_score"], 6),
        "regime_change_detected": cm["regime_shift_intensity"] > 0.0,
        "dominant_response_factors": dominant,
        "affected_nodes": c["target_nodes"],
        "affected_corridors": c["target_corridors"],
        "scenario_similarity_score": compute_scenario_similarity(bm, cm),
        "comparison_explanation": expl,
    }
    out["comparison_checksum"] = _checksum(out)
    return out


def rank_scenarios_by_impact(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(records, key=lambda r: (-float(r.get("scenario_impact_score", 0.0)), -float(r.get("regime_shift_intensity", 0.0)), -float(r.get("fragmentation_delta", 0.0)), -float(r.get("overload_delta", 0.0)), str(r.get("scenario_id", ""))))


def summarize_scenario_comparison(comparison: Dict[str, Any]) -> Dict[str, Any]:
    return {k: comparison[k] for k in ["baseline_scenario", "candidate_scenario", "impact_score_delta", "regime_change_detected", "scenario_similarity_score", "comparison_checksum"]}
