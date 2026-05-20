from __future__ import annotations

from typing import Any

from .chronic_instability import compute_chronic_instability
from .durability_replay import replay_durability_timeline
from .persistence_signatures import compute_persistence_checksum
from .resilience_erosion import compute_resilience_erosion
from .stabilization_longevity import compute_stabilization_longevity


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def _classification(score: float) -> str:
    if score >= 0.8:
        return "durable"
    if score >= 0.6:
        return "sustained"
    if score >= 0.35:
        return "fragile"
    return "degrading"


def compute_persistence_durability(node_states: list[dict[str, Any]], durability_id: str = "tier4_persistence") -> dict[str, Any]:
    source = [dict(s) for s in node_states]
    erosion = compute_resilience_erosion(source)
    instability = compute_chronic_instability(source)
    longevity = compute_stabilization_longevity(source)
    replay = replay_durability_timeline(sorted(source, key=lambda x: str(x.get("node_id", ""))), window_size=len(source))

    survivability = _b(1.0 - ((erosion["resilience_erosion_score"] + instability["chronic_instability_score"]) / 2.0))
    decay = _b((erosion["resilience_erosion_score"] + (1.0 - longevity["stabilization_longevity_score"])) / 2.0)
    score = _b((survivability * 0.45) + (longevity["stabilization_longevity_score"] * 0.35) + ((1.0 - instability["chronic_instability_score"]) * 0.20))

    dominant = sorted([
        ("erosion", erosion["resilience_erosion_score"]),
        ("instability", instability["chronic_instability_score"]),
        ("longevity", 1.0 - longevity["stabilization_longevity_score"]),
    ], key=lambda x: (-x[1], x[0]))[0][0]

    out = {
        "durability_id": durability_id,
        "durability_score": score,
        "bounded_durability_score": score,
        "persistence_survivability_score": survivability,
        "resilience_erosion_score": erosion["resilience_erosion_score"],
        "stabilization_longevity_score": longevity["stabilization_longevity_score"],
        "chronic_instability_score": instability["chronic_instability_score"],
        "durability_decay_score": decay,
        "dominant_durability_factor": dominant,
        "durability_classification": _classification(score),
        "durability_replay_checksum": replay["durability_replay_checksum"],
        "erosion_checksum": erosion["erosion_checksum"],
        "instability_checksum": instability["instability_checksum"],
        "longevity_checksum": longevity["longevity_checksum"],
        "chronic_instability_detected": instability["chronic_instability_detected"],
        "durability_decay_detected": decay >= 0.5,
        "persistent_survivability_detected": survivability >= 0.5,
        "durability_consistency_valid": replay["chronology_preserved"],
        "durability_replay_window_size": replay["durability_replay_window_size"],
    }
    out["persistence_checksum"] = compute_persistence_checksum(out)
    return out
