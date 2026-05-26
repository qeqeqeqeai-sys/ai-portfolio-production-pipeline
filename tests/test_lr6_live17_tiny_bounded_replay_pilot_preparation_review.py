from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live17_tiny_bounded_replay_pilot_preparation_review as live17,
)


def test_api_surface_exists():
    names = [
        "build_lr6_live17_tiny_pilot_preparation_module",
        "build_lr6_live17_deterministic_pilot_envelope",
        "build_lr6_live17_replay_richness_only_candidate_cohort",
        "build_lr6_live17_operator_approval_checklist",
        "build_lr6_live17_preflight_governance_checklist",
        "build_lr6_live17_observability_readiness_checklist",
        "build_lr6_live17_stop_condition_readiness_checklist",
        "build_lr6_live17_rollback_readiness_checklist",
        "build_lr6_live17_pilot_readiness_classification",
        "build_lr6_live17_live18_eligibility_gate",
        "build_lr6_live17_supervisor_review",
        "build_lr6_live17_markdown_report",
        "certify_lr6_live17_preparation_boundary",
    ]
    for n in names:
        assert hasattr(live17, n)


def test_envelope_and_cohort_are_tiny_and_replay_richness_only():
    envelope = live17.build_lr6_live17_deterministic_pilot_envelope()
    cohort = live17.build_lr6_live17_replay_richness_only_candidate_cohort()
    assert envelope["max_rows"] <= 5
    assert envelope["execution_mode"] == "dry_run_only_preflight"
    assert envelope["allowed_metric_dimension"] == "replay_richness"
    assert cohort["candidate_count"] <= 5
    assert cohort["metric_dimension"] == "replay_richness"
    assert cohort["execution_candidates_materialized"] is False


def test_readiness_gate_and_boundary_block_execution_and_scaling():
    readiness = live17.build_lr6_live17_pilot_readiness_classification()
    gate = live17.build_lr6_live17_live18_eligibility_gate()
    boundary = live17.certify_lr6_live17_preparation_boundary()

    assert readiness["classification"] == "LIVE17_PREPARATION_READY_NOT_EXECUTABLE"
    assert readiness["may_execute_pilot"] is False
    assert gate["live18_gate"] == "LIVE18_TINY_PILOT_DRY_RUN_REHEARSAL_DISCUSSABLE"
    assert gate["execution_authorized"] is False

    assert boundary["pilot_execution_enabled"] is False
    assert boundary["live_persistence_enabled"] is False
    assert boundary["broad_replay_scaling_enabled"] is False
    assert boundary["replay_density_scaling_enabled"] is False
    assert boundary["schema_expansion_enabled"] is False
    assert boundary["direct_sql_allowed"] is False
    assert boundary["historical_row_rewrite_enabled"] is False
    assert boundary["prediction_enabled"] is False
    assert boundary["trading_enabled"] is False


def test_supervisor_review_and_markdown_sections():
    review = live17.build_lr6_live17_supervisor_review()
    assert review["live15_longitudinal_gate_reference"]["governance_only_eligibility"] is True
    md = live17.build_lr6_live17_markdown_report(review)
    required_sections = [
        "## objective",
        "## tiny pilot preparation module",
        "## deterministic pilot envelope",
        "## replay_richness-only candidate cohort",
        "## operator approval checklist",
        "## governance pre-flight checklist",
        "## observability readiness checklist",
        "## stop-condition readiness checklist",
        "## rollback readiness checklist",
        "## deterministic pilot readiness classification",
        "## LIVE18 eligibility gate",
        "## governance boundary certification",
    ]
    for section in required_sections:
        assert section in md


def test_report_file_exists():
    report_path = Path("reports/lr6_live17_tiny_bounded_replay_pilot_preparation_review.md")
    assert report_path.exists()
    assert "# LR6-LIVE17 — Tiny Bounded Replay Pilot Preparation Review" in report_path.read_text(encoding="utf-8")
