from pathlib import Path

from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import (
    certify_phase_a_observational_expansion_boundary,
)
from transmission_layers.expectation_failure.phase_a3_derived_replay_ecology_measurement import *


def test_api_existence():
    required = [
        build_phase_a3_replay_ecology_measurement_configuration,
        build_phase_a3_topology_entropy_measurement,
        build_phase_a3_contradiction_entropy_measurement,
        build_phase_a3_propagation_diversity_measurement,
        build_phase_a3_hub_concentration_measurement,
        build_phase_a3_replay_overlap_risk_measurement,
        build_phase_a3_monoculture_pressure_measurement,
        build_phase_a3_weak_node_amplification_measurement,
        build_phase_a3_structural_balance_score,
        build_phase_a3_replay_ecology_measurement_summary,
        build_phase_a3_supervisor_review,
        build_phase_a3_markdown_report,
    ]
    assert all(callable(x) for x in required)


def test_determinism_all_metrics_and_configuration():
    assert build_phase_a3_replay_ecology_measurement_configuration() == build_phase_a3_replay_ecology_measurement_configuration()
    assert build_phase_a3_topology_entropy_measurement() == build_phase_a3_topology_entropy_measurement()
    assert build_phase_a3_contradiction_entropy_measurement() == build_phase_a3_contradiction_entropy_measurement()
    assert build_phase_a3_propagation_diversity_measurement() == build_phase_a3_propagation_diversity_measurement()
    assert build_phase_a3_hub_concentration_measurement() == build_phase_a3_hub_concentration_measurement()
    assert build_phase_a3_replay_overlap_risk_measurement() == build_phase_a3_replay_overlap_risk_measurement()
    assert build_phase_a3_monoculture_pressure_measurement() == build_phase_a3_monoculture_pressure_measurement()
    assert build_phase_a3_weak_node_amplification_measurement() == build_phase_a3_weak_node_amplification_measurement()
    assert build_phase_a3_structural_balance_score() == build_phase_a3_structural_balance_score()


def test_measurement_shape_and_supervisor_review():
    m = build_phase_a3_topology_entropy_measurement()
    for k in ["metric_name", "deterministic_inputs_used", "measurement_value", "interpretation", "replay_ecology_risk", "mitigation_guidance", "governance_status"]:
        assert k in m
    review = build_phase_a3_supervisor_review()
    assert set(["phase", "status", "measurement_count", "structural_balance_score", "governance_boundary"]).issubset(review.keys())


def test_markdown_report_sections_present():
    md = build_phase_a3_markdown_report().lower()
    for section in [
        "objective", "relationship to a2", "observational-only boundary", "measurement methodology",
        "topology entropy measurement", "contradiction entropy measurement", "propagation diversity measurement",
        "hub concentration measurement", "replay overlap risk measurement", "monoculture pressure measurement",
        "weak-node amplification measurement", "structural balance score", "governance preservation",
        "residual risks", "recommendation for phase a4 or b1",
    ]:
        assert f"## {section}" in md


def test_governance_boundary_unchanged_and_restricted_paths_absent():
    expected = certify_phase_a_observational_expansion_boundary()
    summary = build_phase_a3_replay_ecology_measurement_summary()
    assert summary["governance_boundary"] == expected
    assert expected["replay_operationalization_enabled"] is False
    assert expected["topology_activation_enabled"] is False
    assert expected["autonomous_replay_activation_enabled"] is False
    assert expected["schema_expansion_enabled"] is False
    assert expected["direct_sql_allowed"] is False
    assert expected["prediction_enabled"] is False
    assert expected["trading_enabled"] is False

    src = Path("transmission_layers/expectation_failure/phase_a3_derived_replay_ecology_measurement.py").read_text(encoding="utf-8").lower()
    banned = ["supabase", "insert into", "update ", "delete from", "from supabase", "sql", "predict", "trading", "topology_activation_enabled = true"]
    assert all(token not in src for token in banned)
