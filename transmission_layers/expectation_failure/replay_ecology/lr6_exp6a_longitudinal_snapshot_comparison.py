from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_EXP6A_LONGITUDINAL_SNAPSHOT_COMPARISON_V1"
DETERMINISTIC_SEED = "LR6_EXP6A_LONGITUDINAL_SNAPSHOT_COMPARISON_SEED_V1"
SOURCE_PHASE = "LR6-EXP6A"
SOURCE_MODULES = [
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp4_replay_ecology_evidence_trace",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp6_replay_ecology_snapshot_export",
]

MAX_TOP_LEVEL_SIGNALS = 10
MAX_DOMAIN_ITEMS = 8
MAX_CAVEATS = 8


def _bounded_unique(values: list[str], limit: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
        if len(out) >= limit:
            break
    return out


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str):
        return [value]
    return []


def normalize_snapshot_sections(snapshot_payload: dict[str, Any]) -> dict[str, Any]:
    payload = snapshot_payload or {}
    return {
        "overview": payload.get("overview", {}),
        "replay_drift": payload.get("replay_drift", {}),
        "propagation_evolution": payload.get("propagation_evolution", {}),
        "contradiction_ecology": payload.get("contradiction_ecology", {}),
        "saturation_monoculture": payload.get("saturation_monoculture", {}),
        "ecosystem_interaction": payload.get("ecosystem_interaction", {}),
        "entity_cluster_attribution": payload.get("entity_cluster_attribution", {}),
        "caveats": _as_list(payload.get("caveats", []))[:MAX_CAVEATS],
        "next_observation_priorities": _as_list(payload.get("next_observation_priorities", []))[:MAX_CAVEATS],
    }


def extract_snapshot_terms(section: dict[str, Any], keys: list[str]) -> list[str]:
    terms: list[str] = []
    for key in keys:
        terms.extend(_as_list(section.get(key, [])))
    if "observations" in section:
        terms.extend(_as_list(section.get("observations", [])))
    return _bounded_unique(terms, MAX_DOMAIN_ITEMS)


def compare_bounded_terms(prior_terms: list[str], current_terms: list[str], limit: int = MAX_DOMAIN_ITEMS) -> dict[str, list[str]]:
    prior = _bounded_unique(prior_terms, 100)
    current = _bounded_unique(current_terms, 100)
    prior_set, current_set = set(prior), set(current)
    return {
        "persisted": _bounded_unique([x for x in current if x in prior_set], limit),
        "emerged": _bounded_unique([x for x in current if x not in prior_set], limit),
        "disappeared": _bounded_unique([x for x in prior if x not in current_set], limit),
    }


def classify_snapshot_change(prior_value: str, current_value: str) -> str:
    if not prior_value and not current_value:
        return "insufficient_evidence"
    if prior_value == current_value:
        return "persisted"
    if not prior_value and current_value:
        return "emerged"
    if prior_value and not current_value:
        return "disappeared"
    return "shifted"


def build_change_summary(label: str, comparison: dict[str, list[str]]) -> str:
    return (
        f"{label} persisted={len(comparison['persisted'])}, "
        f"emerged={len(comparison['emerged'])}, disappeared={len(comparison['disappeared'])}."
    )


def build_ecology_state_change_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    return {
        "state_change_status": classify_snapshot_change(prior.get("dominant_replay_ecology_state", ""), current.get("dominant_replay_ecology_state", "")),
        "prior_state": prior.get("dominant_replay_ecology_state"),
        "current_state": current.get("dominant_replay_ecology_state"),
        "density_band_change": classify_snapshot_change(prior.get("replay_ecology_density_band", ""), current.get("replay_ecology_density_band", "")),
        "maturity_band_change": classify_snapshot_change(prior.get("replay_ecology_maturity_band", ""), current.get("replay_ecology_maturity_band", "")),
        "confidence_band_change": classify_snapshot_change(prior.get("observation_confidence_band", ""), current.get("observation_confidence_band", "")),
        "strongest_signal_change": classify_snapshot_change(prior.get("strongest_observed_signal", ""), current.get("strongest_observed_signal", "")),
        "weakest_signal_change": classify_snapshot_change(prior.get("weakest_observed_signal", ""), current.get("weakest_observed_signal", "")),
    }


def _domain_compare(prior: dict[str, Any], current: dict[str, Any], keys: list[str], label: str) -> dict[str, Any]:
    changes = compare_bounded_terms(extract_snapshot_terms(prior, keys), extract_snapshot_terms(current, keys))
    return {**changes, "summary": build_change_summary(label, changes)}


def build_replay_drift_snapshot_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    d = _domain_compare(prior, current, ["semantic_velocity_indicators", "recurrence_topology_stability_indicators", "fragmentation_compression_signals"], "Replay drift")
    return {
        "replay_drift_change_status": "persisted" if d["persisted"] else "shifted",
        "persisted_drift_signals": d["persisted"],
        "emerged_drift_signals": d["emerged"],
        "weakened_drift_signals": d["disappeared"],
        "drift_change_summary": d["summary"],
    }


def build_propagation_snapshot_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    d = _domain_compare(prior, current, ["strongest_propagation_pathways", "replay_bridge_entities", "pathway_concentration_zones", "cross_cluster_propagation_references"], "Propagation")
    return {
        "persisted_propagation_pathways": d["persisted"],
        "emerged_propagation_pathways": d["emerged"],
        "disappeared_propagation_pathways": d["disappeared"],
        "bridge_entity_changes": d["summary"],
        "propagation_change_summary": d["summary"],
    }


def build_contradiction_snapshot_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    d = _domain_compare(prior, current, ["strongest_contradiction_surfaces", "contradiction_heavy_clusters", "contradiction_persistence_zones", "contradiction_migration_summaries"], "Contradiction")
    return {
        "persistent_contradiction_surfaces": d["persisted"],
        "emerged_contradiction_surfaces": d["emerged"],
        "disappeared_contradiction_surfaces": d["disappeared"],
        "contradiction_cluster_changes": d["summary"],
        "contradiction_change_summary": d["summary"],
    }


def build_saturation_monoculture_snapshot_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    prior_terms = extract_snapshot_terms(prior, ["saturation_zones", "novelty_decay_areas", "semantic_gravity_observations", "cluster_concentration_references", "monoculture_contributors"])
    current_terms = extract_snapshot_terms(current, ["saturation_zones", "novelty_decay_areas", "semantic_gravity_observations", "cluster_concentration_references", "monoculture_contributors"])
    c = compare_bounded_terms(prior_terms, current_terms)
    return {
        "saturation_change_status": "persisted" if c["persisted"] else "shifted",
        "semantic_gravity_changes": c["emerged"],
        "monoculture_risk_change": classify_snapshot_change("present" if prior_terms else "", "present" if current_terms else ""),
        "novelty_decay_change": c["disappeared"],
        "saturation_change_summary": build_change_summary("Saturation/monoculture", c),
    }


def build_ecosystem_interaction_snapshot_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    d = _domain_compare(prior, current, ["interaction_zones", "replay_cascade_structures", "cross_cluster_coupling_summaries", "entity_cluster_interaction_references"], "Interaction")
    return {
        "persisted_interaction_zones": d["persisted"],
        "emerged_interaction_zones": d["emerged"],
        "disappeared_interaction_zones": d["disappeared"],
        "coupling_change_summary": d["summary"],
        "interaction_change_summary": d["summary"],
    }


def build_entity_cluster_snapshot_comparison(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    entity_changes = compare_bounded_terms(extract_snapshot_terms(prior, ["most_referenced_entities", "strongest_bridge_entities", "strongest_contradiction_contributors", "strongest_propagation_contributors"]), extract_snapshot_terms(current, ["most_referenced_entities", "strongest_bridge_entities", "strongest_contradiction_contributors", "strongest_propagation_contributors"]))
    cluster_changes = compare_bounded_terms(extract_snapshot_terms(prior, ["most_referenced_clusters"]), extract_snapshot_terms(current, ["most_referenced_clusters"]))
    return {
        "persistent_entities": entity_changes["persisted"],
        "emerged_entities": entity_changes["emerged"],
        "disappeared_entities": entity_changes["disappeared"],
        "persistent_clusters": cluster_changes["persisted"],
        "emerged_clusters": cluster_changes["emerged"],
        "disappeared_clusters": cluster_changes["disappeared"],
        "attribution_change_summary": f"Entities {build_change_summary('changes', entity_changes)} Clusters {build_change_summary('changes', cluster_changes)}",
    }


def build_replay_ecology_snapshot_comparison(prior_snapshot: dict[str, Any], current_snapshot: dict[str, Any]) -> dict[str, Any]:
    prior = normalize_snapshot_sections(prior_snapshot.get("payload", prior_snapshot))
    current = normalize_snapshot_sections(current_snapshot.get("payload", current_snapshot))
    ecology = build_ecology_state_change_comparison(prior["overview"], current["overview"])
    drift = build_replay_drift_snapshot_comparison(prior["replay_drift"], current["replay_drift"])
    propagation = build_propagation_snapshot_comparison(prior["propagation_evolution"], current["propagation_evolution"])
    contradiction = build_contradiction_snapshot_comparison(prior["contradiction_ecology"], current["contradiction_ecology"])
    saturation = build_saturation_monoculture_snapshot_comparison(prior["saturation_monoculture"], current["saturation_monoculture"])
    interaction = build_ecosystem_interaction_snapshot_comparison(prior["ecosystem_interaction"], current["ecosystem_interaction"])
    attribution = build_entity_cluster_snapshot_comparison(prior["entity_cluster_attribution"], current["entity_cluster_attribution"])

    all_prior = _bounded_unique(sum([extract_snapshot_terms(prior[k], []) for k in ["replay_drift", "propagation_evolution", "contradiction_ecology", "saturation_monoculture", "ecosystem_interaction", "entity_cluster_attribution"]], []), 200)
    all_current = _bounded_unique(sum([extract_snapshot_terms(current[k], []) for k in ["replay_drift", "propagation_evolution", "contradiction_ecology", "saturation_monoculture", "ecosystem_interaction", "entity_cluster_attribution"]], []), 200)
    top = compare_bounded_terms(all_prior, all_current, MAX_TOP_LEVEL_SIGNALS)

    caveats = _bounded_unique([
        "Comparison remains observational and non-predictive.",
        "Missing optional sections reduce evidence density." if not prior_snapshot or not current_snapshot else "",
    ] + prior["caveats"] + current["caveats"], MAX_CAVEATS)

    return {
        "comparison_metadata": {
            "comparison_id": f"{DETERMINISTIC_VERSION}::{prior_snapshot.get('metadata', {}).get('snapshot_id', 'prior')}::{current_snapshot.get('metadata', {}).get('snapshot_id', 'current')}",
            "prior_snapshot_id": prior_snapshot.get("metadata", {}).get("snapshot_id", "prior"),
            "current_snapshot_id": current_snapshot.get("metadata", {}).get("snapshot_id", "current"),
            "prior_comparison_key": prior_snapshot.get("metadata", {}).get("deterministic_comparison_key", ""),
            "current_comparison_key": current_snapshot.get("metadata", {}).get("deterministic_comparison_key", ""),
            "source_phase": SOURCE_PHASE,
            "source_modules": SOURCE_MODULES,
            "deterministic_comparison_mode": True,
            "experimental_mode_only": True,
            "no_prediction": True,
            "no_trading": True,
            "no_governed_activation": True,
        },
        "ecology_state_change": ecology,
        "replay_drift_change": drift,
        "propagation_change": propagation,
        "contradiction_change": contradiction,
        "saturation_monoculture_change": saturation,
        "ecosystem_interaction_change": interaction,
        "entity_cluster_attribution_change": attribution,
        "persistent_ecological_signals": top["persisted"],
        "emerged_ecological_signals": top["emerged"],
        "disappeared_ecological_signals": top["disappeared"],
        "intensified_ecological_signals": top["emerged"],
        "weakened_ecological_signals": top["disappeared"],
        "comparison_confidence_band": current["overview"].get("observation_confidence_band", "insufficient_evidence"),
        "comparison_caveats": caveats,
        "next_observation_priorities": _bounded_unique(current["next_observation_priorities"], MAX_CAVEATS),
    }


def build_replay_ecology_snapshot_sequence_comparison(snapshot_sequence: list[dict[str, Any]]) -> dict[str, Any]:
    bounded = snapshot_sequence[:4]
    pairwise = [
        build_replay_ecology_snapshot_comparison(bounded[i], bounded[i + 1])
        for i in range(len(bounded) - 1)
    ]
    return {
        "sequence_size": len(bounded),
        "pairwise_comparisons": pairwise,
        "final_summary": build_lr6_exp6a_comparison_summary(pairwise[-1] if pairwise else {}),
    }


def build_lr6_exp6a_comparison_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    if not comparison:
        return {"summary": "No comparison available."}
    return {
        "summary": (
            f"Ecology {comparison['ecology_state_change']['state_change_status']}; "
            f"persisted={len(comparison['persistent_ecological_signals'])}, "
            f"emerged={len(comparison['emerged_ecological_signals'])}, "
            f"disappeared={len(comparison['disappeared_ecological_signals'])}."
        ),
        "comparison_confidence_band": comparison.get("comparison_confidence_band", "insufficient_evidence"),
        "observational_only": True,
    }


def certify_lr6_exp6a_experimental_boundaries() -> dict[str, Any]:
    return {
        "experimental_mode_only": True,
        "governed_lr6_activation": False,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "deterministic_bounded_outputs": True,
        "additive_architecture_preserved": True,
    }
