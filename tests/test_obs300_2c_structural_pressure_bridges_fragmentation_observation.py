from transmission_layers.expectation_failure.obs300_2c_structural_pressure_bridges_fragmentation_observation import (
    score_obs300_2c_structural_pressure_bridges,
)


def _payload():
    return {
        "bridge_connectivity_pressure": 78,
        "instability_transmission_intensity": 74,
        "contradiction_bridge_escalation": 69,
        "bridge_stress_concentration": 72,
        "bridge_pathway_reuse": 66,
        "adjacency_continuity": 63,
        "cohesion_weakening_signal": 64,
        "propagation_fragmentation": 67,
        "narrative_divergence": 61,
        "topology_decomposition": 58,
        "propagation_exhaustion": 56,
        "diffusion_decay": 54,
        "contradiction_dissipation": 52,
        "saturation_cooling": 49,
        "strongest_pressure_bridges": ["ai_infrastructure->utilities_stress", "liquidity_tightening->banks->consumer_fragility"],
        "highest_instability_transmission_pathways": ["capex_saturation->semis->margin_compression"],
        "highest_fragmentation_domains": ["regional_banks_credit", "semis_capacity_chain"],
    }


def test_obs300_2c_deterministic_outputs_and_required_surfaces():
    first = score_obs300_2c_structural_pressure_bridges(_payload())
    second = score_obs300_2c_structural_pressure_bridges(_payload())

    assert first == second
    assert first["module"] == "OBS300-2C"
    assert first["status"].startswith("deterministic_")

    required = {
        "pressure_bridge_score",
        "fragmentation_score",
        "ecosystem_cohesion_score",
        "propagation_decay_score",
        "strongest_pressure_bridges",
        "highest_fragmentation_domains",
        "propagation_exhaustion_summary",
        "decomposition_risk_summary",
        "operator_facing_summary",
        "structural_ecosystem_intelligence",
        "governance_certification",
    }
    assert required.issubset(first.keys())


def test_obs300_2c_bounded_ranges_fragmentation_and_decay_stability():
    result = score_obs300_2c_structural_pressure_bridges(_payload())

    for field in (
        "pressure_bridge_score",
        "bridge_propagation_continuity_score",
        "fragmentation_score",
        "ecosystem_cohesion_score",
        "propagation_decay_score",
    ):
        assert 0 <= result[field] <= 100

    assert "fragmentation_score=" in result["decomposition_risk_summary"]
    assert "propagation_decay_score=" in result["propagation_exhaustion_summary"]


def test_obs300_2c_governance_boundaries_and_no_autonomous_or_execution_paths():
    result = score_obs300_2c_structural_pressure_bridges(_payload())
    governance = result["governance_certification"]

    assert governance == {
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

    summary = result["operator_facing_summary"]
    assert summary["governance_certification"]["no_autonomous_replay"] is True
    assert summary["governance_certification"]["no_sql_write_introduction"] is True
