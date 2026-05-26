from pathlib import Path

from transmission_layers.expectation_failure.phase_a6_observational_replay_ecology_stress_simulation import *


def test_api_existence():
    apis = [
        build_phase_a6_stress_simulation_configuration,
        build_phase_a6_density_escalation_scenarios,
        build_phase_a6_topology_stress_propagation_simulation,
        build_phase_a6_entropy_degradation_simulation,
        build_phase_a6_recurrence_cascade_simulation,
        build_phase_a6_replay_overlap_amplification_simulation,
        build_phase_a6_semantic_crowding_escalation_simulation,
        build_phase_a6_structural_redundancy_escalation_simulation,
        build_phase_a6_weak_node_amplification_simulation,
        build_phase_a6_novelty_decay_stress_simulation,
        build_phase_a6_survivability_threshold_analysis,
        build_phase_a6_decompression_effectiveness_review,
        build_phase_a6_ecology_collapse_threshold_review,
        build_phase_a6_supervisor_review,
        build_phase_a6_markdown_report,
    ]
    assert all(callable(x) for x in apis)


def test_determinism_and_shapes():
    funcs = [
        build_phase_a6_stress_simulation_configuration,
        build_phase_a6_density_escalation_scenarios,
        build_phase_a6_topology_stress_propagation_simulation,
        build_phase_a6_entropy_degradation_simulation,
        build_phase_a6_recurrence_cascade_simulation,
        build_phase_a6_replay_overlap_amplification_simulation,
        build_phase_a6_semantic_crowding_escalation_simulation,
        build_phase_a6_structural_redundancy_escalation_simulation,
        build_phase_a6_weak_node_amplification_simulation,
        build_phase_a6_novelty_decay_stress_simulation,
        build_phase_a6_survivability_threshold_analysis,
        build_phase_a6_decompression_effectiveness_review,
        build_phase_a6_ecology_collapse_threshold_review,
        build_phase_a6_supervisor_review,
    ]
    for f in funcs:
        assert f() == f()

    for sim in build_phase_a6_topology_stress_propagation_simulation():
        for k in ["simulation_name", "deterministic_inputs_used", "simulated_density_band", "simulated_pressure_effects", "survivability_effect", "collapse_risk_band", "mitigation_guidance", "governance_status"]:
            assert k in sim


def test_density_bands_present():
    bands = [x["simulated_density_band"] for x in build_phase_a6_density_escalation_scenarios()]
    assert bands == ["low_density", "moderate_density", "elevated_density", "high_density", "saturation_risk_density"]


def test_supervisor_and_collapse_shapes():
    collapse = build_phase_a6_ecology_collapse_threshold_review()
    for k in ["earliest_observed_collapse_risk_regime", "dominant_collapse_driver", "weakest_survivability_dimension", "most_resilient_dimension", "stabilization_sufficiency_assessment", "operational_replay_readiness_status"]:
        assert k in collapse
    review = build_phase_a6_supervisor_review()
    for k in ["overall_ecology_stability", "highest_stress_risk", "earliest_destabilization_signal", "replay_operationalization_readiness", "replay_density_scaling_readiness", "residual_risks", "recommended_next_phase_action"]:
        assert k in review


def test_markdown_sections_present():
    text = build_phase_a6_markdown_report().lower()
    sections = [
        "## objective", "## relationship to a5", "## observational-only boundary", "## simulation methodology", "## density escalation scenarios",
        "## topology stress propagation simulation", "## entropy degradation simulation", "## recurrence cascade simulation", "## replay overlap amplification simulation",
        "## semantic crowding escalation simulation", "## structural redundancy escalation simulation", "## weak-node amplification simulation", "## novelty decay stress simulation",
        "## survivability threshold analysis", "## decompression effectiveness review", "## ecology collapse threshold review", "## supervisor recommendation",
        "## governance preservation", "## residual risks", "## recommendation for phase a7 or b1",
    ]
    for s in sections:
        assert s in text


def test_governance_boundary_unchanged_and_blocked_paths():
    gs = build_phase_a6_stress_simulation_configuration()["governance_status"]
    assert gs["observational_expansion_only"] is True
    for key in [
        "replay_operationalization_enabled", "replay_density_scaling_enabled", "topology_activation_enabled", "contradiction_persistence_migration_enabled",
        "autonomous_replay_activation_enabled", "prediction_enabled", "trading_enabled", "write_path_expansion_enabled", "schema_expansion_enabled", "direct_sql_allowed",
    ]:
        assert gs[key] is False
    assert gs["append_only_required"] is True
    assert gs["deterministic_governance_required"] is True
    for key in [
        "replay_execution_permitted", "topology_execution_permitted", "live_api_calls_permitted",
        "persistence_adapter_permitted", "execution_workflow_permitted", "historical_ingestion_permitted",
    ]:
        assert gs[key] is False


def test_static_negative_source_scan():
    src = Path("transmission_layers/expectation_failure/phase_a6_observational_replay_ecology_stress_simulation.py").read_text().lower()
    forbidden = [
        "select ", "insert ", "update ", "delete from", "create table", "alter table", "drop table", "execute(", "cursor(",
        "supabase", "create_client", "requests", "httpx", "urllib", "aiohttp", "websocket", "sqlalchemy", "psycopg", "persistence adapter", "workflow activation", "autonomous replay loop",
    ]
    for token in forbidden:
        assert token not in src


def test_report_file_exists_and_sections_present():
    path = Path("reports/phase_a6_observational_replay_ecology_stress_simulation.md")
    assert path.exists()
    text = path.read_text().lower()
    assert "# phase a6 observational replay ecology stress simulation" in text
    assert "## governance preservation" in text
    assert "deterministic structural pressure behavior rather than realistic replay execution dynamics" in text


def test_monotonic_escalation_across_density_bands():
    risk_order = {"contained": 0, "low": 1, "moderate": 2, "elevated": 3, "high": 4, "collapse_risk": 5}
    simulation_builders = [
        build_phase_a6_density_escalation_scenarios,
        build_phase_a6_topology_stress_propagation_simulation,
        build_phase_a6_entropy_degradation_simulation,
        build_phase_a6_recurrence_cascade_simulation,
        build_phase_a6_replay_overlap_amplification_simulation,
        build_phase_a6_semantic_crowding_escalation_simulation,
        build_phase_a6_structural_redundancy_escalation_simulation,
        build_phase_a6_weak_node_amplification_simulation,
        build_phase_a6_novelty_decay_stress_simulation,
    ]

    for builder in simulation_builders:
        rows = builder()
        survivability = [r["survivability_effect"] for r in rows]
        avg_pressure = [sum(r["simulated_pressure_effects"].values()) / len(r["simulated_pressure_effects"]) for r in rows]
        risk = [risk_order[r["collapse_risk_band"]] for r in rows]

        assert all(survivability[i] >= survivability[i + 1] for i in range(len(survivability) - 1)), builder.__name__
        assert all(avg_pressure[i] <= avg_pressure[i + 1] for i in range(len(avg_pressure) - 1)), builder.__name__
        assert all(risk[i] <= risk[i + 1] for i in range(len(risk) - 1)), builder.__name__
