from transmission_layers.intelligence.tier4.cascade_explanations import explain_cascade


def test_explanation_template_stability():
    summary = {"cascade_id": "A", "structural_criticality_score": 0.5, "systemic_cascade_score": 0.5, "cascade_escalation_score": 0.4, "dominant_cascade_factor": "systemic_cascade", "cascade_classification": "contained", "cascade_checksum": "abc"}
    assert explain_cascade(summary) == explain_cascade(dict(summary))
