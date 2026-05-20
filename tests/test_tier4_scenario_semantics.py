from transmission_layers.intelligence.tier4.scenario_semantics import normalize_structural_scenario, compute_scenario_checksum


def test_scenario_normalization_stable_and_bounded():
    s = normalize_structural_scenario({"scenario_id": "x", "scenario_type": "node_stressed", "target_nodes": ["b", "a", "a"], "perturbation_strength": 9})
    assert s["target_nodes"] == ["a", "b"]
    assert s["perturbation_strength"] == 1.0


def test_scenario_checksum_stable():
    a = normalize_structural_scenario({"scenario_id": "s1", "target_nodes": ["a", "b"]})
    b = normalize_structural_scenario({"scenario_id": "s1", "target_nodes": ["b", "a"]})
    assert compute_scenario_checksum(a) == compute_scenario_checksum(b)


def test_scenario_checksum_metadata_rounding_and_sorting_stable():
    a = normalize_structural_scenario({"scenario_id": "s1", "metadata": {"z": ["b", "a"], "w": 0.12345678}})
    b = normalize_structural_scenario({"scenario_id": "s1", "metadata": {"w": 0.123456781, "z": ["a", "b"]}})
    assert compute_scenario_checksum(a) == compute_scenario_checksum(b)
