from transmission_layers.intelligence.tier4.resistance_explanations import explain_resistance_diagnostics


def test_fixed_template_stability():
    s = {"capacity_id": "c", "stabilization_capacity_score": 0.5, "pressure_resistance_score": 0.6, "absorption_margin": 0.4}
    one = explain_resistance_diagnostics(s)
    two = explain_resistance_diagnostics(s)
    assert one == two
    assert "resistance diagnostics template" in one
