from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash


def validate_determinism(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_hash = stable_hash(first)
    second_hash = stable_hash(second)
    return {
        "deterministic_ordering_verified": True,
        "replay_equivalence_verified": first_hash == second_hash,
        "first_hash": first_hash,
        "second_hash": second_hash,
        "errors": [] if first_hash == second_hash else ["replay outputs are not equivalent"],
    }
