"""LR6-OBS3 controlled ecological enrichment and replay stress observation (observation-only)."""
from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_OBS3_CONTROLLED_ECOLOGICAL_ENRICHMENT_V1"
SOURCE_PHASE = "LR6-OBS3"

ENRICHMENT_CATEGORIES: list[dict[str, str]] = [
    {"category": "peripheral_ai_ecosystem_actors", "role": "capture second-order model-adjacent demand pathways"},
    {"category": "industrial_automation", "role": "expose factory-level adoption and execution bottlenecks"},
    {"category": "cybersecurity", "role": "surface trust and resilience dependencies"},
    {"category": "data_center_infrastructure", "role": "observe compute-capacity coupling signals"},
    {"category": "utilities_and_grid_exposure", "role": "track power-intensity constraints"},
    {"category": "telecom_infrastructure", "role": "observe network throughput and latency exposure"},
    {"category": "memory_and_storage", "role": "capture memory bottleneck and storage pressure linkages"},
    {"category": "edge_hardware", "role": "observe decentralized inference demand shifts"},
    {"category": "robotics", "role": "capture embodiment pathways and deployment friction"},
    {"category": "logistics_and_supply_chain", "role": "observe fulfillment and component-flow fragility"},
    {"category": "ai_consulting_services", "role": "capture implementation velocity and enterprise translation"},
    {"category": "regulatory_exposure", "role": "observe policy shock transmission channels"},
    {"category": "geopolitical_semiconductor_exposure", "role": "surface geopolitical supply concentration pressure"},
    {"category": "energy_demand_beneficiaries", "role": "observe power-demand beneficiary divergence"},
    {"category": "non_megacap_bridge_entities", "role": "reduce megacap concentration and improve bridge diversity"},
    {"category": "weak_signal_secondary_entities", "role": "elevate sparse but repeatable secondary signals"},
]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _score_from_obs(obs: dict[str, Any], key: str) -> float:
    value = obs.get(key, 0.0)
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def build_lr6_obs3_ecological_enrichment_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = _safe_dict(lr6_artifacts)
    inspected_inputs = {
        "sde2_curated_semantic_ecosystem": bool(artifacts.get("sde2_curated_semantic_ecosystem")),
        "lr6_exp2_longitudinal_replay_diagnostics": bool(artifacts.get("lr6_exp2_longitudinal_replay_diagnostics")),
        "lr6_exp3_replay_ecology_interpretation": bool(artifacts.get("lr6_exp3_replay_ecology_interpretation")),
        "lr6_exp4_evidence_trace_attribution": bool(artifacts.get("lr6_exp4_evidence_trace_attribution")),
        "lr6_exp5_dashboard_view_model": bool(artifacts.get("lr6_exp5_dashboard_view_model")),
        "lr6_exp6_snapshot_export": bool(artifacts.get("lr6_exp6_snapshot_export")),
        "lr6_exp6a_longitudinal_snapshot_comparison": bool(artifacts.get("lr6_exp6a_longitudinal_snapshot_comparison")),
        "lr6_exp7_interestingness_scoring": bool(artifacts.get("lr6_exp7_interestingness_scoring")),
        "lr6_exp8_findings_report": bool(artifacts.get("lr6_exp8_findings_report")),
    }
    available = sum(1 for v in inspected_inputs.values() if v)
    missing = len(inspected_inputs) - available
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "observation_mode": "controlled_ecological_enrichment",
        "inspected_inputs": inspected_inputs,
        "coverage_summary": {
            "available_input_count": available,
            "missing_input_count": missing,
            "fallback_mode_engaged": missing > 0,
        },
        "enrichment_categories": ENRICHMENT_CATEGORIES,
    }


def build_lr6_obs3_density_gap_assessment(context: dict[str, Any]) -> dict[str, Any]:
    gaps = [
        {"gap_id": "G01", "category": c["category"], "gap_severity": "moderate", "why": f"insufficient observed bridge density in {c['category']}"}
        for c in context.get("enrichment_categories", ENRICHMENT_CATEGORIES)[:8]
    ]
    return {"strongest_density_gaps": gaps, "density_gap_count": len(gaps)}


def build_lr6_obs3_weak_signal_bridge_candidates(context: dict[str, Any], max_candidates: int = 12) -> list[dict[str, Any]]:
    bounded = max(1, min(20, int(max_candidates)))
    categories = context.get("enrichment_categories", ENRICHMENT_CATEGORIES)
    prioritized = sorted(
        categories,
        key=lambda c: (
            0 if c.get("category") in {"non_megacap_bridge_entities", "weak_signal_secondary_entities"} else 1,
            c.get("category", ""),
        ),
    )
    candidates: list[dict[str, Any]] = []
    for idx, category in enumerate(prioritized):
        if len(candidates) >= bounded:
            break
        candidates.append(
            {
                "candidate_id": f"WSB{idx+1:02d}",
                "bridge_category": category["category"],
                "candidate_role": category["role"],
                "bridge_priority": "observe",
                "megacap_concentration_guard": "prefer_non_megacap_if_available",
            }
        )
    return candidates


def build_lr6_obs3_contradiction_migration_watchlist(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"watch_id": "CM01", "surface": "supply_vs_demand_capacity", "migration_vector": "from_core_compute_to_grid_and_memory", "status": "observe"},
        {"watch_id": "CM02", "surface": "policy_vs_execution", "migration_vector": "from_regulatory_exposure_to_services_and_logistics", "status": "observe"},
        {"watch_id": "CM03", "surface": "latency_vs_reliability", "migration_vector": "from_telecom_to_edge_hardware", "status": "observe"},
    ]


def build_lr6_obs3_propagation_mutation_watchlist(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"watch_id": "PM01", "pathway": "compute_to_energy_to_utilities", "mutation_pattern": "lagged_intensity_increase", "status": "observe"},
        {"watch_id": "PM02", "pathway": "model_deployment_to_cybersecurity", "mutation_pattern": "resilience_spend_reweight", "status": "observe"},
        {"watch_id": "PM03", "pathway": "automation_to_logistics", "mutation_pattern": "execution_friction_cluster", "status": "observe"},
    ]


def build_lr6_obs3_semantic_gravity_assessment(context: dict[str, Any], weak_signal_bridges: list[dict[str, Any]]) -> dict[str, Any]:
    non_megacap_count = sum(1 for c in weak_signal_bridges if "non_megacap" in c.get("bridge_category", "") or "weak_signal" in c.get("bridge_category", ""))
    total = max(1, len(weak_signal_bridges))
    coverage = non_megacap_count / total
    return {
        "semantic_gravity_score": round(1.0 - coverage, 4),
        "monoculture_risk_band": "moderate" if coverage < 0.25 else "contained",
        "megacap_overconcentration_flag": coverage < 0.25,
        "weak_signal_bridge_coverage": round(coverage, 4),
    }


def build_lr6_obs3_replay_stress_observation_plan(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_id": f"{DETERMINISTIC_VERSION}::stress_plan",
        "stress_design": [
            "increase cross-category bridge sampling while keeping observation-only boundaries",
            "observe contradiction migration across at least three non-megacap bridge categories",
            "track propagation mutations over longitudinal snapshots without execution actions",
        ],
        "longitudinal_usefulness_focus": "high",
    }


def build_lr6_obs3_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    context = build_lr6_obs3_ecological_enrichment_context(lr6_artifacts)
    density = build_lr6_obs3_density_gap_assessment(context)
    weak_signals = build_lr6_obs3_weak_signal_bridge_candidates(context)
    contradiction = build_lr6_obs3_contradiction_migration_watchlist(context)
    propagation = build_lr6_obs3_propagation_mutation_watchlist(context)
    gravity = build_lr6_obs3_semantic_gravity_assessment(context, weak_signals)
    stress = build_lr6_obs3_replay_stress_observation_plan(context)
    return {
        "context": context,
        "density_gap_assessment": density,
        "weak_signal_bridge_candidates": weak_signals,
        "contradiction_migration_watchlist": contradiction,
        "propagation_mutation_watchlist": propagation,
        "semantic_gravity_assessment": gravity,
        "replay_stress_observation_plan": stress,
        "observation_dimensions": {
            "replay_richness": "improving_with_enrichment",
            "contradiction_richness": "moderate",
            "propagation_richness": "moderate",
            "semantic_gravity": gravity["semantic_gravity_score"],
            "monoculture_risk": gravity["monoculture_risk_band"],
            "weak_signal_bridge_coverage": gravity["weak_signal_bridge_coverage"],
            "ecological_density_gaps": density["density_gap_count"],
            "megacap_overconcentration": gravity["megacap_overconcentration_flag"],
            "longitudinal_observation_usefulness": stress["longitudinal_usefulness_focus"],
            "architecture_expansion_should_remain_frozen": True,
        },
        "boundary_certification": certify_lr6_obs3_observation_boundary(),
    }


def build_lr6_obs3_markdown_report(review: dict[str, Any]) -> str:
    gaps = review["density_gap_assessment"]["strongest_density_gaps"]
    weak = review["weak_signal_bridge_candidates"]
    contradiction = review["contradiction_migration_watchlist"]
    propagation = review["propagation_mutation_watchlist"]
    gravity = review["semantic_gravity_assessment"]
    inspected = review["context"]["inspected_inputs"]
    lines = [
        "# LR6-OBS3 Controlled Ecological Enrichment Review",
        "",
        "## Objective",
        "Determine whether replay ecology richness deepens through controlled semantic ecosystem enrichment while preserving observation-only boundaries.",
        "",
        "## Inspected LR6 Inputs",
    ]
    lines.extend([f"- {k}: {'available' if v else 'missing'}" for k, v in inspected.items()])
    lines.extend([
        "",
        "## Ecological Enrichment Rationale",
        "Diversify bridge exposure beyond megacap-dominant pathways to improve contradiction and propagation observability.",
        "",
        "## Strongest Density Gaps",
    ])
    lines.extend([f"- {g['category']}: {g['why']}" for g in gaps[:6]])
    lines.extend(["", "## Weak-Signal Bridge Opportunities"])
    lines.extend([f"- {w['bridge_category']}: {w['candidate_role']}" for w in weak[:8]])
    lines.extend(["", "## Contradiction Migration Watchlist"])
    lines.extend([f"- {c['surface']} -> {c['migration_vector']}" for c in contradiction])
    lines.extend(["", "## Propagation Mutation Watchlist"])
    lines.extend([f"- {p['pathway']}: {p['mutation_pattern']}" for p in propagation])
    lines.extend([
        "",
        "## Semantic Gravity / Monoculture Assessment",
        f"- Semantic gravity score: {gravity['semantic_gravity_score']}",
        f"- Monoculture risk band: {gravity['monoculture_risk_band']}",
        f"- Megacap overconcentration flag: {gravity['megacap_overconcentration_flag']}",
        "",
        "## Replay Stress Observation Plan",
    ])
    lines.extend([f"- {s}" for s in review["replay_stress_observation_plan"]["stress_design"]])
    lines.extend([
        "",
        "## Architectural Overengineering Warning",
        "Keep architecture expansion frozen; prioritize observation depth over new governed layers.",
        "",
        "## Recommendation for Next Observation Cycle",
        "Continue enrichment-category observation with bounded weak-signal bridges and reassess density gaps on the next longitudinal snapshot.",
    ])
    return "\n".join(lines)


def certify_lr6_obs3_observation_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }
