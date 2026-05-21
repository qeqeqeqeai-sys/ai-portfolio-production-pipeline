from __future__ import annotations

from copy import deepcopy
from typing import Any

from .federation_common import clamp_score, mean_bounded
from .federation_determinism import stable_checksum
from .federation_export_contracts import collect_tier5_export_inventory
from .federation_replay_contracts import validate_replay_contract
from .federation_score_contracts import validate_score_contracts


INTEGRITY_CONTRACT_HEALTHY_THRESHOLD = 1.0
INTEGRITY_STABLE_THRESHOLD = 0.95
EXPECTED_TIER_PAYLOAD_KEYS = ("5a", "5b", "5c", "5d", "5e", "5f", "5g")


def _is_degraded(value: float) -> bool:
    return float(value) < INTEGRITY_CONTRACT_HEALTHY_THRESHOLD


def _has_fragmented_inventory(*, ordered_payloads: dict[str, dict[str, Any]], exports: dict[str, Any]) -> bool:
    missing_tiers = [tier for tier in EXPECTED_TIER_PAYLOAD_KEYS if tier not in ordered_payloads]
    empty_tiers = [tier for tier, payload in ordered_payloads.items() if not payload]
    missing_report_exports = [name for name in ("build_federation_stabilization_report",) if name not in exports.get("tier5_public_exports", [])]
    return bool(missing_tiers or empty_tiers or missing_report_exports)


def _resolve_integrity_classification(*,
    integrity_score: float,
    score_contracts: dict[str, Any],
    replay: dict[str, Any],
    exports: dict[str, Any],
    immutability_score: float,
    fragmented_inventory: bool,
) -> str:
    score_contract_gap = _is_degraded(score_contracts["federation_score_contract_score"]) or len(score_contracts.get("bounded_score_keys", [])) != len(score_contracts.get("score_keys", []))
    checksum_contract_gap = _is_degraded(score_contracts["federation_checksum_contract_score"])
    replay_contract_gap = _is_degraded(replay["federation_replay_contract_score"])
    export_contract_gap = _is_degraded(exports["federation_export_contract_score"])
    immutability_contract_gap = _is_degraded(immutability_score)

    determinism_acceptable = not replay_contract_gap and float(replay["federation_determinism_score"]) >= INTEGRITY_CONTRACT_HEALTHY_THRESHOLD

    if score_contract_gap:
        return "score_contract_gap"
    if checksum_contract_gap:
        return "checksum_contract_gap"
    if replay_contract_gap:
        return "replay_contract_gap"
    if export_contract_gap:
        return "export_contract_gap"
    if immutability_contract_gap:
        return "immutability_contract_gap"
    if determinism_acceptable and fragmented_inventory and integrity_score < INTEGRITY_STABLE_THRESHOLD:
        return "deterministic_but_fragmented"
    if integrity_score < INTEGRITY_STABLE_THRESHOLD:
        return "stabilization_required"
    return "stable"


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
    fragmented_inventory = _has_fragmented_inventory(ordered_payloads=ordered_payloads, exports=exports)
    classification = _resolve_integrity_classification(
        integrity_score=integrity_score,
        score_contracts=score_contracts,
        replay=replay,
        exports=exports,
        immutability_score=immutability_score,
        fragmented_inventory=fragmented_inventory,
    )
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
