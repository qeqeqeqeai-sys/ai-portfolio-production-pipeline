from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    assemble_b3_certified_snapshot_from_b2_candidate,
    build_b2_controlled_ingestion_adapter,
    validate_b4_snapshot_persistence_input,
)


def _b3_envelope():
    raw = [{"symbol": "NVDA", "metric_name": "price", "metric_value": 99, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"}]
    candidate = build_b2_controlled_ingestion_adapter(raw, "2026-05-21")["candidate"]
    return assemble_b3_certified_snapshot_from_b2_candidate(candidate)


def test_b4_validator_blocks_degraded_when_not_allowed_and_immutability():
    env = _b3_envelope()
    env["b3_decision"] = "DEGRADED_SNAPSHOT_READY"
    frozen = deepcopy(env)
    out = validate_b4_snapshot_persistence_input(env, allow_degraded=False)
    assert out["status"] == "BLOCKED"
    assert "degraded_not_allowed" in out["errors"]
    assert env == frozen


def test_b4_validator_blocks_malformed_and_missing_fields():
    out = validate_b4_snapshot_persistence_input({"b3_decision": "CERTIFIED_SNAPSHOT_READY"})
    assert out["status"] == "BLOCKED"
    assert "missing_b3_checksum" in out["errors"]
