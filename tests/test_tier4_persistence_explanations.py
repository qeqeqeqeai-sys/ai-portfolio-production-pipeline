from transmission_layers.intelligence.tier4.persistence_explanations import explain_persistence_durability


def test_persistence_explanation_fixed_template():
    txt = explain_persistence_durability({"durability_id": "d1", "durability_score": 0.5, "persistence_checksum": "abc"})
    assert txt.startswith("persistence durability template:")
    assert "durability_id=d1" in txt
    assert "persistence_checksum=abc" in txt
