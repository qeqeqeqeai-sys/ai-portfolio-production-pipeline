from pathlib import Path

from transmission_layers.expectation_failure import phase_a7_replay_ecology_stabilization_hardening as mod


def test_api_existence():
    names = [
        "build_phase_a7_stabilization_configuration",
        "build_phase_a7_entropy_reinforcement_model",
        "build_phase_a7_replay_corridor_decompression_model",
        "build_phase_a7_gravity_well_dispersion_model",
        "build_phase_a7_recurrence_dispersion_model",
        "build_phase_a7_topology_diversification_model",
        "build_phase_a7_anti_monoculture_hardening_model",
        "build_phase_a7_weak_node_resilience_model",
        "build_phase_a7_structural_escape_route_model",
        "build_phase_a7_novelty_preservation_model",
        "build_phase_a7_adaptive_survivability_model",
        "build_phase_a7_density_resilience_review",
        "build_phase_a7_collapse_resistance_review",
        "build_phase_a7_ecology_resilience_scorecard",
        "build_phase_a7_supervisor_review",
        "build_phase_a7_markdown_report",
    ]
    for n in names:
        assert hasattr(mod, n)


def test_deterministic_outputs():
    assert mod.build_phase_a7_supervisor_review() == mod.build_phase_a7_supervisor_review()
    assert mod.build_phase_a7_ecology_resilience_scorecard() == mod.build_phase_a7_ecology_resilience_scorecard()


def test_model_shapes_and_determinism():
    required = {"stabilization_model", "stabilization_objective", "deterministic_inputs_used", "targeted_failure_modes", "stabilization_mechanisms", "survivability_effect", "entropy_preservation_effect", "recurrence_resistance_effect", "topology_resilience_effect", "residual_risk", "governance_status"}
    builders = [
        mod.build_phase_a7_entropy_reinforcement_model,
        mod.build_phase_a7_replay_corridor_decompression_model,
        mod.build_phase_a7_gravity_well_dispersion_model,
        mod.build_phase_a7_recurrence_dispersion_model,
        mod.build_phase_a7_topology_diversification_model,
        mod.build_phase_a7_anti_monoculture_hardening_model,
        mod.build_phase_a7_weak_node_resilience_model,
        mod.build_phase_a7_structural_escape_route_model,
        mod.build_phase_a7_novelty_preservation_model,
        mod.build_phase_a7_adaptive_survivability_model,
    ]
    for fn in builders:
        a, b = fn(), fn()
        assert a == b
        assert required.issubset(set(a.keys()))


def test_stabilization_monotonic_consistency():
    entropy = mod.build_phase_a7_entropy_reinforcement_model()
    decompression = mod.build_phase_a7_replay_corridor_decompression_model()
    adaptive = mod.build_phase_a7_adaptive_survivability_model()
    assert adaptive["survivability_effect"] >= entropy["survivability_effect"]
    assert decompression["topology_resilience_effect"] >= entropy["topology_resilience_effect"]


def test_density_resilience_determinism_and_monotonicity():
    review = mod.build_phase_a7_density_resilience_review()
    bands = review["stabilization_effectiveness_by_density"]
    vals = [bands[k]["survivability_preservation"] for k in ["low_density", "moderate_density", "elevated_density", "high_density", "saturation_risk_density"]]
    assert review == mod.build_phase_a7_density_resilience_review()
    assert vals == sorted(vals, reverse=True)


def test_collapse_resistance_determinism_and_non_regression():
    collapse = mod.build_phase_a7_collapse_resistance_review()
    decomp = mod.build_phase_a7_replay_corridor_decompression_model()
    assert collapse == mod.build_phase_a7_collapse_resistance_review()
    assert collapse["collapse_resistance_score"] >= decomp["survivability_effect"] - 0.05


def test_scorecard_and_supervisor_shape():
    sc = mod.build_phase_a7_ecology_resilience_scorecard()
    for k in ["entropy_resilience", "recurrence_resilience", "topology_resilience", "novelty_resilience", "weak_node_resilience", "gravity_well_resistance", "monoculture_resistance", "collapse_resistance", "overall_ecology_resilience"]:
        assert k in sc
    sup = mod.build_phase_a7_supervisor_review()
    for k in ["overall_ecology_resilience", "strongest_stabilization_dimension", "weakest_remaining_dimension", "collapse_resistance_status", "replay_operationalization_readiness", "replay_density_scaling_readiness", "residual_structural_risks", "recommended_next_phase_action"]:
        assert k in sup


def test_governance_boundary_unchanged():
    g = mod.build_phase_a7_stabilization_configuration()["governance_status"]
    assert g["observational_expansion_only"] is True
    for k in [
        "replay_operationalization_enabled", "replay_density_scaling_enabled", "topology_activation_enabled", "contradiction_persistence_migration_enabled", "autonomous_replay_activation_enabled", "prediction_enabled", "trading_enabled", "write_path_expansion_enabled", "schema_expansion_enabled", "direct_sql_allowed", "replay_execution_permitted", "topology_execution_permitted", "live_api_calls_permitted", "persistence_adapter_permitted", "execution_workflow_permitted", "historical_ingestion_permitted",
    ]:
        assert g[k] is False


def test_markdown_report_sections_present():
    text = Path("reports/phase_a7_replay_ecology_stabilization_hardening.md").read_text().lower()
    for s in ["objective", "relationship to a6", "observational-only boundary", "stabilization methodology", "entropy reinforcement modeling", "replay corridor decompression modeling", "gravity-well dispersion modeling", "recurrence dispersion modeling", "topology diversification modeling", "anti-monoculture hardening modeling", "weak-node resilience modeling", "structural escape route modeling", "novelty preservation modeling", "adaptive survivability modeling", "density resilience review", "collapse resistance review", "ecology resilience scorecard", "supervisor interpretation", "governance preservation", "residual risks", "recommendation regarding b1"]:
        assert f"## {s}" in text


def test_static_negative_constraints():
    text = Path("transmission_layers/expectation_failure/phase_a7_replay_ecology_stabilization_hardening.py").read_text().lower()
    banned = ["supabase", "requests", "httpx", "urllib", "socket", "sqlite", "psycopg", "cursor.execute(", "airflow", "prefect", "autonomous replay loop", "persistence adapter"]
    for b in banned:
        assert b not in text
