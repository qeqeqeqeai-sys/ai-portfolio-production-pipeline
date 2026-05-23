"""B3 deterministic assembler from certified B2 candidate to B1-compatible certified snapshot."""

from __future__ import annotations

from copy import deepcopy

from .b1_fragility_payload_builder import build_deterministic_fragility_payload
from .b1_market_snapshot_builder import build_deterministic_market_snapshot
from .b1_snapshot_certification import certify_b1_snapshot
from .b3_certified_snapshot_envelope import build_b3_certified_snapshot_envelope
from .b3_snapshot_assembly_certification import decide_b3_snapshot_assembly
from .b3_snapshot_assembly_validation import validate_b3_candidate_for_assembly
from .b3_snapshot_input_mapper import map_b2_candidate_to_b1_snapshot_inputs


def assemble_b3_certified_snapshot_from_b2_candidate(b2_candidate_envelope: dict) -> dict:
    frozen = deepcopy(b2_candidate_envelope)
    validation = validate_b3_candidate_for_assembly(frozen)
    decision = decide_b3_snapshot_assembly(validation)

    accepted = deepcopy(frozen.get("accepted_records", []))
    mapped = map_b2_candidate_to_b1_snapshot_inputs(accepted, frozen.get("as_of_date", ""))
    b1_snapshot = build_deterministic_market_snapshot(mapped["b1_entity_score_inputs"], mapped["b1_benchmark_score_inputs"])
    b1_fragility = build_deterministic_fragility_payload(b1_snapshot)
    b1_cert = certify_b1_snapshot(b1_fragility)

    return build_b3_certified_snapshot_envelope(
        {
            "b3_decision": decision,
            "b1_snapshot_payload": b1_snapshot,
            "b1_fragility_payload": b1_fragility,
            "b1_certification_payload": b1_cert,
            "b2_candidate_reference": {
                "snapshot_stage": frozen.get("snapshot_stage"),
                "as_of_date": frozen.get("as_of_date"),
                "deterministic_checksum": frozen.get("deterministic_checksum"),
                "certification_status": frozen.get("certification_status"),
            },
            "b3_mapping_summary": mapped["mapping_summary"],
            "b3_validation_summary": validation,
            "degraded_visibility": {
                "b2_degraded_input_flags": deepcopy(frozen.get("degraded_input_flags", [])),
                "quarantined_record_count": len(frozen.get("quarantined_records", [])),
            },
            "replay_contract": {
                "deterministic_ordering": True,
                "immutable_input_safety": True,
                "canonical_json_serialization": True,
                "b1_b2_b3_replay_compatible": True,
            },
        }
    )
