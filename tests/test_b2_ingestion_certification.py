from transmission_layers.expectation_failure.real_data.b2_ingestion_candidate_builder import build_ingestion_candidate
from transmission_layers.expectation_failure.real_data.b2_ingestion_certification import certify_b2_ingestion_candidate
from transmission_layers.expectation_failure.real_data.b1_real_entity_registry import FIXED_ENTITY_ORDER
from transmission_layers.expectation_failure.real_data.b1_benchmark_registry import FIXED_BENCHMARK_ORDER


def test_b2_certification_blocked_on_checksum_mismatch():
    candidate = build_ingestion_candidate([], [], FIXED_ENTITY_ORDER, FIXED_BENCHMARK_ORDER, "2026-05-21")
    candidate["deterministic_checksum"] = "bad"
    out = certify_b2_ingestion_candidate(candidate)
    assert out["certification"]["certification_status"] == "BLOCKED_INGESTION_INVALID"


def test_b2_additive_export_integrity_and_b1_smoke():
    from transmission_layers.expectation_failure.real_data import build_b2_controlled_ingestion_adapter
    from transmission_layers.expectation_failure.real_data.b1_market_snapshot_builder import build_deterministic_market_snapshot

    assert callable(build_b2_controlled_ingestion_adapter)
    snapshot = build_deterministic_market_snapshot([], [])
    assert snapshot["snapshot_stage"] == "B1_REAL_DATA_MARKET_SNAPSHOT"
