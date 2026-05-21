from transmission_layers.intelligence.tier5.federation_recoverability import federation_recoverability_assessment


def test_recoverability_classification_and_bounds():
    out=federation_recoverability_assessment({"federation_recovery_readiness_score":0.8},{"federation_evolution_score":0.2},{"federation_structural_health_score":0.9})
    assert out["federation_resilience_classification"]=="recoverable"
    assert 0<=out["federation_recoverability_score"]<=1
