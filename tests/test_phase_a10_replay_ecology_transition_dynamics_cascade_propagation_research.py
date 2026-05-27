from pathlib import Path

from transmission_layers.expectation_failure import phase_a10_replay_ecology_transition_dynamics_cascade_propagation_research as mod


REQUIRED_KEYS = {
    "model_name",
    "research_objective",
    "deterministic_inputs_used",
    "transition_dynamics_signals",
    "cascade_propagation_signals",
    "acceleration_effect",
    "containment_effect",
    "propagation_risk",
    "recovery_constraint",
    "governance_status",
}


def test_api_existence() -> None:
    required = [
        "build_phase_a10_transition_dynamics_configuration",
        "build_phase_a10_transition_velocity_model",
        "build_phase_a10_metastability_decay_model",
        "build_phase_a10_cascade_topology_sequence_model",
        "build_phase_a10_bifurcation_acceleration_model",
        "build_phase_a10_collapse_wavefront_model",
        "build_phase_a10_stabilization_latency_model",
        "build_phase_a10_attractor_recapture_model",
        "build_phase_a10_irreversible_topology_drift_model",
        "build_phase_a10_recovery_asymmetry_model",
        "build_phase_a10_cascade_propagation_risk_review",
        "build_phase_a10_transition_dynamics_scorecard",
        "build_phase_a10_supervisor_review",
        "build_phase_a10_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name), name


def test_deterministic_outputs() -> None:
    assert mod.build_phase_a10_supervisor_review() == mod.build_phase_a10_supervisor_review()
    assert mod.build_phase_a10_transition_dynamics_scorecard() == mod.build_phase_a10_transition_dynamics_scorecard()
    assert mod.build_phase_a10_markdown_report() == mod.build_phase_a10_markdown_report()


def test_model_output_shape() -> None:
    builders = [
        mod.build_phase_a10_transition_velocity_model,
        mod.build_phase_a10_metastability_decay_model,
        mod.build_phase_a10_cascade_topology_sequence_model,
        mod.build_phase_a10_bifurcation_acceleration_model,
        mod.build_phase_a10_collapse_wavefront_model,
        mod.build_phase_a10_stabilization_latency_model,
        mod.build_phase_a10_attractor_recapture_model,
        mod.build_phase_a10_irreversible_topology_drift_model,
        mod.build_phase_a10_recovery_asymmetry_model,
    ]
    for builder in builders:
        assert REQUIRED_KEYS.issubset(builder().keys())


def test_governance_boundary_unchanged() -> None:
    gov = mod.build_phase_a10_transition_dynamics_configuration()["governance_status"]
    assert gov["observational_expansion_only"] is True
    assert gov["replay_execution_permitted"] is False
    assert gov["topology_execution_permitted"] is False
    assert gov["live_api_calls_permitted"] is False
    assert gov["execution_workflow_permitted"] is False


def test_scorecard_shape() -> None:
    sc = mod.build_phase_a10_transition_dynamics_scorecard()
    expected = {
        "transition_velocity_containment",
        "metastability_decay_resistance",
        "cascade_sequence_containment",
        "bifurcation_acceleration_resistance",
        "collapse_wavefront_containment",
        "stabilization_latency_resilience",
        "attractor_recapture_resistance",
        "topology_drift_reversibility",
        "recovery_symmetry_strength",
        "overall_transition_dynamics_resilience",
        "governance_status",
    }
    assert expected.issubset(sc.keys())


def test_supervisor_review_shape() -> None:
    review = mod.build_phase_a10_supervisor_review()
    expected = {
        "overall_transition_dynamics_resilience",
        "dominant_transition_dynamic",
        "strongest_containment_dimension",
        "weakest_containment_dimension",
        "primary_cascade_risk",
        "replay_operationalization_readiness",
        "replay_density_scaling_readiness",
        "b1_transition_readiness",
        "recommended_next_phase_action",
        "governance_status",
    }
    assert expected.issubset(review.keys())


def test_markdown_report_sections_present() -> None:
    text = Path("reports/phase_a10_replay_ecology_transition_dynamics_cascade_propagation_research.md").read_text().lower()
    for section in [
        "## objective",
        "## relationship to a9",
        "## observational-only boundary",
        "## transition dynamics research methodology",
        "## transition velocity model",
        "## metastability decay model",
        "## cascade topology sequence model",
        "## bifurcation acceleration model",
        "## collapse wavefront model",
        "## stabilization latency model",
        "## attractor recapture model",
        "## irreversible topology drift model",
        "## recovery asymmetry model",
        "## cascade propagation risk review",
        "## transition dynamics scorecard",
        "## supervisor interpretation",
        "## governance preservation",
        "## residual risks",
        "## recommendation regarding b1",
        "a10 models deterministic structural transition dynamics rather than realistic replay execution dynamics.",
    ]:
        assert section in text


def test_static_negative_checks() -> None:
    text = Path("transmission_layers/expectation_failure/phase_a10_replay_ecology_transition_dynamics_cascade_propagation_research.py").read_text().lower()
    forbidden = [
        "supabase",
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import sqlite",
        "import sqlalchemy",
        "from sqlalchemy",
        ".execute(",
        "replay_execution_enabled = true",
        "topology_activation_enabled = true",
        "prediction_enabled = true",
        "trading_enabled = true",
    ]
    for token in forbidden:
        assert token not in text


def test_transition_dynamics_consistency() -> None:
    review = mod.build_phase_a10_supervisor_review()
    assert review["replay_operationalization_readiness"] == "blocked"
    assert review["b1_transition_readiness"] == "blocked"

    risk = mod.build_phase_a10_cascade_propagation_risk_review()
    assert risk["operational_replay_readiness_status"] != "ready"
    assert risk["b1_transition_readiness_status"] == "blocked"

    asymmetry = mod.build_phase_a10_recovery_asymmetry_model()
    assert asymmetry["model_name"] == "recovery_asymmetry"
    assert "stronger" in asymmetry["recovery_constraint"]

    latency = mod.build_phase_a10_stabilization_latency_model()
    assert "lagging_response" in latency["propagation_risk"]

    drift = mod.build_phase_a10_irreversible_topology_drift_model()
    assert "bounded" in drift["recovery_constraint"]
    assert "irreversible_drift_risk" in drift["propagation_risk"]
