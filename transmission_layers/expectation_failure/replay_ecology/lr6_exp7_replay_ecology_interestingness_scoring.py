from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_EXP7_REPLAY_ECOLOGY_INTERESTINGNESS_SCORING_V1"
DETERMINISTIC_SEED = "LR6_EXP7_REPLAY_ECOLOGY_INTERESTINGNESS_SCORING_SEED_V1"
SOURCE_PHASE = "LR6-EXP7"
SOURCE_MODULES = [
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp4_replay_ecology_evidence_trace",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp6_replay_ecology_snapshot_export",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp6a_longitudinal_snapshot_comparison",
]

MAX_RANKED_CHANGES = 12
MAX_LOW_INFORMATION = 8
MAX_TOP_DRIVERS = 10
MAX_CAVEATS = 8
MAX_REFS = 6
MAX_ENTITIES = 8
MAX_CLUSTERS = 6
MAX_PATHWAYS = 6
MAX_CONTRADICTIONS = 6


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return []


def _bounded_unique(values: list[str], limit: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
        if len(out) >= limit:
            break
    return out


def normalize_comparison_terms(comparison: dict[str, Any]) -> dict[str, Any]:
    comp = comparison or {}
    return {
        "metadata": comp.get("comparison_metadata", {}),
        "ecology": comp.get("ecology_state_change", {}),
        "drift": comp.get("replay_drift_change", {}),
        "propagation": comp.get("propagation_change", {}),
        "contradiction": comp.get("contradiction_change", {}),
        "saturation": comp.get("saturation_monoculture_change", {}),
        "interaction": comp.get("ecosystem_interaction_change", {}),
        "attribution": comp.get("entity_cluster_attribution_change", {}),
        "caveats": _as_list(comp.get("comparison_caveats", [])),
        "priorities": _as_list(comp.get("next_observation_priorities", [])),
    }


def calculate_bounded_interestingness_score(raw_score: float) -> float:
    return round(max(0.0, min(1.0, raw_score)), 4)


def classify_interestingness_band(score: float) -> str:
    if score <= 0.24:
        return "low_information"
    if score <= 0.49:
        return "routine_change"
    if score <= 0.74:
        return "notable_ecological_change"
    return "high_interestingness_ecological_shift"


def extract_evidence_refs(*sections: Any) -> list[str]:
    refs: list[str] = []
    for section in sections:
        if isinstance(section, dict):
            refs.extend(_as_list(section.get("evidence_refs", [])))
            refs.extend(_as_list(section.get("supporting_evidence", [])))
        refs.extend(_as_list(section))
    return _bounded_unique(refs, MAX_REFS)


def extract_involved_ecology_terms(section: dict[str, Any], keys: list[str], limit: int) -> list[str]:
    terms: list[str] = []
    for key in keys:
        terms.extend(_as_list(section.get(key, [])))
    return _bounded_unique(terms, limit)


def apply_saturation_penalty(score: float, saturation_terms: list[str], emerged_terms: list[str]) -> tuple[float, list[str]]:
    if len(saturation_terms) >= 3 and not emerged_terms:
        return calculate_bounded_interestingness_score(score - 0.12), ["saturation pressure increased without replay novelty support"]
    return score, []


def apply_monoculture_penalty(score: float, cluster_terms: list[str]) -> tuple[float, list[str]]:
    if len(cluster_terms) <= 1:
        return calculate_bounded_interestingness_score(score - 0.1), ["cross-cluster coupling breadth remains narrow and indicates monoculture pressure"]
    return score, []


def build_scored_change_item(*, item_id: str, domain: str, score: float, drivers: list[str], evidence_refs: list[str], entities: list[str], clusters: list[str], pathways: list[str], contradictions: list[str], caveats: list[str]) -> dict[str, Any]:
    bounded_score = calculate_bounded_interestingness_score(score)
    return {
        "item_id": item_id,
        "domain": domain,
        "score": bounded_score,
        "score_band": classify_interestingness_band(bounded_score),
        "interestingness_drivers": _bounded_unique(drivers, MAX_TOP_DRIVERS),
        "evidence_refs": _bounded_unique(evidence_refs, MAX_REFS),
        "involved_entities": _bounded_unique(entities, MAX_ENTITIES),
        "involved_clusters": _bounded_unique(clusters, MAX_CLUSTERS),
        "involved_pathways": _bounded_unique(pathways, MAX_PATHWAYS),
        "involved_contradiction_surfaces": _bounded_unique(contradictions, MAX_CONTRADICTIONS),
        "caveats": _bounded_unique(caveats, MAX_CAVEATS),
    }


def score_ecology_state_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    ecology = n["ecology"]
    shifts = [ecology.get("state_change_status"), ecology.get("density_band_change"), ecology.get("maturity_band_change"), ecology.get("confidence_band_change")]
    shift_count = sum(1 for x in shifts if x in {"shifted", "emerged", "disappeared"})
    score = 0.25 + (0.12 * shift_count)
    return build_scored_change_item(item_id="ecology_state", domain="ecology_state_interestingness", score=score, drivers=["dominant ecology state shift", "semantic gravity movement in density/maturity bands"], evidence_refs=extract_evidence_refs(ecology), entities=[], clusters=[], pathways=[], contradictions=[], caveats=["weak evidence support" if not extract_evidence_refs(ecology) else ""])


def score_replay_drift_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    drift = n["drift"]
    emerged = _as_list(drift.get("emerged_drift_signals", []))
    persisted = _as_list(drift.get("persisted_drift_signals", []))
    score = 0.18 + min(0.32, 0.06 * len(emerged)) + min(0.2, 0.04 * len(persisted))
    return build_scored_change_item(item_id="replay_drift", domain="replay_drift_interestingness", score=score, drivers=["replay novelty and replay recurrence tension", "semantic velocity and fragmentation/compression movement"], evidence_refs=extract_evidence_refs(drift), entities=[], clusters=[], pathways=[], contradictions=[], caveats=["missing evidence sections" if not extract_evidence_refs(drift) else ""])


def score_propagation_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    p = n["propagation"]
    emerged = _as_list(p.get("emerged_propagation_pathways", []))
    persisted = _as_list(p.get("persisted_propagation_pathways", []))
    score = 0.22 + min(0.36, 0.08 * len(emerged)) + min(0.18, 0.03 * len(persisted))
    return build_scored_change_item(item_id="propagation", domain="propagation_interestingness", score=score, drivers=["emerged propagation bridge pathways", "persistent propagation bridge continuity"], evidence_refs=extract_evidence_refs(p), entities=[], clusters=[], pathways=emerged + persisted, contradictions=[], caveats=["low evidence quality" if not extract_evidence_refs(p) else ""])


def score_contradiction_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    c = n["contradiction"]
    emerged = _as_list(c.get("emerged_contradiction_surfaces", []))
    persisted = _as_list(c.get("persistent_contradiction_surfaces", []))
    score = 0.24 + min(0.32, 0.08 * len(emerged)) + min(0.28, 0.05 * len(persisted))
    return build_scored_change_item(item_id="contradiction", domain="contradiction_interestingness", score=score, drivers=["contradiction persistence", "contradiction migration across clusters"], evidence_refs=extract_evidence_refs(c), entities=[], clusters=[], pathways=[], contradictions=emerged + persisted, caveats=["missing contradiction evidence" if not extract_evidence_refs(c) else ""])


def score_saturation_monoculture_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    s = n["saturation"]
    gravity = _as_list(s.get("semantic_gravity_changes", []))
    score = 0.2 + min(0.35, 0.08 * len(gravity))
    score, sat_notes = apply_saturation_penalty(score, gravity, gravity)
    score, mono_notes = apply_monoculture_penalty(score, extract_involved_ecology_terms(n["attribution"], ["persistent_clusters", "emerged_clusters"], MAX_CLUSTERS))
    return build_scored_change_item(item_id="saturation_monoculture", domain="saturation_monoculture_interestingness", score=score, drivers=["semantic gravity shift", "saturation pressure and monoculture pressure movement"], evidence_refs=extract_evidence_refs(s), entities=[], clusters=[], pathways=[], contradictions=[], caveats=sat_notes + mono_notes + (["missing saturation evidence"] if not extract_evidence_refs(s) else []))


def score_ecosystem_interaction_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    i = n["interaction"]
    emerged = _as_list(i.get("emerged_interaction_zones", []))
    persisted = _as_list(i.get("persisted_interaction_zones", []))
    score = 0.2 + min(0.35, 0.08 * len(emerged)) + min(0.2, 0.04 * len(persisted))
    return build_scored_change_item(item_id="ecosystem_interaction", domain="ecosystem_interaction_interestingness", score=score, drivers=["cross-cluster coupling changes", "interaction zone and replay cascade movement"], evidence_refs=extract_evidence_refs(i), entities=[], clusters=[], pathways=emerged + persisted, contradictions=[], caveats=["missing interaction evidence" if not extract_evidence_refs(i) else ""])


def score_entity_cluster_attribution_interestingness(n: dict[str, Any]) -> dict[str, Any]:
    a = n["attribution"]
    emerged_entities = _as_list(a.get("emerged_entities", []))
    persisted_entities = _as_list(a.get("persistent_entities", []))
    emerged_clusters = _as_list(a.get("emerged_clusters", []))
    score = 0.2 + min(0.28, 0.05 * len(emerged_entities)) + min(0.25, 0.07 * len(emerged_clusters)) + min(0.15, 0.03 * len(persisted_entities))
    return build_scored_change_item(item_id="entity_cluster_attribution", domain="entity_cluster_attribution_interestingness", score=score, drivers=["entity/cluster attribution shifts", "cross-cluster coupling breadth changes"], evidence_refs=extract_evidence_refs(a), entities=emerged_entities + persisted_entities, clusters=emerged_clusters + _as_list(a.get("persistent_clusters", [])), pathways=[], contradictions=[], caveats=["attribution evidence is sparse" if not extract_evidence_refs(a) else ""])


def build_replay_ecology_interestingness_scores(comparison: dict[str, Any]) -> dict[str, Any]:
    n = normalize_comparison_terms(comparison)
    items = [
        score_ecology_state_interestingness(n),
        score_replay_drift_interestingness(n),
        score_propagation_interestingness(n),
        score_contradiction_interestingness(n),
        score_saturation_monoculture_interestingness(n),
        score_ecosystem_interaction_interestingness(n),
        score_entity_cluster_attribution_interestingness(n),
    ]
    return {"scoring_metadata": {"scoring_id": f"{DETERMINISTIC_VERSION}::{n['metadata'].get('comparison_id', 'unknown')}", "source_phase": SOURCE_PHASE, "source_modules": SOURCE_MODULES, "input_comparison_id": n["metadata"].get("comparison_id", "unknown"), "deterministic_scoring_mode": True, "scoring_version": DETERMINISTIC_VERSION, "experimental_mode_only": True, "no_prediction": True, "no_trading": True, "no_governed_activation": True}, "domain_scores": items}


def build_ranked_interesting_ecological_changes(scores: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    domains = list(scores.get("domain_scores", []))
    ranked = sorted(domains, key=lambda x: (-x["score"], x["item_id"]))[:MAX_RANKED_CHANGES]
    low_info = [x for x in sorted(domains, key=lambda x: (x["score"], x["item_id"])) if x["score_band"] == "low_information"][:MAX_LOW_INFORMATION]
    return {"ranked_interesting_changes": ranked, "low_information_changes": low_info}


def build_interestingness_summary(scores: dict[str, Any]) -> dict[str, Any]:
    ranked = build_ranked_interesting_ecological_changes(scores)
    domain_scores = scores.get("domain_scores", [])
    avg = calculate_bounded_interestingness_score(sum(x["score"] for x in domain_scores) / max(1, len(domain_scores)))
    drivers = _bounded_unique(sum([x.get("interestingness_drivers", []) for x in domain_scores], []), MAX_TOP_DRIVERS)
    caveats = _bounded_unique(sum([x.get("caveats", []) for x in domain_scores], []) + ["Observational interestingness only; no prediction or trading outputs."], MAX_CAVEATS)
    return {
        **scores,
        **ranked,
        "top_interestingness_drivers": drivers,
        "saturation_penalty_notes": [c for c in caveats if "saturation pressure" in c][:MAX_CAVEATS],
        "monoculture_penalty_notes": [c for c in caveats if "monoculture pressure" in c][:MAX_CAVEATS],
        "evidence_quality_band": "supported" if any(d.get("evidence_refs") for d in domain_scores) else "weak",
        "replay_ecology_interestingness_band": classify_interestingness_band(avg),
        "caveats": caveats,
        "next_observation_priorities": _bounded_unique(["Monitor contradiction persistence tied to propagation bridge movement", "Track semantic gravity movement and saturation pressure changes", "Observe replay novelty and replay recurrence balance across cross-cluster coupling"] , MAX_CAVEATS),
    }


def build_lr6_exp7_dashboard_payload(comparison: dict[str, Any]) -> dict[str, Any]:
    summary = build_interestingness_summary(build_replay_ecology_interestingness_scores(comparison))
    return {"lr6_exp7_interestingness_dashboard": summary, "experimental_certification": certify_lr6_exp7_experimental_boundaries()}


def certify_lr6_exp7_experimental_boundaries() -> dict[str, Any]:
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
