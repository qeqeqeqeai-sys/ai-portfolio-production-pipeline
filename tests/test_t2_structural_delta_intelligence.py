from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    build_structural_delta_checksum_chain,
    build_structural_delta_records,
    build_structural_delta_summary,
    build_t2_structural_delta_report,
    certify_structural_delta_intelligence,
    certify_temporal_snapshot_sequence,
    validate_structural_delta_inputs,
)


def _snap(sid, dt, chk, entities, status="CERTIFIED"):
    return {"snapshot_id": sid, "as_of_date": dt, "checksum": chk, "certification_status": status, "entities": entities}


def _t1_env(snaps):
    return certify_temporal_snapshot_sequence(snaps)


def test_public_api_exports_exist():
    assert callable(validate_structural_delta_inputs)
    assert callable(build_structural_delta_records)
    assert callable(build_structural_delta_summary)
    assert callable(build_structural_delta_checksum_chain)
    assert callable(certify_structural_delta_intelligence)
    assert callable(build_t2_structural_delta_report)


def test_valid_sequence_two_snapshots_certified_and_lineage_preserved():
    snaps = [
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"narrative": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 12.34567, "score_band": "MODERATE", "relative_fragility_rank": 1, "driver_map": {"narrative": 2}}]),
    ]
    r = certify_structural_delta_intelligence(_t1_env(snaps))
    assert r["t2_status"] == "STRUCTURAL_DELTA_CERTIFIED"
    assert r["temporal_lineage"]["t1_sequence_checksum"]


def test_fewer_than_two_snapshots_blocked():
    r = certify_structural_delta_intelligence(_t1_env([_snap("s1", "2026-01-01", "c1", [])]))
    assert r["t2_status"] == "STRUCTURAL_DELTA_BLOCKED"


def test_deterministic_pairing_and_entity_ordering_and_repeatable_checksum_and_immutable_inputs():
    snaps = [
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "B", "ai_expectation_failure_score": 10}, {"entity_id": "A", "ai_expectation_failure_score": 9}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 8}, {"entity_id": "B", "ai_expectation_failure_score": 11}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 7}, {"entity_id": "B", "ai_expectation_failure_score": 12}]),
    ]
    env = _t1_env(snaps)
    before = deepcopy(env)
    one = certify_structural_delta_intelligence(env)
    two = certify_structural_delta_intelligence(env)
    assert [p["pair_index"] for p in one["delta_records"]] == [0, 1]
    assert one["delta_records"][0]["comparable_entities"] == ["A", "B"]
    assert one["result_checksum"] == two["result_checksum"]
    assert env == before


def test_score_missing_labels_band_rank_driver_and_membership_and_degraded_and_forbidden_false_and_t1_smoke():
    snaps = [
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": "x", "score_band": "HIGH", "relative_fragility_rank": 5, "driver_map": {"a": 2}}, {"entity_id": "B", "ai_expectation_failure_score": 1}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 1.00555, "score_band": "MODERATE", "relative_fragility_rank": 6, "driver_map": {"a": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 2}]),
    ]
    cert = certify_structural_delta_intelligence(_t1_env(snaps))
    rec = cert["delta_records"][0]
    labels = {d["label"] for d in rec["score_deltas"]}
    assert "SCORE_MISSING_PREVIOUS" in labels
    assert rec["band_transitions"][0]["label"] in {"BAND_IMPROVED", "BAND_DETERIORATED", "BAND_UNCHANGED", "BAND_UNKNOWN"}
    assert rec["rank_transitions"][0]["rank_direction"] in {"RANK_IMPROVED", "RANK_DETERIORATED", "RANK_UNCHANGED", "RANK_UNKNOWN"}
    assert rec["driver_deltas"][0]["label"] in {"DRIVER_STRENGTHENED", "DRIVER_WEAKENED", "DRIVER_UNCHANGED", "DRIVER_UNKNOWN"}
    assert rec["missing_entities_from_previous"] == ["B"] and rec["new_entities_in_current"] == ["C"]
    assert cert["t2_status"] == "STRUCTURAL_DELTA_DEGRADED"
    assert all(v is False for v in cert["forbidden_capabilities"].values())
    assert certify_temporal_snapshot_sequence(snaps)["t1_status"] in {"TEMPORAL_SEQUENCE_CERTIFIED", "TEMPORAL_SEQUENCE_DEGRADED"}


def test_numeric_score_delta_rounding_and_checksum_chain_builder_and_report():
    snaps = [
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 1.11111, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 2.22222, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 2}}]),
    ]
    env = _t1_env(snaps)
    records = build_structural_delta_records(env)
    assert records[0]["score_deltas"][0]["delta"] == 1.1111
    chain = build_structural_delta_checksum_chain(records)
    assert chain["delta_chain_checksum"]
    summary = build_structural_delta_summary(records)
    assert summary["pair_count"] == 1
    cert = certify_structural_delta_intelligence(env)
    assert "T2 Structural Delta Intelligence Report" in build_t2_structural_delta_report(cert)
