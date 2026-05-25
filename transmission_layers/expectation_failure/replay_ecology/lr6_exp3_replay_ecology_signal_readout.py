from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation import (
    build_lr6_exp2_dashboard_payload,
)

DETERMINISTIC_VERSION = "LR6_EXP3_REPLAY_ECOLOGY_SIGNAL_READOUT_V1"
DETERMINISTIC_SEED = "LR6_EXP3_REPLAY_ECOLOGY_SIGNAL_READOUT_SEED_V1"
MAX_FINDINGS = 8
MAX_CAVEATS = 6
MAX_PRIORITIES = 6


_ALLOWED_STATES = {
    "sparse_observation_environment",
    "emerging_replay_ecology",
    "contradiction_heavy_ecology",
    "propagation_dense_ecology",
    "saturation_risk_ecology",
    "monoculture_risk_ecology",
    "fragmented_replay_ecology",
    "maturing_replay_ecology",
}


def _band(value: float, low: float = 0.35, high: float = 0.65) -> str:
    if value < low:
        return "low"
    if value < high:
        return "moderate"
    return "high"


def _finding(domain: str, signal: str, strength: float, interpretation: str, evidence: dict[str, float]) -> dict[str, Any]:
    return {
        "domain": domain,
        "signal": signal,
        "strength": round(max(0.0, min(1.0, strength)), 6),
        "interpretation": interpretation,
        "evidence": {k: round(float(v), 6) for k, v in sorted(evidence.items())},
    }


def build_replay_drift_readout(metrics: dict[str, Any]) -> dict[str, Any]:
    drift = float(metrics["replay_drift_score"])
    persistence = float(metrics["replay_persistence_score"])
    recurrence = float(metrics["replay_recurrence"])
    velocity = float(metrics["semantic_velocity"])

    state = "stable" if drift <= 0.12 and velocity <= 0.03 else "drifting" if drift <= 0.28 else "fragmenting"
    if recurrence >= 0.9 and drift < 0.08:
        state = "compressing"
    meaning = "meaningful_longitudinal_movement" if drift > 0.08 or velocity > 0.02 else "low_signal_movement"
    strength = min(1.0, (drift * 1.6) + (velocity * 6.0) + (1.0 - persistence) * 0.5)

    return {
        "domain": "replay_drift",
        "state": state,
        "movement_signal": meaning,
        "signal_strength": round(strength, 6),
        "evidence": {
            "replay_drift_score": round(drift, 6),
            "replay_persistence_score": round(persistence, 6),
            "replay_recurrence": round(recurrence, 6),
            "semantic_velocity": round(velocity, 6),
        },
    }


def build_propagation_evolution_readout(metrics: dict[str, Any]) -> dict[str, Any]:
    entropy = float(metrics["propagation_entropy"])
    concentration = float(metrics["pathway_concentration"])
    diversity_delta = float(metrics["pathway_diversity_delta"])
    fragmentation = float(metrics["propagation_fragmentation"])

    structure = "fragmenting" if fragmentation > 0.16 else "concentrating" if concentration > 0.2 else "broadening" if diversity_delta > 0 else "narrowing"
    useful = "increasing_ecological_usefulness" if entropy > 2.5 and fragmentation <= 0.16 else "limited_ecological_usefulness"
    strength = min(1.0, (entropy / 4.0) * 0.45 + concentration * 0.25 + max(0.0, diversity_delta) * 0.15 + (1.0 - min(1.0, fragmentation * 5.0)) * 0.15)

    return {
        "domain": "propagation_evolution",
        "state": structure,
        "ecological_usefulness": useful,
        "signal_strength": round(strength, 6),
        "evidence": {
            "propagation_entropy": round(entropy, 6),
            "pathway_concentration": round(concentration, 6),
            "pathway_diversity_delta": round(diversity_delta, 6),
            "propagation_fragmentation": round(fragmentation, 6),
        },
    }


def build_contradiction_ecology_readout(metrics: dict[str, Any]) -> dict[str, Any]:
    persistence = float(metrics["contradiction_persistence"])
    cluster_drift = float(metrics["contradiction_cluster_drift"])
    density_delta = float(metrics["contradiction_density_delta"])

    state = "migrating" if cluster_drift > 0.14 else "persisting" if persistence >= 0.5 else "stabilizing" if persistence >= 0.3 else "decaying"
    if density_delta > 0.12:
        state = "emerging"
    density_band = _band(persistence + max(0.0, density_delta) * 0.5)
    strength = min(1.0, persistence * 0.7 + cluster_drift * 0.8 + max(0.0, density_delta) * 0.5)

    return {
        "domain": "contradiction_ecology",
        "state": state,
        "contradiction_density_band": density_band,
        "signal_strength": round(strength, 6),
        "evidence": {
            "contradiction_persistence": round(persistence, 6),
            "contradiction_cluster_drift": round(cluster_drift, 6),
            "contradiction_density_delta": round(density_delta, 6),
        },
    }


def build_saturation_novelty_readout(metrics: dict[str, Any]) -> dict[str, Any]:
    saturation_velocity = float(metrics["saturation_velocity"])
    redundancy_growth = float(metrics["semantic_redundancy_growth"])
    novelty_decay = float(metrics["novelty_decay_rate"])
    compression = float(metrics["replay_compression_index"])

    state = "saturating" if (saturation_velocity > 0.02 or redundancy_growth > 0.05 or novelty_decay > 0.2) else "stable"
    risk = "rising_semantic_compression_risk" if compression > 0.15 or novelty_decay > 0.2 else "bounded_compression_risk"
    strength = min(1.0, max(0.0, saturation_velocity) * 8.0 + max(0.0, redundancy_growth) * 4.0 + novelty_decay * 0.5 + compression * 0.6)

    return {
        "domain": "saturation_novelty",
        "state": state,
        "compression_risk": risk,
        "signal_strength": round(strength, 6),
        "evidence": {
            "saturation_velocity": round(saturation_velocity, 6),
            "semantic_redundancy_growth": round(redundancy_growth, 6),
            "novelty_decay_rate": round(novelty_decay, 6),
            "replay_compression_index": round(compression, 6),
        },
    }


def build_monoculture_diversity_readout(metrics: dict[str, Any]) -> dict[str, Any]:
    monoculture_drift = float(metrics["monoculture_drift"])
    diversity_decay = float(metrics["diversity_decay"])
    gravity = float(metrics["semantic_gravity_index"])

    state = "monoculture_pressure" if gravity > 0.22 or monoculture_drift > 0.03 else "diversity_healthy"
    gravity_state = "semantic_gravity_forming" if gravity > 0.22 else "bounded_semantic_gravity"
    strength = min(1.0, max(0.0, monoculture_drift) * 8.0 + diversity_decay * 1.5 + gravity * 1.2)

    return {
        "domain": "monoculture_diversity",
        "state": state,
        "semantic_gravity_state": gravity_state,
        "signal_strength": round(strength, 6),
        "evidence": {
            "monoculture_drift": round(monoculture_drift, 6),
            "diversity_decay": round(diversity_decay, 6),
            "semantic_gravity_index": round(gravity, 6),
        },
    }


def build_ecosystem_interaction_readout(metrics: dict[str, Any]) -> dict[str, Any]:
    density_delta = float(metrics["interaction_density_delta"])
    cohesion = float(metrics["ecosystem_cohesion_shift"])
    cascades = float(metrics["replay_cascade_emergence"])
    coupling = float(metrics["cross_cluster_replay_coupling"])

    state = "interaction_increasing" if density_delta > 0.0 or coupling > 0.16 else "interaction_flat"
    ecology_mode = "ecology_like_behavior" if cohesion >= 5.0 and coupling >= 0.16 else "partially_isolated_behavior"
    cascade_state = "replay_cascades_emerging" if cascades > 0 else "replay_cascades_not_detected"
    strength = min(1.0, max(0.0, density_delta) * 0.3 + min(1.0, cohesion / 10.0) * 0.35 + min(1.0, coupling * 2.5) * 0.25 + min(1.0, cascades / 3.0) * 0.1)

    return {
        "domain": "ecosystem_interaction",
        "state": state,
        "ecosystem_mode": ecology_mode,
        "cascade_state": cascade_state,
        "signal_strength": round(strength, 6),
        "evidence": {
            "interaction_density_delta": round(density_delta, 6),
            "ecosystem_cohesion_shift": round(cohesion, 6),
            "replay_cascade_emergence": round(cascades, 6),
            "cross_cluster_replay_coupling": round(coupling, 6),
        },
    }


def build_replay_ecology_interpretation_summary(readouts: dict[str, dict[str, Any]], exp2_payload: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(((name, float(v["signal_strength"])) for name, v in readouts.items()), key=lambda x: (-x[1], x[0]))
    strongest, weakest = ranked[0], ranked[-1]

    contradiction_strength = float(readouts["contradiction_ecology"]["signal_strength"])
    saturation_strength = float(readouts["saturation_novelty"]["signal_strength"])
    mono_strength = float(readouts["monoculture_diversity"]["signal_strength"])
    prop_strength = float(readouts["propagation_evolution"]["signal_strength"])
    interaction_strength = float(readouts["ecosystem_interaction"]["signal_strength"])
    drift_state = readouts["replay_drift"]["state"]

    state = "emerging_replay_ecology"
    if exp2_payload["observation_window"]["slice_count"] < 3:
        state = "sparse_observation_environment"
    elif drift_state == "fragmenting":
        state = "fragmented_replay_ecology"
    elif mono_strength >= 0.5:
        state = "monoculture_risk_ecology"
    elif saturation_strength >= 0.55:
        state = "saturation_risk_ecology"
    elif contradiction_strength >= 0.5:
        state = "contradiction_heavy_ecology"
    elif prop_strength >= 0.55:
        state = "propagation_dense_ecology"
    elif interaction_strength >= 0.55 and contradiction_strength >= 0.35 and prop_strength >= 0.45:
        state = "maturing_replay_ecology"

    assert state in _ALLOWED_STATES
    maturity_score = (interaction_strength * 0.3) + (prop_strength * 0.25) + (contradiction_strength * 0.2) + (1.0 - saturation_strength) * 0.15 + (1.0 - mono_strength) * 0.1
    confidence_score = sum(v[1] for v in ranked) / len(ranked)

    findings = [
        _finding("replay_drift", readouts["replay_drift"]["state"], readouts["replay_drift"]["signal_strength"], f"Observed replay drift is {readouts['replay_drift']['state']} with {readouts['replay_drift']['movement_signal']}.", readouts["replay_drift"]["evidence"]),
        _finding("propagation", readouts["propagation_evolution"]["state"], readouts["propagation_evolution"]["signal_strength"], f"Propagation structure is {readouts['propagation_evolution']['state']} and {readouts['propagation_evolution']['ecological_usefulness']}.", readouts["propagation_evolution"]["evidence"]),
        _finding("contradiction", readouts["contradiction_ecology"]["state"], readouts["contradiction_ecology"]["signal_strength"], f"Contradiction persistence indicates {readouts['contradiction_ecology']['state']} behavior.", readouts["contradiction_ecology"]["evidence"]),
        _finding("saturation", readouts["saturation_novelty"]["state"], readouts["saturation_novelty"]["signal_strength"], f"Replay saturation profile is {readouts['saturation_novelty']['state']} with {readouts['saturation_novelty']['compression_risk']}.", readouts["saturation_novelty"]["evidence"]),
        _finding("diversity", readouts["monoculture_diversity"]["state"], readouts["monoculture_diversity"]["signal_strength"], f"Semantic gravity profile is {readouts['monoculture_diversity']['semantic_gravity_state']}.", readouts["monoculture_diversity"]["evidence"]),
        _finding("interaction", readouts["ecosystem_interaction"]["state"], readouts["ecosystem_interaction"]["signal_strength"], f"Interaction density indicates {readouts['ecosystem_interaction']['ecosystem_mode']}.", readouts["ecosystem_interaction"]["evidence"]),
    ][:MAX_FINDINGS]

    caveats = [
        "Observation caveat: bounded deterministic slices may underrepresent low-frequency semantic transitions.",
        "Observation caveat: interpretation is evidence-linked to LR6-EXP2 diagnostics and not a predictive surface.",
        "Observation caveat: replay ecology state labels are experimental readout categories only.",
    ][:MAX_CAVEATS]
    priorities = [
        "Monitor contradiction persistence versus contradiction cluster migration in the next bounded slice.",
        "Monitor propagation concentration against propagation fragmentation to detect semantic gravity spillover.",
        "Monitor novelty decay and replay compression index for saturation inflection.",
        "Monitor cross-cluster replay coupling and cascade emergence for ecology cohesion progression.",
    ][:MAX_PRIORITIES]

    return {
        "dominant_replay_ecology_state": state,
        "strongest_observed_signal": {"domain": strongest[0], "strength": round(strongest[1], 6)},
        "weakest_observed_signal": {"domain": weakest[0], "strength": round(weakest[1], 6)},
        "replay_ecology_maturity_band": _band(maturity_score),
        "observation_confidence_band": _band(confidence_score),
        "key_ecological_findings": findings,
        "caveats": caveats,
        "next_observation_priorities": priorities,
    }


def certify_lr6_exp3_experimental_boundaries() -> dict[str, Any]:
    return {
        "experimental_mode_only": True,
        "governed_lr6_activation": False,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "bounded_observation_only": True,
        "additive_architecture_preserved": True,
        "anti_monoculture_controls_preserved": True,
        "saturation_guardrails_preserved": True,
    }


def build_replay_ecology_signal_readout(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    exp2 = build_lr6_exp2_dashboard_payload(max_entities=max_entities, slice_count=slice_count)
    metrics = exp2["observation_metrics"]

    readouts = {
        "replay_drift": build_replay_drift_readout(metrics["replay_drift"]),
        "propagation_evolution": build_propagation_evolution_readout(metrics["propagation"]),
        "contradiction_ecology": build_contradiction_ecology_readout(metrics["contradiction"]),
        "saturation_novelty": build_saturation_novelty_readout(metrics["saturation"]),
        "monoculture_diversity": build_monoculture_diversity_readout(metrics["monoculture"]),
        "ecosystem_interaction": build_ecosystem_interaction_readout(metrics["interaction"]),
    }
    summary = build_replay_ecology_interpretation_summary(readouts, exp2)

    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "observation_window": exp2["observation_window"],
        "input_diagnostics_reference": {
            "source_module": "lr6_exp2_longitudinal_replay_observation",
            "deterministic_version": exp2["deterministic_version"],
            "deterministic_seed": exp2["deterministic_seed"],
        },
        "domain_readouts": readouts,
        "interpretation_summary": summary,
        "experimental_certification": certify_lr6_exp3_experimental_boundaries(),
    }


def build_lr6_exp3_dashboard_payload(max_entities: int = 120, slice_count: int = 4) -> dict[str, Any]:
    payload = build_replay_ecology_signal_readout(max_entities=max_entities, slice_count=slice_count)
    return {
        "phase": "LR6-EXP3",
        "objective": "Replay ecology signal readout and interpretation layer",
        "readout_payload": payload,
        "dashboard_sections": {
            "replay_drift": payload["domain_readouts"]["replay_drift"],
            "propagation_evolution": payload["domain_readouts"]["propagation_evolution"],
            "contradiction_ecology": payload["domain_readouts"]["contradiction_ecology"],
            "saturation_novelty": payload["domain_readouts"]["saturation_novelty"],
            "monoculture_diversity": payload["domain_readouts"]["monoculture_diversity"],
            "ecosystem_interaction": payload["domain_readouts"]["ecosystem_interaction"],
            "composite_interpretation": payload["interpretation_summary"],
        },
    }
