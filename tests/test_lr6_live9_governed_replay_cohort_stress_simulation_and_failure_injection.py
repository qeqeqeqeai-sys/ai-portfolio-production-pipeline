from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live9_governed_replay_cohort_stress_simulation_and_failure_injection as live9,
)


def test_api_existence_and_context_flags():
    for name in [
        "build_lr6_live9_stress_simulation_context",
        "build_lr6_live9_synthetic_failure_cohorts",
        "run_lr6_live9_failure_injection_suite",
        "build_lr6_live9_stress_result_summary",
        "build_lr6_live9_supervisor_review",
        "build_lr6_live9_markdown_report",
        "certify_lr6_live9_stress_boundary",
    ]:
        assert hasattr(live9, name)

    ctx = live9.build_lr6_live9_stress_simulation_context()
    assert ctx["simulation_only"] is True
    assert ctx["synthetic_only"] is True
    assert ctx["no_live_write_certified"] is True


def test_synthetic_cohort_determinism_and_no_persistence_dependency():
    c1 = live9.build_lr6_live9_synthetic_failure_cohorts()
    c2 = live9.build_lr6_live9_synthetic_failure_cohorts()
    assert c1 == c2

    module_text = Path(
        "transmission_layers/expectation_failure/replay_ecology/lr6_live9_governed_replay_cohort_stress_simulation_and_failure_injection.py"
    ).read_text(encoding="utf-8")
    assert "supabase" not in module_text.lower()
    assert "from supabase" not in module_text.lower()
    assert "supabase." not in module_text.lower()


def test_expected_anomalies_and_blocking_behaviors():
    suite = live9.run_lr6_live9_failure_injection_suite()
    got = {r["cohort_name"]: r for r in suite["simulation_results"]}

    assert got["valid_control_cohort"]["actual_anomalies"] == ["NO_ANOMALY"]
    assert got["multi_wave_failure_cohort"]["failure_caught"] is True
    assert got["duplicate_key_failure_cohort"]["failure_caught"] is True
    assert got["missing_entity_id_failure_cohort"]["failure_caught"] is True
    assert got["metric_scope_failure_cohort"]["failure_caught"] is True
    assert got["append_only_boundary_failure_cohort"]["failure_caught"] is True
    assert got["over_bound_failure_cohort"]["failure_caught"] is True
    assert got["historical_compatibility_failure_case"]["failure_caught"] is True
    assert all(r["blocking_behavior_correct"] for r in suite["simulation_results"])


def test_report_sections_boundary_flags_forbidden_expansion_and_summary_correctness():
    review = live9.build_lr6_live9_supervisor_review()
    md = live9.build_lr6_live9_markdown_report(review)
    for sec in [
        "## objective",
        "## simulation-only boundary",
        "## synthetic cohort inventory",
        "## expected anomaly matrix",
        "## actual detection results",
        "## missed/false-positive review",
        "## append-only/governance boundary certification",
        "## residual risks",
        "## LIVE10 recommendation",
    ]:
        assert sec in md

    boundary = live9.certify_lr6_live9_stress_boundary()
    assert boundary == {
        "simulation_only": True,
        "synthetic_only": True,
        "live_persistence_enabled": False,
        "direct_sql_enabled": False,
        "scaling_enabled": False,
        "new_metrics_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only_expected": True,
    }

    summary = review["stress_summary"]
    assert summary["total_cohorts_simulated"] == 8
    assert summary["passed_simulations"] == 8
    assert summary["failed_simulations"] == 0
    assert summary["caught_anomalies"] == 7
    assert summary["missed_anomalies"] == 0
    assert summary["false_positives"] == 0
    assert summary["false_negatives"] == 0
    assert summary["blocking_behavior_correct"] is True
    assert summary["aggregate_pass"] is True

    report_path = Path("reports/lr6_live9_governed_replay_cohort_stress_simulation_and_failure_injection.md")
    report_path.write_text(md, encoding="utf-8")
    assert report_path.exists()
