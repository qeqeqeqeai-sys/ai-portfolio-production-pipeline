from transmission_layers.intelligence.tier4.fragility_explanations import explain_fragility


def test_fragility_explanations_use_fixed_template():
    txt = explain_fragility({"fragility_id": "x", "fragility_score": 0.8, "bounded_fragility_score": 0.8, "dominant_fragility_factor": "overload", "fragility_classification": "critical", "structural_survivability_score": 0.2, "threshold_proximity_score": 1.0, "fragility_checksum": "abc"})
    assert txt.startswith("fragility status template:")
    assert "fragility_id=x" in txt
    assert "fragility_checksum=abc" in txt
