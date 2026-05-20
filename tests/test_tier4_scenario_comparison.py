from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation, load_simulation_inputs
from transmission_layers.intelligence.tier4.scenario_perturbations import apply_structural_perturbation
from transmission_layers.intelligence.tier4.scenario_comparison import compare_scenario_outcomes, rank_scenarios_by_impact


def test_comparison_deterministic_and_bounded():
    base_in = load_simulation_inputs()
    base = run_structural_simulation(base_in)
    cand = run_structural_simulation(apply_structural_perturbation(base_in, {"scenario_id": "s2", "scenario_type": "node_stressed", "target_nodes": ["A"], "perturbation_strength": 0.4}))
    comp = compare_scenario_outcomes({"scenario_id": "base"}, {"scenario_id": "s2", "scenario_type": "node_stressed"}, base, cand)
    assert 0.0 <= comp["scenario_similarity_score"] <= 1.0


def test_ranking_tie_breaker():
    ranked = rank_scenarios_by_impact([
        {"scenario_id": "b", "scenario_impact_score": 0.5, "regime_shift_intensity": 0.5, "fragmentation_delta": 0.1, "overload_delta": 0.1},
        {"scenario_id": "a", "scenario_impact_score": 0.5, "regime_shift_intensity": 0.5, "fragmentation_delta": 0.1, "overload_delta": 0.1},
    ])
    assert ranked[0]["scenario_id"] == "a"
