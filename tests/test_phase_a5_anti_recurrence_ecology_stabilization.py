from pathlib import Path

from transmission_layers.expectation_failure.phase_a5_anti_recurrence_ecology_stabilization import *


def test_api_existence():
    for fn in [
        build_phase_a5_anti_recurrence_stabilization_configuration,
        build_phase_a5_replay_corridor_diversification_plan,
        build_phase_a5_topology_decompression_plan,
        build_phase_a5_contradiction_orthogonalization_plan,
        build_phase_a5_bridge_node_diversification_plan,
        build_phase_a5_recurrence_suppression_guardrails,
        build_phase_a5_entropy_preservation_guardrails,
        build_phase_a5_novelty_preservation_guardrails,
        build_phase_a5_replay_survivability_stabilization_review,
        build_phase_a5_stabilization_priority_ranking,
        build_phase_a5_supervisor_review,
        build_phase_a5_markdown_report,
    ]:
        assert callable(fn)


def test_determinism_and_shapes():
    assert build_phase_a5_anti_recurrence_stabilization_configuration() == build_phase_a5_anti_recurrence_stabilization_configuration()
    assert build_phase_a5_replay_corridor_diversification_plan() == build_phase_a5_replay_corridor_diversification_plan()
    assert build_phase_a5_topology_decompression_plan() == build_phase_a5_topology_decompression_plan()
    assert build_phase_a5_contradiction_orthogonalization_plan() == build_phase_a5_contradiction_orthogonalization_plan()
    assert build_phase_a5_bridge_node_diversification_plan() == build_phase_a5_bridge_node_diversification_plan()
    assert build_phase_a5_recurrence_suppression_guardrails() == build_phase_a5_recurrence_suppression_guardrails()
    assert build_phase_a5_entropy_preservation_guardrails() == build_phase_a5_entropy_preservation_guardrails()
    assert build_phase_a5_novelty_preservation_guardrails() == build_phase_a5_novelty_preservation_guardrails()
    assert build_phase_a5_replay_survivability_stabilization_review() == build_phase_a5_replay_survivability_stabilization_review()
    assert build_phase_a5_stabilization_priority_ranking() == build_phase_a5_stabilization_priority_ranking()


def test_stabilization_outputs_contain_required_fields():
    required = {
        "stabilization_name",
        "deterministic_inputs_used",
        "target_pressure",
        "stabilization_actions",
        "expected_effect",
        "replay_ecology_risk_if_ignored",
        "governance_status",
    }
    for obj in [
        build_phase_a5_replay_corridor_diversification_plan(),
        build_phase_a5_topology_decompression_plan(),
        build_phase_a5_contradiction_orthogonalization_plan(),
        build_phase_a5_bridge_node_diversification_plan(),
    ]:
        assert required.issubset(set(obj.keys()))


def test_priority_and_supervisor_review_and_boundary_flags():
    ranking = build_phase_a5_stabilization_priority_ranking()
    expected = [
        "replay_recurrence_pressure",
        "replay_path_repetition",
        "structural_redundancy",
        "semantic_crowding",
        "narrative_saturation_pressure",
        "novelty_decay_risk",
        "contradiction_recurrence_density",
        "contradiction_exhaustion_risk",
    ]
    assert [r["pressure"] for r in ranking] == expected

    review = build_phase_a5_supervisor_review()
    for key in ["stabilization_status", "highest_priority_pressure", "immediate_guardrail_focus", "deferred_focus", "residual_risks", "recommended_next_phase_action"]:
        assert key in review

    boundary = review["governance_boundary"]
    assert boundary["observational_expansion_only"] is True
    assert boundary["replay_operationalization_enabled"] is False
    assert boundary["replay_density_scaling_enabled"] is False
    assert boundary["topology_activation_enabled"] is False
    assert boundary["contradiction_persistence_migration_enabled"] is False
    assert boundary["autonomous_replay_activation_enabled"] is False
    assert boundary["prediction_enabled"] is False
    assert boundary["trading_enabled"] is False
    assert boundary["write_path_expansion_enabled"] is False
    assert boundary["schema_expansion_enabled"] is False
    assert boundary["direct_sql_allowed"] is False
    assert boundary["append_only_required"] is True
    assert boundary["deterministic_governance_required"] is True


def test_markdown_report_sections_and_write_file():
    markdown = build_phase_a5_markdown_report()
    required_sections = [
        "## objective",
        "## relationship to a4",
        "## observational-only boundary",
        "## stabilization methodology",
        "## replay corridor diversification plan",
        "## topology decompression plan",
        "## contradiction orthogonalization plan",
        "## bridge-node diversification plan",
        "## recurrence suppression guardrails",
        "## entropy preservation guardrails",
        "## novelty preservation guardrails",
        "## replay survivability stabilization review",
        "## stabilization priority ranking",
        "## supervisor recommendation",
        "## governance preservation",
        "## residual risks",
        "## recommendation for phase a6 or b1",
    ]
    lower = markdown.lower()
    for section in required_sections:
        assert section in lower

    path = Path("reports/phase_a5_anti_recurrence_ecology_stabilization.md")
    path.write_text(markdown + "\n", encoding="utf-8")
    assert path.exists()
