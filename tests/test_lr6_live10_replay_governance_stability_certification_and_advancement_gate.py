from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live10_replay_governance_stability_certification_and_advancement_gate as live10,
)


def test_api_existence():
    for name in [
        "build_lr6_live10_governance_certification_context",
        "build_lr6_live10_stability_certification_review",
        "build_lr6_live10_advancement_gate_review",
        "build_lr6_live10_governance_confidence_review",
        "build_lr6_live10_allowed_advancement_scope",
        "build_lr6_live10_supervisor_review",
        "build_lr6_live10_markdown_report",
        "certify_lr6_live10_governance_boundary",
    ]:
        assert hasattr(live10, name)


def test_governance_context_and_gate_deterministic():
    assert live10.build_lr6_live10_governance_certification_context() == live10.build_lr6_live10_governance_certification_context()
    assert live10.build_lr6_live10_advancement_gate_review() == live10.build_lr6_live10_advancement_gate_review()


def test_stability_and_gate_classifications():
    stability = live10.build_lr6_live10_stability_certification_review()
    gate = live10.build_lr6_live10_advancement_gate_review()
    assert stability["classification"] in {"certified", "conditionally_certified", "not_certified"}
    assert gate["classification"] in {
        "ADVANCEMENT_BLOCKED",
        "ADVANCEMENT_CONDITIONALLY_ALLOWED",
        "ADVANCEMENT_READY_FOR_NEXT_STABILIZATION_PHASE",
    }


def test_confidence_boundedness_and_explainability():
    review = live10.build_lr6_live10_governance_confidence_review()
    score = review["governance_confidence_score"]
    assert review["score_bounds"] == {"min": 0.0, "max": 1.0}
    assert 0.0 <= score <= 1.0
    assert "not a trading" in review["explainability_note"].lower()


def test_allowed_disallowed_scope_and_forbidden_paths():
    scope = live10.build_lr6_live10_allowed_advancement_scope()
    assert "additional_dry_run_replay_simulations" in scope["allowed_scope"]
    forbidden = {"prediction", "trading", "schema_expansion", "direct_sql_bypass"}
    assert forbidden.issubset(set(scope["blocked_scope"]))


def test_boundary_flags_exactness_and_no_live_persistence_dependencies():
    boundary = live10.certify_lr6_live10_governance_boundary()
    assert boundary == {
        "governance_certification_only": True,
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


def test_supervisor_review_consistency_and_report_completeness():
    review = live10.build_lr6_live10_supervisor_review()
    assert review["stability_review"]["classification"] == "certified"
    assert review["advancement_gate"]["classification"] != "ADVANCEMENT_BLOCKED"
    md = live10.build_lr6_live10_markdown_report(review)
    required_sections = [
        "## objective",
        "## governance lineage",
        "## stability certification findings",
        "## advancement gate findings",
        "## governance confidence findings",
        "## allowed advancement scope",
        "## blocked advancement scope",
        "## governance boundary certification",
        "## residual risks",
        "## LIVE11 recommendation",
    ]
    for section in required_sections:
        assert section in md


def test_report_file_present_and_sections_complete():
    report_path = Path("reports/lr6_live10_replay_governance_stability_certification_and_advancement_gate.md")
    assert report_path.exists()
    contents = report_path.read_text(encoding="utf-8")
    for header in [
        "# LR6-LIVE10 — Replay Governance Stability Certification & Advancement Gate",
        "## objective",
        "## governance lineage",
        "## stability certification findings",
        "## advancement gate findings",
        "## governance confidence findings",
        "## allowed advancement scope",
        "## blocked advancement scope",
        "## governance boundary certification",
        "## residual risks",
        "## LIVE11 recommendation",
    ]:
        assert header in contents
