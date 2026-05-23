from copy import deepcopy

from transmission_layers.expectation_failure import (
    BLOCKED_RELATIVE_FRAGILITY,
    CERTIFIED_RELATIVE_FRAGILITY,
    DEGRADED_RELATIVE_FRAGILITY,
    build_cohort_relative_baselines,
    build_path2b_relative_fragility_report,
    build_relative_deterioration_velocity_comparison,
    build_relative_fragility_driver_summary,
    build_relative_fragility_input_contract,
    build_relative_fragility_score,
    build_relative_persistence_weakness_comparison,
    certify_relative_fragility_scoring,
    compare_peer_fragility_distribution,
)
from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import build_cohort_registry_contracts
from transmission_layers.expectation_failure.phase_a1_contracts import build_expectation_failure_score_contracts


def _payload(**overrides):
    base = {
        "entity_id": "A",
        "cohort_id": "C1",
        "cohort_version": "1.0",
        "cohort_members": [
            {"entity_id": "A", "fragility_level_divergence": 80, "deterioration_velocity_divergence": 70, "persistence_weakness_divergence": 60, "regime_instability_divergence": 50, "benchmark_divergence": 40},
            {"entity_id": "B", "fragility_level_divergence": 60, "deterioration_velocity_divergence": 55, "persistence_weakness_divergence": 50, "regime_instability_divergence": 45, "benchmark_divergence": 35},
            {"entity_id": "C", "fragility_level_divergence": 40, "deterioration_velocity_divergence": 35, "persistence_weakness_divergence": 30, "regime_instability_divergence": 25, "benchmark_divergence": 20},
        ],
        "fragility_level_divergence": 80,
        "deterioration_velocity_divergence": 70,
        "persistence_weakness_divergence": 60,
        "regime_instability_divergence": 50,
        "benchmark_divergence": 40,
    }
    base.update(overrides)
    return base


def test_public_api_and_smoke_imports():
    assert build_relative_fragility_input_contract
    assert build_cohort_relative_baselines
    assert compare_peer_fragility_distribution
    assert build_relative_fragility_score
    assert build_relative_deterioration_velocity_comparison
    assert build_relative_persistence_weakness_comparison
    assert build_relative_fragility_driver_summary
    assert certify_relative_fragility_scoring
    assert build_path2b_relative_fragility_report
    assert build_cohort_registry_contracts
    assert build_expectation_failure_score_contracts


def test_deterministic_output_checksum_and_immutability():
    payload = _payload()
    original = deepcopy(payload)
    a = build_relative_fragility_score(payload)
    b = build_relative_fragility_score(payload)
    assert a == b
    assert a["checksum"] == b["checksum"]
    assert payload == original


def test_fixed_weights_and_bounded_score_and_tiers():
    contract = build_relative_fragility_input_contract()
    assert sum(contract["fixed_component_weights"].values()) == 100
    high = build_relative_fragility_score(_payload(fragility_level_divergence=100, deterioration_velocity_divergence=100, persistence_weakness_divergence=100, regime_instability_divergence=100, benchmark_divergence=100))
    assert high["relative_fragility_score"] == 100
    assert high["relative_fragility_tier"] == "EXTREME_RELATIVE_FRAGILITY"
    moderate = build_relative_fragility_score(_payload(fragility_level_divergence=50, deterioration_velocity_divergence=50, persistence_weakness_divergence=50, regime_instability_divergence=50, benchmark_divergence=50))
    assert moderate["relative_fragility_tier"] == "MODERATE_RELATIVE_FRAGILITY"
    low = build_relative_fragility_score(_payload(fragility_level_divergence=0, deterioration_velocity_divergence=0, persistence_weakness_divergence=0, regime_instability_divergence=0, benchmark_divergence=0))
    assert low["relative_fragility_tier"] == "RELATIVE_STRENGTH"


def test_clamped_and_missing_optional_degradation():
    out = build_relative_fragility_score(_payload(fragility_level_divergence=999, benchmark_divergence=-5, regime_instability_divergence=None))
    assert out["component_scores"]["fragility_level_divergence"] == 100
    assert out["component_scores"]["benchmark_divergence"] == 0
    assert "regime_instability_divergence" in out["quality_flags"]["missing_optional_components"]
    cert = certify_relative_fragility_scoring(_payload(fragility_level_divergence=999, benchmark_divergence=-5, regime_instability_divergence=None), out)
    assert cert["decision_status"] == DEGRADED_RELATIVE_FRAGILITY


def test_blocking_cases_and_membership_gate():
    blocked_entity = certify_relative_fragility_scoring(_payload(entity_id=""))
    assert blocked_entity["decision_status"] == BLOCKED_RELATIVE_FRAGILITY
    blocked_cohort = certify_relative_fragility_scoring(_payload(cohort_id=""))
    assert blocked_cohort["decision_status"] == BLOCKED_RELATIVE_FRAGILITY
    blocked_membership = certify_relative_fragility_scoring(_payload(entity_id="Z"))
    assert blocked_membership["decision_status"] == BLOCKED_RELATIVE_FRAGILITY


def test_baselines_deltas_comparisons_and_driver_summary():
    members = _payload()["cohort_members"]
    baseline = build_cohort_relative_baselines(members)
    assert baseline["peer_median"] == 60
    peer = compare_peer_fragility_distribution(80, baseline["peer_median"])
    assert peer["peer_median_delta"] == 20
    vel = build_relative_deterioration_velocity_comparison(70, 55)
    per = build_relative_persistence_weakness_comparison(60, 50)
    assert vel["deterioration_velocity_delta"] == 15
    assert per["persistence_weakness_delta"] == 10
    drv = build_relative_fragility_driver_summary(_payload(), build_relative_fragility_input_contract()["fixed_component_weights"])
    assert drv["primary_driver"]
    assert len(drv["ranked_contributions"]) == 5


def test_certified_status_and_forbidden_inventory_and_report_smoke():
    payload = _payload()
    scored = build_relative_fragility_score(payload)
    cert = certify_relative_fragility_scoring(payload, scored)
    assert cert["decision_status"] == CERTIFIED_RELATIVE_FRAGILITY
    assert "adaptive_weighting" in cert["forbidden_capability_inventory"]
    report = build_path2b_relative_fragility_report(payload)
    assert report["path_id"] == "P2-B"
    assert report["final_supervisor_interpretation"] in {
        CERTIFIED_RELATIVE_FRAGILITY,
        DEGRADED_RELATIVE_FRAGILITY,
        BLOCKED_RELATIVE_FRAGILITY,
    }
