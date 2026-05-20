from __future__ import annotations

from typing import Any

from .federation_boundary_history import boundary_recurrence_score
from .federation_bottleneck_persistence import bottleneck_persistence_score
from .federation_bridge_persistence import bridge_persistence_score
from .federation_common import clamp_score, weighted_bounded_score
from .federation_persistence_explanations import fixed_federation_persistence_explanations
from .federation_recovery_history import recovery_dependency_recurrence_score
from .federation_replay_history import ingest_federation_replay_history
from .federation_temporal_signatures import federation_signature_stability, federation_temporal_checksum
from .inter_system_contagion_history import contagion_corridor_persistence_score
from .distributed_survivability_history import survivability_dependency_recurrence_score


def _continuity_drift_score(history: list[dict[str, Any]]) -> float:
    if len(history) <= 1:
        return 0.0
    drifts: list[float] = []
    for i in range(1, len(history)):
        prev = set(tuple(x) for x in history[i - 1]["bridges"])
        curr = set(tuple(x) for x in history[i]["bridges"])
        union = len(prev | curr)
        changed = len(prev ^ curr)
        drifts.append(0.0 if union == 0 else changed / union)
    return clamp_score(sum(drifts) / len(drifts))


def run_tier5b_federation_persistence(*, replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    history = ingest_federation_replay_history(replay_snapshots)
    bridge_score = bridge_persistence_score([s["bridges"] for s in history])
    boundary_score = boundary_recurrence_score([s["boundary_weaknesses"] for s in history])
    contagion_score = contagion_corridor_persistence_score([s["contagion_corridors"] for s in history])
    bottleneck_score = bottleneck_persistence_score([s["bottlenecks"] for s in history])
    survivability_score = survivability_dependency_recurrence_score([s["survivability_dependencies"] for s in history])
    recovery_score = recovery_dependency_recurrence_score([s["recovery_dependencies"] for s in history])
    signatures = [federation_temporal_checksum(s) for s in history]
    signature_stability = federation_signature_stability(signatures)
    continuity_drift = _continuity_drift_score(history)
    persistence_score = weighted_bounded_score([
        (bridge_score, 0.2), (boundary_score, 0.1), (contagion_score, 0.15), (bottleneck_score, 0.15),
        (survivability_score, 0.15), (recovery_score, 0.15), (signature_stability, 0.1),
    ])

    factors = sorted([
        ("bridge_persistence_score", bridge_score),
        ("boundary_recurrence_score", boundary_score),
        ("contagion_corridor_persistence_score", contagion_score),
        ("bottleneck_persistence_score", bottleneck_score),
        ("survivability_dependency_recurrence_score", survivability_score),
        ("recovery_dependency_recurrence_score", recovery_score),
        ("federation_signature_stability_score", signature_stability),
    ], key=lambda x: (-x[1], x[0]))

    result = {
        "federation_persistence_id": f"fp_{federation_temporal_checksum({'history': history})}",
        "replay_window_size": len(history),
        "federation_persistence_score": persistence_score,
        "bounded_federation_persistence_score": clamp_score(persistence_score),
        "bridge_persistence_score": bridge_score,
        "boundary_recurrence_score": boundary_score,
        "contagion_corridor_persistence_score": contagion_score,
        "bottleneck_persistence_score": bottleneck_score,
        "survivability_dependency_recurrence_score": survivability_score,
        "recovery_dependency_recurrence_score": recovery_score,
        "federation_signature_stability_score": signature_stability,
        "federation_continuity_drift_score": continuity_drift,
        "dominant_persistence_factor": factors[0][0] if factors else "none",
        "federation_persistence_classification": "stable" if persistence_score >= 0.66 else "mixed" if persistence_score >= 0.33 else "volatile",
    }
    checksum_payload = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in sorted(result.items()) if k != "federation_persistence_checksum"}
    result["federation_persistence_checksum"] = f"tier5b_chk_{federation_temporal_checksum(checksum_payload)}"
    result.update(fixed_federation_persistence_explanations(result))
    return result
