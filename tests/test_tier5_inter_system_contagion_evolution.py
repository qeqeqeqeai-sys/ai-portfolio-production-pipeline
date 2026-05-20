from transmission_layers.intelligence.tier5.inter_system_contagion_evolution import inter_system_contagion_evolution_score


def test_contagion_evolution_bounded():
    assert 0.0 <= inter_system_contagion_evolution_score([[], [("a", "b")]]) <= 1.0
