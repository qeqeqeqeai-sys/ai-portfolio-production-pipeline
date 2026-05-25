from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation import (
    build_lr6_exp2_dashboard_payload,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout import (
    build_replay_ecology_signal_readout,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_exp4_replay_ecology_evidence_trace import (
    build_replay_ecology_evidence_trace,
)

DETERMINISTIC_VERSION = "LR6_EXP5_REPLAY_ECOLOGY_DASHBOARD_VIEW_MODEL_V1"
DETERMINISTIC_SEED = "LR6_EXP5_REPLAY_ECOLOGY_DASHBOARD_VIEW_MODEL_SEED_V1"
MAX_ITEMS = 6
MAX_TEXT = 180


_ALLOWED_STATE_ORDER = [
    "maturing_replay_ecology",
    "propagation_dense_ecology",
    "contradiction_heavy_ecology",
    "emerging_replay_ecology",
    "saturation_risk_ecology",
    "monoculture_risk_ecology",
    "fragmented_replay_ecology",
    "sparse_observation_environment",
]


def _clip(text: str, limit: int = MAX_TEXT) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _top_names(items: list[dict[str, Any]], key: str = "name", limit: int = MAX_ITEMS) -> list[str]:
    return [_clip(str(item.get(key, "unknown"))) for item in items[:limit]]


def _panel(name: str, observations: list[str], evidence_refs: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel": name,
        "observations": [_clip(x) for x in observations[:MAX_ITEMS]],
        "evidence_refs": evidence_refs,
    }


def build_replay_ecology_overview_panel(exp2: dict[str, Any], exp3: dict[str, Any], exp4: dict[str, Any]) -> dict[str, Any]:
    summary = exp3["interpretation_summary"]
    attribution_summary = exp4["composite_attribution_summary"]
    return {
        "dominant_replay_ecology_state": summary["dominant_replay_ecology_state"],
        "replay_ecology_density_band": attribution_summary["replay_ecology_density_band"],
        "replay_ecology_maturity_band": summary["replay_ecology_maturity_band"],
        "observation_confidence_band": summary["observation_confidence_band"],
        "strongest_observed_signal": summary["strongest_observed_signal"],
        "weakest_observed_signal": summary["weakest_observed_signal"],
        "ecological_caveat_summary": _clip(summary["caveats"][0]),
        "evidence_refs": {
            "exp2_version": exp2["deterministic_version"],
            "exp3_version": exp3["deterministic_version"],
            "exp4_version": exp4["deterministic_version"],
        },
    }


def build_replay_drift_panel(exp2: dict[str, Any], exp3: dict[str, Any], exp4: dict[str, Any]) -> dict[str, Any]:
    m = exp2["observation_metrics"]["replay_drift"]
    r = exp3["domain_readouts"]["replay_drift"]
    pathways = _top_names(exp4["attribution_domains"]["replay_drift_pathway_refs"])
    return _panel(
        "replay_drift_panel",
        [
            f"Replay drift direction is {r['state']} with movement signal {r['movement_signal']}.",
            f"Replay recurrence is {m['replay_recurrence']:.3f} with recurrence decay {m['recurrence_decay']:.3f}.",
            f"Topology stability index is {m['topology_stability_index']:.3f} and semantic velocity is {m['semantic_velocity']:.3f}.",
            f"Replay fragmentation/compression context combines replay drift score {m['replay_drift_score']:.3f} and persistence {m['replay_persistence_score']:.3f}.",
            f"Most referenced drift pathways: {', '.join(pathways[:4])}.",
        ],
        {"drift_evidence": r["evidence"], "pathway_refs": exp4["attribution_domains"]["replay_drift_pathway_refs"][:MAX_ITEMS]},
    )


def build_propagation_evolution_panel(exp2: dict[str, Any], exp3: dict[str, Any], exp4: dict[str, Any]) -> dict[str, Any]:
    m = exp2["observation_metrics"]["propagation"]
    r = exp3["domain_readouts"]["propagation_evolution"]
    ad = exp4["attribution_domains"]
    return _panel(
        "propagation_evolution_panel",
        [
            f"Strongest propagation pathways are concentrated around {', '.join(_top_names(ad['pathway_concentration_refs'])[:3])}.",
            f"Replay bridge entities include {', '.join(_top_names(ad['replay_bridge_entities'])[:4])}.",
            f"Pathway concentration is {m['pathway_concentration']:.3f} with propagation entropy {m['propagation_entropy']:.3f}.",
            f"Cross-cluster propagation structures emphasize {', '.join(_top_names(ad['cross_cluster_pathway_links'])[:3])}.",
            f"Propagation fragmentation observation: {r['state']} with fragmentation score {m['propagation_fragmentation']:.3f}.",
        ],
        {"propagation_evidence": r["evidence"], "attribution_refs": ad["pathway_concentration_refs"][:MAX_ITEMS]},
    )


def build_contradiction_ecology_panel(exp2: dict[str, Any], exp3: dict[str, Any], exp4: dict[str, Any]) -> dict[str, Any]:
    m = exp2["observation_metrics"]["contradiction"]
    r = exp3["domain_readouts"]["contradiction_ecology"]
    ad = exp4["attribution_domains"]
    return _panel("contradiction_ecology_panel", [
        f"Strongest contradiction surfaces are {', '.join(_top_names(ad['contradiction_surface_density'])[:4])}.",
        f"Contradiction persistence zones show persistence {m['contradiction_persistence']:.3f}.",
        f"Contradiction-heavy clusters include {', '.join(_top_names(ad['contradiction_cluster_refs'])[:4])}.",
        f"Contradiction migration summary indicates drift {m['contradiction_cluster_drift']:.3f} with density delta {m['contradiction_density_delta']:.3f}.",
    ], {"contradiction_evidence": r["evidence"], "surface_refs": ad["contradiction_surface_density"][:MAX_ITEMS]})


def build_saturation_monoculture_panel(exp2: dict[str, Any], exp3: dict[str, Any], exp4: dict[str, Any]) -> dict[str, Any]:
    s = exp2["observation_metrics"]["saturation"]
    m = exp2["observation_metrics"]["monoculture"]
    ad = exp4["attribution_domains"]
    return _panel("saturation_monoculture_panel", [
        f"Replay saturation zones center on {', '.join(_top_names(ad['saturation_pressure_entities'])[:4])}.",
        f"Novelty decay areas include clusters {', '.join(_top_names(ad['novelty_decay_clusters'])[:4])}.",
        f"Semantic gravity observation reports gravity index {m['semantic_gravity_index']:.3f} with dominant concentration {m['replay_concentration_trend']:.3f}.",
        f"Monoculture risk contributors include {', '.join(_top_names(ad['replay_monoculture_entities'])[:4])}.",
        f"Replay concentration observations: saturation velocity {s['saturation_velocity']:.3f}, novelty decay {s['novelty_decay_rate']:.3f}, compression {s['replay_compression_index']:.3f}.",
    ], {"saturation_evidence": s, "monoculture_evidence": m})


def build_ecosystem_interaction_panel(exp2: dict[str, Any], exp3: dict[str, Any], exp4: dict[str, Any]) -> dict[str, Any]:
    m = exp2["observation_metrics"]["interaction"]
    r = exp3["domain_readouts"]["ecosystem_interaction"]
    ad = exp4["attribution_domains"]
    return _panel("ecosystem_interaction_panel", [
        f"Strongest interaction zones include {', '.join(_top_names(ad['cross_cluster_interaction_refs'])[:4])}.",
        f"Replay cascade structures highlight {', '.join(_top_names(ad['replay_cascade_refs'])[:4])}.",
        f"Cross-cluster coupling summary: coupling {m['cross_cluster_replay_coupling']:.3f} and semantic neighbor influence {m['semantic_neighbor_influence']:.3f}.",
        f"Interaction-density observation: delta {m['interaction_density_delta']:.3f} with cohesion shift {m['ecosystem_cohesion_shift']:.3f}.",
        f"Replay ecology cohesion observation: {r['ecosystem_mode']} and {r['cascade_state']}.",
    ], {"interaction_evidence": r["evidence"]})


def build_entity_cluster_attribution_panel(exp4: dict[str, Any]) -> dict[str, Any]:
    s = exp4["composite_attribution_summary"]
    return {
        "panel": "entity_cluster_attribution_panel",
        "most_referenced_entities": s["most_referenced_entities"][:MAX_ITEMS],
        "most_referenced_clusters": s["most_referenced_clusters"][:MAX_ITEMS],
        "strongest_replay_bridge_entities": s["strongest_replay_bridge_entities"][:MAX_ITEMS],
        "strongest_propagation_contributors": s["strongest_propagation_pathways"][:MAX_ITEMS],
        "strongest_contradiction_contributors": s["strongest_contradiction_surfaces"][:MAX_ITEMS],
        "evidence_refs": {"attribution_domains": "lr6_exp4_replay_ecology_evidence_trace"},
    }


def build_replay_ecology_dashboard_view_model(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    exp2 = build_lr6_exp2_dashboard_payload(max_entities=max_entities, slice_count=slice_count)
    exp3 = build_replay_ecology_signal_readout(max_entities=max_entities, slice_count=slice_count)
    exp4 = build_replay_ecology_evidence_trace(max_entities=max_entities, slice_count=slice_count)

    overview = build_replay_ecology_overview_panel(exp2, exp3, exp4)
    dashboard = {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "observation_window": {"max_entities": max_entities, "slice_count": slice_count},
        "overview_panel": overview,
        "replay_drift_panel": build_replay_drift_panel(exp2, exp3, exp4),
        "propagation_evolution_panel": build_propagation_evolution_panel(exp2, exp3, exp4),
        "contradiction_ecology_panel": build_contradiction_ecology_panel(exp2, exp3, exp4),
        "saturation_monoculture_panel": build_saturation_monoculture_panel(exp2, exp3, exp4),
        "ecosystem_interaction_panel": build_ecosystem_interaction_panel(exp2, exp3, exp4),
        "entity_cluster_attribution_panel": build_entity_cluster_attribution_panel(exp4),
        "ecological_caveats": exp3["interpretation_summary"]["caveats"][:MAX_ITEMS],
        "next_observation_priorities": exp3["interpretation_summary"]["next_observation_priorities"][:MAX_ITEMS],
        "experimental_certification": certify_lr6_exp5_experimental_boundaries(),
    }
    return dashboard


def build_replay_ecology_dashboard_summary(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    vm = build_replay_ecology_dashboard_view_model(max_entities=max_entities, slice_count=slice_count)
    overview = vm["overview_panel"]
    return {
        "dominant_replay_ecology_state": overview["dominant_replay_ecology_state"],
        "replay_ecology_density_band": overview["replay_ecology_density_band"],
        "replay_ecology_maturity_band": overview["replay_ecology_maturity_band"],
        "observation_confidence_band": overview["observation_confidence_band"],
        "strongest_observed_signal": overview["strongest_observed_signal"],
        "weakest_observed_signal": overview["weakest_observed_signal"],
        "ecological_caveats": vm["ecological_caveats"],
        "next_observation_priorities": vm["next_observation_priorities"],
    }


def certify_lr6_exp5_experimental_boundaries() -> dict[str, Any]:
    return {
        "experimental_mode_only": True,
        "governed_lr6_activation": False,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "additive_architecture_preserved": True,
        "anti_monoculture_controls_preserved": True,
        "saturation_guardrails_preserved": True,
    }
