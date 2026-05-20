from __future__ import annotations

from copy import deepcopy
from typing import Any


def ingest_federation_replay_history(replay_snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return deterministic, chronologically sorted, immutable replay history."""
    normalized: list[dict[str, Any]] = []
    for idx, snapshot in enumerate(replay_snapshots):
        snap = deepcopy(snapshot)
        federation_id = str(snap.get("federation_id", "unknown"))
        replay_index = int(snap.get("replay_index", idx))
        systems = sorted(str(s) for s in snap.get("systems", []))
        bridges = sorted((str(a), str(b)) for a, b in (tuple(x) for x in snap.get("bridges", [])))
        boundaries = sorted(str(x) for x in snap.get("boundary_weaknesses", []))
        contagion = sorted((str(a), str(b)) for a, b in (tuple(x) for x in snap.get("contagion_corridors", [])))
        bottlenecks = sorted(str(x) for x in snap.get("bottlenecks", []))
        survivability = sorted((str(a), str(b)) for a, b in (tuple(x) for x in snap.get("survivability_dependencies", [])))
        recovery = sorted((str(a), str(b)) for a, b in (tuple(x) for x in snap.get("recovery_dependencies", [])))
        normalized.append(
            {
                "federation_id": federation_id,
                "replay_index": replay_index,
                "systems": systems,
                "bridges": bridges,
                "boundary_weaknesses": boundaries,
                "contagion_corridors": contagion,
                "bottlenecks": bottlenecks,
                "survivability_dependencies": survivability,
                "recovery_dependencies": recovery,
            }
        )
    return sorted(normalized, key=lambda x: (x["replay_index"], x["federation_id"]))
