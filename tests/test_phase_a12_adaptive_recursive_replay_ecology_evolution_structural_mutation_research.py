from pathlib import Path

from transmission_layers.expectation_failure import phase_a12_adaptive_recursive_replay_ecology_evolution_structural_mutation_research as mod


REQUIRED_KEYS = {
    "model_name",
    "research_objective",
    "deterministic_inputs_used",
    "mutation_signals",
    "adaptive_evolution_signals",
    "mutation_effect",
    "containment_effect",
    "mutation_risk",
    "reversibility_constraint",
    "governance_status",
}


def test_api_existence() -> None:
    required = [
        "build_phase_a12_structural_mutation_configuration",
        "build_phase_a12_recursive_topology_mutation_model",
        "build_phase_a12_adaptive_propagation_evolution_model",
        "build_phase_a12_recursive_attractor_adaptation_model",
        "build_phase_a12_synchronization_mutation_cascade_model",
        "build_phase_a12_evolving_topology_memory_model",
        "build_phase_a12_recursive_stabilization_degradation_model",
        "build_phase_a12_self_modifying_corridor_model",
        "build_phase_a12_mutation_driven_cascade_acceleration_model",
        "build_phase_a12_structural_mutation_persistence_model",
        "build_phase_a12_mutation_reversibility_limit_model",
        "build_phase_a12_structural_mutation_risk_review",
        "build_phase_a12_evolution_mutation_scorecard",
        "build_phase_a12_supervisor_review",
        "build_phase_a12_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name), name


def test_deterministic_outputs() -> None:
    assert mod.build_phase_a12_supervisor_review() == mod.build_phase_a12_supervisor_review()
    assert mod.build_phase_a12_evolution_mutation_scorecard() == mod.build_phase_a12_evolution_mutation_scorecard()
    assert mod.build_phase_a12_markdown_report() == mod.build_phase_a12_markdown_report()


def test_model_output_shape() -> None:
    builders = [
        mod.build_phase_a12_recursive_topology_mutation_model,
        mod.build_phase_a12_adaptive_propagation_evolution_model,
        mod.build_phase_a12_recursive_attractor_adaptation_model,
        mod.build_phase_a12_synchronization_mutation_cascade_model,
        mod.build_phase_a12_evolving_topology_memory_model,
        mod.build_phase_a12_recursive_stabilization_degradation_model,
        mod.build_phase_a12_self_modifying_corridor_model,
        mod.build_phase_a12_mutation_driven_cascade_acceleration_model,
        mod.build_phase_a12_structural_mutation_persistence_model,
        mod.build_phase_a12_mutation_reversibility_limit_model,
    ]
    for builder in builders:
        assert REQUIRED_KEYS.issubset(builder().keys())


def test_governance_boundary_unchanged() -> None:
    gov = mod.build_phase_a12_structural_mutation_configuration()["governance_status"]
    assert gov["observational_expansion_only"] is True
    assert gov["replay_execution_permitted"] is False
    assert gov["topology_execution_permitted"] is False
    assert gov["live_api_calls_permitted"] is False
    assert gov["execution_workflow_permitted"] is False


def test_scorecard_shape() -> None:
    sc = mod.build_phase_a12_evolution_mutation_scorecard()
    expected = {
        "topology_mutation_containment",
        "propagation_evolution_resistance",
        "attractor_adaptation_resistance",
        "synchronization_mutation_resistance",
        "topology_memory_reversibility",
        "stabilization_degradation_resistance",
        "corridor_self_modification_resistance",
        "mutation_acceleration_resistance",
        "structural_persistence_containment",
        "mutation_reversibility_strength",
        "overall_structural_mutation_resilience",
        "governance_status",
    }
    assert expected.issubset(sc.keys())


def test_supervisor_review_shape() -> None:
    review = mod.build_phase_a12_supervisor_review()
    expected = {
        "overall_structural_mutation_resilience",
        "dominant_mutation_dynamic",
        "strongest_containment_dimension",
        "weakest_reversibility_dimension",
        "primary_mutation_risk",
        "replay_operationalization_readiness",
        "replay_density_scaling_readiness",
        "b1_transition_readiness",
        "recommended_next_phase_action",
        "governance_status",
    }
    assert expected.issubset(review.keys())


def test_markdown_report_sections_present() -> None:
    text = Path("reports/phase_a12_adaptive_recursive_replay_ecology_evolution_structural_mutation_research.md").read_text().lower()
    for section in [
        "## objective",
        "## relationship to a11",
        "## observational-only boundary",
        "## structural mutation research methodology",
        "## recursive topology mutation model",
        "## adaptive propagation evolution model",
        "## recursive attractor adaptation model",
        "## synchronization mutation cascade model",
        "## evolving topology memory model",
        "## recursive stabilization degradation model",
        "## self-modifying corridor model",
        "## mutation-driven cascade acceleration model",
        "## structural mutation persistence model",
        "## mutation reversibility limit model",
        "## structural mutation risk review",
        "## evolution mutation scorecard",
        "## supervisor interpretation",
        "## governance preservation",
        "## residual risks",
        "## recommendation regarding b1",
        "a12 models deterministic structural mutation behavior rather than realistic replay execution dynamics.",
    ]:
        assert section in text


def test_static_negative_checks() -> None:
    text = Path("transmission_layers/expectation_failure/phase_a12_adaptive_recursive_replay_ecology_evolution_structural_mutation_research.py").read_text().lower()
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


def test_structural_mutation_consistency() -> None:
    review = mod.build_phase_a12_supervisor_review()
    assert review["replay_operationalization_readiness"] == "blocked"
    assert review["b1_transition_readiness"] == "blocked"

    risk = mod.build_phase_a12_structural_mutation_risk_review()
    assert risk["operational_replay_readiness_status"] != "ready"
    assert risk["b1_transition_readiness_status"] == "blocked"

    memory = mod.build_phase_a12_evolving_topology_memory_model()
    assert "memory" in memory["model_name"]

    persistence = mod.build_phase_a12_structural_mutation_persistence_model()
    assert "persist" in persistence["model_name"]

    reversibility = mod.build_phase_a12_mutation_reversibility_limit_model()
    assert "reverse" in reversibility["research_objective"]
    assert "threshold" in reversibility["reversibility_constraint"]

    degradation = mod.build_phase_a12_recursive_stabilization_degradation_model()
    assert "degrad" in degradation["model_name"]
