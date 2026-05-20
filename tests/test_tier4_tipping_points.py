from transmission_layers.intelligence.tier4.tipping_points import detect_tipping_points


def test_tipping_points_detection_deterministic():
    seq = [{"system_fragility_score": 0.1}, {"system_fragility_score": 0.4}, {"system_fragility_score": 0.45}]
    a = detect_tipping_points(seq, jump_threshold=0.2)
    b = detect_tipping_points(seq, jump_threshold=0.2)
    assert a == b
    assert a["tipping_point_count"] == 1
    assert a["first_tipping_step"] == 1
