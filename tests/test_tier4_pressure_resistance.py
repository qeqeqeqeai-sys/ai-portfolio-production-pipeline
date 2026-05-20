from transmission_layers.intelligence.tier4.stabilization_capacity import compute_stabilization_capacity
from transmission_layers.intelligence.tier4.pressure_resistance import compute_pressure_resistance


def test_pressure_resistance_bounded_and_stable():
    capacity = compute_stabilization_capacity([{"node_id": "x", "overload": 0.4, "resilience": 0.5}, {"node_id": "y", "overload": 0.7, "resilience": 0.2}])
    one = compute_pressure_resistance(capacity)
    two = compute_pressure_resistance(capacity)
    assert 0.0 <= one["pressure_resistance_score"] <= 1.0
    assert one == two
