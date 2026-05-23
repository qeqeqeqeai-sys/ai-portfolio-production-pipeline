from transmission_layers.expectation_failure.real_data import (
    assemble_b3_certified_snapshot_from_b2_candidate,
    build_b2_controlled_ingestion_adapter,
    certify_b4_snapshot_persistence_readiness,
)


def _envelope():
    raw = [{"symbol": "NVDA", "metric_name": "price", "metric_value": 99, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"}]
    candidate = build_b2_controlled_ingestion_adapter(raw, "2026-05-21")["candidate"]
    return assemble_b3_certified_snapshot_from_b2_candidate(candidate)


def test_b4_certification_ready_and_blocked_paths():
    env = _envelope()
    env["b3_decision"] = "CERTIFIED_SNAPSHOT_READY"
    ready = certify_b4_snapshot_persistence_readiness(env)
    assert ready["decision"] == "CERTIFIED_PERSISTENCE_READY"

    blocked = certify_b4_snapshot_persistence_readiness({"b3_decision": "BLOCKED_SNAPSHOT_INVALID"})
    assert blocked["decision"] == "BLOCKED_PERSISTENCE_INVALID"


def test_b1_b2_b3_non_regression_smoke_via_b4_path():
    env = _envelope()
    assert env["b2_candidate_reference"]["snapshot_stage"] == "B2_CONTROLLED_MARKET_INGESTION_CANDIDATE"
    assert "deterministic_checksum" in env
