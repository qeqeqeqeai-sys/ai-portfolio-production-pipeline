from copy import deepcopy

from transmission_layers.expectation_failure import (
    BLOCKED_RELATIVE_RANKING,
    CERTIFIED_RELATIVE_RANKING,
    DEGRADED_RELATIVE_RANKING,
    assign_percentile_ranking_tiers,
    build_deterministic_cohort_ranking,
    build_path2c_percentile_ranking_report,
    build_percentile_ranking_input_contract,
    build_ranking_explanation_summary,
    calculate_cohort_percentiles,
    certify_percentile_ranking_engine,
    resolve_relative_ranking_ties,
)
from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import build_cohort_registry_contracts
from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import build_relative_fragility_input_contract
from transmission_layers.expectation_failure.phase_a1_contracts import build_expectation_failure_score_contracts


def _payload(**overrides):
    base = {
        "cohort_id": "C1",
        "cohort_version": "2026.05",
        "cohort_members": [
            {"entity_id": "B", "relative_fragility_score": 80, "persistence_weakness_divergence": 60, "deterioration_velocity_divergence": 55, "benchmark_divergence": 50},
            {"entity_id": "A", "relative_fragility_score": 80, "persistence_weakness_divergence": 60, "deterioration_velocity_divergence": 55, "benchmark_divergence": 50},
            {"entity_id": "C", "relative_fragility_score": 30, "persistence_weakness_divergence": 20, "deterioration_velocity_divergence": 10, "benchmark_divergence": 10},
        ],
    }
    base.update(overrides)
    return base


def test_public_api_and_dependency_smoke_imports():
    assert build_percentile_ranking_input_contract
    assert build_deterministic_cohort_ranking
    assert resolve_relative_ranking_ties
    assert calculate_cohort_percentiles
    assert assign_percentile_ranking_tiers
    assert build_ranking_explanation_summary
    assert certify_percentile_ranking_engine
    assert build_path2c_percentile_ranking_report
    assert build_cohort_registry_contracts
    assert build_relative_fragility_input_contract
    assert build_expectation_failure_score_contracts


def test_deterministic_output_checksum_and_immutability():
    payload = _payload()
    original = deepcopy(payload)
    a = build_deterministic_cohort_ranking(payload)
    b = build_deterministic_cohort_ranking(payload)
    assert a == b
    assert [x["checksum"] for x in a["ranked_entities"]] == [x["checksum"] for x in b["ranked_entities"]]
    assert payload == original


def test_required_sort_order_and_entity_id_tie_breaker():
    out = build_deterministic_cohort_ranking(_payload())
    assert [x["entity_id"] for x in out["ranked_entities"]] == ["A", "B", "C"]


def test_multi_and_single_percentile_and_bounds_and_tiers():
    out = build_deterministic_cohort_ranking(_payload())
    assert [x["percentile"] for x in out["ranked_entities"]] == [100, 50, 0]
    assert all(0 <= x["percentile"] <= 100 for x in out["ranked_entities"])
    assert out["ranked_entities"][0]["percentile_tier"] == "EXTREME_FRAGILITY_PERCENTILE"
    single = build_deterministic_cohort_ranking(_payload(cohort_members=[{"entity_id": "S", "relative_fragility_score": 60}]))
    assert single["ranked_entities"][0]["percentile"] == 100
    assert "SINGLE_MEMBER_COHORT" in single["ranked_entities"][0]["quality_flags"]
    assert assign_percentile_ranking_tiers(89) == "ELEVATED_FRAGILITY_PERCENTILE"
    assert assign_percentile_ranking_tiers(74) == "MODERATE_FRAGILITY_PERCENTILE"
    assert assign_percentile_ranking_tiers(49) == "LOWER_FRAGILITY_PERCENTILE"
    assert assign_percentile_ranking_tiers(24) == "RELATIVE_STRENGTH_PERCENTILE"


def test_blocking_validation_cases_and_duplicates():
    assert certify_percentile_ranking_engine(_payload(cohort_id=""))["decision_status"] == BLOCKED_RELATIVE_RANKING
    assert certify_percentile_ranking_engine(_payload(cohort_members=[{"entity_id": "", "relative_fragility_score": 1}]))["decision_status"] == BLOCKED_RELATIVE_RANKING
    assert certify_percentile_ranking_engine(_payload(cohort_members=[{"entity_id": "A"}]))["decision_status"] == BLOCKED_RELATIVE_RANKING
    dup = _payload(cohort_members=[{"entity_id": "A", "relative_fragility_score": 60}, {"entity_id": "A", "relative_fragility_score": 30}])
    assert certify_percentile_ranking_engine(dup)["decision_status"] == BLOCKED_RELATIVE_RANKING


def test_degraded_optional_tie_breakers_and_clamping_and_explanations():
    payload = _payload(cohort_members=[{"entity_id": "A", "relative_fragility_score": 999, "persistence_weakness_divergence": None, "deterioration_velocity_divergence": 5, "benchmark_divergence": 5}])
    out = build_deterministic_cohort_ranking(payload)
    row = out["ranked_entities"][0]
    assert row["relative_fragility_score"] == 100
    assert "CLAMPED_RELATIVE_FRAGILITY_SCORE" in row["quality_flags"]
    assert "rank_explanation" in row and "ranking_driver_summary" in row
    cert = certify_percentile_ranking_engine(payload, out)
    assert cert["decision_status"] == DEGRADED_RELATIVE_RANKING


def test_certified_status_forbidden_inventory_and_report_smoke():
    payload = _payload()
    out = build_deterministic_cohort_ranking(payload)
    cert = certify_percentile_ranking_engine(payload, out)
    assert cert["decision_status"] == CERTIFIED_RELATIVE_RANKING
    assert "dynamic_cohort_creation" in cert["forbidden_capability_inventory"]
    report = build_path2c_percentile_ranking_report(payload)
    assert report["path_id"] == "P2-C"
    assert report["final_supervisor_interpretation"]
