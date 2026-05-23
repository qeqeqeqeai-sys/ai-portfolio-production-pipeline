from copy import deepcopy

from transmission_layers.expectation_failure import (
    BLOCKED_BENCHMARK_DIVERGENCE,
    CERTIFIED_BENCHMARK_DIVERGENCE,
    DEGRADED_BENCHMARK_DIVERGENCE,
    assign_benchmark_divergence_tier,
    build_benchmark_divergence_explanation,
    build_benchmark_divergence_input_contract,
    build_benchmark_divergence_score,
    build_path2d_benchmark_divergence_report,
    calculate_fragility_divergence,
    calculate_percentile_divergence,
    calculate_persistence_divergence,
    calculate_velocity_divergence,
    certify_benchmark_divergence_intelligence,
    resolve_benchmark_alignment,
)
from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import build_cohort_registry_contracts
from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import build_relative_fragility_input_contract
from transmission_layers.expectation_failure.path2c_percentile_ranking_engine import build_percentile_ranking_input_contract


def _payload(**overrides):
    base = {
        "entity_id": "E1",
        "cohort_id": "C1",
        "cohort_version": "1.0",
        "benchmark_id": "B1",
        "benchmark_version": "1.0",
        "benchmark_mapping": {"benchmark_id": "B1", "benchmark_version": "1.0"},
        "fragility_divergence": 80,
        "persistence_divergence": 70,
        "velocity_divergence": 60,
        "percentile_divergence": 50,
    }
    base.update(overrides)
    return base


def test_public_api_presence_and_smoke_imports():
    assert build_benchmark_divergence_input_contract()["path_id"] == "P2-D"
    assert build_cohort_registry_contracts()["path_id"] == "P2-A"
    assert build_relative_fragility_input_contract()["path_id"] == "P2-B"
    assert build_percentile_ranking_input_contract()["path_id"] == "P2-C"


def test_deterministic_output_and_checksum_stability_and_immutable_input():
    p = _payload()
    snapshot = deepcopy(p)
    one = certify_benchmark_divergence_intelligence(p)
    two = certify_benchmark_divergence_intelligence(p)
    assert p == snapshot
    assert one["output"] == two["output"]
    assert one["output"]["checksum"] == two["output"]["checksum"]


def test_fixed_weights_total_100_and_bounded_score_and_tiers():
    contract = build_benchmark_divergence_input_contract()
    assert sum(contract["fixed_divergence_weights"].values()) == 100
    assert 0 <= build_benchmark_divergence_score({"fragility_divergence": 150, "persistence_divergence": -10, "velocity_divergence": 50, "percentile_divergence": 40}) <= 100
    assert assign_benchmark_divergence_tier(85) == "EXTREME_BENCHMARK_DIVERGENCE"
    assert assign_benchmark_divergence_tier(70) == "ELEVATED_BENCHMARK_DIVERGENCE"
    assert assign_benchmark_divergence_tier(50) == "MODERATE_BENCHMARK_DIVERGENCE"
    assert assign_benchmark_divergence_tier(30) == "LIMITED_BENCHMARK_DIVERGENCE"
    assert assign_benchmark_divergence_tier(29) == "BENCHMARK_ALIGNED"


def test_component_calculations_and_clamping():
    p = _payload(fragility_divergence=120, persistence_divergence=-3, velocity_divergence="x", percentile_divergence=45)
    assert calculate_fragility_divergence(p)["value"] == 100
    assert calculate_persistence_divergence(p)["value"] == 0
    assert calculate_velocity_divergence(p)["value"] == 0
    assert calculate_percentile_divergence(p)["value"] == 45


def test_missing_optional_component_degrades():
    result = certify_benchmark_divergence_intelligence(_payload(percentile_divergence=None))
    assert result["decision_status"] == DEGRADED_BENCHMARK_DIVERGENCE


def test_missing_required_fields_block():
    assert certify_benchmark_divergence_intelligence(_payload(entity_id=""))["decision_status"] == BLOCKED_BENCHMARK_DIVERGENCE
    assert certify_benchmark_divergence_intelligence(_payload(cohort_id=""))["decision_status"] == BLOCKED_BENCHMARK_DIVERGENCE
    assert certify_benchmark_divergence_intelligence(_payload(benchmark_id=""))["decision_status"] == BLOCKED_BENCHMARK_DIVERGENCE
    assert certify_benchmark_divergence_intelligence(_payload(benchmark_version=""))["decision_status"] == BLOCKED_BENCHMARK_DIVERGENCE


def test_invalid_benchmark_mapping_and_alignment_resolution():
    bad = resolve_benchmark_alignment(_payload(benchmark_mapping=None))
    assert bad["benchmark_alignment_status"] == "INVALID_BENCHMARK_MAPPING"
    mismatch = resolve_benchmark_alignment(_payload(benchmark_mapping={"benchmark_id": "B2", "benchmark_version": "1.0"}))
    assert mismatch["benchmark_alignment_status"] == "BENCHMARK_MAPPING_MISMATCH"


def test_explanation_driver_summary_and_certification_states():
    cert = certify_benchmark_divergence_intelligence(_payload())
    assert cert["decision_status"] == CERTIFIED_BENCHMARK_DIVERGENCE
    out = cert["output"]
    assert "fragility=" in out["divergence_driver_summary"]
    assert build_benchmark_divergence_explanation(out)


def test_forbidden_inventory_report_builder_and_path1_smoke_import():
    cert = certify_benchmark_divergence_intelligence(_payload())
    assert "adaptive_divergence_weighting" in cert["forbidden_capability_inventory"]
    report = build_path2d_benchmark_divergence_report(_payload())
    assert report["path_id"] == "P2-D"
    from transmission_layers.expectation_failure.phase_a1_contracts import build_expectation_failure_score_contracts

    assert isinstance(build_expectation_failure_score_contracts(), list)
