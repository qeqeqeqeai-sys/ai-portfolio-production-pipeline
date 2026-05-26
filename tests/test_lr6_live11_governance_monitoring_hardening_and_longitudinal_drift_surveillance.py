from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live11_governance_monitoring_hardening_and_longitudinal_drift_surveillance as live11,
)


def test_api_existence():
    for name in [
        "build_lr6_live11_governance_telemetry_context",
        "build_lr6_live11_governance_snapshot",
        "build_lr6_live11_snapshot_series",
        "build_lr6_live11_governance_drift_review",
        "build_lr6_live11_drift_classification",
        "build_lr6_live11_longitudinal_trend_review",
        "build_lr6_live11_governance_degradation_review",
        "build_lr6_live11_governance_safeguards",
        "build_lr6_live11_supervisor_review",
        "build_lr6_live11_markdown_report",
        "certify_lr6_live11_governance_monitoring_boundary",
    ]:
        assert hasattr(live11, name)


def test_scenario_determinism_stable_degrading_improving():
    for scenario in ["stable", "degrading", "improving"]:
        assert live11.build_lr6_live11_snapshot_series(scenario=scenario) == live11.build_lr6_live11_snapshot_series(scenario=scenario)
        assert live11.build_lr6_live11_longitudinal_trend_review(scenario=scenario) == live11.build_lr6_live11_longitudinal_trend_review(scenario=scenario)


def test_stable_scenario_not_forced_high_drift_and_live12_not_blocked():
    drift = live11.build_lr6_live11_governance_drift_review(scenario="stable")
    assert drift["drift_classification"]["classification"] in {"NO_GOVERNANCE_DRIFT", "LOW_GOVERNANCE_DRIFT"}
    review = live11.build_lr6_live11_supervisor_review(scenario="stable")
    assert review["live12_recommendation"] == "allow_live12_with_monitoring_hardening_guardrails"


def test_degrading_scenario_can_trigger_high_drift_and_live12_blocked():
    drift = live11.build_lr6_live11_governance_drift_review(scenario="degrading")
    assert drift["drift_classification"]["classification"] in {"MODERATE_GOVERNANCE_DRIFT", "HIGH_GOVERNANCE_DRIFT"}
    assert drift["drift_classification"]["live12_may_proceed_safely"] is False
    review = live11.build_lr6_live11_supervisor_review(scenario="degrading")
    assert review["live12_recommendation"] == "defer_live12_pending_governance_remediation"


def test_improving_scenario_supported_and_not_forced_degradation():
    drift = live11.build_lr6_live11_governance_drift_review(scenario="improving")
    assert drift["drift_classification"]["classification"] in {"NO_GOVERNANCE_DRIFT", "LOW_GOVERNANCE_DRIFT"}


def test_safeguards_activate_by_scenario():
    stable = live11.build_lr6_live11_governance_safeguards(scenario="stable")
    degrading = live11.build_lr6_live11_governance_safeguards(scenario="degrading")
    assert stable["require_operator_signoff_before_live12"] is False
    assert degrading["require_operator_signoff_before_live12"] is True


def test_boundary_flags_exact_and_no_forbidden_paths():
    boundary = live11.certify_lr6_live11_governance_monitoring_boundary()
    assert boundary == {
        "governance_monitoring_only": True,
        "longitudinal_surveillance_only": True,
        "live_persistence_enabled": False,
        "scaling_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only": True,
        "append_only_required": True,
        "deterministic_governance_required": True,
    }


def test_supervisor_review_consistency_and_report_sections():
    review = live11.build_lr6_live11_supervisor_review(scenario="stable")
    assert review["governance_telemetry_context"]["telemetry_layer_mode"] == "neutral_observational"
    assert len(review["governance_continuity_snapshots"]) == 5
    assert review["governance_boundary_certification"]["scaling_enabled"] is False
    md = live11.build_lr6_live11_markdown_report(review)
    for section in [
        "## objective",
        "## governance telemetry context",
        "## governance continuity snapshots",
        "## longitudinal drift findings",
        "## drift classifications",
        "## governance trend findings",
        "## governance degradation safeguards",
        "## governance continuity assessment",
        "## governance boundary certification",
        "## residual risks",
        "## LIVE12 recommendation",
    ]:
        assert section in md


def test_report_file_present_and_complete():
    report_path = Path("reports/lr6_live11_governance_monitoring_hardening_and_longitudinal_drift_surveillance.md")
    assert report_path.exists()
    contents = report_path.read_text(encoding="utf-8")
    for header in [
        "# LR6-LIVE11 — Governance Monitoring Hardening & Longitudinal Drift Surveillance",
        "## objective",
        "## governance telemetry context",
        "## governance continuity snapshots",
        "## longitudinal drift findings",
        "## drift classifications",
        "## governance trend findings",
        "## governance degradation safeguards",
        "## governance continuity assessment",
        "## governance boundary certification",
        "## residual risks",
        "## LIVE12 recommendation",
    ]:
        assert header in contents
