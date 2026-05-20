from transmission_layers.intelligence.tier4.fragility_explanations import explain_fragility


def test_fragility_explanations_use_fixed_template():
    txt = explain_fragility({"system_fragility_score": 0.8, "threshold_breach_count": 2, "cascade_irreversibility_detected": True})
    assert txt.startswith("fragility status template:")
    assert "band=high" in txt
