from copy import deepcopy
from pathlib import Path

from transmission_layers.expectation_failure import (
    build_cross_sectional_explainability_input_contract,
    build_peer_relative_explanation,
    build_percentile_ranking_explanation,
    build_benchmark_divergence_explanation_packet,
    build_relative_evolution_explanation_packet,
    build_driver_attribution_hierarchy,
    build_structural_evidence_summary,
    validate_explainability_consistency,
    certify_cross_sectional_explainability,
    build_path2f_cross_sectional_explainability_report,
)
from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import build_cohort_registry_contracts
from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import build_relative_fragility_input_contract
from transmission_layers.expectation_failure.path2c_percentile_ranking_engine import build_percentile_ranking_input_contract
from transmission_layers.expectation_failure.path2d_benchmark_divergence_intelligence import build_benchmark_divergence_input_contract
from transmission_layers.expectation_failure.path2e_relative_evolution_interpretation import build_relative_evolution_input_contract
from transmission_layers.expectation_failure.real_data.t1_temporal_snapshot_sequencing import build_temporal_snapshot_sequence


def _payload():
    return {
        "entity_id": "E1",
        "cohort_id": "C1",
        "cohort_version": "V1",
        "benchmark_id": "B1",
        "explanation_version": "1.0.0",
        "relative_fragility": {"relative_fragility_score": 82.0},
        "percentile_ranking": {"percentile": 91.5, "rank": 9, "cohort_size": 100},
        "benchmark_divergence": {"benchmark_divergence_score": 2.75},
        "relative_evolution": {
            "relative_evolution_direction": "WORSENING",
            "rank_migration": {"movement": "WORSENING", "delta": 2.0},
            "percentile_movement": {"movement": "WORSENING", "delta": 1.2},
            "benchmark_divergence_trend": {"trend": "WORSENING", "delta": 0.4},
            "relative_weakness_persistence": {"coverage_ratio": 0.8},
            "relative_deterioration_acceleration": {"delta_change": 0.6},
        },
        "quality_flags": [],
        "replay_metadata": {"path1_snapshot_id": "S1", "input_immutability_preserved": True},
    }


def test_public_api_export_presence():
    assert callable(build_cross_sectional_explainability_input_contract)
    assert callable(build_path2f_cross_sectional_explainability_report)


def test_deterministic_repeated_output_and_checksum_stability_and_immutability():
    payload = _payload()
    baseline = deepcopy(payload)
    r1 = certify_cross_sectional_explainability(payload)
    r2 = certify_cross_sectional_explainability(payload)
    assert r1 == r2
    assert r1["checksum"] == r2["checksum"]
    assert payload == baseline


def test_explanation_component_generation_and_hierarchy_and_summary():
    payload = _payload()
    assert "Peer-relative" in build_peer_relative_explanation(payload)
    assert "Percentile" in build_percentile_ranking_explanation(payload)
    assert "Benchmark divergence" in build_benchmark_divergence_explanation_packet(payload)
    assert "Relative evolution" in build_relative_evolution_explanation_packet(payload)
    hierarchy = build_driver_attribution_hierarchy(payload)
    assert hierarchy["primary_driver"] == "percentile"
    assert hierarchy["secondary_driver"] == "relative_fragility_score"
    summary = build_structural_evidence_summary(payload)
    assert "relative_fragility_score" in summary and "benchmark_divergence_trend_delta" in summary


def test_consistency_validation_and_certification_outcomes():
    certified = certify_cross_sectional_explainability(_payload())
    checks = validate_explainability_consistency(certified)
    assert checks["explanation_consistency_validated"] is True
    assert certified["certification_decision"] == "CERTIFIED_CROSS_SECTIONAL_EXPLAINABILITY"

    degraded_payload = _payload()
    degraded_payload["quality_flags"] = ["MISSING_OPTIONAL"]
    degraded = certify_cross_sectional_explainability(degraded_payload)
    assert degraded["certification_decision"] == "DEGRADED_CROSS_SECTIONAL_EXPLAINABILITY"

    blocked_entity = _payload()
    blocked_entity["entity_id"] = ""
    assert certify_cross_sectional_explainability(blocked_entity)["certification_decision"] == "BLOCKED_CROSS_SECTIONAL_EXPLAINABILITY"

    blocked_cohort = _payload()
    blocked_cohort["cohort_id"] = ""
    assert certify_cross_sectional_explainability(blocked_cohort)["certification_decision"] == "BLOCKED_CROSS_SECTIONAL_EXPLAINABILITY"

    blocked_version = _payload()
    blocked_version["explanation_version"] = ""
    assert certify_cross_sectional_explainability(blocked_version)["certification_decision"] == "BLOCKED_CROSS_SECTIONAL_EXPLAINABILITY"


def test_forbidden_capabilities_contract_inventory_and_report_builder_smoke():
    contract = build_cross_sectional_explainability_input_contract()
    forbidden = contract["forbidden_capabilities"]
    assert "trading_signals" in forbidden
    assert "dynamic_benchmark_creation" in forbidden
    path = build_path2f_cross_sectional_explainability_report()
    assert Path(path).exists()


def test_path2_import_smoke_and_path1_non_regression_imports():
    assert isinstance(build_cohort_registry_contracts(), dict)
    assert isinstance(build_relative_fragility_input_contract(), dict)
    assert isinstance(build_percentile_ranking_input_contract(), dict)
    assert isinstance(build_benchmark_divergence_input_contract(), dict)
    assert isinstance(build_relative_evolution_input_contract(), dict)
    assert isinstance(build_temporal_snapshot_sequence([]), dict)
