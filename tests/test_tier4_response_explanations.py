from transmission_layers.intelligence.tier4.response_explanations import explain_response_policy


def test_explanation_stability():
    a = explain_response_policy("reinforce_resilience", {"b": 0.2, "a": 0.1})
    b = explain_response_policy("reinforce_resilience", {"a": 0.1, "b": 0.2})
    assert a == b
    assert len(a) <= 280
