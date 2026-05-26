from transmission_layers.expectation_failure import replay_ecology as mod
from transmission_layers.expectation_failure.replay_ecology.lr6_exec2_first_dry_run_execution_review import (
    build_lr6_exec2_first_dry_run_execution_review,
)

SYNTHETIC_LABELS = {
    "synthetic_validation": True,
    "empirical_evidence": False,
    "replay_execution_performed": False,
    "improvement_claim_authorized": False,
}


def _synthetic_full_payload() -> dict:
    return {
        "synthetic_validation": True,
        "empirical_evidence": False,
        "metrics": {
            "weak_signal_attribution": {
                "weak_signal_attribution_count": 2,
                "weak_signal_candidate_count": 10,
                "weak_signal_attribution_ratio": 0.2,
                "weak_signal_entities_observed": ["A"],
                "weak_signal_entities_missing": ["B"],
            },
            "contradiction_persistence_migration": {
                "contradiction_cluster_count": 3,
                "persistent_contradiction_count": 1,
                "migrated_contradiction_count": 1,
                "cross_cluster_contradiction_count": 1,
                "contradiction_persistence_ratio": 0.33,
            },
            "propagation_diversity": {
                "propagation_bridge_count": 4,
                "distinct_propagation_role_count": 3,
                "non_obvious_bridge_count": 2,
                "cross_cluster_bridge_count": 1,
                "propagation_diversity_score": 0.8,
            },
            "topology_drift": {
                "topology_drift_indicator": True,
                "new_bridge_count": 1,
                "disappeared_bridge_count": 0,
                "changed_bridge_count": 1,
                "topology_drift_score": 0.5,
            },
            "replay_saturation_monoculture": {
                "saturation_score": 0.4,
                "concentration_score": 0.6,
                "dominant_theme_share": 0.7,
                "repeated_entity_share": 0.5,
                "diversity_gain_indicator": True,
            },
            "megacap_semantic_gravity": {
                "megacap_attribution_count": 3,
                "total_attribution_count": 8,
                "megacap_concentration_ratio": 0.375,
                "non_megacap_bridge_count": 2,
                "megacap_gravity_status": "balanced",
            },
            "replay_richness": {
                "replay_entity_count": 14,
                "distinct_role_count": 5,
                "distinct_cluster_count": 4,
                "novel_bridge_count": 3,
                "richness_score": 0.9,
            },
        },
    }


def _synthetic_partial_payload() -> dict:
    return {
        "synthetic_validation": True,
        "empirical_evidence": False,
        "metrics": {
            "weak_signal_attribution": {"weak_signal_attribution_count": 1},
            "contradiction_persistence_migration": {"contradiction_cluster_count": 1},
            "propagation_diversity": {"propagation_bridge_count": 1},
            "topology_drift": {"topology_drift_indicator": True},
            "replay_saturation_monoculture": {"saturation_score": 0.2},
            "megacap_semantic_gravity": {"megacap_attribution_count": 1},
            "replay_richness": {"replay_entity_count": 2},
        },
    }


def _synthetic_invalid_payload() -> dict:
    return {
        "synthetic_validation": True,
        "empirical_evidence": False,
        "metrics": {
            "weak_signal_attribution": {
                "weak_signal_attribution_count": -1,
                "weak_signal_candidate_count": -10,
                "weak_signal_attribution_ratio": 1.5,
                "weak_signal_entities_observed": "not-a-list",
                "weak_signal_entities_missing": [],
            },
            "contradiction_persistence_migration": {
                "contradiction_cluster_count": -3,
                "persistent_contradiction_count": -1,
                "migrated_contradiction_count": -1,
                "cross_cluster_contradiction_count": -1,
                "contradiction_persistence_ratio": -0.1,
            },
            "propagation_diversity": {
                "propagation_bridge_count": -4,
                "distinct_propagation_role_count": -3,
                "non_obvious_bridge_count": -2,
                "cross_cluster_bridge_count": -1,
                "propagation_diversity_score": 1.8,
            },
            "topology_drift": {
                "topology_drift_indicator": "not-bool",
                "new_bridge_count": -1,
                "disappeared_bridge_count": -1,
                "changed_bridge_count": -1,
                "topology_drift_score": -0.5,
            },
            "replay_saturation_monoculture": {
                "saturation_score": -0.4,
                "concentration_score": 1.6,
                "dominant_theme_share": 2.7,
                "repeated_entity_share": -0.5,
                "diversity_gain_indicator": "not-bool",
            },
            "megacap_semantic_gravity": {
                "megacap_attribution_count": -3,
                "total_attribution_count": -8,
                "megacap_concentration_ratio": 1.375,
                "non_megacap_bridge_count": -2,
                "megacap_gravity_status": "",
            },
            "replay_richness": {
                "replay_entity_count": -14,
                "distinct_role_count": -5,
                "distinct_cluster_count": -4,
                "novel_bridge_count": -3,
                "richness_score": 1.9,
            },
        },
    }


def _emit(payload: dict, replay_phase: str = "ENRICHED", wave_id: str = "W_SYN", scope_id: str = "S_SYN"):
    return mod.emit_lr6_replay_metric_evidence(
        replay_phase=replay_phase,
        wave_id=wave_id,
        candidate_scope_id=scope_id,
        candidate_count=16,
        timestamp_or_snapshot_label="T_SYN",
        replay_observation_payload=payload,
    )


def test_synthetic_full_payload_emits_seven_measured_and_comparison_ready_records():
    payload = _synthetic_full_payload()
    records = _emit(payload)

    assert all(payload[k] == v for k, v in SYNTHETIC_LABELS.items() if k in payload)
    assert len(records) == 7
    assert all(r["evidence_status"] == "MEASURED" for r in records)
    assert all(r["comparison_ready"] is True for r in records)
    assert all(r["scaffold_only"] is False for r in records)

    required_by_dimension = mod.build_lr6_evid6_required_field_contract()
    by_dim = {r["metric_dimension"]: r for r in records}
    for dim, required_fields in required_by_dimension.items():
        measured_fields = by_dim[dim]["measured_fields"]
        assert all(field in measured_fields for field in required_fields)

    compat = mod.build_lr6_evid6_evid3_compatibility_summary(records)
    assert compat["record_count"] == 7
    assert compat["all_required_keys_present"] is True

    one = _emit(payload)
    two = _emit(payload)
    assert one == two


def test_synthetic_partial_payload_emits_partial_non_comparison_ready_records():
    payload = _synthetic_partial_payload()
    records = _emit(payload)
    assert len(records) == 7
    assert all(r["evidence_status"] == "PARTIAL" for r in records)
    assert all(r["comparison_ready"] is False for r in records)
    assert all(r["scaffold_only"] is False for r in records)


def test_synthetic_invalid_payload_is_conservative_and_no_false_measured():
    payload = _synthetic_invalid_payload()
    records = _emit(payload, replay_phase="INVALID_PHASE", wave_id="", scope_id="")

    assert len(records) == 7
    assert all(r["comparison_ready"] is False for r in records)
    assert all(r["evidence_status"] == "NOT_COMPARABLE" for r in records)
    assert all(r["evidence_status"] != "MEASURED" for r in records)

    weak_signal = [r for r in records if r["metric_dimension"] == "weak_signal_attribution"][0]
    assert "weak_signal_entities_missing" in weak_signal["measured_fields"]
    assert "weak_signal_attribution_count" not in weak_signal["measured_fields"]


def test_evid7_dry_run_scaffold_only_behavior_remains_unchanged():
    out = build_lr6_exec2_first_dry_run_execution_review()
    assert out["evidence_records_are_empirical"] is False
    assert out["evidence_emission_mode"] == "DRY_RUN_IN_MEMORY"
    assert len(out["evidence_records"]) == 7
    assert {r["evidence_status"] for r in out["evidence_records"]} == {"SCAFFOLD_ONLY"}
    assert out["evidence_emission_summary"]["measured_record_count"] == 0
    assert out["evidence_emission_summary"]["partial_record_count"] == 0


def test_no_replay_execution_or_sql_persistence_prediction_trading_paths_introduced():
    boundary = mod.certify_lr6_evid6_hook_boundary()
    assert SYNTHETIC_LABELS["replay_execution_performed"] is False
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
