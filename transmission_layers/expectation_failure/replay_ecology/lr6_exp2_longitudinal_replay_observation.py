from __future__ import annotations

from collections import Counter
from math import log2
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.curated_stock_universe import (
    load_curated_300_stock_universe,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_exp1_bounded_semantic_observation import (
    DEFAULT_MAX_ENTITIES,
)

DETERMINISTIC_VERSION = "LR6_EXP2_LONGITUDINAL_REPLAY_OBSERVATION_V1"
DETERMINISTIC_SEED = "LR6_EXP2_LONGITUDINAL_REPLAY_OBSERVATION_SEED_V1"
DEFAULT_SLICE_COUNT = 4


def _entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((v / total) * log2(v / total) for v in counter.values() if v)


def _build_longitudinal_slices(max_entities: int = DEFAULT_MAX_ENTITIES, slice_count: int = DEFAULT_SLICE_COUNT) -> list[dict[str, Any]]:
    records = sorted(load_curated_300_stock_universe(), key=lambda r: (r["semantic_cluster"], r["ticker"]))
    step = max(1, len(records) // slice_count)
    slices: list[dict[str, Any]] = []
    for idx in range(slice_count):
        start = (idx * step) % len(records)
        entities = [records[(start + n) % len(records)] for n in range(min(max_entities, len(records)))]
        slices.append({"slice_index": idx, "entities": entities})
    return slices


def build_longitudinal_replay_drift(slices: list[dict[str, Any]]) -> dict[str, Any]:
    first = Counter(r["semantic_cluster"] for r in slices[0]["entities"])
    last = Counter(r["semantic_cluster"] for r in slices[-1]["entities"])
    delta = sum(abs(first.get(k, 0) - last.get(k, 0)) for k in sorted(set(first) | set(last)))
    drift = delta / max(1, len(slices[0]["entities"]))
    return {"replay_drift_score": round(drift, 6), "topology_stability_index": round(1.0 - min(1.0, drift), 6), "replay_persistence_score": round(1.0 - min(1.0, drift / 2.0), 6)}


def build_semantic_velocity_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    entropies = [_entropy(Counter(r["semantic_cluster"] for r in s["entities"])) for s in slices]
    diffs = [abs(entropies[i] - entropies[i - 1]) for i in range(1, len(entropies))]
    return {"semantic_velocity": round(sum(diffs) / max(1, len(diffs)), 6), "topology_entropy_series": [round(v, 6) for v in entropies]}


def build_replay_recurrence_evolution(slices: list[dict[str, Any]]) -> dict[str, Any]:
    sets = [set(r["ticker"] for r in s["entities"]) for s in slices]
    overlap = [len(sets[i] & sets[i - 1]) / max(1, len(sets[i])) for i in range(1, len(sets))]
    recurrence = sum(overlap) / max(1, len(overlap))
    return {"recurrence_decay": round(1.0 - recurrence, 6), "replay_recurrence": round(recurrence, 6)}


def build_propagation_evolution_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    path_counters = [Counter(tag for r in s["entities"] for tag in r["propagation_pathway_tags"]) for s in slices]
    first_entropy = _entropy(path_counters[0])
    last_entropy = _entropy(path_counters[-1])
    concentration = max(path_counters[-1].values()) / max(1, sum(path_counters[-1].values()))
    return {"propagation_entropy": round(last_entropy, 6), "pathway_concentration": round(concentration, 6), "pathway_diversity_delta": round(last_entropy - first_entropy, 6)}


def build_replay_flow_fragmentation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    counter = Counter(tag for s in slices for r in s["entities"] for tag in r["propagation_pathway_tags"])
    fragmentation = len(counter) / max(1, sum(counter.values()))
    return {"propagation_fragmentation": round(fragmentation, 6), "replay_flow_stability": round(1.0 - min(1.0, fragmentation * 10), 6)}


def build_pathway_diversity_evolution(slices: list[dict[str, Any]]) -> dict[str, Any]:
    diversity = [len({tag for r in s["entities"] for tag in r["propagation_pathway_tags"]}) for s in slices]
    return {"pathway_diversity_series": diversity, "pathway_diversity_delta": diversity[-1] - diversity[0]}


def build_contradiction_ecology_evolution(slices: list[dict[str, Any]]) -> dict[str, Any]:
    sets = [set(tag for r in s["entities"] for tag in r["contradiction_surface_tags"]) for s in slices]
    persistence = len(set.intersection(*sets)) / max(1, len(set.union(*sets)))
    return {"contradiction_persistence": round(persistence, 6), "contradiction_recurrence": round(persistence, 6), "contradiction_stability": round(persistence, 6)}


def build_contradiction_cluster_drift(slices: list[dict[str, Any]]) -> dict[str, Any]:
    counts = [Counter(r["semantic_cluster"] for r in s["entities"] if "valuation excess" in r["contradiction_surface_tags"]) for s in slices]
    keys = sorted(set().union(*[set(c) for c in counts]))
    drift = sum(abs(counts[0].get(k, 0) - counts[-1].get(k, 0)) for k in keys) / max(1, len(slices[0]["entities"]))
    return {"contradiction_cluster_drift": round(drift, 6), "contradiction_density_delta": round((sum(counts[-1].values()) - sum(counts[0].values())) / max(1, len(slices[0]["entities"])), 6)}


def build_contradiction_persistence_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    return build_contradiction_ecology_evolution(slices)


def build_saturation_evolution_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    max_shares = []
    for s in slices:
        c = Counter(r["semantic_cluster"] for r in s["entities"])
        max_shares.append(max(c.values()) / len(s["entities"]))
    velocity = (max_shares[-1] - max_shares[0]) / max(1, len(max_shares) - 1)
    return {"saturation_velocity": round(velocity, 6), "semantic_redundancy_growth": round(max_shares[-1] - max_shares[0], 6)}


def build_novelty_decay_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    unique_tags = [len({tag for r in s["entities"] for tag in r["narrative_tags"]}) for s in slices]
    return {"novelty_decay_rate": round((unique_tags[0] - unique_tags[-1]) / max(1, unique_tags[0]), 6)}


def build_semantic_compression_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    uniques = [len({r["semantic_cluster"] for r in s["entities"]}) for s in slices]
    return {"replay_compression_index": round(1.0 - (uniques[-1] / max(1, uniques[0])), 6)}


def build_monoculture_drift_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    c0 = Counter(r["semantic_cluster"] for r in slices[0]["entities"])
    c1 = Counter(r["semantic_cluster"] for r in slices[-1]["entities"])
    m0 = max(c0.values()) / len(slices[0]["entities"])
    m1 = max(c1.values()) / len(slices[-1]["entities"])
    return {"monoculture_drift": round(m1 - m0, 6), "diversity_decay": round(max(0.0, m1 - m0), 6), "replay_concentration_trend": round(m1, 6)}


def build_semantic_gravity_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    last = Counter(r["semantic_cluster"] for r in slices[-1]["entities"])
    return {"semantic_gravity_index": round(max(last.values()) / len(slices[-1]["entities"]), 6)}


def build_cluster_dominance_evolution(slices: list[dict[str, Any]]) -> dict[str, Any]:
    names = [Counter(r["semantic_cluster"] for r in s["entities"]).most_common(1)[0][0] for s in slices]
    return {"cluster_dominance_shift": len(set(names)) - 1, "dominant_cluster_series": names}


def build_ecosystem_interaction_evolution(slices: list[dict[str, Any]]) -> dict[str, Any]:
    densities = []
    for s in slices:
        edges = sum(len(set(r["propagation_pathway_tags"])) + len(set(r["contradiction_surface_tags"])) for r in s["entities"])
        densities.append(edges / len(s["entities"]))
    return {"interaction_density_delta": round(densities[-1] - densities[0], 6), "ecosystem_cohesion_shift": round(sum(densities) / len(densities), 6)}


def build_replay_cascade_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    cascades = [len({tag for r in s["entities"] for tag in r["propagation_pathway_tags"] if "chain" in tag}) for s in slices]
    return {"replay_cascade_emergence": cascades[-1] - cascades[0]}


def build_cross_cluster_coupling_observation(slices: list[dict[str, Any]]) -> dict[str, Any]:
    ratios = []
    for s in slices:
        total = 0
        cross = 0
        for r in s["entities"]:
            total += len(r["propagation_pathway_tags"])
            cross += sum(1 for tag in r["propagation_pathway_tags"] if "chain" in tag)
        ratios.append(cross / max(1, total))
    return {"cross_cluster_replay_coupling": round(sum(ratios) / len(ratios), 6), "semantic_neighbor_influence": round(ratios[-1], 6)}


def build_longitudinal_replay_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    score = (
        metrics["replay_drift"]["topology_stability_index"]
        + (1.0 - metrics["saturation"]["semantic_redundancy_growth"])
        + metrics["interaction"]["ecosystem_cohesion_shift"] / 10.0
        + metrics["contradiction"]["contradiction_persistence"]
    ) / 4.0
    return {"longitudinal_replay_ecology_score": round(score, 6), "bounded_observation_only": True}


def certify_lr6_exp2_experimental_boundaries() -> dict[str, Any]:
    return {"experimental_mode_only": True, "governed_lr6_activation": False, "no_persistence_writes": True, "no_direct_sql": True, "no_external_apis": True, "no_prediction_or_trading": True, "additive_architecture_preserved": True, "anti_monoculture_controls_preserved": True}


def build_lr6_exp2_dashboard_payload(max_entities: int = DEFAULT_MAX_ENTITIES, slice_count: int = DEFAULT_SLICE_COUNT) -> dict[str, Any]:
    slices = _build_longitudinal_slices(max_entities=max_entities, slice_count=slice_count)
    metrics = {
        "replay_drift": {**build_longitudinal_replay_drift(slices), **build_semantic_velocity_observation(slices), **build_replay_recurrence_evolution(slices)},
        "propagation": {**build_propagation_evolution_observation(slices), **build_replay_flow_fragmentation(slices), **build_pathway_diversity_evolution(slices)},
        "contradiction": {**build_contradiction_ecology_evolution(slices), **build_contradiction_cluster_drift(slices), **build_contradiction_persistence_observation(slices)},
        "saturation": {**build_saturation_evolution_observation(slices), **build_novelty_decay_observation(slices), **build_semantic_compression_observation(slices)},
        "monoculture": {**build_monoculture_drift_observation(slices), **build_semantic_gravity_observation(slices), **build_cluster_dominance_evolution(slices)},
        "interaction": {**build_ecosystem_interaction_evolution(slices), **build_replay_cascade_observation(slices), **build_cross_cluster_coupling_observation(slices)},
    }
    return {"deterministic_version": DETERMINISTIC_VERSION, "deterministic_seed": DETERMINISTIC_SEED, "observation_window": {"max_entities": max_entities, "slice_count": slice_count}, "observation_metrics": metrics, "longitudinal_summary": build_longitudinal_replay_summary(metrics), "experimental_certification": certify_lr6_exp2_experimental_boundaries()}
