from __future__ import annotations

from copy import deepcopy
from typing import Any

from .federation_common import clamp_score, mean_bounded
from .federation_determinism import stable_checksum
from .federation_export_contracts import collect_tier5_export_inventory
from .federation_replay_contracts import validate_replay_contract
from .federation_score_contracts import validate_score_contracts


def run_tier5h_federation_integrity(*, federation_id: str, tier_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    frozen = deepcopy(tier_payloads)
    ordered_payloads = {k: frozen[k] for k in sorted(frozen)}
    merged: dict[str, Any] = {}
    for key in sorted(ordered_payloads):
        merged.update(ordered_payloads[key])

    score_contracts = validate_score_contracts(merged)
    exports = collect_tier5_export_inventory()
    replay = validate_replay_contract(merged)

    immutability_score = 1.0 if frozen == tier_payloads else 0.0
    scores = [
        replay["federation_determinism_score"],
        score_contracts["federation_score_contract_score"],
        score_contracts["federation_checksum_contract_score"],
        replay["federation_replay_contract_score"],
        exports["federation_export_contract_score"],
        immutability_score,
    ]
    integrity_score = mean_bounded(scores)
    gap = round(1.0 - integrity_score, 6)
    classification = "stable" if integrity_score >= 0.95 else "stabilization_required"
    dominant = "federation_stabilization_gap_score" if gap > 0 else "federation_integrity_score"

    result = {
        "federation_integrity_id": stable_checksum({"federation_id": federation_id}, prefix="fiid"),
        "federation_integrity_score": integrity_score,
        "bounded_federation_integrity_score": clamp_score(integrity_score),
        "federation_determinism_score": replay["federation_determinism_score"],
        "federation_score_contract_score": score_contracts["federation_score_contract_score"],
        "federation_checksum_contract_score": score_contracts["federation_checksum_contract_score"],
        "federation_replay_contract_score": replay["federation_replay_contract_score"],
        "federation_export_contract_score": exports["federation_export_contract_score"],
        "federation_immutability_contract_score": immutability_score,
        "federation_stabilization_gap_score": gap,
        "dominant_integrity_factor": dominant,
        "federation_integrity_classification": classification,
        "federation_determinism_checksum": replay["federation_determinism_checksum"],
        "federation_score_contracts_checksum": score_contracts["federation_score_contracts_checksum"],
        "federation_export_contracts_checksum": exports["federation_export_contracts_checksum"],
        "federation_replay_contracts_checksum": replay["federation_replay_contracts_checksum"],
    }
    result["federation_integrity_checksum"] = stable_checksum({k: result[k] for k in sorted(result) if k != "federation_integrity_checksum"}, prefix="tier5h_integrity")
    return result
