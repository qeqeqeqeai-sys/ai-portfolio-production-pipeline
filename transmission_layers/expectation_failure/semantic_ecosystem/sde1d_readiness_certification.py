from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

DETERMINISTIC_VERSION = "SDE1D_READINESS_V1"
DETERMINISTIC_SEED = "SDE1D_READINESS_SEED_V1"
READINESS_THRESHOLD = 0.70


def load_sde1d_pruned_universe(config_path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(config_path).read_text())
    return payload


def _selected(pruned_universe: dict[str, Any]) -> list[dict[str, Any]]:
    return list(pruned_universe.get("selected_entities", []))


def build_sde1d_ecosystem_coverage_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    counts = Counter(e["primary_ecosystem"] for e in entities)
    total = len(entities)
    ecosystem_count = len(counts)
    coverage_completeness = round(ecosystem_count / 12, 6)
    expected_share = 1 / max(1, ecosystem_count)
    concentration_gap = sum(abs((v / total) - expected_share) for v in counts.values()) / 2
    ecosystem_balance_score = round(max(0.0, 1.0 - concentration_gap), 6)

    cross_connections = 0
    for e in entities:
        sec = set(e.get("secondary_ecosystems", []))
        if any(s != e["primary_ecosystem"] for s in sec):
            cross_connections += 1
    cross_connectivity = round(cross_connections / max(1, total), 6)

    return {
        "ecosystem_coverage_completeness": coverage_completeness,
        "ecosystem_balance_score": ecosystem_balance_score,
        "cross_ecosystem_connectivity_score": cross_connectivity,
        "ecosystem_counts": dict(counts),
    }


def build_sde1d_topology_richness_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    avg_links = sum(len(e.get("propagation_links", [])) for e in entities) / max(1, len(entities))
    avg_secondary = sum(len(set(e.get("secondary_ecosystems", []))) for e in entities) / max(1, len(entities))
    topology_score = round(min(1.0, ((avg_links / 3) * 0.6) + ((avg_secondary / 2) * 0.4)), 6)
    return {
        "average_propagation_links": round(avg_links, 6),
        "average_secondary_ecosystems": round(avg_secondary, 6),
        "topology_richness_score": topology_score,
    }


def build_sde1d_contradiction_density_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    avg_contradictions = sum(len(e.get("contradiction_surfaces", [])) for e in entities) / max(1, len(entities))
    score = round(min(1.0, avg_contradictions / 2.5), 6)
    return {
        "average_contradiction_surfaces": round(avg_contradictions, 6),
        "contradiction_density_score": score,
    }


def build_sde1d_propagation_pathway_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    role_diversity = len({e.get("propagation_role") for e in entities if e.get("propagation_role")})
    avg_links = sum(len(e.get("propagation_links", [])) for e in entities) / max(1, len(entities))
    score = round(min(1.0, (role_diversity / 4) * 0.4 + (avg_links / 3) * 0.6), 6)
    return {
        "propagation_role_diversity": role_diversity,
        "average_pathway_links": round(avg_links, 6),
        "propagation_pathway_richness_score": score,
    }


def build_sde1d_regime_exposure_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    exposures = Counter()
    for e in entities:
        exposures.update(set(e.get("regime_exposures", [])))
    diversity = len(exposures)
    total = sum(exposures.values())
    normalized_concentration = 0.0
    if total:
        normalized_concentration = sum((v / total) ** 2 for v in exposures.values())
    score = round(max(0.0, min(1.0, (diversity / 6) * 0.7 + (1 - normalized_concentration) * 0.3)), 6)
    return {
        "unique_regime_exposures": diversity,
        "regime_exposure_distribution": dict(exposures),
        "regime_exposure_diversity_score": score,
    }


def build_sde1d_monoculture_risk_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    counts = Counter(e["primary_ecosystem"] for e in entities)
    max_share = max(counts.values()) / max(1, len(entities))
    risk = round(min(1.0, max_share / 0.25), 6)
    return {"max_primary_ecosystem_share": round(max_share, 6), "monoculture_risk_score": risk}


def build_sde1d_low_information_risk_diagnostics(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    entities = _selected(pruned_universe)
    low_info = [e for e in entities if float(e.get("information_quality_score", 0.0)) < 0.60]
    ratio = len(low_info) / max(1, len(entities))
    risk = round(min(1.0, ratio / 0.30), 6)
    return {
        "low_information_entity_count": len(low_info),
        "low_information_entity_ratio": round(ratio, 6),
        "low_information_risk_score": risk,
    }


def certify_sde1d_semantic_ecosystem_readiness(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    coverage = build_sde1d_ecosystem_coverage_diagnostics(pruned_universe)
    topology = build_sde1d_topology_richness_diagnostics(pruned_universe)
    contradiction = build_sde1d_contradiction_density_diagnostics(pruned_universe)
    propagation = build_sde1d_propagation_pathway_diagnostics(pruned_universe)
    regime = build_sde1d_regime_exposure_diagnostics(pruned_universe)
    monoculture = build_sde1d_monoculture_risk_diagnostics(pruned_universe)
    low_info = build_sde1d_low_information_risk_diagnostics(pruned_universe)

    readiness_score = round(
        (
            coverage["ecosystem_coverage_completeness"] * 0.12
            + coverage["ecosystem_balance_score"] * 0.12
            + coverage["cross_ecosystem_connectivity_score"] * 0.10
            + topology["topology_richness_score"] * 0.16
            + contradiction["contradiction_density_score"] * 0.12
            + propagation["propagation_pathway_richness_score"] * 0.12
            + regime["regime_exposure_diversity_score"] * 0.12
            + (1 - monoculture["monoculture_risk_score"]) * 0.08
            + (1 - low_info["low_information_risk_score"]) * 0.06
        ),
        6,
    )
    ready = readiness_score >= READINESS_THRESHOLD
    return {
        "topology_readiness_score": readiness_score,
        "readiness_threshold": READINESS_THRESHOLD,
        "lr6_reactivation_readiness_flag": ready,
        "readiness_decision": "certified_ready" if ready else "not_ready",
        "gating_status": "gate_passed" if ready else "gate_blocked",
    }


def build_sde1d_governance_certification() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "no_replay_execution_introduced": True,
        "no_replay_waves_introduced": True,
        "no_persistence_write_path_introduced": True,
        "no_direct_sql_introduced": True,
        "no_external_api_calls_introduced": True,
        "no_prediction_or_trading_logic_introduced": True,
        "no_autonomous_entity_expansion_introduced": True,
        "additive_architecture_preserved": True,
    }


def build_sde1d_readiness_report_payload(pruned_universe: dict[str, Any]) -> dict[str, Any]:
    coverage = build_sde1d_ecosystem_coverage_diagnostics(pruned_universe)
    topology = build_sde1d_topology_richness_diagnostics(pruned_universe)
    contradiction = build_sde1d_contradiction_density_diagnostics(pruned_universe)
    propagation = build_sde1d_propagation_pathway_diagnostics(pruned_universe)
    regime = build_sde1d_regime_exposure_diagnostics(pruned_universe)
    monoculture = build_sde1d_monoculture_risk_diagnostics(pruned_universe)
    low_info = build_sde1d_low_information_risk_diagnostics(pruned_universe)
    certification = certify_sde1d_semantic_ecosystem_readiness(pruned_universe)
    return {
        "version": DETERMINISTIC_VERSION,
        "seed": DETERMINISTIC_SEED,
        "source_pruned_universe": pruned_universe.get("source_config", "configs/sde1c_pruned_entity_universe.yaml"),
        "diagnostics": {
            **coverage,
            **topology,
            **contradiction,
            **propagation,
            **regime,
            **monoculture,
            **low_info,
            **certification,
        },
        "governance_certification": build_sde1d_governance_certification(),
        "next_recommended_phase": "SDE-1E / LR6 reactivation planning (no execution in SDE-1D)",
    }
