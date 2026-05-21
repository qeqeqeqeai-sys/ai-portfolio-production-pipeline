from transmission_layers.intelligence.tier5.federation_recovery import federation_recovery_readiness


def test_recovery_bounded_and_checksum_stable():
    governance={"federation_governance_score":0.7,"continuity_constraints_score":0.6,"policy_boundaries_score":0.5}
    persistence={"federation_persistence_score":0.8,"federation_recovery_history_score":0.7,"federation_replay_history_score":0.9}
    observability={"federation_observability_score":0.75,"federation_continuity_observability_score":0.7,"federation_replay_observability_score":0.65}
    a=federation_recovery_readiness(governance,persistence,observability)
    b=federation_recovery_readiness(governance,persistence,observability)
    assert a==b
    for k,v in a.items():
        if k.endswith("_score"):
            assert 0<=v<=1
