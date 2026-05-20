from __future__ import annotations

from typing import Any

from .distributed_survivability_evolution import distributed_survivability_evolution_score
from .federation_boundary_evolution import federation_boundary_evolution_score
from .federation_bottleneck_evolution import federation_bottleneck_evolution_score
from .federation_bridge_evolution import federation_bridge_evolution_score
from .federation_common import clamp_score, weighted_bounded_score
from .federation_dependency_evolution import federation_dependency_evolution_score
from .federation_evolution_explanations import fixed_federation_evolution_explanations
from .federation_evolution_signatures import federation_evolution_checksum
from .federation_phase_transitions import federation_phase_transition_score
from .federation_recovery_evolution import federation_recovery_evolution_score
from .federation_replay_history import ingest_federation_replay_history
from .inter_system_contagion_evolution import inter_system_contagion_evolution_score


def run_tier5c_federation_temporal_evolution(*, replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    history = ingest_federation_replay_history(replay_snapshots)
    topology_counts = [len(s["bridges"]) + len(s["systems"]) for s in history]

    topology_evolution_score = clamp_score(0.0 if len(topology_counts) <= 1 else sum(abs(topology_counts[i] - topology_counts[i - 1]) / max(1, topology_counts[i - 1]) for i in range(1, len(topology_counts))) / (len(topology_counts) - 1))
    phase_transition_score = federation_phase_transition_score(topology_counts)
    bridge_evolution_score = federation_bridge_evolution_score([s["bridges"] for s in history])
    dependency_evolution_score = federation_dependency_evolution_score([s["survivability_dependencies"] for s in history])
    boundary_evolution_score = federation_boundary_evolution_score([s["boundary_weaknesses"] for s in history])
    contagion_evolution_score = inter_system_contagion_evolution_score([s["contagion_corridors"] for s in history])
    bottleneck_evolution_score = federation_bottleneck_evolution_score([s["bottlenecks"] for s in history])
    survivability_evolution_score = distributed_survivability_evolution_score([s["survivability_dependencies"] for s in history])
    recovery_evolution_score = federation_recovery_evolution_score([s["recovery_dependencies"] for s in history])
    continuity_evolution_score = clamp_score((bridge_evolution_score + dependency_evolution_score + recovery_evolution_score) / 3.0)

    federation_evolution_score = weighted_bounded_score([
        (topology_evolution_score, 0.13), (phase_transition_score, 0.12), (bridge_evolution_score, 0.12),
        (dependency_evolution_score, 0.11), (boundary_evolution_score, 0.1), (contagion_evolution_score, 0.1),
        (bottleneck_evolution_score, 0.1), (survivability_evolution_score, 0.1), (recovery_evolution_score, 0.07),
        (continuity_evolution_score, 0.05),
    ])

    factors = sorted([
        ("topology_evolution_score", topology_evolution_score),
        ("phase_transition_score", phase_transition_score),
        ("bridge_evolution_score", bridge_evolution_score),
        ("dependency_evolution_score", dependency_evolution_score),
        ("contagion_evolution_score", contagion_evolution_score),
        ("bottleneck_evolution_score", bottleneck_evolution_score),
        ("boundary_evolution_score", boundary_evolution_score),
        ("survivability_evolution_score", survivability_evolution_score),
        ("recovery_evolution_score", recovery_evolution_score),
    ], key=lambda x: (-x[1], x[0]))

    result = {
        "federation_evolution_id": f"fe_{federation_evolution_checksum({'history': history})}",
        "replay_window_count": len(history),
        "federation_evolution_score": federation_evolution_score,
        "bounded_federation_evolution_score": clamp_score(federation_evolution_score),
        "topology_evolution_score": topology_evolution_score,
        "phase_transition_score": phase_transition_score,
        "bridge_evolution_score": bridge_evolution_score,
        "dependency_evolution_score": dependency_evolution_score,
        "boundary_evolution_score": boundary_evolution_score,
        "contagion_evolution_score": contagion_evolution_score,
        "bottleneck_evolution_score": bottleneck_evolution_score,
        "survivability_evolution_score": survivability_evolution_score,
        "recovery_evolution_score": recovery_evolution_score,
        "continuity_evolution_score": continuity_evolution_score,
        "dominant_evolution_factor": factors[0][0] if factors else "none",
        "federation_evolution_classification": "phase_shifting" if federation_evolution_score >= 0.66 else "stabilizing" if federation_evolution_score >= 0.33 else "steady",
    }
    payload = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in sorted(result.items())}
    result["federation_temporal_evolution_checksum"] = federation_evolution_checksum(payload, prefix="tier5c_temporal")
    result["federation_phase_transition_checksum"] = federation_evolution_checksum({"phase_transition_score": phase_transition_score}, prefix="tier5c_phase")
    result["federation_bridge_evolution_checksum"] = federation_evolution_checksum({"bridge_evolution_score": bridge_evolution_score}, prefix="tier5c_bridge")
    result["federation_dependency_evolution_checksum"] = federation_evolution_checksum({"dependency_evolution_score": dependency_evolution_score}, prefix="tier5c_dependency")
    result["federation_boundary_evolution_checksum"] = federation_evolution_checksum({"boundary_evolution_score": boundary_evolution_score}, prefix="tier5c_boundary")
    result["inter_system_contagion_evolution_checksum"] = federation_evolution_checksum({"contagion_evolution_score": contagion_evolution_score}, prefix="tier5c_contagion")
    result["federation_bottleneck_evolution_checksum"] = federation_evolution_checksum({"bottleneck_evolution_score": bottleneck_evolution_score}, prefix="tier5c_bottleneck")
    result["distributed_survivability_evolution_checksum"] = federation_evolution_checksum({"survivability_evolution_score": survivability_evolution_score}, prefix="tier5c_survivability")
    result["federation_recovery_evolution_checksum"] = federation_evolution_checksum({"recovery_evolution_score": recovery_evolution_score}, prefix="tier5c_recovery")
    result["federation_evolution_signature_checksum"] = federation_evolution_checksum({"id": result["federation_evolution_id"], "score": federation_evolution_score}, prefix="tier5c_signature")
    result["federation_evolution_checksum"] = federation_evolution_checksum({k: v for k, v in sorted(result.items()) if k != "federation_evolution_checksum"}, prefix="tier5c_chk")
    result.update(fixed_federation_evolution_explanations(result))
    return result
