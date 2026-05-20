from transmission_layers.intelligence.tier4.recovery_explanations import explain_structural_recovery


def test_fixed_template_explanation_stability():
    summary = {"recovery_classification": "stabilizing", "dominant_recovery_factor": "reintegration_stability_score", "structural_recovery_score": 0.7, "reintegration_stability_score": 0.8, "recovery_relapse_score": 0.2}
    e1 = explain_structural_recovery(summary)
    e2 = explain_structural_recovery(summary)
    assert e1 == e2
    assert "classification=stabilizing" in e1
