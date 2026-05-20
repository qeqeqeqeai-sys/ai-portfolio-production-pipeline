from transmission_layers.intelligence.tier4.transition_explanations import explain_regime_transition


def test_fixed_template_explanation_stability():
    txt = explain_regime_transition({"transition_id": "t1", "transition_classification": "transition_watch", "dominant_transition_factor": "structural_entropy", "transition_vulnerability_score": 0.5, "transition_checksum": "abc"})
    assert txt.startswith("transition intelligence template:")
    assert "transition_checksum=abc" in txt
