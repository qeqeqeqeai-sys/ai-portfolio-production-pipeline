from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as m
from transmission_layers.expectation_failure.replay_ecology import lr6_obs9_execution_review_framework as obs9


def test_public_apis_exist():
    names = [
        "build_lr6_obs9_review_framework_context",
        "build_lr6_obs9_success_criteria",
        "build_lr6_obs9_failure_criteria",
        "build_lr6_obs9_replay_delta_interpretation_rules",
        "build_lr6_obs9_contradiction_usefulness_criteria",
        "build_lr6_obs9_topology_diversification_criteria",
        "build_lr6_obs9_weak_signal_success_criteria",
        "build_lr6_obs9_fail_closed_review_thresholds",
        "build_lr6_obs9_continuation_vs_termination_logic",
        "build_lr6_obs9_confirmation_bias_safeguards",
        "build_lr6_obs9_supervisor_review",
        "build_lr6_obs9_markdown_report",
        "certify_lr6_obs9_review_framework_boundary",
    ]
    for name in names:
        assert hasattr(obs9, name)
        assert hasattr(m, name)


def test_deterministic_outputs_repeated_calls():
    a = obs9.build_lr6_obs9_supervisor_review()
    b = obs9.build_lr6_obs9_supervisor_review()
    assert a == b


def test_fallback_behavior_when_inputs_missing(monkeypatch):
    monkeypatch.setattr(obs9, "build_lr6_obs6_first_wave_candidates", lambda: 42)
    monkeypatch.setattr(obs9, "build_lr6_obs7_simulated_observation_routes", lambda: None)
    monkeypatch.setattr(obs9, "build_lr6_obs8_governance_requirements", lambda: {"x": 1})
    review = obs9.build_lr6_obs9_supervisor_review()
    assert review["inspected_obs6_inputs"]["first_wave_candidates"] == []
    assert review["inspected_obs7_inputs"]["simulated_observation_routes"] == []
    assert review["inspected_obs8_inputs"]["governance_requirements"] == []


def test_criteria_and_logic_present_and_non_empty():
    review = obs9.build_lr6_obs9_supervisor_review()
    for key in [
        "success_criteria", "failure_criteria", "replay_delta_interpretation_rules",
        "contradiction_usefulness_criteria", "topology_diversification_criteria",
        "weak_signal_success_criteria", "fail_closed_review_thresholds",
        "confirmation_bias_safeguards",
    ]:
        assert isinstance(review[key], list)
        assert len(review[key]) > 0
    logic = review["continuation_vs_termination_logic"]
    assert set(logic.keys()) == {"CONTINUE_ONLY_IF", "TERMINATE_OR_PAUSE_IF"}


def test_boundary_flags_and_execution_false():
    boundary = obs9.certify_lr6_obs9_review_framework_boundary()
    expected_true = [
        "observation_only", "review_framework_only", "no_prediction", "no_trading",
        "no_direct_sql", "no_live_ingestion", "no_persistence_write",
        "no_governed_activation", "architecture_expansion_frozen",
    ]
    for key in expected_true:
        assert boundary[key] is True
    assert boundary["execution_authorized"] is False


def test_report_required_sections_and_safety_language():
    review = obs9.build_lr6_obs9_supervisor_review()
    text = obs9.build_lr6_obs9_markdown_report(review)
    required_sections = [
        "## Objective", "## Inspected OBS6/OBS7/OBS8 Inputs", "## Success Criteria",
        "## Failure Criteria", "## Replay Delta Interpretation Rules",
        "## Contradiction Usefulness Criteria", "## Topology Diversification Criteria",
        "## Weak-Signal Success Criteria", "## Fail-Closed Review Thresholds",
        "## Continuation vs Termination Logic", "## Confirmation Bias Safeguards",
        "## Explicit Non-Authorization Notice", "## Architectural Overengineering Warning",
        "## Recommendation for Next Phase",
    ]
    for section in required_sections:
        assert section in text
    lower = text.lower()
    assert "sql" not in lower
    assert "insert into" not in lower
    assert "update " not in lower
    assert "delete from" not in lower
    assert "persistence write" not in lower
    assert "persist to" not in lower
    assert "trading" not in lower
    assert "prediction" not in lower


def test_report_file_exists_and_contains_sections():
    path = Path("reports/lr6_obs9_execution_review_framework.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "# LR6-OBS9 Execution Review Framework" in content
    assert "## Explicit Non-Authorization Notice" in content
