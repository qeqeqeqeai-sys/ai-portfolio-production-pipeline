from transmission_layers.intelligence.tier4.stabilization_capacity import compute_stabilization_capacity
from transmission_layers.intelligence.tier4.pressure_resistance import compute_pressure_resistance
from transmission_layers.intelligence.tier4.intervention_saturation import detect_intervention_saturation


def test_saturation_and_recovery_fatigue_detection():
    pressure = compute_pressure_resistance(compute_stabilization_capacity([{"node_id": "n", "overload": 0.95, "resilience": 0.1, "intervention_effectiveness": 0.1}]))
    out = detect_intervention_saturation(pressure, threshold=0.5)
    row = out["saturation_ranking"][0]
    assert row["saturation_detected"] is True
    assert row["recovery_fatigue_detected"] is True
