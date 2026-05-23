from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_p3a_breadth_stability_summary,
    build_p3a_relative_integrity_summary,
    build_p3a_resilience_certification,
    build_p3a_resilience_explainability_summary,
    build_p3a_resilience_signal_registry,
    build_p3a_stability_persistence_summary,
    classify_p3a_resilience_state,
    run_p3a_structural_resilience_foundation,
)


def _base_input():
    return {
        "path1": {"stability_score": 80, "deterioration_intensity": 20},
        "path2": {
            "relative_fragility_score": 30,
            "fragility_percentile": 45,
            "benchmark_divergence": 40,
            "weakness_participation_rate": 0.2,
            "benchmark_resilience_delta": 20,
            "top_fragility_share": 0.25,
        },
    }


def test_public_api_and_registry_shape():
    reg = build_p3a_resilience_signal_registry(_base_input())
    assert set(reg.keys()) == {
        "fragility_resistance", "stability_persistence", "percentile_stability", "benchmark_resilience", "breadth_support", "deterioration_absorption", "divergence_resilience", "concentration_resistance"
    }
    assert isinstance(build_p3a_stability_persistence_summary(reg), dict)
    assert isinstance(build_p3a_relative_integrity_summary(reg), dict)
    assert isinstance(build_p3a_breadth_stability_summary(reg), dict)
    assert isinstance(build_p3a_resilience_explainability_summary(reg, "STABLE"), dict)


def test_deterministic_output_and_checksum_stability():
    inp = _base_input()
    a = run_p3a_structural_resilience_foundation(inp)
    b = run_p3a_structural_resilience_foundation(inp)
    assert a == b
    assert a["checksum_metadata"]["checksum"] == b["checksum_metadata"]["checksum"]


def test_input_immutability_and_bounded_scores():
    inp = _base_input()
    before = deepcopy(inp)
    out = run_p3a_structural_resilience_foundation(inp)
    assert inp == before
    assert out["invariant_flags"]["input_immutability"] is True
    assert all(0 <= v <= 100 for v in out["resilience_dimensions"].values())


def test_missing_input_degrades_gracefully():
    out = run_p3a_structural_resilience_foundation({"path1": {}, "path2": {}})
    assert out["resilience_state"] in {
        "RESILIENT", "STABLE", "NEUTRAL", "VULNERABLE", "DETERIORATING", "DIVERGENT_RESILIENT"
    }


def test_state_classifications():
    assert classify_p3a_resilience_state({
        "fragility_resistance": 95, "stability_persistence": 90, "percentile_stability": 85, "benchmark_resilience": 88,
        "breadth_support": 82, "deterioration_absorption": 84, "divergence_resilience": 70, "concentration_resistance": 81,
    }) == "RESILIENT"
    assert classify_p3a_resilience_state({
        "fragility_resistance": 65, "stability_persistence": 64, "percentile_stability": 62, "benchmark_resilience": 63,
        "breadth_support": 61, "deterioration_absorption": 62, "divergence_resilience": 60, "concentration_resistance": 59,
    }) == "STABLE"
    assert classify_p3a_resilience_state({
        "fragility_resistance": 55, "stability_persistence": 55, "percentile_stability": 50, "benchmark_resilience": 52,
        "breadth_support": 55, "deterioration_absorption": 53, "divergence_resilience": 56, "concentration_resistance": 54,
    }) == "NEUTRAL"
    assert classify_p3a_resilience_state({
        "fragility_resistance": 52, "stability_persistence": 49, "percentile_stability": 49, "benchmark_resilience": 51,
        "breadth_support": 40, "deterioration_absorption": 48, "divergence_resilience": 50, "concentration_resistance": 41,
    }) == "VULNERABLE"
    assert classify_p3a_resilience_state({
        "fragility_resistance": 20, "stability_persistence": 25, "percentile_stability": 30, "benchmark_resilience": 20,
        "breadth_support": 25, "deterioration_absorption": 20, "divergence_resilience": 15, "concentration_resistance": 24,
    }) == "DETERIORATING"
    assert classify_p3a_resilience_state({
        "fragility_resistance": 66, "stability_persistence": 60, "percentile_stability": 62, "benchmark_resilience": 40,
        "breadth_support": 58, "deterioration_absorption": 60, "divergence_resilience": 80, "concentration_resistance": 56,
    }) == "DIVERGENT_RESILIENT"


def test_certification_outcomes_and_forbidden_flags():
    out = run_p3a_structural_resilience_foundation(_base_input())
    cert = build_p3a_resilience_certification(out)
    assert cert["certification_status"] in {
        "CERTIFIED_P3A_RESILIENCE_READY", "DEGRADED_P3A_RESILIENCE_READY", "BLOCKED_P3A_RESILIENCE_INVALID"
    }
    blocked_envelope = deepcopy(out)
    blocked_envelope["forbidden_capability_flags"] = {"forbidden_trade": True}
    blocked = build_p3a_resilience_certification(blocked_envelope)
    assert blocked["certification_status"] == "BLOCKED_P3A_RESILIENCE_INVALID"


def test_no_network_write_runtime_behavior_encoded_and_non_regression_smoke():
    out = run_p3a_structural_resilience_foundation(_base_input())
    joined = str(out).lower()
    assert "http" not in joined
    assert "supabase" not in joined
    assert "write" not in joined
    assert "path2" not in out
