from transmission_layers.intelligence.tier4.contagion_explanations import explain_contagion


def test_fixed_template_explanation_stability():
    txt = explain_contagion({"contagion_id": "cg1", "contagion_classification": "contained", "dominant_contagion_factor": "stress_concentration_score", "stress_concentration_score": 0.2, "stress_amplification_score": 0.3, "contagion_checksum": "abc"})
    assert txt.startswith("contagion intelligence template:")
    assert "contagion_checksum=abc" in txt
