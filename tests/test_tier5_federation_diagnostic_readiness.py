from transmission_layers.intelligence.tier5.federation_diagnostic_readiness import federation_diagnostic_readiness


def test_scores_bounded_and_deterministic():
    g={"federation_violation_score":0.2,"federation_continuity_constraint_score":0.8,"governance_containment_effectiveness_score":0.9}
    o={"federation_observability_score":0.7,"federation_continuity_observability_score":0.6,"federation_propagation_visibility_score":0.5}
    p={"federation_replay_consistency_score":0.8}
    a=federation_diagnostic_readiness(g,o,p)
    b=federation_diagnostic_readiness(g,o,p)
    assert a==b
    for k,v in a.items():
        assert 0<=v<=1
