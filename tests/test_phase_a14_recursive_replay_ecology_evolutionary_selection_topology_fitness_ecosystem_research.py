from pathlib import Path

from transmission_layers.expectation_failure import phase_a14_recursive_replay_ecology_evolutionary_selection_topology_fitness_ecosystem_research as mod


def test_api_existence():
    required = [
        "build_phase_a14_fitness_ecosystem_configuration",
        "build_phase_a14_topology_fitness_selection_model",
        "build_phase_a14_lineage_survival_competition_model",
        "build_phase_a14_recursive_extinction_replacement_model",
        "build_phase_a14_adaptive_mutation_reproduction_model",
        "build_phase_a14_attractor_predation_ecosystem_model",
        "build_phase_a14_stabilization_fitness_collapse_model",
        "build_phase_a14_topology_ecological_succession_model",
        "build_phase_a14_recursive_ecosystem_collapse_rebirth_model",
        "build_phase_a14_nonlinear_topology_evolutionary_pressure_model",
        "build_phase_a14_fitness_reversibility_constraint_model",
        "build_phase_a14_fitness_ecosystem_risk_review",
        "build_phase_a14_topology_fitness_scorecard",
        "build_phase_a14_supervisor_review",
        "build_phase_a14_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name), name


def test_deterministic_outputs():
    assert mod.build_phase_a14_supervisor_review() == mod.build_phase_a14_supervisor_review()
    assert mod.build_phase_a14_topology_fitness_scorecard() == mod.build_phase_a14_topology_fitness_scorecard()
    assert mod.build_phase_a14_markdown_report() == mod.build_phase_a14_markdown_report()


def test_model_shape():
    keys = {"model_name", "research_objective", "deterministic_inputs_used", "fitness_signals", "ecosystem_evolution_signals", "selection_effect", "containment_effect", "ecosystem_risk", "reversibility_constraint", "governance_status"}
    models = [
        mod.build_phase_a14_topology_fitness_selection_model,
        mod.build_phase_a14_lineage_survival_competition_model,
        mod.build_phase_a14_recursive_extinction_replacement_model,
        mod.build_phase_a14_adaptive_mutation_reproduction_model,
        mod.build_phase_a14_attractor_predation_ecosystem_model,
        mod.build_phase_a14_stabilization_fitness_collapse_model,
        mod.build_phase_a14_topology_ecological_succession_model,
        mod.build_phase_a14_recursive_ecosystem_collapse_rebirth_model,
        mod.build_phase_a14_nonlinear_topology_evolutionary_pressure_model,
        mod.build_phase_a14_fitness_reversibility_constraint_model,
    ]
    for fn in models:
        assert set(fn().keys()) == keys


def test_governance_boundary_unchanged():
    gov = mod.build_phase_a14_fitness_ecosystem_configuration()["governance_status"]
    assert gov["observational_expansion_only"] is True
    for k in [
        "replay_operationalization_enabled", "replay_density_scaling_enabled", "topology_activation_enabled",
        "prediction_enabled", "trading_enabled", "write_path_expansion_enabled", "schema_expansion_enabled",
        "direct_sql_allowed", "replay_execution_permitted", "topology_execution_permitted", "live_api_calls_permitted",
        "persistence_adapter_permitted", "execution_workflow_permitted", "historical_ingestion_permitted"
    ]:
        assert gov[k] is False


def test_scorecard_and_supervisor_shape():
    sc = mod.build_phase_a14_topology_fitness_scorecard()
    for key in [
        "topology_fitness_selection_containment", "lineage_survival_balance", "extinction_replacement_resistance",
        "mutation_reproduction_resistance", "attractor_predation_resistance", "stabilization_fitness_resilience",
        "ecological_succession_containment", "collapse_rebirth_cycle_resistance", "nonlinear_evolutionary_pressure_resistance",
        "fitness_reversibility_strength", "overall_topology_fitness_resilience", "governance_status"
    ]:
        assert key in sc
    review = mod.build_phase_a14_supervisor_review()
    for key in [
        "overall_topology_fitness_resilience", "dominant_evolutionary_dynamic", "strongest_containment_dimension",
        "weakest_reversibility_dimension", "primary_fitness_ecosystem_risk", "replay_operationalization_readiness",
        "replay_density_scaling_readiness", "b1_transition_readiness", "recommended_next_phase_action", "governance_status"
    ]:
        assert key in review


def test_markdown_sections_present():
    text = Path("reports/phase_a14_recursive_replay_ecology_evolutionary_selection_topology_fitness_ecosystem_research.md").read_text().lower()
    for s in [
        "## objective", "## relationship to a13", "## observational-only boundary", "## topology fitness research methodology",
        "## topology fitness selection model", "## lineage survival competition model", "## recursive extinction replacement model",
        "## adaptive mutation reproduction model", "## attractor predation ecosystem model", "## stabilization fitness collapse model",
        "## topology ecological succession model", "## recursive ecosystem collapse rebirth model", "## nonlinear topology evolutionary pressure model",
        "## fitness reversibility constraint model", "## fitness ecosystem risk review", "## topology fitness scorecard",
        "## supervisor interpretation", "## governance preservation", "## residual risks", "## recommendation regarding b1",
        "a14 models deterministic structural topology fitness behavior rather than realistic replay execution dynamics"
    ]:
        assert s in text


def test_static_negative_checks():
    text = Path("transmission_layers/expectation_failure/phase_a14_recursive_replay_ecology_evolutionary_selection_topology_fitness_ecosystem_research.py").read_text().lower()
    banned = ["supabase", "import requests", "import httpx", "import urllib", "import socket", "import sqlite", "import sqlalchemy", "from sqlalchemy", ".execute(", "replay_execution_enabled = true", "topology_activation_enabled = true", "prediction_enabled = true", "trading_enabled = true"]
    for token in banned:
        assert token not in text


def test_topology_fitness_consistency():
    risk = mod.build_phase_a14_fitness_ecosystem_risk_review()
    review = mod.build_phase_a14_supervisor_review()
    selection = mod.build_phase_a14_topology_fitness_selection_model()
    lineage = mod.build_phase_a14_lineage_survival_competition_model()
    stabilization = mod.build_phase_a14_stabilization_fitness_collapse_model()
    reversibility = mod.build_phase_a14_fitness_reversibility_constraint_model()

    assert risk["operational_replay_readiness_status"] in {"blocked", "not_ready_blocked"}
    assert review["replay_operationalization_readiness"] != "ready"
    assert review["b1_transition_readiness"] != "ready"
    assert "fitness" in selection["model_name"]
    assert "lineage" in lineage["model_name"]
    assert "stabilization" in stabilization["model_name"]
    assert "reversibility" in reversibility["model_name"]
    assert "full" in reversibility["reversibility_constraint"] or "bounded" in reversibility["reversibility_constraint"]
