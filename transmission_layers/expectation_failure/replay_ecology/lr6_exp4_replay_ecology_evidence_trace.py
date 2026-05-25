from __future__ import annotations

from collections import Counter
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.curated_stock_universe import load_curated_300_stock_universe
from transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation import (
    _build_longitudinal_slices,
    build_lr6_exp2_dashboard_payload,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout import (
    build_replay_ecology_signal_readout,
)

DETERMINISTIC_VERSION = "LR6_EXP4_REPLAY_ECOLOGY_EVIDENCE_TRACE_V1"
DETERMINISTIC_SEED = "LR6_EXP4_REPLAY_ECOLOGY_EVIDENCE_TRACE_SEED_V1"
MAX_ATTRIBUTION_ITEMS = 12


def _top(counter: Counter[str], limit: int = MAX_ATTRIBUTION_ITEMS) -> list[dict[str, Any]]:
    return [{"name": k, "count": int(v)} for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _band(value: float, low: float = 0.35, high: float = 0.65) -> str:
    if value < low:
        return "low"
    if value < high:
        return "moderate"
    return "high"


def _slice_records(max_entities: int, slice_count: int) -> list[dict[str, Any]]:
    slices = _build_longitudinal_slices(max_entities=max_entities, slice_count=slice_count)
    return [r for s in slices for r in s["entities"]]


def build_replay_drift_entity_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    entity_counts = Counter(r["ticker"] for r in rows)
    role_counts = Counter(r["ecosystem_role"] for r in rows)
    pathway_counts = Counter(tag for r in rows for tag in r["propagation_pathway_tags"])
    return {
        "top_replay_drift_entities": _top(entity_counts),
        "replay_drift_ecosystem_roles": _top(role_counts),
        "replay_drift_pathway_refs": _top(pathway_counts),
    }


def build_replay_drift_cluster_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    return {"replay_drift_cluster_contributors": _top(Counter(r["semantic_cluster"] for r in rows))}


def build_propagation_pathway_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    pathway_counts = Counter(tag for r in rows for tag in r["propagation_pathway_tags"])
    entity_counts = Counter(r["ticker"] for r in rows if len(r["propagation_pathway_tags"]) >= 2)
    cross_links = Counter(f"{r['semantic_cluster']}::{tag}" for r in rows for tag in r["propagation_pathway_tags"])
    return {
        "propagation_dense_entities": _top(entity_counts),
        "pathway_concentration_refs": _top(pathway_counts),
        "cross_cluster_pathway_links": _top(cross_links),
    }


def build_replay_bridge_entity_observation(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    bridge = Counter(r["ticker"] for r in rows if any("chain" in t for t in r["propagation_pathway_tags"]))
    return {"replay_bridge_entities": _top(bridge)}


def build_contradiction_entity_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    entity_counts = Counter(r["ticker"] for r in rows if r["contradiction_surface_tags"])
    cluster_counts = Counter(r["semantic_cluster"] for r in rows for _ in r["contradiction_surface_tags"])
    return {
        "contradiction_persistent_entities": _top(entity_counts),
        "contradiction_cluster_refs": _top(cluster_counts),
    }


def build_contradiction_surface_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    slices = _build_longitudinal_slices(max_entities=max_entities, slice_count=slice_count)
    first = Counter(tag for r in slices[0]["entities"] for tag in r["contradiction_surface_tags"])
    last = Counter(tag for r in slices[-1]["entities"] for tag in r["contradiction_surface_tags"])
    migration = Counter({k: abs(first.get(k, 0) - last.get(k, 0)) for k in sorted(set(first) | set(last))})
    return {
        "contradiction_surface_density": _top(last),
        "contradiction_migration_refs": _top(migration),
    }


def build_saturation_entity_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    recurrence = Counter(r["ticker"] for r in rows)
    saturation = Counter(r["ticker"] for r in rows if r["volatility_profile"] in {"high", "medium_high"})
    density = Counter(r["semantic_cluster"] for r in rows)
    return {
        "replay_recurrence_entities": _top(recurrence),
        "saturation_pressure_entities": _top(saturation),
        "replay_density_refs": _top(density),
    }


def build_novelty_decay_entity_trace(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    slices = _build_longitudinal_slices(max_entities=max_entities, slice_count=slice_count)
    first_tags = Counter(tag for r in slices[0]["entities"] for tag in r["narrative_tags"])
    last_tags = Counter(tag for r in slices[-1]["entities"] for tag in r["narrative_tags"])
    cluster_decay = Counter(r["semantic_cluster"] for r in slices[-1]["entities"])
    for r in slices[0]["entities"]:
        cluster_decay[r["semantic_cluster"]] -= 1
    return {
        "novelty_decay_clusters": _top(Counter({k: abs(v) for k, v in cluster_decay.items()})),
        "novelty_tag_decay_refs": _top(Counter({k: max(0, first_tags.get(k, 0) - last_tags.get(k, 0)) for k in first_tags})),
    }


def build_monoculture_entity_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    concentration = Counter(r["semantic_cluster"] for r in rows)
    entities = Counter(r["ticker"] for r in rows if r["semantic_cluster"] in {k for k, _ in concentration.most_common(2)})
    return {
        "replay_monoculture_entities": _top(entities),
        "cluster_concentration_refs": _top(concentration),
    }


def build_semantic_gravity_trace(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    gravity_entities = Counter(r["ticker"] for r in rows if r["ecosystem_role"] in {"propagation_hub", "replay_density_node", "regime_bridge"})
    diversity = Counter(r["semantic_cluster"] for r in rows)
    return {
        "semantic_gravity_entities": _top(gravity_entities),
        "diversity_decay_refs": _top(diversity),
    }


def build_ecosystem_interaction_attribution(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    interactions = Counter(r["ticker"] for r in rows if r["propagation_pathway_tags"] and r["contradiction_surface_tags"])
    cluster_pairs = Counter(f"{r['semantic_cluster']}::{r['ecosystem_role']}" for r in rows)
    coupling = Counter(r["ecosystem_role"] for r in rows)
    return {
        "replay_interaction_entities": _top(interactions),
        "cross_cluster_interaction_refs": _top(cluster_pairs),
        "ecosystem_coupling_entities": _top(coupling),
    }


def build_replay_cascade_entity_trace(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    rows = _slice_records(max_entities, slice_count)
    cascade = Counter(r["ticker"] for r in rows if any("chain" in t for t in r["propagation_pathway_tags"]))
    return {"replay_cascade_refs": _top(cascade)}


def build_replay_ecology_entity_attribution_summary(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    drift = build_replay_drift_entity_attribution(max_entities, slice_count)
    clusters = build_replay_drift_cluster_attribution(max_entities, slice_count)
    propagation = build_propagation_pathway_attribution(max_entities, slice_count)
    bridges = build_replay_bridge_entity_observation(max_entities, slice_count)
    contradiction = build_contradiction_entity_attribution(max_entities, slice_count)
    surfaces = build_contradiction_surface_attribution(max_entities, slice_count)
    saturation = build_saturation_entity_attribution(max_entities, slice_count)
    novelty = build_novelty_decay_entity_trace(max_entities, slice_count)
    monoculture = build_monoculture_entity_attribution(max_entities, slice_count)
    gravity = build_semantic_gravity_trace(max_entities, slice_count)
    interaction = build_ecosystem_interaction_attribution(max_entities, slice_count)
    cascades = build_replay_cascade_entity_trace(max_entities, slice_count)

    return {**drift, **clusters, **propagation, **bridges, **contradiction, **surfaces, **saturation, **novelty, **monoculture, **gravity, **interaction, **cascades}


def certify_lr6_exp4_experimental_boundaries() -> dict[str, Any]:
    return {"experimental_mode_only": True, "governed_lr6_activation": False, "no_persistence_writes": True, "no_direct_sql": True, "no_external_apis": True, "no_prediction_or_trading": True, "bounded_observation_only": True}


def build_replay_ecology_evidence_trace(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    exp2 = build_lr6_exp2_dashboard_payload(max_entities=max_entities, slice_count=slice_count)
    exp3 = build_replay_ecology_signal_readout(max_entities=max_entities, slice_count=slice_count)
    attribution = build_replay_ecology_entity_attribution_summary(max_entities, slice_count)

    summary = {
        "most_referenced_entities": attribution["top_replay_drift_entities"],
        "most_referenced_clusters": attribution["replay_drift_cluster_contributors"],
        "strongest_replay_bridge_entities": attribution["replay_bridge_entities"],
        "strongest_contradiction_surfaces": attribution["contradiction_surface_density"],
        "strongest_propagation_pathways": attribution["pathway_concentration_refs"],
        "strongest_saturation_signals": attribution["saturation_pressure_entities"],
        "strongest_interaction_zones": attribution["cross_cluster_interaction_refs"],
        "replay_ecology_density_band": _band(exp2["longitudinal_summary"]["longitudinal_replay_ecology_score"]),
        "replay_ecology_maturity_band": exp3["interpretation_summary"]["replay_ecology_maturity_band"],
        "observation_confidence_band": exp3["interpretation_summary"]["observation_confidence_band"],
        "ecological_caveats": exp3["interpretation_summary"]["caveats"],
        "next_observation_priorities": exp3["interpretation_summary"]["next_observation_priorities"],
    }

    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "observation_window": {"max_entities": max_entities, "slice_count": slice_count},
        "input_references": {
            "exp2": {"deterministic_version": exp2["deterministic_version"], "deterministic_seed": exp2["deterministic_seed"]},
            "exp3": {"deterministic_version": exp3["deterministic_version"], "deterministic_seed": exp3["deterministic_seed"]},
            "sde2_universe_size": len(load_curated_300_stock_universe()),
        },
        "attribution_domains": attribution,
        "composite_attribution_summary": summary,
        "experimental_certification": certify_lr6_exp4_experimental_boundaries(),
    }


def build_lr6_exp4_dashboard_payload(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    payload = build_replay_ecology_evidence_trace(max_entities=max_entities, slice_count=slice_count)
    return {
        "phase": "LR6-EXP4",
        "objective": "Replay ecology evidence trace and entity-level attribution",
        "evidence_trace_payload": payload,
        "dashboard_sections": {
            "replay_drift_attribution": {"entities": payload["attribution_domains"]["top_replay_drift_entities"], "clusters": payload["attribution_domains"]["replay_drift_cluster_contributors"]},
            "propagation_pathway_attribution": {"dense_entities": payload["attribution_domains"]["propagation_dense_entities"], "bridges": payload["attribution_domains"]["replay_bridge_entities"]},
            "contradiction_ecology_attribution": {"persistent_entities": payload["attribution_domains"]["contradiction_persistent_entities"], "surface_density": payload["attribution_domains"]["contradiction_surface_density"]},
            "saturation_novelty_attribution": {"recurrence_entities": payload["attribution_domains"]["replay_recurrence_entities"], "novelty_decay_clusters": payload["attribution_domains"]["novelty_decay_clusters"]},
            "monoculture_diversity_attribution": {"gravity_entities": payload["attribution_domains"]["semantic_gravity_entities"], "concentration_refs": payload["attribution_domains"]["cluster_concentration_refs"]},
            "ecosystem_interaction_attribution": {"interaction_entities": payload["attribution_domains"]["replay_interaction_entities"], "cascade_refs": payload["attribution_domains"]["replay_cascade_refs"]},
            "composite_summary": payload["composite_attribution_summary"],
        },
    }
