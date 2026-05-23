from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_p3d_acceleration_summary,
    build_p3d_asymmetry_persistence_summary,
    build_p3d_exhaustion_summary,
    build_p3d_persistence_certification,
    build_p3d_persistence_explainability_summary,
    build_p3d_persistence_report,
    build_p3d_persistence_signal_registry,
    build_p3d_stabilization_summary,
    classify_p3d_persistence_acceleration_state,
    run_p3d_structural_persistence_acceleration_layer,
)
from transmission_layers.expectation_failure.path2h_relative_fragility_certification import certify_relative_fragility_stack
from transmission_layers.expectation_failure.path3a_structural_resilience_foundation import run_p3a_structural_resilience_foundation
from transmission_layers.expectation_failure.path3b_structural_asymmetry_engine import run_p3b_structural_asymmetry_engine
from transmission_layers.expectation_failure.path3c_benchmark_relative_asymmetry import run_p3c_benchmark_relative_asymmetry_intelligence


def _base_inputs():
    return {
        "path3b": {"asymmetry_dimensions": {"downside_asymmetry": 62.0, "upside_resilience": 44.0}},
        "path3c": {"benchmark_asymmetry_dimensions": {"benchmark_relative_pressure": 58.0}},
        "temporal_history": [58.0, 60.0, 62.0],
    }


def test_public_api_and_export_presence():
    data = _base_inputs()
    registry = build_p3d_persistence_signal_registry(data)
    state = classify_p3d_persistence_acceleration_state(registry)
    explain = build_p3d_persistence_explainability_summary(registry, state)
    assert isinstance(build_p3d_asymmetry_persistence_summary(registry), dict)
    assert isinstance(build_p3d_acceleration_summary(registry), dict)
    assert isinstance(build_p3d_stabilization_summary(registry), dict)
    assert isinstance(build_p3d_exhaustion_summary(registry), dict)
    assert len(explain["persistence_explanations"]) >= 5


def test_deterministic_output_checksum_stability_and_immutability():
    data = _base_inputs()
    frozen = deepcopy(data)
    out1 = run_p3d_structural_persistence_acceleration_layer(data)
    out2 = run_p3d_structural_persistence_acceleration_layer(data)
    assert out1 == out2
    assert out1["checksum_metadata"]["checksum"] == out2["checksum_metadata"]["checksum"]
    assert data == frozen


def test_bounded_outputs_and_degraded_missing_history_behavior():
    data = _base_inputs()
    data["temporal_history"] = []
    out = run_p3d_structural_persistence_acceleration_layer(data)
    assert out["persistence_status"] == "DEGRADED_MISSING_TEMPORAL_HISTORY"
    assert out["certification_status"] == "DEGRADED_P3D_PERSISTENCE_READY"
    for value in out["persistence_dimensions"].values():
        assert 0 <= float(value) <= 100


def test_all_required_states_classification():
    cases = {
        "DURABLE_STRUCTURAL_ASYMMETRY": {"asymmetry_persistence": 80, "asymmetry_acceleration": 55, "asymmetry_deceleration": 45, "stabilization_pressure": 75, "compression_pressure": 40, "exhaustion_pressure": 60, "durability_score": 80, "temporal_consistency": 80, "benchmark_relative_persistence": 70, "downside_persistence": 75, "resilience_persistence": 45},
        "COMPRESSING_ASYMMETRY": {"asymmetry_persistence": 60, "asymmetry_acceleration": 48, "asymmetry_deceleration": 52, "stabilization_pressure": 60, "compression_pressure": 70, "exhaustion_pressure": 50, "durability_score": 50, "temporal_consistency": 52, "benchmark_relative_persistence": 40, "downside_persistence": 58, "resilience_persistence": 70},
        "EXHAUSTING_ASYMMETRY": {"asymmetry_persistence": 72, "asymmetry_acceleration": 30, "asymmetry_deceleration": 70, "stabilization_pressure": 62, "compression_pressure": 40, "exhaustion_pressure": 80, "durability_score": 60, "temporal_consistency": 58, "benchmark_relative_persistence": 64, "downside_persistence": 72, "resilience_persistence": 42},
        "ACCELERATING_ASYMMETRY": {"asymmetry_persistence": 65, "asymmetry_acceleration": 75, "asymmetry_deceleration": 25, "stabilization_pressure": 45, "compression_pressure": 40, "exhaustion_pressure": 52, "durability_score": 56, "temporal_consistency": 55, "benchmark_relative_persistence": 62, "downside_persistence": 68, "resilience_persistence": 40},
        "STABILIZING_ASYMMETRY": {"asymmetry_persistence": 58, "asymmetry_acceleration": 53, "asymmetry_deceleration": 47, "stabilization_pressure": 78, "compression_pressure": 45, "exhaustion_pressure": 55, "durability_score": 57, "temporal_consistency": 64, "benchmark_relative_persistence": 50, "downside_persistence": 57, "resilience_persistence": 49},
        "PERSISTENT_ASYMMETRY": {"asymmetry_persistence": 56, "asymmetry_acceleration": 50, "asymmetry_deceleration": 50, "stabilization_pressure": 55, "compression_pressure": 45, "exhaustion_pressure": 45, "durability_score": 52, "temporal_consistency": 50, "benchmark_relative_persistence": 52, "downside_persistence": 56, "resilience_persistence": 46},
        "TRANSIENT_ASYMMETRY": {"asymmetry_persistence": 40, "asymmetry_acceleration": 45, "asymmetry_deceleration": 55, "stabilization_pressure": 62, "compression_pressure": 55, "exhaustion_pressure": 42, "durability_score": 45, "temporal_consistency": 48, "benchmark_relative_persistence": 45, "downside_persistence": 40, "resilience_persistence": 52},
    }
    for expected, registry in cases.items():
        assert classify_p3d_persistence_acceleration_state(registry) == expected


def test_certification_outcomes_and_forbidden_flags_and_language_constraints():
    ready = run_p3d_structural_persistence_acceleration_layer(_base_inputs())
    assert ready["certification_status"] == "CERTIFIED_P3D_PERSISTENCE_READY"
    blocked_input = _base_inputs()
    blocked_input["note"] = "buy signal"
    blocked = run_p3d_structural_persistence_acceleration_layer(blocked_input)
    assert blocked["certification_status"] == "BLOCKED_P3D_PERSISTENCE_INVALID"
    assert any(blocked["forbidden_capability_flags"].values())
    text = " ".join(blocked["persistence_explanations"]).lower()
    for bad in ["go long", "go short", "buy/sell/hold", "expected return", "portfolio action", "trade signal"]:
        assert bad not in text


def test_non_regression_smoke_for_prior_paths_and_report_build():
    assert isinstance(run_p3a_structural_resilience_foundation({"entity": {}}), dict)
    assert isinstance(run_p3b_structural_asymmetry_engine({"path3a": {"resilience_dimensions": {"fragility_pressure": 55, "resilience_support": 45}}}), dict)
    assert isinstance(run_p3c_benchmark_relative_asymmetry_intelligence({"path3b": {"asymmetry_dimensions": {"downside_asymmetry": 50, "upside_resilience": 50}}, "benchmark": {"asymmetry_score": 50, "resilience_score": 50}}), dict)
    assert isinstance(certify_relative_fragility_stack({}), dict)
    path = build_p3d_persistence_report()
    assert path.endswith("path3d_structural_persistence_acceleration_report.md")
    cert = build_p3d_persistence_certification(run_p3d_structural_persistence_acceleration_layer(_base_inputs()))
    assert cert["certification_status"] in {"CERTIFIED_P3D_PERSISTENCE_READY", "DEGRADED_P3D_PERSISTENCE_READY", "BLOCKED_P3D_PERSISTENCE_INVALID"}
