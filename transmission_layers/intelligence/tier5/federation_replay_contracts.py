from __future__ import annotations

from copy import deepcopy
from typing import Any

from .federation_determinism import deterministic_replay_stability, stable_checksum


def validate_replay_contract(payload: dict[str, Any]) -> dict[str, Any]:
    snapshot = deepcopy(payload)
    stability, deterministic_checksum = deterministic_replay_stability(snapshot, runs=5)
    return {
        "federation_replay_contract_score": stability,
        "federation_determinism_score": stability,
        "federation_determinism_checksum": deterministic_checksum,
        "federation_replay_contracts_checksum": stable_checksum({"stability": stability, "checksum": deterministic_checksum}, prefix="tier5h_replay"),
    }
