from transmission_layers.intelligence.tier4.containment_integrity import compute_containment_integrity


def test_containment_integrity_diagnostics():
    out = compute_containment_integrity([{"corridor_id": "c", "containment": 0.2}])
    assert out["containment_weakening_detected"] is True
    assert 0.0 <= out["containment_integrity_score"] <= 1.0
