from transmission_layers.intelligence.tier5.federation_health_alignment import federation_health_alignment


def test_alignment_bounded():
    r={"observability_alignment_score":1.0,"governance_alignment_score":0.0,"replay_health_score":1.0,"continuity_health_score":0.0,"propagation_health_score":1.0}
    out=federation_health_alignment(r)
    assert out["federation_health_alignment_score"]==0.0
