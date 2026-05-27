from pathlib import Path

from transmission_layers.expectation_failure import phase_a11_recursive_replay_ecology_cascade_interaction_wavefront_competition_research as mod


REQUIRED_KEYS = {
    "model_name",
    "research_objective",
    "deterministic_inputs_used",
    "recursive_cascade_signals",
    "wavefront_interaction_signals",
    "interaction_effect",
    "containment_effect",
    "recursive_risk",
    "exhaustion_constraint",
    "governance_status",
}


def test_api_existence() -> None:
    required = [
        "build_phase_a11_recursive_cascade_configuration",
        "build_phase_a11_recursive_cascade_propagation_model",
        "build_phase_a11_wavefront_competition_model",
        "build_phase_a11_secondary_cascade_formation_model",
        "build_phase_a11_attractor_competition_model",
        "build_phase_a11_basin_interference_model",
        "build_phase_a11_propagation_recursion_model",
        "build_phase_a11_topology_memory_accumulation_model",
        "build_phase_a11_stabilization_exhaustion_model",
        "build_phase_a11_nonlinear_cascade_synchronization_model",
        "build_phase_a11_recursive_cascade_risk_review",
        "build_phase_a11_cascade_interaction_scorecard",
        "build_phase_a11_supervisor_review",
        "build_phase_a11_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name), name


def test_deterministic_outputs() -> None:
    assert mod.build_phase_a11_supervisor_review() == mod.build_phase_a11_supervisor_review()
    assert mod.build_phase_a11_cascade_interaction_scorecard() == mod.build_phase_a11_cascade_interaction_scorecard()
    assert mod.build_phase_a11_markdown_report() == mod.build_phase_a11_markdown_report()


def test_model_output_shape() -> None:
    builders = [
        mod.build_phase_a11_recursive_cascade_propagation_model,
        mod.build_phase_a11_wavefront_competition_model,
        mod.build_phase_a11_secondary_cascade_formation_model,
        mod.build_phase_a11_attractor_competition_model,
        mod.build_phase_a11_basin_interference_model,
        mod.build_phase_a11_propagation_recursion_model,
        mod.build_phase_a11_topology_memory_accumulation_model,
        mod.build_phase_a11_stabilization_exhaustion_model,
        mod.build_phase_a11_nonlinear_cascade_synchronization_model,
    ]
    for builder in builders:
        assert REQUIRED_KEYS.issubset(builder().keys())


def test_governance_boundary_unchanged() -> None:
    gov = mod.build_phase_a11_recursive_cascade_configuration()["governance_status"]
    assert gov["observational_expansion_only"] is True
    assert gov["replay_execution_permitted"] is False
    assert gov["topology_execution_permitted"] is False
    assert gov["live_api_calls_permitted"] is False
    assert gov["execution_workflow_permitted"] is False


def test_scorecard_shape() -> None:
    sc = mod.build_phase_a11_cascade_interaction_scorecard()
    expected = {
        "recursive_cascade_containment",
        "wavefront_competition_resilience",
        "secondary_cascade_resistance",
        "attractor_competition_stability",
        "basin_interference_resistance",
        "propagation_recursion_resistance",
        "topology_memory_reversibility",
        "stabilization_exhaustion_resilience",
        "cascade_synchronization_resistance",
        "overall_recursive_cascade_resilience",
        "governance_status",
    }
    assert expected.issubset(sc.keys())


def test_supervisor_review_shape() -> None:
    review = mod.build_phase_a11_supervisor_review()
    expected = {
        "overall_recursive_cascade_resilience",
        "dominant_recursive_dynamic",
        "strongest_containment_dimension",
        "weakest_containment_dimension",
        "primary_recursive_cascade_risk",
        "replay_operationalization_readiness",
        "replay_density_scaling_readiness",
        "b1_transition_readiness",
        "recommended_next_phase_action",
        "governance_status",
    }
    assert expected.issubset(review.keys())


def test_markdown_report_sections_present() -> None:
    text = Path("reports/phase_a11_recursive_replay_ecology_cascade_interaction_wavefront_competition_research.md").read_text().lower()
    for section in [
        "## objective",
        "## relationship to a10",
        "## observational-only boundary",
        "## recursive cascade research methodology",
        "## recursive cascade propagation model",
        "## wavefront competition model",
        "## secondary cascade formation model",
        "## attractor competition model",
        "## basin interference model",
        "## propagation recursion model",
        "## topology memory accumulation model",
        "## stabilization exhaustion model",
        "## nonlinear cascade synchronization model",
        "## recursive cascade risk review",
        "## cascade interaction scorecard",
        "## supervisor interpretation",
        "## governance preservation",
        "## residual risks",
        "## recommendation regarding b1",
        "a11 models deterministic structural recursive cascade behavior rather than realistic replay execution dynamics.",
    ]:
        assert section in text


def test_static_negative_checks() -> None:
    text = Path("transmission_layers/expectation_failure/phase_a11_recursive_replay_ecology_cascade_interaction_wavefront_competition_research.py").read_text().lower()
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


def test_recursive_cascade_consistency() -> None:
    review = mod.build_phase_a11_supervisor_review()
    assert review["replay_operationalization_readiness"] == "blocked"
    assert review["b1_transition_readiness"] == "blocked"

    risk = mod.build_phase_a11_recursive_cascade_risk_review()
    assert risk["operational_replay_readiness_status"] != "ready"
    assert risk["b1_transition_readiness_status"] == "blocked"

    exhaustion = mod.build_phase_a11_stabilization_exhaustion_model()
    assert "exhaust" in exhaustion["recursive_risk"]

    memory = mod.build_phase_a11_topology_memory_accumulation_model()
    assert "memory" in memory["model_name"]
    assert "memory" in memory["recursive_risk"]

    sync = mod.build_phase_a11_nonlinear_cascade_synchronization_model()
    assert "bounded" in sync["recursive_risk"]
    assert "synchron" in sync["interaction_effect"]
