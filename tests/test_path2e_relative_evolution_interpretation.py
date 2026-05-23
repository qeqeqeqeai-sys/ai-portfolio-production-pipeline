from copy import deepcopy

from transmission_layers.expectation_failure import (
    BLOCKED_RELATIVE_EVOLUTION,
    CERTIFIED_RELATIVE_EVOLUTION,
    DEGRADED_RELATIVE_EVOLUTION,
    build_path2e_relative_evolution_report,
    build_relative_evolution_input_contract,
    build_relative_evolution_narrative,
    build_relative_position_timeline,
    certify_relative_evolution_interpretation,
    interpret_benchmark_divergence_trend,
    interpret_percentile_movement,
    interpret_rank_migration,
    interpret_relative_deterioration_acceleration,
    interpret_relative_weakness_persistence,
)
from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import build_cohort_registry_contracts
from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import build_relative_fragility_input_contract
from transmission_layers.expectation_failure.path2c_percentile_ranking_engine import build_percentile_ranking_input_contract
from transmission_layers.expectation_failure.path2d_benchmark_divergence_intelligence import build_benchmark_divergence_input_contract
from transmission_layers.expectation_failure.phase_a1_contracts import build_expectation_failure_score_contracts


def _payload(**overrides):
    base = {
        "entity_id": "E1",
        "cohort_id": "C1",
        "cohort_version": "1.0",
        "replay_window_id": "RW1",
        "timeline": [
            {"sequence_id": "t0", "rank": 2, "percentile": 40, "benchmark_divergence_score": 20, "relative_fragility_score": 45},
            {"sequence_id": "t1", "rank": 3, "percentile": 50, "benchmark_divergence_score": 35, "relative_fragility_score": 72},
            {"sequence_id": "t2", "rank": 5, "percentile": 70, "benchmark_divergence_score": 50, "relative_fragility_score": 85},
        ],
    }
    base.update(overrides)
    return base


def test_public_api_export_presence_and_smoke_imports():
    assert build_relative_evolution_input_contract()["path_id"] == "P2-E"
    assert build_cohort_registry_contracts()["path_id"] == "P2-A"
    assert build_relative_fragility_input_contract()["path_id"] == "P2-B"
    assert build_percentile_ranking_input_contract()["path_id"] == "P2-C"
    assert build_benchmark_divergence_input_contract()["path_id"] == "P2-D"
    assert isinstance(build_expectation_failure_score_contracts(), list)


def test_deterministic_output_checksum_stability_and_input_immutability():
    p = _payload()
    snapshot = deepcopy(p)
    one = certify_relative_evolution_interpretation(p)
    two = certify_relative_evolution_interpretation(p)
    assert p == snapshot
    assert one["output"] == two["output"]
    assert one["output"]["checksum"] == two["output"]["checksum"]


def test_timeline_ordering_and_rank_percentile_benchmark_interpretations():
    p = _payload(timeline=list(reversed(_payload()["timeline"])))
    timeline_info = build_relative_position_timeline(p)
    assert timeline_info["timeline"][0]["sequence_id"] == "t0"
    assert interpret_rank_migration(timeline_info["timeline"])["movement"] == "WORSENING"
    assert interpret_percentile_movement(timeline_info["timeline"])["movement"] == "WORSENING"
    assert interpret_benchmark_divergence_trend(timeline_info["timeline"])["trend"] == "WORSENING"


def test_rank_and_percentile_improving_and_stable_cases():
    improving = [{"sequence_id": "a", "rank": 5, "percentile": 80, "benchmark_divergence_score": 30}, {"sequence_id": "b", "rank": 2, "percentile": 40, "benchmark_divergence_score": 10}]
    stable = [{"sequence_id": "a", "rank": 3, "percentile": 50, "benchmark_divergence_score": 10}, {"sequence_id": "b", "rank": 3, "percentile": 50, "benchmark_divergence_score": 10}]
    assert interpret_rank_migration(improving)["movement"] == "IMPROVING"
    assert interpret_percentile_movement(improving)["movement"] == "IMPROVING"
    assert interpret_rank_migration(stable)["movement"] == "STABLE"
    assert interpret_percentile_movement(stable)["movement"] == "STABLE"


def test_acceleration_and_persistence_interpretations():
    t = _payload()["timeline"]
    accel = interpret_relative_deterioration_acceleration(t)
    assert accel["acceleration"] == "ACCELERATING_WORSENING"
    persistence = interpret_relative_weakness_persistence(t)
    assert persistence["classification"] in {"MODERATE_PERSISTENCE", "HIGH_PERSISTENCE"}


def test_single_point_timeline_degrades_not_crashes_and_missing_optional_metric_degrades():
    single = certify_relative_evolution_interpretation(_payload(timeline=[{"sequence_id": "t0", "rank": 3, "percentile": 60, "benchmark_divergence_score": 20}]))
    assert single["decision_status"] == DEGRADED_RELATIVE_EVOLUTION
    missing_optional = certify_relative_evolution_interpretation(_payload(timeline=[{"sequence_id": "t0", "rank": 2, "percentile": 30, "benchmark_divergence_score": 10}, {"sequence_id": "t1", "rank": 3, "percentile": 45, "benchmark_divergence_score": 20}]))
    assert missing_optional["decision_status"] == DEGRADED_RELATIVE_EVOLUTION


def test_missing_required_fields_blocking():
    assert certify_relative_evolution_interpretation(_payload(entity_id=""))["decision_status"] == BLOCKED_RELATIVE_EVOLUTION
    assert certify_relative_evolution_interpretation(_payload(cohort_id=""))["decision_status"] == BLOCKED_RELATIVE_EVOLUTION
    assert certify_relative_evolution_interpretation(_payload(replay_window_id=""))["decision_status"] == BLOCKED_RELATIVE_EVOLUTION


def test_narrative_completeness_and_status_outcomes_and_forbidden_inventory():
    cert = certify_relative_evolution_interpretation(_payload())
    assert cert["decision_status"] == CERTIFIED_RELATIVE_EVOLUTION
    out = cert["output"]
    assert out["relative_evolution_narrative"] == build_relative_evolution_narrative(out)
    assert "coverage=" in out["relative_evolution_narrative"]
    assert "network_api_calls" in cert["forbidden_capability_inventory"]


def test_report_builder_smoke():
    report = build_path2e_relative_evolution_report(_payload())
    assert report["path_id"] == "P2-E"
