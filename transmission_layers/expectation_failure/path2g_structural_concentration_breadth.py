"""P2-G Structural Concentration & Breadth Intelligence: deterministic replay-safe cohort diagnostics."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CERTIFIED_CONCENTRATION_BREADTH = "CERTIFIED_CONCENTRATION_BREADTH"
DEGRADED_CONCENTRATION_BREADTH = "DEGRADED_CONCENTRATION_BREADTH"
BLOCKED_CONCENTRATION_BREADTH = "BLOCKED_CONCENTRATION_BREADTH"

CONCENTRATED_FRAGILITY = "CONCENTRATED_FRAGILITY"
BROAD_BASED_WEAKNESS = "BROAD_BASED_WEAKNESS"
MIXED_CONCENTRATION_BREADTH = "MIXED_CONCENTRATION_BREADTH"
LOW_STRUCTURAL_WEAKNESS = "LOW_STRUCTURAL_WEAKNESS"
INSUFFICIENT_BREADTH_EVIDENCE = "INSUFFICIENT_BREADTH_EVIDENCE"

THRESHOLDS = {
    "high_top_fragility_share": 0.55,
    "moderate_top_fragility_share": 0.40,
    "high_elevated_breadth": 0.50,
    "moderate_elevated_breadth": 0.30,
    "high_weakness_participation": 0.60,
    "moderate_weakness_participation": 0.40,
}

FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "trading_signals", "price_prediction", "portfolio_construction", "portfolio_optimization", "autonomous_execution",
    "adaptive_thresholds", "adaptive_weighting", "ml_clustering", "dynamic_cohort_creation", "dynamic_benchmark_creation",
    "stochastic_interpretation", "hidden_scoring_logic", "network_api_calls", "supabase_database_writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _clamp_0_100(value: Any, flags: List[str], field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        flags.append(f"MISSING_{field.upper()}")
        return -1.0
    clamped = max(0.0, min(100.0, parsed))
    if clamped != parsed:
        flags.append(f"CLAMPED_{field.upper()}")
    return clamped


def _top_n_from_size(size: int, flags: List[str]) -> int:
    if size >= 10:
        return 3
    if size >= 5:
        return 2
    flags.append("SMALL_COHORT")
    return 1


def build_concentration_breadth_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-G",
        "required_inputs": ["cohort_manifest", "relative_fragility", "percentile_ranking", "cross_sectional_explainability", "replay_metadata", "quality_flags", "checksums"],
        "required_output_fields": [
            "cohort_id", "cohort_version", "cohort_size", "usable_member_count", "top_n", "top_fragility_share", "elevated_fragility_breadth",
            "weakness_participation_rate", "fragility_dispersion", "breadth_deterioration_signal", "concentration_breadth_regime",
            "concentration_interpretation", "participation_interpretation", "structural_breadth_explanation", "quality_flags", "replay_metadata", "checksum",
        ],
        "thresholds": deepcopy(THRESHOLDS),
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def build_cohort_fragility_distribution(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    quality_flags: List[str] = list(payload.get("quality_flags", []))
    members = list(payload.get("cohort_members", []))
    scores = payload.get("relative_fragility_scores", {})
    percentiles = payload.get("percentiles", {})
    if not percentiles:
        quality_flags.append("MISSING_PERCENTILE_OR_RANKING")
    distribution = []
    for member in members:
        entity_id = str(member.get("entity_id", ""))
        score = _clamp_0_100(scores.get(entity_id), quality_flags, f"score_{entity_id}")
        if score < 0:
            continue
        pct = _clamp_0_100(percentiles.get(entity_id, 0.0), quality_flags, f"percentile_{entity_id}") if percentiles else 0.0
        distribution.append({"entity_id": entity_id, "relative_fragility_score": score, "percentile": pct})
    distribution.sort(key=lambda x: (-x["relative_fragility_score"], x["entity_id"]))
    return {
        "cohort_id": str(payload.get("cohort_id", "")),
        "cohort_version": str(payload.get("cohort_version", "")),
        "cohort_size": len(members),
        "usable_member_count": len(distribution),
        "distribution": distribution,
        "quality_flags": quality_flags,
    }


def calculate_top_fragility_share(distribution: List[Dict[str, Any]], cohort_size: int, quality_flags: List[str]) -> Dict[str, Any]:
    top_n = _top_n_from_size(cohort_size, quality_flags)
    total = sum(row["relative_fragility_score"] for row in distribution)
    top = sum(row["relative_fragility_score"] for row in distribution[:top_n])
    share = (top / total) if total > 0 else 0.0
    return {"top_n": top_n, "top_fragility_share": round(share, 6)}


def interpret_fragility_concentration(top_fragility_share: float) -> str:
    if top_fragility_share >= THRESHOLDS["high_top_fragility_share"]:
        return "Fragility is concentrated in the highest-ranked weak members."
    if top_fragility_share >= THRESHOLDS["moderate_top_fragility_share"]:
        return "Fragility concentration is moderate across leading weak members."
    return "Fragility concentration is limited; weakness is not dominated by top members."


def calculate_elevated_fragility_breadth(distribution: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(distribution)
    if n == 0:
        return {"elevated_fragility_breadth": 0.0, "weakness_participation_rate": 0.0, "fragility_dispersion": 0.0}
    elevated = sum(1 for row in distribution if row["relative_fragility_score"] >= 70.0 or row["percentile"] >= 75.0)
    weak = sum(1 for row in distribution if row["relative_fragility_score"] >= 50.0)
    scores = [row["relative_fragility_score"] for row in distribution]
    return {
        "elevated_fragility_breadth": round(elevated / n, 6),
        "weakness_participation_rate": round(weak / n, 6),
        "fragility_dispersion": round(max(scores) - min(scores), 6),
    }


def interpret_cohort_participation_deterioration(elevated_fragility_breadth: float, weakness_participation_rate: float) -> str:
    if elevated_fragility_breadth >= THRESHOLDS["high_elevated_breadth"] and weakness_participation_rate >= THRESHOLDS["high_weakness_participation"]:
        return "BREADTH_DETERIORATION_HIGH"
    if elevated_fragility_breadth >= THRESHOLDS["moderate_elevated_breadth"] or weakness_participation_rate >= THRESHOLDS["moderate_weakness_participation"]:
        return "BREADTH_DETERIORATION_MODERATE"
    return "BREADTH_DETERIORATION_LOW"


def classify_concentration_breadth_regime(top_fragility_share: float, elevated_fragility_breadth: float, weakness_participation_rate: float, usable_member_count: int) -> str:
    if usable_member_count < 2:
        return INSUFFICIENT_BREADTH_EVIDENCE
    high_top = top_fragility_share >= THRESHOLDS["high_top_fragility_share"]
    high_elev = elevated_fragility_breadth >= THRESHOLDS["high_elevated_breadth"]
    high_part = weakness_participation_rate >= THRESHOLDS["high_weakness_participation"]
    mod_elev = elevated_fragility_breadth >= THRESHOLDS["moderate_elevated_breadth"]
    mod_part = weakness_participation_rate >= THRESHOLDS["moderate_weakness_participation"]
    if high_elev and high_part:
        return BROAD_BASED_WEAKNESS
    if high_top and not mod_elev:
        return CONCENTRATED_FRAGILITY
    if high_top and (mod_elev or mod_part):
        return MIXED_CONCENTRATION_BREADTH
    if top_fragility_share < THRESHOLDS["moderate_top_fragility_share"] and not mod_elev and not mod_part:
        return LOW_STRUCTURAL_WEAKNESS
    return MIXED_CONCENTRATION_BREADTH


def build_structural_breadth_explanation(result: Dict[str, Any]) -> str:
    return (
        f"Regime={result['concentration_breadth_regime']}; top_n={result['top_n']}; top_fragility_share={result['top_fragility_share']:.3f}; "
        f"elevated_breadth={result['elevated_fragility_breadth']:.3f}; weakness_participation={result['weakness_participation_rate']:.3f}; "
        f"dispersion={result['fragility_dispersion']:.2f}; signal={result['breadth_deterioration_signal']}."
    )


def certify_concentration_breadth_intelligence(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    contract = build_concentration_breadth_input_contract()
    dist = build_cohort_fragility_distribution(payload)
    flags = list(dist["quality_flags"])
    if dist["usable_member_count"] < dist["cohort_size"]:
        flags.append("PARTIAL_MEMBER_SCORES_EXCLUDED")
    top = calculate_top_fragility_share(dist["distribution"], dist["cohort_size"], flags)
    breadth = calculate_elevated_fragility_breadth(dist["distribution"])
    signal = interpret_cohort_participation_deterioration(breadth["elevated_fragility_breadth"], breadth["weakness_participation_rate"])
    regime = classify_concentration_breadth_regime(top["top_fragility_share"], breadth["elevated_fragility_breadth"], breadth["weakness_participation_rate"], dist["usable_member_count"])
    result = {
        "cohort_id": dist["cohort_id"], "cohort_version": dist["cohort_version"], "cohort_size": dist["cohort_size"], "usable_member_count": dist["usable_member_count"],
        "top_n": top["top_n"], "top_fragility_share": top["top_fragility_share"], "elevated_fragility_breadth": breadth["elevated_fragility_breadth"],
        "weakness_participation_rate": breadth["weakness_participation_rate"], "fragility_dispersion": breadth["fragility_dispersion"],
        "breadth_deterioration_signal": signal, "concentration_breadth_regime": regime,
        "concentration_interpretation": interpret_fragility_concentration(top["top_fragility_share"]),
        "participation_interpretation": f"Participation signal is {signal}.",
        "structural_breadth_explanation": "", "quality_flags": flags,
        "replay_metadata": deepcopy(payload.get("replay_metadata", {"input_immutability_preserved": True, "stable_serialization": True})),
    }
    result["structural_breadth_explanation"] = build_structural_breadth_explanation(result)
    result["checksum"] = _checksum({k: v for k, v in result.items() if k != "checksum"})

    gates = {
        "input_contract_present": isinstance(contract, dict), "cohort_id_present": bool(result["cohort_id"]), "cohort_version_present": bool(result["cohort_version"]),
        "cohort_members_present": result["cohort_size"] > 0, "relative_fragility_scores_present": result["usable_member_count"] > 0,
        "rankings_or_percentiles_present": "MISSING_PERCENTILE_OR_RANKING" not in flags, "usable_member_count_evaluated": isinstance(result["usable_member_count"], int),
        "top_fragility_share_generated": isinstance(result["top_fragility_share"], float), "elevated_fragility_breadth_generated": isinstance(result["elevated_fragility_breadth"], float),
        "weakness_participation_rate_generated": isinstance(result["weakness_participation_rate"], float), "fragility_dispersion_generated": isinstance(result["fragility_dispersion"], float),
        "concentration_breadth_regime_assigned": bool(result["concentration_breadth_regime"]), "structural_breadth_explanation_generated": bool(result["structural_breadth_explanation"]),
        "checksum_stable": result["checksum"] == _checksum({k: v for k, v in result.items() if k != "checksum"}),
        "forbidden_dynamic_capabilities_absent": all(token not in _stable_json(result).lower() for token in ("prediction", "trading", "optimization")),
        "input_immutability_preserved": payload == deepcopy(input_payload),
    }
    blocked = not all((gates["cohort_id_present"], gates["cohort_version_present"], gates["cohort_members_present"], gates["relative_fragility_scores_present"]))
    degraded = blocked or (not gates["rankings_or_percentiles_present"]) or ("SMALL_COHORT" in flags) or ("PARTIAL_MEMBER_SCORES_EXCLUDED" in flags)
    result["certification_gates"] = gates
    result["certification_decision"] = BLOCKED_CONCENTRATION_BREADTH if blocked else (DEGRADED_CONCENTRATION_BREADTH if degraded else CERTIFIED_CONCENTRATION_BREADTH)
    return result


def build_path2g_structural_concentration_breadth_report(output_path: str = "reports/path2g_structural_concentration_breadth_report.md") -> str:
    report = """# P2-G Structural Concentration & Breadth Intelligence Report

## Objective
Deliver deterministic, replay-safe concentration and breadth diagnostics that determine whether weakness is isolated, concentrated, mixed, or broad-based.

## Scope
Consumes P2-A manifests, P2-B scores, P2-C percentiles/rankings, P2-F explanation packets, replay metadata, checksums, and quality flags.

## Non-Goals
No recalculation of P2-B/P2-C/P2-F outputs. No prediction, trading, optimization, portfolio logic, dynamic cohorts, dynamic benchmarks, network calls, or database writes.

## Architecture Summary
Input contract -> deterministic cohort fragility distribution -> concentration/breadth metrics -> fixed-threshold regime classification -> deterministic explanation -> certification.

## Input Contract
See `build_concentration_breadth_input_contract`.

## Cohort Fragility Distribution Methodology
Deterministic extraction by cohort_members order with stable score sorting (descending score then entity_id). Missing scores are excluded deterministically and flagged.

## Top-Fragility Share Methodology
Top-N share of total fragility score with deterministic top_n policy: >=10 => 3, 5-9 => 2, <5 => 1 + SMALL_COHORT flag.

## Elevated Breadth Methodology
Share of usable members with score >=70 or percentile >=75.

## Weakness Participation Methodology
Share of usable members with score >=50.

## Fragility Dispersion Methodology
max(score) - min(score) over usable members.

## Concentration/Breadth Regime Policy
CONCENTRATED_FRAGILITY, BROAD_BASED_WEAKNESS, MIXED_CONCENTRATION_BREADTH, LOW_STRUCTURAL_WEAKNESS, INSUFFICIENT_BREADTH_EVIDENCE via fixed thresholds.

## Fixed Threshold Policy
high_top_fragility_share>=0.55; moderate_top_fragility_share>=0.40; high_elevated_breadth>=0.50; moderate_elevated_breadth>=0.30; high_weakness_participation>=0.60; moderate_weakness_participation>=0.40.

## Missing/Clamped Data Policy
Missing cohort identity/members or all scores blocks. Partial scores degrade. Missing percentile/ranking degrades. Out-of-range scores/percentiles clamp to [0,100] and are flagged.

## Deterministic Explanation Policy
Narrative text is deterministic templates only.

## Replay/Checksum Guarantees
deepcopy input immutability and stable JSON serialization for checksum.

## Certification Decision Logic
Blocked for required identity/members/score failures; degraded for small cohort, partial scores, or missing percentile/ranking; certified otherwise.

## Forbidden Capabilities
Trading, prediction, optimization, dynamic/adaptive methods, clustering, hidden logic, network/API calls, and database writes.

## Final Supervisor Interpretation
P2-G provides deterministic structural diagnostics describing whether fragility is concentrated or broad across the cohort while preserving additive-only integration boundaries.
"""
    Path(output_path).write_text(report, encoding="utf-8")
    return output_path
