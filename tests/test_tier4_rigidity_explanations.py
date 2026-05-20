from transmission_layers.intelligence.tier4.rigidity_explanations import explain_structural_rigidity


def test_rigidity_explanation_is_stable():
    summary = {
        "rigidity_classification": "rigid",
        "dominant_rigidity_factor": "adaptation_constraint_score",
        "structural_rigidity_score": 0.8,
        "adaptation_constraint_score": 0.9,
        "resilience_saturation_score": 0.7,
    }
    a = explain_structural_rigidity(summary)
    b = explain_structural_rigidity(dict(summary))
    assert a == b
    assert "deterministic rigidity diagnostics" in a
