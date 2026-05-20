from transmission_layers.intelligence.tier5.federation_violation_detection import federation_violation_score

def test_violation_bounded():
    r = federation_violation_score(constraint_score=1, guardrail_score=1, boundary_enforcement_score=0, continuity_score=0)
    assert r["federation_violation_score"] == 1.0
