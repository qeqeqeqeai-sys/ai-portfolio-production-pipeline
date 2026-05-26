from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live8_replay_cohort_integrity_monitoring_and_regression_safeguards as live8,
)


def _row(i: int, **overrides):
    base = {
        "wave_id": "LR6_LIVE7_WAVE_ABC123",
        "duplicate_prevention_key": f"k{i}",
        "entity_id": f"E{i}",
        "metric_target": "replay_richness",
        "metric_dimension": "replay_richness",
        "evidence_status": "MEASURED",
        "comparison_ready": False,
        "scaffold_only": False,
        "adapter_name": "replay_richness_wave0_shadow_append_only_adapter",
        "execution_mode": "append_only_insert",
    }
    base.update(overrides)
    return base


def _historical_rows():
    return [{"wave_id": "LR6_LIVE5_WAVE_1FB274FE8C0A"}, {"wave_id": "LR6_LIVE5_WAVE_62418FB64AB0"}]


def test_valid_live7_cohort_passes_monitoring():
    review = live8.build_lr6_live8_supervisor_review(inserted_rows=[_row(1), _row(2)], historical_rows=_historical_rows())
    assert review["anomaly_classification"]["anomalies"][0]["anomaly"] == "NO_ANOMALY"
    assert review["anomaly_classification"]["live9_may_proceed"] is True


def test_multi_wave_batch_classified_as_anomaly():
    review = live8.build_lr6_live8_supervisor_review(
        inserted_rows=[_row(1, wave_id="LR6_LIVE7_WAVE_A"), _row(2, wave_id="LR6_LIVE7_WAVE_B")],
        historical_rows=_historical_rows(),
    )
    names = {a["anomaly"] for a in review["anomaly_classification"]["anomalies"]}
    assert "MULTI_WAVE_BATCH_ANOMALY" in names


def test_duplicate_key_batch_classified_as_anomaly():
    review = live8.build_lr6_live8_supervisor_review(inserted_rows=[_row(1), _row(2, duplicate_prevention_key="k1")], historical_rows=_historical_rows())
    names = {a["anomaly"] for a in review["anomaly_classification"]["anomalies"]}
    assert "DUPLICATE_KEY_ANOMALY" in names


def test_missing_entity_id_classified_as_anomaly():
    review = live8.build_lr6_live8_supervisor_review(inserted_rows=[_row(1), _row(2, entity_id="")], historical_rows=_historical_rows())
    names = {a["anomaly"] for a in review["anomaly_classification"]["anomalies"]}
    assert "MISSING_ENTITY_ID_ANOMALY" in names


def test_non_replay_richness_metric_classified():
    review = live8.build_lr6_live8_supervisor_review(inserted_rows=[_row(1, metric_target="topology_drift")], historical_rows=_historical_rows())
    names = {a["anomaly"] for a in review["anomaly_classification"]["anomalies"]}
    assert "METRIC_SCOPE_ANOMALY" in names


def test_append_only_boundary_violation_classified():
    review = live8.build_lr6_live8_supervisor_review(inserted_rows=[_row(1, execution_mode="upsert")], historical_rows=_historical_rows())
    names = {a["anomaly"] for a in review["anomaly_classification"]["anomalies"]}
    assert "APPEND_ONLY_BOUNDARY_ANOMALY" in names


def test_historical_live5_rows_remain_legacy_compatible():
    hist = live8.build_lr6_live8_historical_compatibility_monitor(historical_rows=_historical_rows())
    assert hist["live5_legacy_rows_present"] is True
    assert all(x == "legacy_pre_remediation" for x in hist["historical_legacy_classifications"])


def test_report_section_completeness_and_boundary_flags_and_forbidden_paths():
    review = live8.build_lr6_live8_supervisor_review(inserted_rows=[_row(1), _row(2)], historical_rows=_historical_rows())
    md = live8.build_lr6_live8_markdown_report(review)
    for sec in [
        "## objective",
        "## inspected invariants",
        "## cohort integrity findings",
        "## regression safeguard findings",
        "## anomaly classification matrix",
        "## LIVE5 historical compatibility",
        "## append-only/governance boundary certification",
        "## residual risks",
        "## LIVE9 recommendation",
    ]:
        assert sec in md

    boundary = live8.certify_lr6_live8_monitoring_boundary()
    assert boundary["scaling_enabled"] is False
    assert boundary["topology_drift_enabled"] is False
    assert boundary["contradiction_persistence_migration_enabled"] is False
    assert boundary["prediction_enabled"] is False
    assert boundary["trading_enabled"] is False
    assert boundary["auto_expansion_enabled"] is False
    assert boundary["schema_expansion_enabled"] is False
    assert boundary["historical_row_rewrite_enabled"] is False

    reg = review["regression_safeguard_findings"]
    assert reg["forbidden_write_paths_absent"] == {
        "update_path_detected": False,
        "delete_path_detected": False,
        "upsert_path_detected": False,
        "direct_sql_path_detected": False,
    }

    report_path = Path("reports/lr6_live8_replay_cohort_integrity_monitoring_and_regression_safeguards.md")
    report_path.write_text(md, encoding="utf-8")
    assert report_path.exists()
