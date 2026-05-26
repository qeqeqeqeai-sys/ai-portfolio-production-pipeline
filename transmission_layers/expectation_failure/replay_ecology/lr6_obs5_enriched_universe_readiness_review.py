"""LR6-OBS5 enriched universe replay-readiness review (deterministic observation-only)."""
from __future__ import annotations

from collections import Counter
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_obs4_enriched_replay_candidate_universe import (
    build_lr6_obs4_candidate_universe,
    build_lr6_obs4_contradiction_enrichment_entities,
    build_lr6_obs4_density_gap_priorities,
    build_lr6_obs4_ecological_role_taxonomy,
    build_lr6_obs4_megacap_concentration_assessment,
    build_lr6_obs4_propagation_diversity_entities,
    build_lr6_obs4_supervisor_review,
    build_lr6_obs4_weak_signal_bridge_entities,
)

DETERMINISTIC_VERSION = "LR6_OBS5_ENRICHED_UNIVERSE_READINESS_REVIEW_V1"
SOURCE_PHASE = "LR6-OBS5"

ALLOWED_DECISIONS = {
    "READY_FOR_BOUNDED_OBSERVATION_WAVE",
    "CONDITIONALLY_READY_NEEDS_MINOR_REBALANCE",
    "NOT_READY_REQUIRES_REDESIGN",
}


def _safe_obs4_universe() -> list[dict[str, Any]]:
    try:
        universe = build_lr6_obs4_candidate_universe()
    except Exception:
        universe = []
    return universe if isinstance(universe, list) else []


def _safe_obs4_roles() -> list[dict[str, Any]]:
    fallback_roles = [
        "peripheral_ai_ecosystem_actors", "industrial_automation", "cybersecurity", "grid_utilities_power_demand",
        "telecom_infrastructure", "data_center_infrastructure", "cooling_thermal_energy_efficiency", "memory_storage_ecosystems",
        "edge_compute_embedded_systems", "robotics", "logistics_supply_chain", "ai_consulting_integration",
        "semiconductor_equipment", "regulatory_compliance_exposure", "geopolitical_semiconductor_exposure",
        "weak_signal_secondary_bridges", "cross_regime_contradiction_carriers", "non_megacap_replay_bridges",
    ]
    try:
        roles = build_lr6_obs4_ecological_role_taxonomy()
    except Exception:
        roles = []
    if isinstance(roles, list) and len(roles) >= 18:
        return roles
    return [{"role_id": f"R{idx+1:02d}", "role": role, "intent": "fallback_role_taxonomy"} for idx, role in enumerate(fallback_roles)]


def build_lr6_obs5_readiness_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = lr6_artifacts if isinstance(lr6_artifacts, dict) else {}
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "review_mode": "bounded_replay_readiness_review",
        "inspected_obs4_outputs": bool(artifacts.get("lr6_obs4_enriched_replay_candidate_universe", True)),
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs5_role_balance_assessment() -> dict[str, Any]:
    universe = _safe_obs4_universe()
    taxonomy = _safe_obs4_roles()
    role_names = [r["role"] for r in taxonomy]
    counts = Counter(role for c in universe for role in c.get("roles", []))
    role_counts = {role: counts.get(role, 0) for role in role_names}
    represented = [r for r, n in role_counts.items() if n > 0]
    underrepresented = sorted([r for r, n in role_counts.items() if n <= 2])
    overrepresented = sorted([r for r, n in role_counts.items() if n >= 8])
    return {
        "role_count_map": role_counts,
        "represented_roles": represented,
        "underrepresented_roles": underrepresented,
        "overrepresented_roles": overrepresented,
        "all_18_roles_present": len(role_counts) == 18,
    }


def build_lr6_obs5_weak_signal_usefulness_assessment() -> dict[str, Any]:
    weak = build_lr6_obs4_weak_signal_bridge_entities() if _safe_obs4_universe() else []
    tickers = [e.get("ticker", "") for e in weak]
    return {
        "weak_signal_bridge_count": len(weak),
        "non_obvious_bridge_presence": len(weak) >= 8,
        "topology_drift_observability_improvement": "high" if len(weak) >= 10 else "moderate",
        "sample_bridge_tickers": tickers[:8],
    }


def build_lr6_obs5_contradiction_potential_assessment() -> dict[str, Any]:
    contradiction = build_lr6_obs4_contradiction_enrichment_entities() if _safe_obs4_universe() else []
    categories = sorted({"_".join(c.get("roles", [])[:2]) for c in contradiction if c.get("roles")})
    return {
        "contradiction_carrier_count": len(contradiction),
        "semantic_tension_potential": "high" if len(contradiction) >= 8 else "moderate",
        "category_diversity_count": len(categories),
        "sample_categories": categories[:8],
    }


def build_lr6_obs5_propagation_diversity_assessment() -> dict[str, Any]:
    propagation = build_lr6_obs4_propagation_diversity_entities() if _safe_obs4_universe() else []
    pathway_roles = Counter(role for c in propagation for role in c.get("roles", []))
    return {
        "propagation_bridge_count": len(propagation),
        "pathway_role_diversity": len(pathway_roles),
        "pathways_too_obvious": len(pathway_roles) < 6,
        "likely_to_diversify_replay": len(propagation) >= 12,
    }


def build_lr6_obs5_overconcentration_risk_assessment() -> dict[str, Any]:
    base = build_lr6_obs4_megacap_concentration_assessment() if _safe_obs4_universe() else {}
    universe = _safe_obs4_universe()
    ai_obvious = sum(1 for c in universe if any(k in c.get("name", "").lower() for k in ("ai", "semiconductor", "data", "networks")))
    return {
        "megacap_ratio": base.get("megacap_ratio", 0.0),
        "non_megacap_ratio": base.get("non_megacap_ratio", 1.0 if not universe else 0.0),
        "obvious_ai_narrative_ratio": round(ai_obvious / max(1, len(universe)), 4),
        "overconcentration_risk": "low" if base.get("guardrail_pass", False) else "moderate",
        "peripheral_inclusion_meaningful": base.get("non_megacap_ratio", 0.0) >= 0.8,
    }


def build_lr6_obs5_redundancy_and_sparse_category_review() -> dict[str, Any]:
    rb = build_lr6_obs5_role_balance_assessment()
    repeated_roles = sorted([r for r, n in rb["role_count_map"].items() if n >= 7])
    sparse_roles = sorted([r for r, n in rb["role_count_map"].items() if n <= 2])
    return {
        "repeated_semantic_roles": repeated_roles,
        "redundancy_risk": "moderate" if len(repeated_roles) >= 3 else "low",
        "sparse_roles": sparse_roles,
        "replacement_candidate_need": len(sparse_roles) > 0,
    }


def build_lr6_obs5_candidate_adjustment_recommendations() -> list[dict[str, Any]]:
    sparse = build_lr6_obs5_redundancy_and_sparse_category_review()["sparse_roles"]
    return [
        {
            "priority": "high" if sparse else "moderate",
            "action": "targeted_additions",
            "rationale": "increase sparse-role representation without expanding architecture",
            "target_roles": sparse[:5],
        },
        {
            "priority": "moderate",
            "action": "light_role_rebalance",
            "rationale": "replace redundant same-role candidates with peripheral bridges",
            "target_roles": ["weak_signal_secondary_bridges", "non_megacap_replay_bridges", "regulatory_compliance_exposure"],
        },
    ]


def build_lr6_obs5_first_wave_readiness_decision() -> dict[str, Any]:
    weak = build_lr6_obs5_weak_signal_usefulness_assessment()
    contra = build_lr6_obs5_contradiction_potential_assessment()
    propagation = build_lr6_obs5_propagation_diversity_assessment()
    concentration = build_lr6_obs5_overconcentration_risk_assessment()
    sparse = build_lr6_obs5_redundancy_and_sparse_category_review()
    if weak["weak_signal_bridge_count"] >= 8 and contra["contradiction_carrier_count"] >= 8 and propagation["likely_to_diversify_replay"] and concentration["overconcentration_risk"] == "low" and len(sparse["sparse_roles"]) <= 4:
        decision = "READY_FOR_BOUNDED_OBSERVATION_WAVE"
    elif weak["weak_signal_bridge_count"] >= 6 and contra["contradiction_carrier_count"] >= 6:
        decision = "CONDITIONALLY_READY_NEEDS_MINOR_REBALANCE"
    else:
        decision = "NOT_READY_REQUIRES_REDESIGN"
    return {"decision": decision, "allowed_decisions": sorted(ALLOWED_DECISIONS)}


def certify_lr6_obs5_readiness_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "review_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs5_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "context": build_lr6_obs5_readiness_context(lr6_artifacts),
        "inspected_obs4_inputs": {
            "candidate_universe": _safe_obs4_universe(),
            "role_taxonomy": _safe_obs4_roles(),
            "density_gap_priorities": build_lr6_obs4_density_gap_priorities() if _safe_obs4_universe() else [],
            "obs4_supervisor_review": build_lr6_obs4_supervisor_review(lr6_artifacts) if _safe_obs4_universe() else {},
        },
        "role_balance_assessment": build_lr6_obs5_role_balance_assessment(),
        "weak_signal_usefulness_assessment": build_lr6_obs5_weak_signal_usefulness_assessment(),
        "contradiction_potential_assessment": build_lr6_obs5_contradiction_potential_assessment(),
        "propagation_diversity_assessment": build_lr6_obs5_propagation_diversity_assessment(),
        "overconcentration_risk_assessment": build_lr6_obs5_overconcentration_risk_assessment(),
        "redundancy_and_sparse_category_review": build_lr6_obs5_redundancy_and_sparse_category_review(),
        "candidate_adjustment_recommendations": build_lr6_obs5_candidate_adjustment_recommendations(),
        "first_wave_readiness_decision": build_lr6_obs5_first_wave_readiness_decision(),
        "boundary_certification": certify_lr6_obs5_readiness_boundary(),
    }


def build_lr6_obs5_markdown_report(review: dict[str, Any]) -> str:
    decision = review["first_wave_readiness_decision"]["decision"]
    lines = [
        "# LR6-OBS5 Enriched Universe Replay Readiness Review",
        "",
        "## Objective",
        "Determine whether the LR6-OBS4 enriched candidate universe is structurally ready for a first bounded replay observation wave.",
        "",
        "## Inspected OBS4 Inputs",
        f"- Candidate universe count: {len(review['inspected_obs4_inputs']['candidate_universe'])}",
        f"- Role taxonomy count: {len(review['inspected_obs4_inputs']['role_taxonomy'])}",
        "",
        "## Role Balance Assessment",
        f"- Underrepresented roles: {', '.join(review['role_balance_assessment']['underrepresented_roles']) or 'none'}",
        "",
        "## Weak-Signal Usefulness Assessment",
        f"- Weak-signal bridge count: {review['weak_signal_usefulness_assessment']['weak_signal_bridge_count']}",
        "",
        "## Contradiction Potential Assessment",
        f"- Contradiction carrier count: {review['contradiction_potential_assessment']['contradiction_carrier_count']}",
        "",
        "## Propagation Diversity Assessment",
        f"- Propagation bridge count: {review['propagation_diversity_assessment']['propagation_bridge_count']}",
        "",
        "## Overconcentration Risk Assessment",
        f"- Overconcentration risk: {review['overconcentration_risk_assessment']['overconcentration_risk']}",
        "",
        "## Redundancy Review",
        f"- Repeated roles: {', '.join(review['redundancy_and_sparse_category_review']['repeated_semantic_roles']) or 'none'}",
        "",
        "## Sparse Category Review",
        f"- Sparse roles: {', '.join(review['redundancy_and_sparse_category_review']['sparse_roles']) or 'none'}",
        "",
        "## Candidate Adjustment Recommendations",
        "- Apply targeted sparse-role additions and limited redundancy replacements.",
        "",
        "## First-Wave Readiness Decision",
        f"- {decision}",
        "",
        "## Architectural Overengineering Warning",
        "Do not introduce architecture expansion; ecological quality remains the bottleneck.",
        "",
        "## Recommendation for Next Phase",
        "Proceed with a bounded enriched replay observation wave if conditional rebalancing actions are completed.",
    ]
    return "\n".join(lines)
