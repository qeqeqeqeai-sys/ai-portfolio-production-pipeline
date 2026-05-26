from transmission_layers.expectation_failure.replay_ecology.lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution import (
    REQUIRED_APPROVAL_PHRASE,
    REQUIRED_EXECUTION_TOKEN,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_live5_first_approved_non_dry_persistence_execution_attempt import *


def _entities(n=3, metric="replay_richness"):
    return [{"entity_id": f"E{i}", "metric_dimension": metric} for i in range(1, n + 1)]


def test_apis_exist():
    required = [
        build_lr6_live5_execution_context, build_lr6_live5_approval_gate, build_lr6_live5_entity_wave_selection,
        build_lr6_live5_payload_preparation, build_lr6_live5_duplicate_prevention_review, build_lr6_live5_append_only_write_plan,
        build_lr6_live5_lineage_and_rollback_metadata, build_lr6_live5_halt_condition_monitor, execute_lr6_live5_approved_non_dry_attempt,
        build_lr6_live5_post_write_verification, build_lr6_live5_execution_summary, build_lr6_live5_supervisor_review,
        build_lr6_live5_markdown_report, certify_lr6_live5_execution_boundary,
    ]
    assert all(callable(f) for f in required)


def test_deterministic_output_and_duplicate_keys():
    a = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    b = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    assert a["duplicate_prevention_review"]["duplicate_keys"] == b["duplicate_prevention_review"]["duplicate_keys"]
    assert a["inserted_rows"] == b["inserted_rows"]


def test_missing_or_invalid_approval_aborts_before_write():
    miss = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(), approval_phrase="", execution_token=REQUIRED_EXECUTION_TOKEN)
    bad = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token="BAD")
    assert miss["persistence_attempted"] is False and miss["inserted_rows"] == 0
    assert bad["persistence_attempted"] is False and bad["inserted_rows"] == 0


def test_scope_and_metric_and_adapter_enforcement():
    overflow = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(7), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    assert overflow["approval_gate"]["checks"]["entity_count_leq_5"] is False
    wrong_metric = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(3, metric="other"), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    assert wrong_metric["persistence_attempted"] is True
    assert wrong_metric["inserted_rows"] >= 0
    assert wrong_metric["append_only_write_plan"]["target_name"] == "replay_richness_wave0_shadow"
    assert wrong_metric["append_only_write_plan"]["adapter_name"] == "replay_richness_wave0_shadow_append_only_adapter"


def test_lineage_rollback_halt_and_no_direct_sql_and_boundary_flags():
    res = execute_lr6_live5_approved_non_dry_attempt(entities=_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    assert res["lineage_and_rollback_metadata"]["lineage_retained"] is True
    assert res["lineage_and_rollback_metadata"]["rollback_metadata_present"] is True
    assert res["append_only_write_plan"]["direct_sql_used"] is False
    post = build_lr6_live5_post_write_verification(res)
    assert "persistence_attempted" in post and post["scaling_authorized"] is False
    boundary = certify_lr6_live5_execution_boundary()
    assert boundary == {
        "approved_non_dry_attempt": True,
        "execution_requires_explicit_approval": True,
        "metric_target": "replay_richness",
        "max_entities": 5,
        "append_only_required": True,
        "isolated_persistence_required": True,
        "direct_sql_used": False,
        "topology_metrics_enabled": False,
        "contradiction_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "scaling_authorized": False,
    }


def test_report_sections_complete():
    review = build_lr6_live5_supervisor_review(entities=_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    report = build_lr6_live5_markdown_report(review)
    for s in [
        "## objective", "## inspected LIVE4/LIVE3/LIVE2/LIVE1/EVID paths", "## approval gate review", "## tiny-wave scope",
        "## payload preparation", "## append-only write plan", "## duplicate prevention", "## lineage and rollback metadata",
        "## halt-condition review", "## execution attempt result", "## post-write verification", "## scaling recommendation",
        "## realism warning", "## boundary certification", "## recommendation for next step",
    ]:
        assert s in report
