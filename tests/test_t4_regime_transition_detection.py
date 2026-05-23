from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    build_t4_regime_transition_report,
    certify_fragility_evolution_curves,
    certify_regime_transition_detection,
    certify_structural_delta_intelligence,
    certify_temporal_snapshot_sequence,
    validate_regime_transition_inputs,
)


def _snap(sid, dt, chk, entities, status="CERTIFIED"):
    return {"snapshot_id": sid, "as_of_date": dt, "checksum": chk, "certification_status": status, "entities": entities}


def _t3(snaps):
    return certify_fragility_evolution_curves(certify_structural_delta_intelligence(certify_temporal_snapshot_sequence(snaps)))


def test_t4_apis_and_blocked_empty_cases():
    assert callable(validate_regime_transition_inputs)
    good = _t3([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 1, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 3, "score_band": "MODERATE", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 6, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
    ])
    assert certify_regime_transition_detection(good)["t4_status"] == "REGIME_TRANSITIONS_CERTIFIED"
    assert certify_regime_transition_detection(None)["t4_status"] == "REGIME_TRANSITIONS_BLOCKED"
    bad = deepcopy(good); bad["curve_records"] = []
    assert certify_regime_transition_detection(bad)["t4_status"] == "REGIME_TRANSITIONS_BLOCKED"


def test_t4_determinism_mapping_confidence_lineage_and_controls():
    env = _t3([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "B", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "D", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 14, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "B", "ai_expectation_failure_score": 7, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "D", "ai_expectation_failure_score": 14, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 18, "score_band": "HIGH", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "B", "ai_expectation_failure_score": 5, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "C", "ai_expectation_failure_score": 10, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}, {"entity_id": "D", "ai_expectation_failure_score": 9, "score_band": "LOW", "relative_fragility_rank": 1, "driver_map": {"x": 1}}]),
    ])
    before = deepcopy(env)
    r1 = certify_regime_transition_detection(env)
    r2 = certify_regime_transition_detection(env)
    assert r1["result_checksum"] == r2["result_checksum"]
    assert env == before
    rows = r1["transition_records"]
    assert [r["subject_id"] for r in rows] == sorted(r["subject_id"] for r in rows)
    by = {r["subject_id"]: r for r in rows}
    assert by["A"]["transition_direction"] == "DETERIORATING"
    assert by["B"]["current_regime_state"] == "REGIME_RECOVERING"
    assert by["C"]["regime_transition"] == "NO_REGIME_CHANGE"
    assert by["D"]["regime_transition"] == "REGIME_TRANSITION_UNCLEAR"
    assert by["A"]["transition_strength"] in {"TRANSITION_STRONG", "TRANSITION_MODERATE", "TRANSITION_WEAK"}
    assert by["A"]["transition_confidence"] in {"TRANSITION_CONFIDENCE_HIGH", "TRANSITION_CONFIDENCE_MEDIUM", "TRANSITION_CONFIDENCE_LOW"}
    assert r1["temporal_lineage"]["t3_result_checksum"] == env["result_checksum"]
    assert all(v is False for v in r1["forbidden_capabilities"].values())
    assert "T4 Regime Transition Detection Report" in build_t4_regime_transition_report(r1)


def test_t4_insufficient_degraded_and_smoke_compatibility():
    insuff = _t3([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": 1, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 2, "score_band": "MODERATE", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
    ])
    assert certify_regime_transition_detection(insuff)["transition_records"][0]["transition_quality"] == "TRANSITION_INSUFFICIENT_HISTORY"

    deg = _t3([
        _snap("s1", "2026-01-01", "c1", [{"entity_id": "A", "ai_expectation_failure_score": "x"}]),
        _snap("s2", "2026-01-02", "c2", [{"entity_id": "A", "ai_expectation_failure_score": 1, "score_band": "LOW", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
        _snap("s3", "2026-01-03", "c3", [{"entity_id": "A", "ai_expectation_failure_score": 2, "score_band": "MODERATE", "relative_fragility_rank": 2, "driver_map": {"x": 1}}]),
    ])
    cert = certify_regime_transition_detection(deg)
    assert cert["t4_status"] == "REGIME_TRANSITIONS_DEGRADED"
    assert cert["transition_records"][0]["transition_quality"] == "TRANSITION_DEGRADED"
