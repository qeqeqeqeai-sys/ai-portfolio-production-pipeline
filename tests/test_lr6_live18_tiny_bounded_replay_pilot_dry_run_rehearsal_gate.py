from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live18_tiny_bounded_replay_pilot_dry_run_rehearsal_gate as live18,
)


def test_api_surface_exists():
    names = [
        "build_lr6_live18_dry_run_rehearsal_gate_module",
        "build_lr6_live18_deterministic_rehearsal_gate_context",
        "validate_lr6_live18_live17_envelope_continuity",
        "build_lr6_live18_rehearsal_precondition_model",
        "build_lr6_live18_rehearsal_pass_fail_classification_model",
        "build_lr6_live18_rehearsal_stop_condition_model",
        "build_lr6_live18_rehearsal_rollback_trigger_model",
        "build_lr6_live18_rehearsal_observability_review",
        "certify_lr6_live18_persistence_write_path_blockade",
        "build_lr6_live18_live19_eligibility_gate",
        "build_lr6_live18_supervisor_review",
        "build_lr6_live18_markdown_report",
    ]
    for n in names:
        assert hasattr(live18, n)


def test_rehearsal_gate_is_dry_run_and_non_executable():
    module = live18.build_lr6_live18_dry_run_rehearsal_gate_module()
    context = live18.build_lr6_live18_deterministic_rehearsal_gate_context()
    assert module["replay_execution_enabled"] is False
    assert module["live_persistence_enabled"] is False
    assert module["write_path_enablement_allowed"] is False
    assert module["replay_richness_only"] is True
    assert context["synthetic_rehearsal_only"] is True
    assert context["allowed_metric_dimension"] == "replay_richness"


def test_live17_envelope_continuity_and_live19_gate_discussable_only():
    continuity = live18.validate_lr6_live18_live17_envelope_continuity()
    gate = live18.build_lr6_live18_live19_eligibility_gate()
    assert continuity["continuity_pass"] is True
    assert all(continuity["continuity_checks"].values())
    assert gate["live19_gate"] == "LIVE19_TINY_PILOT_DRY_RUN_REHEARSAL_EXECUTION_DISCUSSABLE"
    assert gate["execution_authorized"] is False


def test_preconditions_classification_stop_and_rollback_models_present():
    preconditions = live18.build_lr6_live18_rehearsal_precondition_model()
    classification = live18.build_lr6_live18_rehearsal_pass_fail_classification_model()
    stop = live18.build_lr6_live18_rehearsal_stop_condition_model()
    rollback = live18.build_lr6_live18_rehearsal_rollback_trigger_model()
    observability = live18.build_lr6_live18_rehearsal_observability_review()
    boundary = live18.certify_lr6_live18_persistence_write_path_blockade()

    assert preconditions["all_required"] is True
    assert classification["pass_classification"] == "LIVE18_REHEARSAL_GATE_READY_DISCUSSABLE"
    assert classification["execution_authorized_when_pass"] is False
    assert "write_path_enablement_attempt_detected" in stop["stop_conditions"]
    assert rollback["historical_row_rollback_required"] is False
    assert observability["live_write_observability_enabled"] is False
    assert boundary["write_path_enabled"] is False
    assert boundary["direct_sql_allowed"] is False
    assert boundary["schema_expansion_enabled"] is False


def test_supervisor_review_and_markdown_sections_and_report_file():
    review = live18.build_lr6_live18_supervisor_review()
    md = live18.build_lr6_live18_markdown_report(review)
    required_sections = [
        "## dry-run rehearsal gate module",
        "## deterministic rehearsal gate context",
        "## LIVE17 envelope continuity validation",
        "## rehearsal precondition model",
        "## rehearsal pass/fail classification model",
        "## rehearsal stop-condition model",
        "## rehearsal rollback trigger model",
        "## rehearsal observability review",
        "## persistence/write-path blockade certification",
        "## LIVE19 eligibility gate",
    ]
    for section in required_sections:
        assert section in md

    report_path = Path("reports/lr6_live18_tiny_bounded_replay_pilot_dry_run_rehearsal_gate.md")
    assert report_path.exists()
    assert "# LR6-LIVE18 — Tiny Bounded Replay Pilot Dry-Run Rehearsal Gate" in report_path.read_text(encoding="utf-8")
