from transmission_layers.expectation_failure.obs300_2a_contradiction_fragility_intelligence import (
    score_obs300_2a_contradiction_fragility,
)


def _payload():
    return {
        "cluster_id": "AI_INFRA_CLUSTER",
        "domain": "ai_infrastructure",
        "thematic_saturation": 86,
        "propagation_congestion": 78,
        "regime_transition_overlap": 71,
        "contradiction_exposure_density": 82,
        "bridge_role_concentration": 76,
        "cross_sector_instability_exposure": 69,
        "contradiction_bridge_entities": ["NVDA", "SMCI"],
        "contradiction_diffusion_candidates": ["MSFT", "AMZN"],
    }


def test_obs300_2a_deterministic_and_bounded_outputs():
    first = score_obs300_2a_contradiction_fragility(_payload())
    second = score_obs300_2a_contradiction_fragility(_payload())
    assert first == second

    for key in (
        "contradiction_pressure_score",
        "narrative_fragility_score",
        "ecosystem_instability_score",
        "thematic_overextension_score",
        "contradiction_concentration_score",
        "propagation_instability_score",
        "saturation_fragility_interaction_score",
        "congestion_fragility_interaction_score",
    ):
        assert 0 <= first[key] <= 100


def test_obs300_2a_governance_boundaries_and_non_autonomous_flags():
    result = score_obs300_2a_contradiction_fragility(_payload())
    cert = result["governance_certification"]
    assert cert == {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    report = result["operational_report"]
    assert report["deterministic"] is True
    assert report["bounded"] is True
    assert report["autonomous_logic"] is False


def test_obs300_2a_contradiction_cluster_and_operator_summaries_present():
    result = score_obs300_2a_contradiction_fragility(_payload())

    cluster = result["contradiction_cluster_summary"]
    assert cluster["cluster_id"] == "AI_INFRA_CLUSTER"
    assert cluster["contradiction_bridge_entities"] == ["NVDA", "SMCI"]
    assert "diffusion_candidates" in cluster["contradiction_concentration_map"]

    operator = result["operator_intelligence_summary"]
    assert operator["highest_contradiction_pressure_domains"]
    assert operator["most_fragile_narrative_clusters"]
    assert operator["saturation_risk_warnings"]
    assert operator["topology_instability_summaries"]
