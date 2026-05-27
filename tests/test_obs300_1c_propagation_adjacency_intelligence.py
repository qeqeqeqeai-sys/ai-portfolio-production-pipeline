from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import (
    build_obs300_1c_propagation_adjacency_intelligence,
)


def test_obs300_1c_deterministic_output_and_summary_contract():
    a = build_obs300_1c_propagation_adjacency_intelligence()
    b = build_obs300_1c_propagation_adjacency_intelligence()
    assert a == b
    summary = a["operator_summary"]
    assert summary["total_entities_inspected"] == 300
    assert "bridge_role_distribution" in summary
    assert "regime_transition_exposure_distribution" in summary
    assert "top_propagation_vectors" in summary
    assert "adjacency_richness_score" in summary
    assert "saturation_warnings" in summary
    assert "cross_sector_propagation_candidates" in summary


def test_obs300_1c_weight_bounds_and_deterministic_ordering():
    data = build_obs300_1c_propagation_adjacency_intelligence()
    links = data["weighted_adjacency"]
    assert links == sorted(links, key=lambda x: (x["source_ticker"], -x["adjacency_weight"], x["target_ticker"]))
    assert all(0.0 <= x["adjacency_weight"] <= 1.0 for x in links)


def test_obs300_1c_bridge_and_regime_exposure_presence_and_consistency():
    data = build_obs300_1c_propagation_adjacency_intelligence()
    entities = data["entities"]
    assert all(e["bridge_role"] for e in entities)
    assert all(len(e["regime_transition_exposures"]) >= 1 for e in entities)
    bridge_sum = sum(data["operator_summary"]["bridge_role_distribution"].values())
    assert bridge_sum == len(entities)


def test_obs300_1c_saturation_and_cross_sector_stability_and_boundary():
    data = build_obs300_1c_propagation_adjacency_intelligence()
    topo = data["topology_pressure_summaries"]
    assert 0.0 <= topo["thematic_saturation_density"] <= 1.0
    assert 0.0 <= topo["propagation_congestion_indicator"] <= 1.0
    candidates = data["cross_sector_transmission_candidates"]
    assert candidates == sorted(candidates, key=lambda x: (x["source_ticker"], -x["adjacency_weight"], x["target_ticker"]))

    gov = data["operator_summary"]["governance_certification"]
    assert gov["observational_only"] is True
    assert gov["no_recursive_replay_operationalization"] is True
    assert gov["no_autonomous_replay"] is True
    assert gov["no_topology_activation"] is True
    assert gov["no_self_modifying_pathways"] is True
    assert gov["no_prediction_or_trading_execution"] is True
    assert gov["no_sql_write_introduction"] is True


def test_obs300_1c_no_prediction_trading_sql_fields_and_no_autonomous_activation():
    data = build_obs300_1c_propagation_adjacency_intelligence()
    serialized = str(data).lower()
    forbidden = [
        "insert into",
        "update ",
        "delete from",
        "execute_trade",
        "prediction_score",
        "autonomous_replay_activation_enabled:true",
    ]
    assert all(token not in serialized for token in forbidden)
