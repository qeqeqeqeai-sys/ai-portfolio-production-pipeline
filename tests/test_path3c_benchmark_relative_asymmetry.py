from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_p3c_benchmark_asymmetry_certification,
    build_p3c_benchmark_asymmetry_explainability_summary,
    build_p3c_benchmark_asymmetry_registry,
    build_p3c_benchmark_asymmetry_report,
    build_p3c_benchmark_divergence_summary,
    build_p3c_relative_asymmetry_spread,
    build_p3c_resilience_divergence_summary,
    classify_p3c_benchmark_relative_asymmetry_state,
    run_p3c_benchmark_relative_asymmetry_intelligence,
)
from transmission_layers.expectation_failure.path3a_structural_resilience_foundation import run_p3a_structural_resilience_foundation
from transmission_layers.expectation_failure.path3b_structural_asymmetry_engine import run_p3b_structural_asymmetry_engine
from transmission_layers.expectation_failure.path2h_relative_fragility_certification import certify_relative_fragility_stack


def _base_input():
    return {
        "path3b": {
            "asymmetry_dimensions": {"downside_asymmetry": 58, "upside_resilience": 54}
        },
        "benchmark": {
            "benchmark_asymmetry_score": 52,
            "benchmark_resilience_score": 51,
        },
    }


def test_public_api_and_envelope_smoke():
    out = run_p3c_benchmark_relative_asymmetry_intelligence(_base_input())
    assert set(out.keys()) == {
        "benchmark_asymmetry_status",
        "benchmark_asymmetry_state",
        "benchmark_asymmetry_dimensions",
        "relative_asymmetry_spread",
        "benchmark_divergence_summary",
        "resilience_divergence_summary",
        "benchmark_asymmetry_drivers",
        "benchmark_asymmetry_explanations",
        "certification_status",
        "replay_metadata",
        "checksum_metadata",
        "invariant_flags",
        "forbidden_capability_flags",
    }
    assert build_p3c_benchmark_asymmetry_report().endswith("path3c_benchmark_relative_asymmetry_report.md")


def test_deterministic_repeat_and_checksum_stability_and_immutability():
    payload = _base_input()
    frozen = deepcopy(payload)
    out1 = run_p3c_benchmark_relative_asymmetry_intelligence(payload)
    out2 = run_p3c_benchmark_relative_asymmetry_intelligence(payload)
    assert out1 == out2
    assert out1["checksum_metadata"]["checksum"] == out2["checksum_metadata"]["checksum"]
    assert payload == frozen


def test_bounded_outputs_and_no_forbidden_language_flags():
    out = run_p3c_benchmark_relative_asymmetry_intelligence(_base_input())
    dims = out["benchmark_asymmetry_dimensions"]
    for key, value in dims.items():
        if key == "spread_direction":
            continue
        assert 0 <= float(value) <= 100
    assert not any(out["forbidden_capability_flags"].values())
    banned = ["buy", "sell", "hold", "expected return", "portfolio action", "trade signal"]
    text = " ".join(out["benchmark_asymmetry_explanations"]).lower()
    assert all(term not in text for term in banned)


def test_missing_benchmark_degraded_handling():
    out = run_p3c_benchmark_relative_asymmetry_intelligence({"path3b": {"asymmetry_dimensions": {"downside_asymmetry": 60, "upside_resilience": 50}}})
    assert out["benchmark_asymmetry_status"] == "DEGRADED_MISSING_BENCHMARK"
    assert out["certification_status"] == "DEGRADED_P3C_BENCHMARK_ASYMMETRY_READY"


def test_all_required_states_via_registry_classification():
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 35, "downside_spread": 50, "upside_resilience_spread": 50, "entity_asymmetry_score": 80, "benchmark_asymmetry_score": 45}) == "EXTREME_BENCHMARK_IMBALANCE"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 20, "downside_spread": 80, "upside_resilience_spread": 50, "entity_asymmetry_score": 80, "benchmark_asymmetry_score": 60}) == "BENCHMARK_RELATIVE_DOWNSIDE_PRESSURE"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 5, "downside_spread": 60, "upside_resilience_spread": 78, "entity_asymmetry_score": 52, "benchmark_asymmetry_score": 61}) == "BENCHMARK_RELATIVE_UPSIDE_RESILIENCE"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 10, "downside_spread": 65, "upside_resilience_spread": 55, "entity_asymmetry_score": 62, "benchmark_asymmetry_score": 52}) == "ASYMMETRY_SPREAD_EXPANSION"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": -12, "downside_spread": 42, "upside_resilience_spread": 45, "entity_asymmetry_score": 44, "benchmark_asymmetry_score": 56}) == "ASYMMETRY_SPREAD_COMPRESSION"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 6, "downside_spread": 62, "upside_resilience_spread": 60, "entity_asymmetry_score": 72, "benchmark_asymmetry_score": 58}) == "BENCHMARK_FRAGILITY_DIVERGENCE"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 4, "downside_spread": 54, "upside_resilience_spread": 66, "entity_asymmetry_score": 50, "benchmark_asymmetry_score": 62}) == "BENCHMARK_RESILIENT_DIVERGENCE"
    assert classify_p3c_benchmark_relative_asymmetry_state({"relative_asymmetry_spread": 2, "downside_spread": 52, "upside_resilience_spread": 54, "entity_asymmetry_score": 53, "benchmark_asymmetry_score": 52}) == "BENCHMARK_ALIGNED"


def test_certified_degraded_and_blocked_statuses():
    ready = run_p3c_benchmark_relative_asymmetry_intelligence(_base_input())
    assert ready["certification_status"] == "CERTIFIED_P3C_BENCHMARK_ASYMMETRY_READY"

    degraded = run_p3c_benchmark_relative_asymmetry_intelligence({"path3b": {"asymmetry_dimensions": {"downside_asymmetry": 58, "upside_resilience": 54}}})
    assert degraded["certification_status"] == "DEGRADED_P3C_BENCHMARK_ASYMMETRY_READY"

    blocked_envelope = deepcopy(ready)
    blocked_envelope["benchmark_asymmetry_dimensions"]["entity_asymmetry_score"] = 999
    cert = build_p3c_benchmark_asymmetry_certification(blocked_envelope)
    assert cert["certification_status"] == "BLOCKED_P3C_BENCHMARK_ASYMMETRY_INVALID"


def test_component_builders_and_additive_smoke_for_existing_paths():
    reg = build_p3c_benchmark_asymmetry_registry(_base_input())
    assert "spread_direction" in reg
    assert "spread_score" in build_p3c_relative_asymmetry_spread(reg)
    assert "fragility_divergence" in build_p3c_benchmark_divergence_summary(reg)
    assert "resilience_divergence" in build_p3c_resilience_divergence_summary(reg)
    explain = build_p3c_benchmark_asymmetry_explainability_summary(reg, "BENCHMARK_ALIGNED")
    assert len(explain["benchmark_asymmetry_explanations"]) >= 6

    assert "resilience_state" in run_p3a_structural_resilience_foundation({})
    assert "asymmetry_state" in run_p3b_structural_asymmetry_engine({})
    assert "relative_fragility_stack_status" in certify_relative_fragility_stack({})
