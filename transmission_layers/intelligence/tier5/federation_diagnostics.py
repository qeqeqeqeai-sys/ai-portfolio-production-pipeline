from __future__ import annotations

from typing import Any

from .federation_common import canonical_checksum, clamp_score, mean_bounded, weighted_bounded_score


def federation_topology_diagnostics(systems: list[dict[str, Any]], bridges: list[dict[str, Any]]) -> dict[str, Any]:
    density = clamp_score(len(bridges) / max(1, len(systems) * (len(systems) - 1)))
    redundancy = mean_bounded([b.get("redundancy", 0.0) for b in bridges])
    cohesion = weighted_bounded_score([(density, 0.6), (redundancy, 0.4)])
    return {"topology_density_score": density, "topology_redundancy_score": redundancy, "topology_cohesion_score": cohesion}


def cross_system_transmission_diagnostics(transmissions: list[dict[str, Any]]) -> dict[str, Any]:
    throughput = mean_bounded([t.get("throughput", 0.0) for t in transmissions])
    integrity = mean_bounded([t.get("integrity", 0.0) for t in transmissions])
    latency_penalty = mean_bounded([t.get("latency_penalty", 0.0) for t in transmissions])
    score = weighted_bounded_score([(throughput, 0.45), (integrity, 0.45), (1.0 - latency_penalty, 0.10)])
    return {"federated_throughput_score": throughput, "federated_integrity_score": integrity, "federated_latency_penalty_score": latency_penalty, "cross_system_transmission_score": score}


def bridge_boundary_diagnostics(bridges: list[dict[str, Any]]) -> dict[str, Any]:
    bridge_stability = mean_bounded([b.get("stability", 0.0) for b in bridges])
    boundary_hardening = mean_bounded([b.get("boundary_hardening", 0.0) for b in bridges])
    breach_exposure = mean_bounded([b.get("breach_exposure", 0.0) for b in bridges])
    return {"bridge_stability_score": bridge_stability, "boundary_hardening_score": boundary_hardening, "bridge_breach_exposure_score": breach_exposure, "bridge_boundary_health_score": weighted_bounded_score([(bridge_stability, 0.4), (boundary_hardening, 0.4), (1.0 - breach_exposure, 0.2)])}


def contagion_bottleneck_diagnostics(contagion_paths: list[dict[str, Any]]) -> dict[str, Any]:
    contagion = mean_bounded([p.get("contagion_risk", 0.0) for p in contagion_paths])
    bottleneck = mean_bounded([p.get("bottleneck_risk", 0.0) for p in contagion_paths])
    containment = mean_bounded([p.get("containment", 0.0) for p in contagion_paths])
    return {"inter_system_contagion_risk_score": contagion, "federation_bottleneck_risk_score": bottleneck, "federation_containment_score": containment, "contagion_bottleneck_pressure_score": weighted_bounded_score([(contagion, 0.45), (bottleneck, 0.45), (1.0 - containment, 0.10)])}


def survivability_recovery_dependency_diagnostics(dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    survivability = mean_bounded([d.get("survivability", 0.0) for d in dependencies])
    recovery = mean_bounded([d.get("recovery_readiness", 0.0) for d in dependencies])
    dependency_fragility = mean_bounded([d.get("dependency_fragility", 0.0) for d in dependencies])
    return {"distributed_survivability_score": survivability, "federated_recovery_readiness_score": recovery, "recovery_dependency_fragility_score": dependency_fragility, "distributed_recovery_health_score": weighted_bounded_score([(survivability, 0.4), (recovery, 0.4), (1.0 - dependency_fragility, 0.2)])}


def fixed_template_explanations(metrics: dict[str, float]) -> dict[str, str]:
    ordered = sorted((k, round(v, 4)) for k, v in metrics.items() if k.endswith("_score"))
    headline = "Tier 5A federation diagnostics computed deterministically with bounded scores."
    detail = "; ".join(f"{k}={v:.4f}" for k, v in ordered)
    return {"federation_explanation_headline": headline, "federation_explanation_detail": detail}


def federation_signatures(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "tier5a_federation_signature": canonical_checksum(payload, prefix="tier5a_sig"),
        "tier5a_federation_checksum": canonical_checksum(payload, prefix="tier5a_chk"),
    }
