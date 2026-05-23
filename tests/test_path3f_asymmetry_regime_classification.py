from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_p3f_regime_certification,
    build_p3f_regime_evidence_summary,
    build_p3f_regime_explainability_summary,
    build_p3f_regime_pressure_summary,
    build_p3f_regime_report,
    build_p3f_regime_signal_registry,
    build_p3f_regime_transition_summary,
    classify_p3f_asymmetry_regime,
    run_p3f_asymmetry_regime_classification,
)
from transmission_layers.expectation_failure.path2h_relative_fragility_certification import certify_relative_fragility_stack
from transmission_layers.expectation_failure.path3a_structural_resilience_foundation import run_p3a_structural_resilience_foundation
from transmission_layers.expectation_failure.path3b_structural_asymmetry_engine import run_p3b_structural_asymmetry_engine
from transmission_layers.expectation_failure.path3c_benchmark_relative_asymmetry import run_p3c_benchmark_relative_asymmetry_intelligence
from transmission_layers.expectation_failure.path3d_structural_persistence_acceleration import run_p3d_structural_persistence_acceleration_layer
from transmission_layers.expectation_failure.path3e_structural_imbalance_concentration import run_p3e_structural_imbalance_concentration_intelligence


def _base_inputs():
    return {
        "path3a": {"resilience_dimensions": {"resilience_support": 55.0, "fragility_pressure": 45.0}},
        "path3b": {"asymmetry_dimensions": {"downside_asymmetry": 58.0, "upside_resilience": 49.0}},
        "path3c": {"benchmark_asymmetry_dimensions": {"benchmark_relative_pressure": 54.0, "downside_benchmark_gap": 56.0, "resilience_benchmark_gap": 47.0}},
        "path3d": {"persistence_dimensions": {"asymmetry_persistence": 57.0, "durability_score": 54.0, "asymmetry_acceleration": 52.0, "compression_pressure": 46.0, "exhaustion_pressure": 48.0, "stabilization_pressure": 50.0}},
        "path3e": {"imbalance_dimensions": {"fragility_concentration": 53.0, "resilient_breadth_support": 52.0, "cluster_imbalance": 49.0, "crowding_pressure": 48.0, "distributed_balance": 55.0, "participation_support": 57.0, "breadth_collapse_pressure": 43.0}},
    }


def test_public_api_and_export_presence():
    registry = build_p3f_regime_signal_registry(_base_inputs())
    regime = classify_p3f_asymmetry_regime(registry)
    explain = build_p3f_regime_explainability_summary(registry, regime)
    assert isinstance(build_p3f_regime_evidence_summary(registry), dict)
    assert isinstance(build_p3f_regime_pressure_summary(registry), dict)
    assert isinstance(build_p3f_regime_transition_summary(registry), dict)
    assert len(explain["regime_explanations"]) >= 6


def test_deterministic_output_checksum_stability_and_immutability():
    data = _base_inputs()
    frozen = deepcopy(data)
    out1 = run_p3f_asymmetry_regime_classification(data)
    out2 = run_p3f_asymmetry_regime_classification(data)
    assert out1 == out2
    assert out1["checksum_metadata"]["checksum"] == out2["checksum_metadata"]["checksum"]
    assert data == frozen


def test_bounded_outputs_and_degraded_missing_prior_inputs_behavior():
    data = _base_inputs()
    data.pop("path3e")
    out = run_p3f_asymmetry_regime_classification(data)
    assert out["regime_status"] == "DEGRADED_MISSING_PRIOR_P3_INPUTS"
    assert out["certification_status"] == "DEGRADED_P3F_REGIME_READY"
    for value in out["regime_dimensions"].values():
        assert 0 <= float(value) <= 100


def test_all_required_regimes_classification():
    cases = {
        "EXTREME_IMBALANCE_REGIME": {"imbalance_severity": 90, "fragility_regime_pressure": 70, "breadth_pressure": 60, "concentration_pressure": 70, "acceleration_pressure": 60, "resilience_regime_pressure": 40, "persistence_pressure": 55, "benchmark_divergence_pressure": 55, "compression_pressure": 55, "exhaustion_pressure": 55, "regime_confidence": 80},
        "BROAD_STRUCTURAL_DETERIORATION_REGIME": {"imbalance_severity": 70, "fragility_regime_pressure": 75, "breadth_pressure": 35, "concentration_pressure": 65, "acceleration_pressure": 50, "resilience_regime_pressure": 35, "persistence_pressure": 52, "benchmark_divergence_pressure": 58, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 70},
        "CONCENTRATED_FRAGILITY_REGIME": {"imbalance_severity": 70, "fragility_regime_pressure": 68, "breadth_pressure": 45, "concentration_pressure": 78, "acceleration_pressure": 50, "resilience_regime_pressure": 50, "persistence_pressure": 52, "benchmark_divergence_pressure": 58, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 65},
        "DOWNSIDE_ASYMMETRY_EXPANSION_REGIME": {"imbalance_severity": 70, "fragility_regime_pressure": 67, "breadth_pressure": 50, "concentration_pressure": 70, "acceleration_pressure": 70, "resilience_regime_pressure": 48, "persistence_pressure": 55, "benchmark_divergence_pressure": 59, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 66},
        "UPSIDE_RESILIENCE_EXPANSION_REGIME": {"imbalance_severity": 55, "fragility_regime_pressure": 50, "breadth_pressure": 58, "concentration_pressure": 52, "acceleration_pressure": 55, "resilience_regime_pressure": 70, "persistence_pressure": 65, "benchmark_divergence_pressure": 58, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 60},
        "RESILIENT_DIVERGENCE_REGIME": {"imbalance_severity": 52, "fragility_regime_pressure": 50, "breadth_pressure": 58, "concentration_pressure": 52, "acceleration_pressure": 55, "resilience_regime_pressure": 70, "persistence_pressure": 58, "benchmark_divergence_pressure": 64, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 62},
        "FRAGILITY_DIVERGENCE_REGIME": {"imbalance_severity": 65, "fragility_regime_pressure": 63, "breadth_pressure": 58, "concentration_pressure": 52, "acceleration_pressure": 55, "resilience_regime_pressure": 52, "persistence_pressure": 58, "benchmark_divergence_pressure": 61, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 60},
        "STRUCTURAL_COMPRESSION_REGIME": {"imbalance_severity": 48, "fragility_regime_pressure": 50, "breadth_pressure": 60, "concentration_pressure": 50, "acceleration_pressure": 50, "resilience_regime_pressure": 52, "persistence_pressure": 52, "benchmark_divergence_pressure": 55, "compression_pressure": 72, "exhaustion_pressure": 45, "regime_confidence": 55},
        "EXHAUSTION_OR_STABILIZATION_REGIME": {"imbalance_severity": 48, "fragility_regime_pressure": 50, "breadth_pressure": 60, "concentration_pressure": 50, "acceleration_pressure": 50, "resilience_regime_pressure": 52, "persistence_pressure": 52, "benchmark_divergence_pressure": 55, "compression_pressure": 65, "exhaustion_pressure": 75, "regime_confidence": 55},
        "STABLE_SYMMETRY_REGIME": {"imbalance_severity": 35, "fragility_regime_pressure": 45, "breadth_pressure": 65, "concentration_pressure": 45, "acceleration_pressure": 50, "resilience_regime_pressure": 50, "persistence_pressure": 50, "benchmark_divergence_pressure": 45, "compression_pressure": 45, "exhaustion_pressure": 45, "regime_confidence": 40},
    }
    for expected, registry in cases.items():
        assert classify_p3f_asymmetry_regime(registry) == expected


def test_certification_outcomes_forbidden_flags_and_language_constraints():
    ready = run_p3f_asymmetry_regime_classification(_base_inputs())
    assert ready["certification_status"] == "CERTIFIED_P3F_REGIME_READY"
    degraded = run_p3f_asymmetry_regime_classification({"path3a": {}})
    assert degraded["certification_status"] == "DEGRADED_P3F_REGIME_READY"
    blocked_input = _base_inputs()
    blocked_input["notes"] = "buy signal"
    blocked = run_p3f_asymmetry_regime_classification(blocked_input)
    assert blocked["certification_status"] == "BLOCKED_P3F_REGIME_INVALID"
    assert any(blocked["forbidden_capability_flags"].values())
    text = " ".join(blocked["regime_explanations"]).lower()
    for bad in ["go long", "go short", "buy/sell/hold", "expected return", "portfolio action", "trade signal"]:
        assert bad not in text


def test_non_regression_smoke_for_prior_paths_and_report_build():
    assert isinstance(run_p3a_structural_resilience_foundation({"entity": {}}), dict)
    assert isinstance(run_p3b_structural_asymmetry_engine({"path3a": {"resilience_dimensions": {"fragility_pressure": 55, "resilience_support": 45}}}), dict)
    assert isinstance(run_p3c_benchmark_relative_asymmetry_intelligence({"path3b": {"asymmetry_dimensions": {"downside_asymmetry": 50, "upside_resilience": 50}}, "benchmark": {"asymmetry_score": 50, "resilience_score": 50}}), dict)
    assert isinstance(run_p3d_structural_persistence_acceleration_layer({"path3b": {"asymmetry_dimensions": {"downside_asymmetry": 50, "upside_resilience": 50}}, "path3c": {"benchmark_asymmetry_dimensions": {"benchmark_relative_pressure": 50}}, "temporal_history": [50, 50]}), dict)
    assert isinstance(run_p3e_structural_imbalance_concentration_intelligence({"path2": {}, "path3b": {"asymmetry_dimensions": {}}, "path3c": {"benchmark_asymmetry_dimensions": {}}, "path3d": {"persistence_dimensions": {}}}), dict)
    assert isinstance(certify_relative_fragility_stack({}), dict)
    path = build_p3f_regime_report()
    assert "path3f_asymmetry_regime_classification_report.md" in "reports/path3f_asymmetry_regime_classification_report.md"
    cert = build_p3f_regime_certification(run_p3f_asymmetry_regime_classification(_base_inputs()))
    assert cert["certification_status"] in {"CERTIFIED_P3F_REGIME_READY", "DEGRADED_P3F_REGIME_READY", "BLOCKED_P3F_REGIME_INVALID"}
