from copy import deepcopy
from transmission_layers.intelligence.tier4.structural_simulation import load_simulation_inputs
from transmission_layers.intelligence.tier4.scenario_perturbations import apply_structural_perturbation


def test_corridor_removed_and_immutability():
    data = load_simulation_inputs()
    orig = deepcopy(data)
    out = apply_structural_perturbation(data, {"scenario_id": "c", "scenario_type": "corridor_removed", "target_corridors": ["A->B"]})
    assert len(out["quality_scored_edges"]) == len(data["quality_scored_edges"]) - 1
    assert data == orig


def test_unsupported_scenario_diagnostics():
    out = apply_structural_perturbation(load_simulation_inputs(), {"scenario_id": "u", "scenario_type": "unknown"})
    assert out["scenario_diagnostics"]["scenario_type"] == "baseline"
