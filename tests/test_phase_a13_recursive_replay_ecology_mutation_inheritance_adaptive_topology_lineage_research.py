from pathlib import Path

from transmission_layers.expectation_failure import phase_a13_recursive_replay_ecology_mutation_inheritance_adaptive_topology_lineage_research as mod


def test_api_existence():
    required = [
        "build_phase_a13_mutation_lineage_configuration",
        "build_phase_a13_recursive_mutation_inheritance_model",
        "build_phase_a13_topology_lineage_evolution_model",
        "build_phase_a13_propagation_lineage_branching_model",
        "build_phase_a13_mutation_selection_pressure_model",
        "build_phase_a13_adaptive_attractor_ecosystem_model",
        "build_phase_a13_recursive_corridor_speciation_model",
        "build_phase_a13_stabilization_extinction_model",
        "build_phase_a13_topology_evolutionary_drift_model",
        "build_phase_a13_nonlinear_mutation_ecosystem_model",
        "build_phase_a13_lineage_reversibility_constraint_model",
        "build_phase_a13_mutation_lineage_risk_review",
        "build_phase_a13_lineage_evolution_scorecard",
        "build_phase_a13_supervisor_review",
        "build_phase_a13_markdown_report",
    ]
    for name in required:
        assert hasattr(mod, name), name


def test_deterministic_outputs():
    assert mod.build_phase_a13_supervisor_review() == mod.build_phase_a13_supervisor_review()
    assert mod.build_phase_a13_lineage_evolution_scorecard() == mod.build_phase_a13_lineage_evolution_scorecard()
    assert mod.build_phase_a13_markdown_report() == mod.build_phase_a13_markdown_report()


def test_model_shape():
    keys = {"model_name", "research_objective", "deterministic_inputs_used", "inheritance_signals", "lineage_evolution_signals", "lineage_effect", "containment_effect", "lineage_risk", "reversibility_constraint", "governance_status"}
    models = [
        mod.build_phase_a13_recursive_mutation_inheritance_model,
        mod.build_phase_a13_topology_lineage_evolution_model,
        mod.build_phase_a13_propagation_lineage_branching_model,
        mod.build_phase_a13_mutation_selection_pressure_model,
        mod.build_phase_a13_adaptive_attractor_ecosystem_model,
        mod.build_phase_a13_recursive_corridor_speciation_model,
        mod.build_phase_a13_stabilization_extinction_model,
        mod.build_phase_a13_topology_evolutionary_drift_model,
        mod.build_phase_a13_nonlinear_mutation_ecosystem_model,
        mod.build_phase_a13_lineage_reversibility_constraint_model,
    ]
    for fn in models:
        assert set(fn().keys()) == keys


def test_governance_boundary_unchanged():
    gov = mod.build_phase_a13_mutation_lineage_configuration()["governance_status"]
    assert gov["observational_expansion_only"] is True
    for k in [
        "replay_operationalization_enabled", "replay_density_scaling_enabled", "topology_activation_enabled",
        "prediction_enabled", "trading_enabled", "write_path_expansion_enabled", "schema_expansion_enabled",
        "direct_sql_allowed", "replay_execution_permitted", "topology_execution_permitted", "live_api_calls_permitted",
        "persistence_adapter_permitted", "execution_workflow_permitted", "historical_ingestion_permitted"
    ]:
        assert gov[k] is False


def test_scorecard_and_supervisor_shape():
    sc = mod.build_phase_a13_lineage_evolution_scorecard()
    for key in [
        "mutation_inheritance_containment", "topology_lineage_stability", "propagation_branching_resistance",
        "mutation_selection_pressure_resistance", "attractor_ecosystem_stability", "corridor_speciation_containment",
        "stabilization_extinction_resistance", "evolutionary_drift_resistance", "mutation_ecosystem_containment",
        "lineage_reversibility_strength", "overall_lineage_resilience", "governance_status"
    ]:
        assert key in sc
    review = mod.build_phase_a13_supervisor_review()
    for key in [
        "overall_lineage_resilience", "dominant_lineage_dynamic", "strongest_containment_dimension",
        "weakest_reversibility_dimension", "primary_lineage_risk", "replay_operationalization_readiness",
        "replay_density_scaling_readiness", "b1_transition_readiness", "recommended_next_phase_action", "governance_status"
    ]:
        assert key in review


def test_markdown_sections_present():
    text = Path("reports/phase_a13_recursive_replay_ecology_mutation_inheritance_adaptive_topology_lineage_research.md").read_text().lower()
    for s in [
        "## objective", "## relationship to a12", "## observational-only boundary", "## mutation lineage research methodology",
        "## recursive mutation inheritance model", "## topology lineage evolution model", "## propagation lineage branching model",
        "## mutation selection pressure model", "## adaptive attractor ecosystem model", "## recursive corridor speciation model",
        "## stabilization extinction model", "## topology evolutionary drift model", "## nonlinear mutation ecosystem model",
        "## lineage reversibility constraint model", "## mutation lineage risk review", "## lineage evolution scorecard",
        "## supervisor interpretation", "## governance preservation", "## residual risks", "## recommendation regarding b1",
        "a13 models deterministic structural mutation lineage behavior rather than realistic replay execution dynamics"
    ]:
        assert s in text


def test_static_negative_checks():
    text = Path("transmission_layers/expectation_failure/phase_a13_recursive_replay_ecology_mutation_inheritance_adaptive_topology_lineage_research.py").read_text().lower()
    banned = ["supabase", "import requests", "import httpx", "import urllib", "import socket", "import sqlite", "import sqlalchemy", "from sqlalchemy", ".execute(", "replay_execution_enabled = true", "topology_activation_enabled = true", "prediction_enabled = true", "trading_enabled = true"]
    for token in banned:
        assert token not in text


def test_mutation_lineage_consistency():
    risk = mod.build_phase_a13_mutation_lineage_risk_review()
    review = mod.build_phase_a13_supervisor_review()
    inheritance = mod.build_phase_a13_recursive_mutation_inheritance_model()
    corridor = mod.build_phase_a13_recursive_corridor_speciation_model()
    extinction = mod.build_phase_a13_stabilization_extinction_model()
    reversibility = mod.build_phase_a13_lineage_reversibility_constraint_model()

    assert risk["operational_replay_readiness_status"] in {"blocked", "not_ready_blocked"}
    assert review["replay_operationalization_readiness"] != "ready"
    assert review["b1_transition_readiness"] != "ready"
    assert any("inherit" in s for s in inheritance["inheritance_signals"])
    assert "corridor" in corridor["model_name"]
    assert "extinction" in extinction["model_name"]
    assert "reversibility" in reversibility["model_name"]
    assert "full" in reversibility["reversibility_constraint"] or "bounded" in reversibility["reversibility_constraint"]
