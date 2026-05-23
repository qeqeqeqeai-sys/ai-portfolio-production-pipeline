from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_p3a_resilience_signal_registry,
    build_p3b_asymmetry_certification,
    build_p3b_asymmetry_explainability_summary,
    build_p3b_asymmetry_signal_registry,
    build_p3b_downside_asymmetry_summary,
    build_p3b_fragility_resilience_balance,
    build_p3b_upside_resilience_summary,
    classify_p3b_structural_asymmetry_state,
    run_p3b_structural_asymmetry_engine,
)
from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import build_relative_fragility_score


def _p3b_input():
    return {
        "path2": {
            "relative_fragility_score": 30,
            "benchmark_divergence": 45,
            "weakness_participation_rate": 0.2,
            "top_fragility_share": 0.25,
        },
        "path3a": {
            "resilience_dimensions": {
                "fragility_resistance": 70,
                "stability_persistence": 75,
                "breadth_support": 74,
                "divergence_resilience": 60,
            }
        },
    }


def test_public_api_export_presence_and_registry_shape():
    reg = build_p3b_asymmetry_signal_registry(_p3b_input())
    assert set(reg.keys()) == {
        "fragility_pressure", "resilience_support", "downside_asymmetry", "upside_resilience", "benchmark_relative_imbalance",
        "concentration_asymmetry", "breadth_asymmetry", "persistence_asymmetry", "divergence_asymmetry"
    }
    assert isinstance(build_p3b_fragility_resilience_balance(reg), dict)
    assert isinstance(build_p3b_downside_asymmetry_summary(reg), dict)
    assert isinstance(build_p3b_upside_resilience_summary(reg), dict)
    assert isinstance(build_p3b_asymmetry_explainability_summary(reg, "BALANCED_STRUCTURE"), dict)


def test_deterministic_output_and_checksum_stability():
    a = run_p3b_structural_asymmetry_engine(_p3b_input())
    b = run_p3b_structural_asymmetry_engine(_p3b_input())
    assert a == b
    assert a["checksum_metadata"]["checksum"] == b["checksum_metadata"]["checksum"]


def test_input_immutability_bounded_outputs_and_missing_degraded_handling():
    inp = _p3b_input()
    before = deepcopy(inp)
    out = run_p3b_structural_asymmetry_engine(inp)
    assert inp == before
    assert out["invariant_flags"]["input_immutability"] is True
    assert all(0 <= v <= 100 for v in out["asymmetry_dimensions"].values())

    degraded = run_p3b_structural_asymmetry_engine({"path2": {}, "path3a": {}})
    assert degraded["asymmetry_state"] in {
        "BALANCED_STRUCTURE", "RESILIENT_TILT", "FRAGILE_TILT", "DOWNSIDE_ASYMMETRY", "UPSIDE_RESILIENCE_ASYMMETRY", "EXTREME_FRAGILITY_CONCENTRATION", "DIVERGENT_RESILIENCE"
    }


def test_all_required_states_covered():
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 52, "resilience_support": 50, "downside_asymmetry": 50, "upside_resilience": 50,
        "benchmark_relative_imbalance": 40, "concentration_asymmetry": 45, "breadth_asymmetry": 45, "persistence_asymmetry": 45, "divergence_asymmetry": 45,
    }) == "BALANCED_STRUCTURE"
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 45, "resilience_support": 60, "downside_asymmetry": 50, "upside_resilience": 65,
        "benchmark_relative_imbalance": 20, "concentration_asymmetry": 45, "breadth_asymmetry": 45, "persistence_asymmetry": 45, "divergence_asymmetry": 45,
    }) == "RESILIENT_TILT"
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 62, "resilience_support": 50, "downside_asymmetry": 60, "upside_resilience": 45,
        "benchmark_relative_imbalance": 30, "concentration_asymmetry": 50, "breadth_asymmetry": 55, "persistence_asymmetry": 45, "divergence_asymmetry": 45,
    }) == "FRAGILE_TILT"
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 80, "resilience_support": 35, "downside_asymmetry": 80, "upside_resilience": 25,
        "benchmark_relative_imbalance": 50, "concentration_asymmetry": 60, "breadth_asymmetry": 70, "persistence_asymmetry": 60, "divergence_asymmetry": 50,
    }) == "DOWNSIDE_ASYMMETRY"
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 35, "resilience_support": 80, "downside_asymmetry": 30, "upside_resilience": 85,
        "benchmark_relative_imbalance": 30, "concentration_asymmetry": 30, "breadth_asymmetry": 35, "persistence_asymmetry": 20, "divergence_asymmetry": 30,
    }) == "UPSIDE_RESILIENCE_ASYMMETRY"
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 85, "resilience_support": 45, "downside_asymmetry": 90, "upside_resilience": 20,
        "benchmark_relative_imbalance": 40, "concentration_asymmetry": 80, "breadth_asymmetry": 60, "persistence_asymmetry": 60, "divergence_asymmetry": 40,
    }) == "EXTREME_FRAGILITY_CONCENTRATION"
    assert classify_p3b_structural_asymmetry_state({
        "fragility_pressure": 40, "resilience_support": 80, "downside_asymmetry": 35, "upside_resilience": 82,
        "benchmark_relative_imbalance": 70, "concentration_asymmetry": 35, "breadth_asymmetry": 40, "persistence_asymmetry": 30, "divergence_asymmetry": 60,
    }) == "DIVERGENT_RESILIENCE"


def test_certification_outcomes_forbidden_flags_and_language_boundaries():
    out = run_p3b_structural_asymmetry_engine(_p3b_input())
    cert = build_p3b_asymmetry_certification(out)
    assert cert["certification_status"] in {
        "CERTIFIED_P3B_ASYMMETRY_READY", "DEGRADED_P3B_ASYMMETRY_READY", "BLOCKED_P3B_ASYMMETRY_INVALID"
    }

    blocked_envelope = deepcopy(out)
    blocked_envelope["forbidden_capability_flags"] = {"forbidden_trade": True}
    blocked = build_p3b_asymmetry_certification(blocked_envelope)
    assert blocked["certification_status"] == "BLOCKED_P3B_ASYMMETRY_INVALID"

    joined = " ".join(out["asymmetry_explanations"]).lower()
    for forbidden in ["buy", "sell", "hold", "expected return", "portfolio action", "go long", "short this"]:
        assert forbidden not in joined


def test_additive_non_regression_smoke_for_p3a_and_path2_apis():
    p3a = build_p3a_resilience_signal_registry({"path1": {}, "path2": {}})
    p2 = build_relative_fragility_score({"entity_id":"E1","cohort_id":"C1","cohort_version":"v1","cohort_members":[{"entity_id":"E1"}],"fragility_level_divergence":60,"deterioration_velocity_divergence":50,"persistence_weakness_divergence":50,"regime_instability_divergence":40,"benchmark_divergence":45})
    assert isinstance(p3a, dict)
    assert isinstance(p2, dict)
