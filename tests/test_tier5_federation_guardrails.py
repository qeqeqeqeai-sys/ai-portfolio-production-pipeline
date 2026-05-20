from transmission_layers.intelligence.tier5.federation_guardrails import federation_guardrail_diagnostics

def test_disconnected_guardrails():
    r = federation_guardrail_diagnostics([])
    assert r["federation_guardrail_score"] == 0.0
    assert r["governance_containment_effectiveness_score"] == 1.0
