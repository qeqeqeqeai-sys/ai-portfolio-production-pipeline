from transmission_layers.intelligence.tier5.federation_failure_containment import federation_failure_containment


def test_containment_scoring():
    out=federation_failure_containment([
        {"path_id":"1","contained":True,"source":"A","target":"B"},
        {"path_id":"2","contained":False,"source":"B","target":"C"},
    ],{"federation_violation_detection_score":0.9},{"federation_propagation_visibility_score":0.8})
    assert 0<=out["federation_failure_containment_score"]<=1
