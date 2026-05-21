from transmission_layers.intelligence.tier5.federation_resilience_explanations import fixed_federation_resilience_explanations


def test_fixed_template_stability():
    payload={
        "federation_resilience_classification":"resilient",
        "federation_resilience_score":0.8,
        "federation_recovery_readiness_score":0.7,
        "federation_recoverability_score":0.75,
        "federation_dependency_resilience_score":0.6,
        "federation_failure_containment_score":0.65,
        "federation_recovery_path_score":0.7,
        "federation_irreversibility_risk_score":0.2,
        "federation_recovery_gap_score":0.3,
        "dominant_resilience_factor":"federation_recoverability_score",
    }
    assert fixed_federation_resilience_explanations(payload)==fixed_federation_resilience_explanations(payload)
