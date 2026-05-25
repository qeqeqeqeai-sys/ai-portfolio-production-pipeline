from __future__ import annotations

from pathlib import Path
import json
from typing import Any


DETERMINISTIC_VERSION = "LR6_EXP1_BOUNDED_SEMANTIC_OBSERVATION_V1"
DETERMINISTIC_SEED = "LR6_EXP1_BOUNDED_SEMANTIC_OBSERVATION_SEED_V1"
DEFAULT_MAX_ENTITIES = 90

INPUT_PATHS = {
    "sde1c_pruned_universe": "configs/sde1c_pruned_entity_universe.yaml",
    "sde1d_readiness": "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    "lr6_governance_freeze": "configs/lr6_governance_freeze_and_mode_separation.yaml",
    "lr6_dry4_guardrails": "configs/lr6_dry4_full_universe_saturation_guardrails.yaml",
}


def _load_json_or_yaml(path: str) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        data: dict[str, Any] = {}
        current_key: str | None = None
        for line in raw.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if ":" in line and not line.startswith("  -"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value:
                    data[key] = value
                    current_key = None
                else:
                    data[key] = []
                    current_key = key
            elif line.strip().startswith("-") and current_key:
                data[current_key].append(line.strip().lstrip("-").strip())
        return data


def load_lr6_exp1_inputs() -> dict[str, Any]:
    return {name: _load_json_or_yaml(path) for name, path in INPUT_PATHS.items()}


def build_lr6_exp1_experimental_mode_context(inputs: dict[str, Any]) -> dict[str, Any]:
    freeze = inputs["lr6_governance_freeze"]
    rules = sorted(set(freeze.get("experimental_mode_rules", [])))
    return {
        "mode": "experimental_mode",
        "profile": "bounded_semantic_replay_observation",
        "deterministic": True,
        "persistence": "disabled",
        "governed_lr6_active": False,
        "safety_rails": sorted(set(freeze.get("retained_safety_rails", []))),
        "experimental_rules": rules,
    }


def _entity_order_key(entity: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entity.get("primary_ecosystem", ""),
        -float(entity.get("information_quality_score", 0.0)),
        entity.get("entity_id", ""),
    )


def build_lr6_exp1_observation_window(
    inputs: dict[str, Any],
    max_entities: int = DEFAULT_MAX_ENTITIES,
) -> dict[str, Any]:
    entities = sorted(inputs["sde1c_pruned_universe"]["selected_entities"], key=_entity_order_key)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        grouped.setdefault(entity["primary_ecosystem"], []).append(entity)

    selected: list[dict[str, Any]] = []
    ecosystems = sorted(grouped)
    while len(selected) < max_entities and any(grouped.values()):
        for ecosystem in ecosystems:
            if grouped[ecosystem] and len(selected) < max_entities:
                selected.append(grouped[ecosystem].pop(0))

    counts: dict[str, int] = {}
    for entity in selected:
        counts[entity["primary_ecosystem"]] = counts.get(entity["primary_ecosystem"], 0) + 1

    max_share = max(counts.values()) / len(selected) if selected else 0.0
    return {
        "max_entities": max_entities,
        "selected_entities": selected,
        "selected_entity_ids": [e["entity_id"] for e in selected],
        "ecosystem_counts": counts,
        "ecosystem_diversity_preserved": len(counts) >= 10,
        "saturation_guardrail_preserved": max_share <= 0.16,
        "monoculture_guardrail_preserved": max_share <= 0.20,
        "max_primary_ecosystem_share": round(max_share, 6),
    }


def build_lr6_exp1_semantic_replay_observations(window: dict[str, Any]) -> dict[str, Any]:
    entities = window["selected_entities"]
    total_secondary = sum(len(e.get("secondary_ecosystems", [])) for e in entities)
    richness = total_secondary / len(entities) if entities else 0.0
    novelty_proxy = sum(float(e.get("information_quality_score", 0.0)) for e in entities) / len(entities)
    return {
        "semantic_adjacency_richness": round(richness, 6),
        "novelty_proxy": round(novelty_proxy, 6),
    }


def build_lr6_exp1_ecosystem_interaction_observations(window: dict[str, Any]) -> dict[str, Any]:
    entities = window["selected_entities"]
    interactions = sum(len(set(e.get("secondary_ecosystems", []))) for e in entities)
    density = interactions / max(1, len(window["ecosystem_counts"]) * len(entities))
    return {"ecosystem_interaction_density": round(density, 6), "interaction_edges": interactions}


def build_lr6_exp1_contradiction_observations(window: dict[str, Any]) -> dict[str, Any]:
    surfaces = sorted({s for e in window["selected_entities"] for s in e.get("contradiction_surfaces", [])})
    return {"contradiction_surface_diversity": len(surfaces), "contradiction_surfaces": surfaces}


def build_lr6_exp1_propagation_observations(window: dict[str, Any]) -> dict[str, Any]:
    entities = window["selected_entities"]
    unique_roles = sorted({e.get("propagation_role", "") for e in entities})
    pathway_diversity = sum(len(e.get("propagation_links", [])) for e in entities) / max(1, len(entities))
    return {"propagation_pathway_diversity": round(pathway_diversity, 6), "propagation_roles": unique_roles}


def build_lr6_exp1_transition_observations(window: dict[str, Any]) -> dict[str, Any]:
    exposures = sorted({r for e in window["selected_entities"] for r in e.get("regime_exposures", [])})
    return {"transition_topology_diversity": len(exposures), "regime_exposure_topology": exposures}


def build_lr6_exp1_saturation_observations(window: dict[str, Any]) -> dict[str, Any]:
    risk = min(1.0, window["max_primary_ecosystem_share"] / 0.20)
    return {"saturation_risk": round(risk, 6), "guardrail_preserved": window["saturation_guardrail_preserved"]}


def build_lr6_exp1_monoculture_observations(window: dict[str, Any]) -> dict[str, Any]:
    risk = min(1.0, window["max_primary_ecosystem_share"] / 0.25)
    return {"monoculture_risk": round(risk, 6), "guardrail_preserved": window["monoculture_guardrail_preserved"]}


def build_lr6_exp1_observation_summary(observations: dict[str, Any]) -> dict[str, Any]:
    value = (
        observations["semantic"]["semantic_adjacency_richness"]
        + observations["ecosystem_interaction"]["ecosystem_interaction_density"]
        + observations["propagation"]["propagation_pathway_diversity"] / 2.0
        + observations["transition"]["transition_topology_diversity"] / 10.0
        + observations["contradiction"]["contradiction_surface_diversity"] / 10.0
    ) / 5.0
    return {
        "replay_ecology_observation_value": round(value, 6),
        "bounded_non_persistent_observation": True,
        "governed_lr6_production_activation": False,
    }


def build_lr6_exp1_governance_certification() -> dict[str, Any]:
    return {
        "experimental_mode_only": True,
        "governed_lr6_production_activation": False,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "additive_architecture_preserved": True,
        "deterministic_reproducibility_preserved": True,
    }


def build_lr6_exp1_report_payload(max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    inputs = load_lr6_exp1_inputs()
    context = build_lr6_exp1_experimental_mode_context(inputs)
    window = build_lr6_exp1_observation_window(inputs, max_entities=max_entities)
    observations = {
        "semantic": build_lr6_exp1_semantic_replay_observations(window),
        "ecosystem_interaction": build_lr6_exp1_ecosystem_interaction_observations(window),
        "contradiction": build_lr6_exp1_contradiction_observations(window),
        "propagation": build_lr6_exp1_propagation_observations(window),
        "transition": build_lr6_exp1_transition_observations(window),
        "saturation": build_lr6_exp1_saturation_observations(window),
        "monoculture": build_lr6_exp1_monoculture_observations(window),
    }
    summary = build_lr6_exp1_observation_summary(observations)
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "input_artifact_references": INPUT_PATHS.copy(),
        "experimental_mode_context": context,
        "observation_window": {
            k: v for k, v in window.items() if k != "selected_entities"
        },
        "observation_metrics": observations,
        "observation_summary": summary,
        "governance_certification_metadata": build_lr6_exp1_governance_certification(),
        "next_recommended_phase": "LR6-EXP2 bounded longitudinal semantic replay observation diagnostics",
    }
