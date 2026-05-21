from transmission_layers.intelligence.tier5.federation_health_classification import federation_health_classification


def test_classification_paths():
    r={"diagnostic_readiness_score":0.9,"observability_alignment_score":0.9,"governance_alignment_score":0.9,"replay_health_score":0.9,"continuity_health_score":0.9,"propagation_health_score":0.9}
    assert federation_health_classification(0.9,0.1,r)=="healthy"
    r["diagnostic_readiness_score"]=0.2
    assert federation_health_classification(0.5,0.4,r)=="diagnostically_limited"
