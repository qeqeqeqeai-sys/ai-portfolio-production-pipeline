from transmission_layers.expectation_failure.obs300_3a_ecosystem_intelligence_visualization_operator_topology import (
    _MAX_LIST_ITEMS,
    _MAX_SUMMARY_CHARS,
    build_obs300_3a_ecosystem_visualization_payloads,
)


def _payload():
    return {
        "ecosystem_topology_signal": 74,
        "propagation_adjacency_clarity": 72,
        "operator_surface_coverage": 69,
        "pressure_bridge_strength": 77,
        "instability_transmission_intensity": 73,
        "bridge_concentration": 68,
        "fragmentation_signal": 66,
        "topology_decomposition": 62,
        "cohesion_weakening": 64,
        "contradiction_pressure": 71,
        "contradiction_recurrence": 67,
        "temporal_persistence": 63,
        "propagation_continuity": 65,
        "propagation_decay": 56,
        "strongest_pressure_bridges": [f"bridge_{i}" for i in range(20)],
        "strongest_instability_pathways": [f"pathway_{i}" for i in range(12)],
        "contradiction_pressure_zones": [f"zone_{i}" for i in range(15)],
    }


def test_obs300_3a_deterministic_payload_generation_and_required_surfaces():
    first = build_obs300_3a_ecosystem_visualization_payloads(_payload())
    second = build_obs300_3a_ecosystem_visualization_payloads(_payload())

    assert first == second
    assert first["module"] == "OBS300-3A"

    required = {
        "visualization_payloads",
        "pressure_bridge_visualization",
        "fragmentation_cohesion_visualization",
        "temporal_persistence_visualization",
        "operator_intelligence_panels",
        "topology_dashboard_architecture_summary",
        "visualization_payload_summary",
        "governance_certification",
    }
    assert required.issubset(first.keys())


def test_obs300_3a_bounded_payload_sizes_and_dashboard_friendly_contracts():
    result = build_obs300_3a_ecosystem_visualization_payloads(_payload())

    assert len(result["pressure_bridge_visualization"]["strongest_pressure_bridge_payloads"]) == _MAX_LIST_ITEMS
    assert len(result["operator_intelligence_panels"]["highest_contradiction_pressure_zones"]) == _MAX_LIST_ITEMS
    assert len(result["operator_intelligence_panels"]["strongest_instability_pathways"]) == _MAX_LIST_ITEMS

    for key, value in result["temporal_persistence_visualization"].items():
        if isinstance(value, str):
            assert len(value) <= _MAX_SUMMARY_CHARS

    assert result["topology_dashboard_architecture_summary"] == {
        "payload_only_contracts": True,
        "frontend_framework_required": False,
        "graph_engine_required": False,
        "rendering_engine_implemented": False,
        "orchestration_complexity": "lightweight",
        "power_bi_dashboard_friendly": True,
    }


def test_obs300_3a_governance_boundaries_and_no_autonomous_or_execution_paths():
    result = build_obs300_3a_ecosystem_visualization_payloads(_payload())

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

    assert result["operational_report"]["autonomous_logic"] is False
    assert result["operational_report"]["sql_writes_enabled"] is False
    assert result["operational_report"]["prediction_or_trading_execution"] is False
