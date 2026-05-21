from transmission_layers.intelligence.tier5.federation_degradation import federation_degradation_score


def test_degradation_bounded():
    r={"observability_alignment_score":0.5,"governance_alignment_score":0.5,"replay_health_score":0.5,"continuity_health_score":0.5,"propagation_health_score":0.5}
    out=federation_degradation_score(r)
    assert out["health_degradation_score"]==0.5
