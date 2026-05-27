from pathlib import Path

from transmission_layers.expectation_failure import phase_a9_replay_ecology_phase_state_regime_transition_research as mod


REQUIRED_KEYS = {
    "model_name",
    "research_objective",
    "deterministic_inputs_used",
    "phase_state_signals",
    "transition_triggers",
    "stability_effect",
    "transition_risk",
    "regime_status",
    "residual_risk",
    "governance_status",
}


def test_api_existence() -> None:
    required = [
        "build_phase_a9_phase_state_configuration",
        "build_phase_a9_replay_phase_state_taxonomy",
        "build_phase_a9_regime_transition_model",
        "build_phase_a9_attractor_basin_model",
        "build_phase_a9_topology_bifurcation_model",
        "build_phase_a9_density_triggered_regime_switch_model",
        "build_phase_a9_metastability_model",
        "build_phase_a9_post_equilibrium_degradation_model",
        "build_phase_a9_phase_boundary_analysis",
        "build_phase_a9_regime_transition_risk_review",
        "build_phase_a9_phase_state_scorecard",
        "build_phase_a9_supervisor_review",
        "build_phase_a9_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name), name


def test_deterministic_outputs() -> None:
    assert mod.build_phase_a9_supervisor_review() == mod.build_phase_a9_supervisor_review()
    assert mod.build_phase_a9_phase_state_scorecard() == mod.build_phase_a9_phase_state_scorecard()
    assert mod.build_phase_a9_markdown_report() == mod.build_phase_a9_markdown_report()


def test_model_output_shape() -> None:
    builders = [
        mod.build_phase_a9_regime_transition_model,
        mod.build_phase_a9_attractor_basin_model,
        mod.build_phase_a9_topology_bifurcation_model,
        mod.build_phase_a9_density_triggered_regime_switch_model,
        mod.build_phase_a9_metastability_model,
        mod.build_phase_a9_post_equilibrium_degradation_model,
        mod.build_phase_a9_phase_boundary_analysis,
    ]
    for builder in builders:
        assert REQUIRED_KEYS.issubset(builder().keys())


def test_taxonomy_shape() -> None:
    tx = mod.build_phase_a9_replay_phase_state_taxonomy()
    assert len(tx) == 8
    assert "collapse_risk_regime" in tx


def test_governance_boundary_unchanged() -> None:
    gov = mod.build_phase_a9_phase_state_configuration()["governance_status"]
    assert gov["observational_expansion_only"] is True
    assert gov["replay_execution_permitted"] is False
    assert gov["topology_execution_permitted"] is False
    assert gov["live_api_calls_permitted"] is False
    assert gov["execution_workflow_permitted"] is False


def test_scorecard_shape() -> None:
    sc = mod.build_phase_a9_phase_state_scorecard()
    expected = {
        "stable_regime_strength",
        "metastability_strength",
        "transition_resistance",
        "attractor_basin_escape_strength",
        "topology_bifurcation_resistance",
        "density_switch_resistance",
        "collapse_risk_containment",
        "overall_phase_state_resilience",
        "governance_status",
    }
    assert expected.issubset(sc.keys())


def test_supervisor_review_shape() -> None:
    review = mod.build_phase_a9_supervisor_review()
    expected = {
        "overall_phase_state_resilience",
        "dominant_current_phase_state",
        "strongest_regime_dimension",
        "weakest_regime_dimension",
        "primary_transition_risk",
        "replay_operationalization_readiness",
        "replay_density_scaling_readiness",
        "b1_transition_readiness",
        "recommended_next_phase_action",
        "governance_status",
    }
    assert expected.issubset(review.keys())


def test_markdown_report_sections_present() -> None:
    text = Path("reports/phase_a9_replay_ecology_phase_state_regime_transition_research.md").read_text().lower()
    for section in [
        "## objective",
        "## relationship to a8",
        "## observational-only boundary",
        "## phase-state research methodology",
        "## replay phase-state taxonomy",
        "## regime transition model",
        "## attractor basin model",
        "## topology bifurcation model",
        "## density-triggered regime switch model",
        "## metastability model",
        "## post-equilibrium degradation model",
        "## phase boundary analysis",
        "## regime transition risk review",
        "## phase-state scorecard",
        "## supervisor interpretation",
        "## governance preservation",
        "## residual risks",
        "## recommendation regarding b1",
        "a9 models deterministic structural phase-state behavior rather than realistic replay execution dynamics.",
    ]:
        assert section in text


def test_static_negative_checks() -> None:
    text = Path("transmission_layers/expectation_failure/phase_a9_replay_ecology_phase_state_regime_transition_research.py").read_text().lower()
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


def test_phase_state_consistency() -> None:
    review = mod.build_phase_a9_supervisor_review()
    assert review["replay_operationalization_readiness"] == "blocked"
    assert review["b1_transition_readiness"] == "blocked"
    assert review["dominant_current_phase_state"] == "adaptive_metastable_regime"

    risk = mod.build_phase_a9_regime_transition_risk_review()
    assert risk["operational_replay_readiness_status"] != "ready"
    assert risk["b1_transition_readiness_status"] == "blocked"

    model = mod.build_phase_a9_regime_transition_model()
    assert "density_pressure" in model["transition_triggers"]
    assert model["transition_risk"]

    scorecard = mod.build_phase_a9_phase_state_scorecard()
    assert 0 <= scorecard["overall_phase_state_resilience"] <= 1
    assert scorecard["collapse_risk_containment"] < scorecard["stable_regime_strength"]
