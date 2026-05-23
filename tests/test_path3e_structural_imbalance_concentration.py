from copy import deepcopy

from transmission_layers.expectation_failure import path3a_structural_resilience_foundation as p3a
from transmission_layers.expectation_failure import path3b_structural_asymmetry_engine as p3b
from transmission_layers.expectation_failure import path3c_benchmark_relative_asymmetry as p3c
from transmission_layers.expectation_failure import path3d_structural_persistence_acceleration as p3d
from transmission_layers.expectation_failure import path3e_structural_imbalance_concentration as p3e
from transmission_layers.expectation_failure import path2g_structural_concentration_breadth as p2g


def _sample_inputs(include_path2=True):
    data = {
        "path3b": {"asymmetry_dimensions": {"downside_asymmetry": 70, "upside_resilience": 45}},
        "path3c": {"benchmark_asymmetry_dimensions": {"downside_benchmark_gap": 65, "resilience_benchmark_gap": 35}},
        "path3d": {"persistence_dimensions": {"downside_persistence": 68, "resilience_persistence": 42, "asymmetry_persistence": 64, "stabilization_pressure": 38, "compression_pressure": 60}},
    }
    if include_path2:
        data["path2"] = {"fragility_concentration": 72, "resilience_concentration": 40, "breadth_collapse_pressure": 70, "participation_support": 35, "cluster_imbalance": 74}
    return data


def test_public_api_presence_and_non_regression_imports():
    required = [
        "build_p3e_imbalance_signal_registry", "build_p3e_concentration_summary", "build_p3e_breadth_collapse_summary",
        "build_p3e_participation_summary", "build_p3e_cluster_imbalance_summary", "classify_p3e_structural_imbalance_state",
        "build_p3e_imbalance_explainability_summary", "run_p3e_structural_imbalance_concentration_intelligence",
        "build_p3e_imbalance_certification", "build_p3e_imbalance_report",
    ]
    for name in required:
        assert hasattr(p3e, name)
    assert hasattr(p3d, "run_p3d_structural_persistence_acceleration_layer")
    assert hasattr(p3c, "run_p3c_benchmark_relative_asymmetry_intelligence")
    assert hasattr(p3b, "run_p3b_structural_asymmetry_engine")
    assert hasattr(p3a, "run_p3a_structural_resilience_foundation")
    assert hasattr(p2g, "build_concentration_breadth_input_contract")


def test_deterministic_checksum_and_immutability_and_bounded():
    inp = _sample_inputs()
    frozen = deepcopy(inp)
    out1 = p3e.run_p3e_structural_imbalance_concentration_intelligence(inp)
    out2 = p3e.run_p3e_structural_imbalance_concentration_intelligence(inp)
    assert out1 == out2
    assert out1["checksum_metadata"]["checksum"] == out2["checksum_metadata"]["checksum"]
    assert inp == frozen
    assert all(0 <= out1["imbalance_dimensions"][k] <= 100 for k in p3e.DIMENSION_KEYS)


def test_degraded_when_missing_path2():
    out = p3e.run_p3e_structural_imbalance_concentration_intelligence(_sample_inputs(include_path2=False))
    assert out["imbalance_status"] == "DEGRADED_MISSING_CONCENTRATION_BREADTH"
    assert out["certification_status"] == p3e.DEGRADED_P3E_IMBALANCE_READY


def test_blocked_on_forbidden_capability_language():
    inp = _sample_inputs()
    inp["note"] = "go long"
    out = p3e.run_p3e_structural_imbalance_concentration_intelligence(inp)
    assert out["certification_status"] == p3e.BLOCKED_P3E_IMBALANCE_INVALID


def test_all_required_states_classification():
    cases = {
        "DISTRIBUTED_BALANCE": {"crowding_pressure": 30, "breadth_collapse_pressure": 30, "cluster_imbalance": 30, "participation_support": 80, "narrowness_pressure": 20, "fragile_breadth_pressure": 40, "resilient_breadth_support": 60, "fragility_concentration": 45, "resilience_concentration": 55},
        "FRAGILITY_CONCENTRATION": {"crowding_pressure": 50, "breadth_collapse_pressure": 40, "cluster_imbalance": 40, "participation_support": 55, "narrowness_pressure": 40, "fragile_breadth_pressure": 50, "resilient_breadth_support": 50, "fragility_concentration": 75, "resilience_concentration": 50},
        "RESILIENCE_CONCENTRATION": {"crowding_pressure": 50, "breadth_collapse_pressure": 40, "cluster_imbalance": 40, "participation_support": 55, "narrowness_pressure": 40, "fragile_breadth_pressure": 50, "resilient_breadth_support": 50, "fragility_concentration": 55, "resilience_concentration": 75},
        "BROAD_FRAGILITY_IMBALANCE": {"crowding_pressure": 50, "breadth_collapse_pressure": 55, "cluster_imbalance": 40, "participation_support": 55, "narrowness_pressure": 45, "fragile_breadth_pressure": 75, "resilient_breadth_support": 45, "fragility_concentration": 60, "resilience_concentration": 50},
        "BROAD_RESILIENCE_SUPPORT": {"crowding_pressure": 45, "breadth_collapse_pressure": 45, "cluster_imbalance": 40, "participation_support": 70, "narrowness_pressure": 30, "fragile_breadth_pressure": 40, "resilient_breadth_support": 72, "fragility_concentration": 50, "resilience_concentration": 60},
        "BREADTH_COLLAPSE": {"crowding_pressure": 70, "breadth_collapse_pressure": 80, "cluster_imbalance": 60, "participation_support": 35, "narrowness_pressure": 70, "fragile_breadth_pressure": 75, "resilient_breadth_support": 30, "fragility_concentration": 68, "resilience_concentration": 40},
        "NARROW_PARTICIPATION": {"crowding_pressure": 60, "breadth_collapse_pressure": 60, "cluster_imbalance": 60, "participation_support": 35, "narrowness_pressure": 70, "fragile_breadth_pressure": 60, "resilient_breadth_support": 45, "fragility_concentration": 55, "resilience_concentration": 50},
        "CLUSTER_DRIVEN_IMBALANCE": {"crowding_pressure": 60, "breadth_collapse_pressure": 60, "cluster_imbalance": 75, "participation_support": 50, "narrowness_pressure": 50, "fragile_breadth_pressure": 55, "resilient_breadth_support": 55, "fragility_concentration": 58, "resilience_concentration": 52},
        "EXTREME_STRUCTURAL_CROWDING": {"crowding_pressure": 90, "breadth_collapse_pressure": 60, "cluster_imbalance": 60, "participation_support": 40, "narrowness_pressure": 60, "fragile_breadth_pressure": 60, "resilient_breadth_support": 40, "fragility_concentration": 65, "resilience_concentration": 55},
    }
    for state, seed in cases.items():
        reg = {k: 50 for k in p3e.DIMENSION_KEYS}
        reg.update(seed)
        assert p3e.classify_p3e_structural_imbalance_state(reg) == state
