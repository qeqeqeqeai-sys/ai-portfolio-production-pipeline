from pathlib import Path

from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import certify_phase_a_observational_expansion_boundary
from transmission_layers.expectation_failure.phase_a4_narrative_saturation_replay_recurrence_pressure import *


def test_api_existence_and_determinism():
    apis = [
        build_phase_a4_narrative_saturation_configuration,
        build_phase_a4_narrative_saturation_pressure_measurement,
        build_phase_a4_replay_recurrence_pressure_measurement,
        build_phase_a4_contradiction_recurrence_density_measurement,
        build_phase_a4_semantic_crowding_measurement,
        build_phase_a4_novelty_decay_risk_measurement,
        build_phase_a4_structural_redundancy_measurement,
        build_phase_a4_replay_path_repetition_measurement,
        build_phase_a4_contradiction_exhaustion_risk_measurement,
        build_phase_a4_saturation_recurrence_composite_score,
        build_phase_a4_supervisor_review,
        build_phase_a4_markdown_report,
    ]
    for fn in apis:
        assert callable(fn)

    assert build_phase_a4_narrative_saturation_configuration() == build_phase_a4_narrative_saturation_configuration()
    assert build_phase_a4_narrative_saturation_pressure_measurement() == build_phase_a4_narrative_saturation_pressure_measurement()
    assert build_phase_a4_replay_recurrence_pressure_measurement() == build_phase_a4_replay_recurrence_pressure_measurement()
    assert build_phase_a4_contradiction_recurrence_density_measurement() == build_phase_a4_contradiction_recurrence_density_measurement()
    assert build_phase_a4_semantic_crowding_measurement() == build_phase_a4_semantic_crowding_measurement()
    assert build_phase_a4_novelty_decay_risk_measurement() == build_phase_a4_novelty_decay_risk_measurement()
    assert build_phase_a4_structural_redundancy_measurement() == build_phase_a4_structural_redundancy_measurement()
    assert build_phase_a4_replay_path_repetition_measurement() == build_phase_a4_replay_path_repetition_measurement()
    assert build_phase_a4_contradiction_exhaustion_risk_measurement() == build_phase_a4_contradiction_exhaustion_risk_measurement()
    assert build_phase_a4_saturation_recurrence_composite_score() == build_phase_a4_saturation_recurrence_composite_score()


def test_measurement_shape_and_composite_fields():
    m = build_phase_a4_narrative_saturation_pressure_measurement()
    for k in ["metric_name", "deterministic_inputs_used", "measurement_value", "interpretation", "replay_ecology_risk", "mitigation_guidance", "governance_status"]:
        assert k in m

    comp = build_phase_a4_saturation_recurrence_composite_score()
    for k in ["score", "band", "strongest_pressure_dimension", "weakest_pressure_dimension", "caveats", "recommended_next_phase_action", "subcomponent_scores"]:
        assert k in comp


def test_supervisor_review_shape_and_governance_boundary_unchanged():
    review = build_phase_a4_supervisor_review()
    assert review["phase"] == "A4"
    assert review["governance_boundary"] == certify_phase_a_observational_expansion_boundary()


def test_markdown_report_sections_and_saved_file():
    md = build_phase_a4_markdown_report().lower()
    expected = [
        "objective", "relationship to a3", "observational-only boundary", "measurement methodology",
        "narrative saturation pressure", "replay recurrence pressure", "contradiction recurrence density",
        "semantic crowding", "novelty decay risk", "structural redundancy", "replay path repetition",
        "contradiction exhaustion risk", "saturation recurrence composite score", "governance preservation",
        "residual risks", "recommendation for phase a5 or b1",
    ]
    for s in expected:
        assert s in md
    saved = Path("reports/phase_a4_narrative_saturation_replay_recurrence_pressure.md").read_text(encoding="utf-8").lower()
    for s in expected:
        assert s in saved


def test_no_operationalization_or_sql_or_prediction_paths_introduced():
    src = Path("transmission_layers/expectation_failure/phase_a4_narrative_saturation_replay_recurrence_pressure.py").read_text(encoding="utf-8").lower()
    blocked = [
        "supabase", "insert(", "update(", "delete(", "create table", "alter table", "select *",
        "http://", "https://", "requests.",
    ]
    for token in blocked:
        assert token not in src


def test_governance_flags_disallow_prediction_trading_and_activation():
    g = build_phase_a4_supervisor_review()["governance_boundary"]
    assert g["prediction_enabled"] is False
    assert g["trading_enabled"] is False
    assert g["topology_activation_enabled"] is False
    assert g["replay_operationalization_enabled"] is False

