from transmission_layers.expectation_failure.obs300_2b_temporal_persistence_intelligence import (
    score_obs300_2b_temporal_persistence,
)


def _payload():
    return {
        "temporal_window_count": 8,
        "propagation_continuity": 68,
        "propagation_pathway_reuse": 64,
        "contradiction_pressure_score": 71,
        "contradiction_carryover_score": 66,
        "narrative_fragility_score": 69,
        "fragility_carryover_score": 63,
        "propagation_congestion": 62,
        "congestion_carryover_score": 58,
        "propagation_acceleration_delta": 14,
        "contradiction_escalation_delta": 11,
        "narrative_cooling_signal": 46,
        "entropy_recovery_signal": 52,
        "contradiction_recurrence_density": 67,
        "contradiction_domains": ["ai_compute_vs_grid_stress", "soft_landing_vs_margin_pressure"],
        "fragility_clusters": ["semis_infrastructure", "consumer_credit"],
        "propagation_continuity_pathways": ["ai->utilities", "rates->duration"],
    }


def test_obs300_2b_deterministic_outputs_and_required_surfaces():
    first = score_obs300_2b_temporal_persistence(_payload())
    second = score_obs300_2b_temporal_persistence(_payload())

    assert first == second
    assert first["module"] == "OBS300-2B"
    assert first["status"].startswith("deterministic_")

    required = {
        "temporal_window_count",
        "propagation_persistence_score",
        "contradiction_persistence_score",
        "fragility_persistence_score",
        "instability_persistence_score",
        "contradiction_recurrence_score",
        "operator_facing_summary",
        "temporal_ecosystem_intelligence",
        "contradiction_persistence_clusters",
        "governance_certification",
    }
    assert required.issubset(first.keys())


def test_obs300_2b_bounded_ranges_and_classification_stability():
    result = score_obs300_2b_temporal_persistence(_payload())

    score_fields = [
        "propagation_persistence_score",
        "contradiction_persistence_score",
        "fragility_persistence_score",
        "congestion_persistence_score",
        "instability_persistence_score",
        "contradiction_recurrence_score",
        "propagation_acceleration_score",
        "contradiction_escalation_score",
        "instability_escalation_score",
        "narrative_cooling_score",
        "stabilization_observation_score",
        "entropy_recovery_score",
    ]
    for field in score_fields:
        assert 0 <= result[field] <= 100

    for _, label in result["persistence_classifications"].items():
        assert label in {"transient", "recurring", "persistent", "entrenched"}


def test_obs300_2b_escalation_stabilization_recurrence_and_governance_boundaries():
    result = score_obs300_2b_temporal_persistence(_payload())
    summary = result["operator_facing_summary"]

    assert "instability_escalation_score=" in summary["escalation_pressure_summary"]
    assert "stabilization_observation_score=" in summary["stabilization_recovery_summary"]
    assert isinstance(result["contradiction_persistence_clusters"]["repeated_instability_pattern_observation"], str)

    governance = result["governance_certification"]
    assert governance["observational_only"] is True
    assert governance["no_recursive_replay_operationalization"] is True
    assert governance["no_autonomous_replay"] is True
    assert governance["no_topology_activation"] is True
    assert governance["no_self_modifying_pathways"] is True
    assert governance["no_prediction_or_trading_execution"] is True
    assert governance["no_sql_write_introduction"] is True

    assert result["operational_report"]["autonomous_logic"] is False
