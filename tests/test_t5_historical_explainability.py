from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    build_historical_explanation_records,
    certify_historical_explainability,
    validate_historical_explainability_inputs,
)


def _t4_envelope():
    records = [
        {
            "subject_id": "A",
            "subject_type": "ENTITY",
            "prior_regime_state": "REGIME_STRETCHED",
            "current_regime_state": "REGIME_FRAGILE",
            "regime_transition": "STRETCHED_TO_FRAGILE",
            "transition_direction": "DETERIORATING",
            "transition_strength": "TRANSITION_STRONG",
            "transition_confidence": "TRANSITION_CONFIDENCE_HIGH",
            "supporting_curve_label": "FRAGILITY_RISING",
            "supporting_metrics": {"cumulative_score_delta": 3.2, "directional_consistency": 0.8, "persistence_count": 2},
            "observation_count": 5,
            "pair_count": 4,
            "first_observed_date": "2024-01-01",
            "last_observed_date": "2024-01-05",
            "source_pair_checksums": ["p1", "p2"],
            "source_curve_checksum": "c1",
            "transition_checksum": "t1",
        },
        {
            "subject_id": "B",
            "subject_type": "ENTITY",
            "prior_regime_state": "REGIME_STRESS",
            "current_regime_state": "REGIME_RECOVERING",
            "regime_transition": "STRESS_TO_RECOVERING",
            "transition_direction": "IMPROVING",
            "transition_strength": "TRANSITION_MODERATE",
            "transition_confidence": "TRANSITION_CONFIDENCE_MEDIUM",
            "supporting_curve_label": "FRAGILITY_FALLING",
            "supporting_metrics": {"cumulative_score_delta": -4.1, "directional_consistency": 0.7, "persistence_count": 2},
            "observation_count": 3,
            "pair_count": 2,
            "first_observed_date": "2024-01-02",
            "last_observed_date": "2024-01-06",
            "source_pair_checksums": ["p3", "p4"],
            "source_curve_checksum": "c2",
            "transition_checksum": "t2",
        },
        {
            "subject_id": "C",
            "subject_type": "BENCHMARK",
            "prior_regime_state": "REGIME_STABLE",
            "current_regime_state": "REGIME_STABLE",
            "regime_transition": "NO_REGIME_CHANGE",
            "transition_direction": "UNCHANGED",
            "transition_strength": "TRANSITION_NONE",
            "transition_confidence": "TRANSITION_CONFIDENCE_HIGH",
            "supporting_curve_label": "FRAGILITY_STABLE",
            "supporting_metrics": {"cumulative_score_delta": 0.1, "directional_consistency": 1.0, "persistence_count": 3},
            "observation_count": 2,
            "pair_count": 2,
            "first_observed_date": "2024-01-03",
            "last_observed_date": "2024-01-04",
            "source_pair_checksums": ["p5"],
            "source_curve_checksum": "c3",
            "transition_checksum": "t3",
        },
        {
            "subject_id": "D",
            "subject_type": "BENCHMARK",
            "prior_regime_state": "REGIME_UNCLEAR",
            "current_regime_state": "REGIME_UNCLEAR",
            "regime_transition": "REGIME_TRANSITION_UNCLEAR",
            "transition_direction": "MIXED",
            "transition_strength": "TRANSITION_WEAK",
            "transition_confidence": "TRANSITION_CONFIDENCE_LOW",
            "supporting_curve_label": "FRAGILITY_VOLATILE",
            "supporting_metrics": {"cumulative_score_delta": 0.2, "directional_consistency": 0.4, "persistence_count": 1},
            "observation_count": 2,
            "pair_count": 2,
            "first_observed_date": "2024-01-01",
            "last_observed_date": "2024-01-02",
            "source_pair_checksums": ["p6"],
            "source_curve_checksum": "c4",
            "transition_checksum": "t4",
        },
        {
            "subject_id": "E",
            "subject_type": "ENTITY",
            "prior_regime_state": "REGIME_INSUFFICIENT_HISTORY",
            "current_regime_state": "REGIME_INSUFFICIENT_HISTORY",
            "regime_transition": "REGIME_TRANSITION_INSUFFICIENT_HISTORY",
            "transition_direction": "UNKNOWN",
            "transition_strength": "TRANSITION_UNKNOWN",
            "transition_confidence": "TRANSITION_CONFIDENCE_INSUFFICIENT",
            "supporting_curve_label": "FRAGILITY_INSUFFICIENT_HISTORY",
            "supporting_metrics": {"cumulative_score_delta": 0, "directional_consistency": 0, "persistence_count": 0},
            "observation_count": 1,
            "pair_count": 1,
            "first_observed_date": "2024-01-04",
            "last_observed_date": "2024-01-04",
            "source_pair_checksums": [],
            "source_curve_checksum": "c5",
            "transition_checksum": "t5",
        },
    ]
    return {
        "t4_status": "REGIME_TRANSITIONS_CERTIFIED",
        "transition_records": records,
        "regime_transition_summary": {"transition_count": len(records)},
        "checksum_chain": {"transition_chain_checksum": "chain"},
        "temporal_lineage": {"t3": "x"},
        "result_checksum": "t4checksum",
    }


def test_exports_and_validation():
    env = _t4_envelope()
    assert validate_historical_explainability_inputs(env)["valid"] is True


def test_certified_and_blocked_paths():
    certified_env = _t4_envelope()
    certified_env["transition_records"] = certified_env["transition_records"][:3]
    cert = certify_historical_explainability(certified_env)
    assert cert["t5_status"] == "HISTORICAL_EXPLAINABILITY_CERTIFIED"
    assert certify_historical_explainability(None)["t5_status"] == "HISTORICAL_EXPLAINABILITY_BLOCKED"
    empty = _t4_envelope()
    empty["transition_records"] = []
    assert certify_historical_explainability(empty)["t5_status"] == "HISTORICAL_EXPLAINABILITY_BLOCKED"


def test_template_mapping_and_ordering_and_determinism():
    env = _t4_envelope()
    records = build_historical_explanation_records(env)
    template_by_subject = {r["subject_id"]: r["bounded_explanation_template_id"] for r in records}
    assert template_by_subject["A"] == "EXPLANATION_RISING_FRAGILITY"
    assert template_by_subject["B"] == "EXPLANATION_RECOVERY"
    assert template_by_subject["C"] == "EXPLANATION_STABLE_CONDITION"
    assert template_by_subject["D"] == "EXPLANATION_VOLATILE_CONDITION"
    assert template_by_subject["E"] == "EXPLANATION_INSUFFICIENT_HISTORY"
    assert records == sorted(records, key=lambda r: (r["subject_type"], r["subject_id"], r["replay_window_summary"]["first_observed_date"], r["explanation_checksum"]))
    a = certify_historical_explainability(env)
    b = certify_historical_explainability(env)
    assert a["result_checksum"] == b["result_checksum"]


def test_degraded_mapping_mutation_policy_and_language_bounds():
    env = _t4_envelope()
    env["t4_status"] = "REGIME_TRANSITIONS_DEGRADED"
    before = deepcopy(env)
    records = build_historical_explanation_records(env)
    assert any(r["bounded_explanation_template_id"] == "EXPLANATION_DEGRADED_INPUT" for r in records)
    assert env == before
    allowed_verbs = {"observed", "classified", "detected", "associated with", "reflected", "persisted"}
    forbidden = ["predicted", "guaranteed", "will happen", "recommend"]
    for r in records:
        txt = r["bounded_explanation_text"].lower()
        assert any(v in txt for v in allowed_verbs)
        assert all(f not in txt for f in forbidden)
        assert r["structural_change_summary"] in {
            "persistent positive fragility movement",
            "mixed directional structural movement",
            "stable structural movement",
            "recovery-aligned fragility reduction",
            "volatile structural instability",
        }
        assert r["replay_window_summary"]["replay_window_classification"] in {
            "SHORT_REPLAY_WINDOW",
            "MEDIUM_REPLAY_WINDOW",
            "LONG_REPLAY_WINDOW",
            "EXTENDED_REPLAY_WINDOW",
            "UNKNOWN_REPLAY_WINDOW",
        }


def test_lineage_forbidden_capabilities_and_smoke_compatibility():
    cert = certify_historical_explainability(_t4_envelope())
    assert cert["checksum_chain"]["input_transition_chain_checksum"] == "chain"
    assert cert["temporal_lineage"]["t4_result_checksum"] == "t4checksum"
    assert cert["forbidden_capabilities"]["prediction"] is False
    assert cert["forbidden_capabilities"]["recommendation_generation"] is False
    assert cert["invariant_flags"]["no_open_ended_generation"] is True
