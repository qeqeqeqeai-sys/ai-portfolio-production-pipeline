from transmission_layers.intelligence.tier4.stabilization_capacity import compute_stabilization_capacity
from transmission_layers.intelligence.tier4.pressure_resistance import compute_pressure_resistance
from transmission_layers.intelligence.tier4.stabilization_exhaustion import detect_stabilization_exhaustion


def test_exhaustion_detection():
    pressure = compute_pressure_resistance(compute_stabilization_capacity([{"node_id": "n", "overload": 0.95, "resilience": 0.1}]))
    out = detect_stabilization_exhaustion(pressure, threshold=0.5)
    assert out["exhaustion_ranking"][0]["exhaustion_detected"] is True
