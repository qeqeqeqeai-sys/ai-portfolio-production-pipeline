from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    build_fragility_curve_checksum_chain,
    build_fragility_curve_summary,
    build_fragility_evolution_curves,
    build_t3_fragility_evolution_report,
    certify_fragility_evolution_curves,
    certify_structural_delta_intelligence,
    certify_temporal_snapshot_sequence,
    validate_fragility_curve_inputs,
)


def _snap(sid, dt, chk, entities, status="CERTIFIED"):
    return {"snapshot_id": sid, "as_of_date": dt, "checksum": chk, "certification_status": status, "entities": entities}


def _t2(snaps):
    return certify_structural_delta_intelligence(certify_temporal_snapshot_sequence(snaps))


def test_public_api_exports_exist():
    assert callable(validate_fragility_curve_inputs)
    assert callable(build_fragility_evolution_curves)
    assert callable(build_fragility_curve_summary)
    assert callable(build_fragility_curve_checksum_chain)
    assert callable(certify_fragility_evolution_curves)
    assert callable(build_t3_fragility_evolution_report)


def test_certified_blocked_and_empty_cases():
    good = _t2([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 1, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 2, "score_band": "MODERATE", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 3, "score_band": "HIGH", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
    ])
    assert certify_fragility_evolution_curves(good)["t3_status"] == "FRAGILITY_CURVES_CERTIFIED"
    assert certify_fragility_evolution_curves(None)["t3_status"] == "FRAGILITY_CURVES_BLOCKED"
    empty = deepcopy(good)
    empty["delta_records"] = []
    assert certify_fragility_evolution_curves(empty)["t3_status"] == "FRAGILITY_CURVES_BLOCKED"


def test_determinism_immutability_metrics_and_labels():
    env = _t2([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "B", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "A", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "D", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "E", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 12, "score_band": "MODERATE", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "B", "ai_expectation_failure_score": 8, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "D", "ai_expectation_failure_score": 12, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "E", "ai_expectation_failure_score": 11, "score_band": "MODERATE", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 14, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "B", "ai_expectation_failure_score": 6, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "D", "ai_expectation_failure_score": 8, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "E", "ai_expectation_failure_score": 12, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
    ])
    before = deepcopy(env)
    one = certify_fragility_evolution_curves(env)
    two = certify_fragility_evolution_curves(env)
    assert one["result_checksum"] == two["result_checksum"]
    assert env == before
    curves = one["curve_records"]
    assert [c["subject_id"] for c in curves] == sorted([c["subject_id"] for c in curves])
    by_id = {c["subject_id"]: c for c in curves}
    assert by_id["A"]["curve_label"] == "FRAGILITY_RISING"
    assert by_id["B"]["curve_label"] == "FRAGILITY_FALLING"
    assert by_id["C"]["curve_label"] == "FRAGILITY_STABLE"
    assert by_id["D"]["curve_label"] == "FRAGILITY_VOLATILE"
    assert by_id["E"]["cumulative_score_delta"] == 2.0 and by_id["E"]["average_pair_delta"] == 1.0
    assert by_id["E"]["directional_consistency"] == 1.0 and by_id["E"]["persistence_count"] == 1
    assert one["temporal_lineage"]["t2_result_checksum"] == env["result_checksum"]
    assert all(v is False for v in one["forbidden_capabilities"].values())


def test_insufficient_history_and_degraded_input_and_smoke_report_helpers():
    insuff = _t2([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 1, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 2, "score_band": "MODERATE", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
    ])
    cert_i = certify_fragility_evolution_curves(insuff)
    assert cert_i["curve_records"][0]["curve_label"] == "FRAGILITY_INSUFFICIENT_HISTORY"

    deg = _t2([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": "x"}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 1, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 2, "score_band": "MODERATE", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
    ])
    cert_d = certify_fragility_evolution_curves(deg)
    assert cert_d["t3_status"] == "FRAGILITY_CURVES_DEGRADED"
    assert cert_d["curve_records"][0]["curve_label"] == "FRAGILITY_DEGRADED_INPUT"
    assert build_fragility_curve_checksum_chain(cert_d["curve_records"]) ["curve_chain_checksum"]
    assert build_fragility_curve_summary(cert_d["curve_records"])["curve_count"] >= 1
    assert "T3 Fragility Evolution Curves Report" in build_t3_fragility_evolution_report(cert_d)
