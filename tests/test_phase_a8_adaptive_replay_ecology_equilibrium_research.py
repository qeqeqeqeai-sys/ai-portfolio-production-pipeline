from pathlib import Path

from transmission_layers.expectation_failure import phase_a8_adaptive_replay_ecology_equilibrium_research as mod


def test_api_existence():
    required = [
        "build_phase_a8_equilibrium_configuration",
        "build_phase_a8_adaptive_equilibrium_model",
        "build_phase_a8_survivability_ceiling_analysis",
        "build_phase_a8_stabilization_interference_model",
        "build_phase_a8_gravity_well_phase_transition_model",
        "build_phase_a8_entropy_equilibrium_model",
        "build_phase_a8_recurrence_equilibrium_model",
        "build_phase_a8_topology_balance_model",
        "build_phase_a8_collapse_delay_analysis",
        "build_phase_a8_equilibrium_failure_review",
        "build_phase_a8_ecology_equilibrium_scorecard",
        "build_phase_a8_supervisor_review",
        "build_phase_a8_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name)
        assert callable(getattr(mod, name))


def test_deterministic_outputs():
    assert mod.build_phase_a8_supervisor_review() == mod.build_phase_a8_supervisor_review()
    assert mod.build_phase_a8_ecology_equilibrium_scorecard() == mod.build_phase_a8_ecology_equilibrium_scorecard()


def test_model_output_shape_and_governance():
    keys = {
        "model_name", "research_objective", "deterministic_inputs_used", "equilibrium_signals", "destabilization_signals",
        "survivability_ceiling_effect", "stabilization_interference_effect", "equilibrium_status", "residual_risk", "governance_status"
    }
    models = [
        mod.build_phase_a8_adaptive_equilibrium_model,
        mod.build_phase_a8_survivability_ceiling_analysis,
        mod.build_phase_a8_stabilization_interference_model,
        mod.build_phase_a8_gravity_well_phase_transition_model,
        mod.build_phase_a8_entropy_equilibrium_model,
        mod.build_phase_a8_recurrence_equilibrium_model,
        mod.build_phase_a8_topology_balance_model,
        mod.build_phase_a8_collapse_delay_analysis,
    ]
    for fn in models:
        out = fn()
        assert keys.issubset(out.keys())
        assert out["governance_status"]["replay_execution_permitted"] is False
        assert out["governance_status"]["topology_execution_permitted"] is False


def test_scorecard_and_supervisor_shapes_and_consistency():
    sc = mod.build_phase_a8_ecology_equilibrium_scorecard()
    for key in [
        "adaptive_equilibrium_strength", "survivability_ceiling_headroom", "entropy_equilibrium_strength",
        "recurrence_equilibrium_strength", "topology_balance_strength", "gravity_well_resistance",
        "stabilization_interference_risk", "collapse_delay_risk", "overall_equilibrium_viability",
    ]:
        assert key in sc
    assert 0 <= sc["stabilization_interference_risk"] <= 1
    sup = mod.build_phase_a8_supervisor_review()
    for key in [
        "overall_equilibrium_viability", "strongest_equilibrium_dimension", "weakest_equilibrium_dimension",
        "primary_failure_mode", "replay_operationalization_readiness", "replay_density_scaling_readiness",
        "b1_transition_readiness", "recommended_next_phase_action",
    ]:
        assert key in sup
    assert sup["replay_operationalization_readiness"] != "ready"
    assert not (sc["overall_equilibrium_viability"] >= 0.6 and sup["replay_operationalization_readiness"] == "ready")
    assert sup["b1_transition_readiness"] == "blocked"
    assert sc["collapse_delay_risk"] > 0


def test_markdown_sections_present():
    text = Path("reports/phase_a8_adaptive_replay_ecology_equilibrium_research.md").read_text().lower()
    for section in [
        "## objective", "## relationship to a7", "## observational-only boundary", "## equilibrium research methodology",
        "## adaptive equilibrium model", "## survivability ceiling analysis", "## stabilization interference model",
        "## gravity-well phase transition model", "## entropy equilibrium model", "## recurrence equilibrium model",
        "## topology balance model", "## collapse delay analysis", "## equilibrium failure review",
        "## ecology equilibrium scorecard", "## supervisor interpretation", "## governance preservation",
        "## residual risks", "## recommendation regarding b1",
        "a8 models deterministic structural equilibrium behavior rather than realistic replay execution dynamics.",
    ]:
        assert section in text


def test_static_negative_checks():
    text = Path("transmission_layers/expectation_failure/phase_a8_adaptive_replay_ecology_equilibrium_research.py").read_text().lower()
    banned_substrings = [
        "import requests", "import httpx", "from requests", "from httpx", "import urllib",
        "import supabase", "from supabase", "psycopg", "asyncpg", "sqlite3.connect(",
        "insert into", "delete from", "create table", "alter table", "execute_workflow",
        "prediction_model", "trading_strategy", "replay_accumulation"
    ]
    for token in banned_substrings:
        assert token not in text
