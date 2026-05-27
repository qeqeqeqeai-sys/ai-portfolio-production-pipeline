from transmission_layers.expectation_failure.obs300_3b_ecosystem_rotation_recovery_absorption_intelligence import (
    _MAX_LIST_ITEMS,
    _MAX_SUMMARY_CHARS,
    build_obs300_3b_ecosystem_rotation_recovery_absorption_intelligence,
)


def _payload():
    return {
        "ai_leadership_decay": 68,
        "defensive_stabilization_emergence": 72,
        "propagation_migration_intensity": 64,
        "liquidity_sensitive_fragmentation_rotation": 61,
        "cyclical_decomposition_shift": 58,
        "topology_leadership_decay": 66,
        "propagation_continuity_loss": 62,
        "duration_stabilization": 74,
        "energy_normalization": 69,
        "liquidity_recovery": 71,
        "stabilization_pathway_strength": 73,
        "normalization_transmission_clarity": 67,
        "recovery_continuity": 70,
        "decompression_disruption": 35,
        "defensive_absorption": 75,
        "quality_balance_sheet_stabilization": 78,
        "utilities_normalization": 68,
        "strongest_recovery_bridges": [f"bridge_{i}" for i in range(20)],
        "resilience_clusters": [f"cluster_{i}" for i in range(16)],
        "stabilization_pathways": [f"pathway_{i}" for i in range(20)],
    }


def test_obs300_3b_deterministic_outputs_and_required_surfaces():
    first = build_obs300_3b_ecosystem_rotation_recovery_absorption_intelligence(_payload())
    second = build_obs300_3b_ecosystem_rotation_recovery_absorption_intelligence(_payload())

    assert first == second
    assert first["module"] == "OBS300-3B"

    required = {
        "ecosystem_rotation_observation",
        "recovery_bridge_intelligence",
        "pressure_absorption_observation",
        "ecosystem_resilience_intelligence",
        "operator_facing_visualization_payloads",
        "recovery_bridge_architecture_summary",
        "governance_certification",
    }
    assert required.issubset(first.keys())


def test_obs300_3b_bounded_payload_sizes_and_scoring_stability():
    result = build_obs300_3b_ecosystem_rotation_recovery_absorption_intelligence(_payload())

    rot = result["ecosystem_rotation_observation"]
    rec = result["recovery_bridge_intelligence"]
    absr = result["pressure_absorption_observation"]

    for field in ["leadership_rotation_score", "thematic_rotation_score", "topology_leadership_decay_score"]:
        assert 0 <= rot[field] <= 100
    for field in ["recovery_bridge_score", "stabilization_propagation_score", "recovery_continuity_score"]:
        assert 0 <= rec[field] <= 100
    assert 0 <= absr["pressure_absorber_score"] <= 100

    assert len(result["ecosystem_resilience_intelligence"]["strongest_recovery_bridges"]) == _MAX_LIST_ITEMS
    assert len(result["ecosystem_resilience_intelligence"]["highest_resilience_clusters"]) == _MAX_LIST_ITEMS
    assert len(result["recovery_bridge_intelligence"]["normalization_transmission_pathways"]) == _MAX_LIST_ITEMS

    for section in [
        result["ecosystem_rotation_observation"],
        result["recovery_bridge_intelligence"],
        result["pressure_absorption_observation"],
        result["ecosystem_resilience_intelligence"],
    ]:
        for value in section.values():
            if isinstance(value, str):
                assert len(value) <= _MAX_SUMMARY_CHARS


def test_obs300_3b_governance_boundaries_and_no_autonomous_execution_paths():
    result = build_obs300_3b_ecosystem_rotation_recovery_absorption_intelligence(_payload())

    assert result["governance_certification"] == {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    assert result["operational_report"]["deterministic"] is True
    assert result["operational_report"]["bounded"] is True
    assert result["operational_report"]["autonomous_logic"] is False
    assert result["operational_report"]["sql_writes_enabled"] is False
    assert result["operational_report"]["prediction_or_trading_execution"] is False
