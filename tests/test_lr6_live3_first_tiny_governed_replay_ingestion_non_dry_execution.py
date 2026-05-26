from transmission_layers.expectation_failure.replay_ecology.lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution import (
    REQUIRED_APPROVAL_PHRASE,
    REQUIRED_EXECUTION_TOKEN,
    TARGET_METRIC,
    build_lr6_live3_append_only_persistence_plan,
    build_lr6_live3_duplicate_prevention_keys,
    build_lr6_live3_entity_wave_selection,
    build_lr6_live3_execution_context,
    build_lr6_live3_execution_summary,
    build_lr6_live3_governance_verification,
    build_lr6_live3_halt_condition_monitor,
    build_lr6_live3_lineage_retention_plan,
    build_lr6_live3_markdown_report,
    build_lr6_live3_payload_preparation,
    build_lr6_live3_post_wave_review,
    build_lr6_live3_rollback_metadata,
    build_lr6_live3_supervisor_review,
    certify_lr6_live3_execution_boundary,
    execute_lr6_live3_non_dry_wave,
)


def _entities(n=6):
    return [
        {"entity_id": f"E{i}", "cluster": "C1", "role": f"R{i}", "metric_dimension": TARGET_METRIC}
        for i in range(1, n + 1)
    ]


def test_public_apis_exist():
    assert callable(build_lr6_live3_execution_context)
    assert callable(build_lr6_live3_governance_verification)
    assert callable(build_lr6_live3_entity_wave_selection)
    assert callable(build_lr6_live3_payload_preparation)
    assert callable(build_lr6_live3_duplicate_prevention_keys)
    assert callable(build_lr6_live3_append_only_persistence_plan)
    assert callable(build_lr6_live3_lineage_retention_plan)
    assert callable(build_lr6_live3_rollback_metadata)
    assert callable(build_lr6_live3_halt_condition_monitor)
    assert callable(execute_lr6_live3_non_dry_wave)
    assert callable(build_lr6_live3_execution_summary)
    assert callable(build_lr6_live3_post_wave_review)
    assert callable(build_lr6_live3_supervisor_review)
    assert callable(build_lr6_live3_markdown_report)
    assert callable(certify_lr6_live3_execution_boundary)


def test_governance_failure_aborts_before_persistence():
    out = execute_lr6_live3_non_dry_wave(entities=_entities(), approval_phrase="bad", execution_token="bad")
    assert out["aborted"] is True
    assert out["persistence_executed"] is False
    assert out["abort_reason"] == "governance_failure"


def test_scope_and_metric_enforced_and_deterministic():
    s1 = build_lr6_live3_entity_wave_selection(_entities(8), max_entities=99)
    s2 = build_lr6_live3_entity_wave_selection(_entities(8), max_entities=99)
    assert s1 == s2
    assert s1["entity_count"] <= 5
    payloads = build_lr6_live3_payload_preparation(s1)
    assert all(p["metric_dimension"] == TARGET_METRIC for p in payloads["prepared_payloads"])


def test_duplicate_keys_deterministic_and_append_only_enforced():
    selection = build_lr6_live3_entity_wave_selection(_entities())
    payloads = build_lr6_live3_payload_preparation(selection)
    d1 = build_lr6_live3_duplicate_prevention_keys(payloads["prepared_payloads"])
    d2 = build_lr6_live3_duplicate_prevention_keys(payloads["prepared_payloads"])
    assert d1 == d2
    assert d1["duplicates_found"] is False
    plan = build_lr6_live3_append_only_persistence_plan(payloads["prepared_payloads"], d1)
    assert plan["append_only"] is True
    assert plan["direct_sql_used"] is False


def test_lineage_rollback_halt_and_summary_review_boundary_report():
    selection = build_lr6_live3_entity_wave_selection(_entities())
    payloads = build_lr6_live3_payload_preparation(selection)
    dup = build_lr6_live3_duplicate_prevention_keys(payloads["prepared_payloads"])
    plan = build_lr6_live3_append_only_persistence_plan(payloads["prepared_payloads"], dup)
    lineage = build_lr6_live3_lineage_retention_plan(payloads["prepared_payloads"])
    rollback = build_lr6_live3_rollback_metadata(payloads["prepared_payloads"])
    gov = build_lr6_live3_governance_verification(build_lr6_live3_execution_context(approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN))
    halt = build_lr6_live3_halt_condition_monitor(governance=gov, prepared_payloads=payloads["prepared_payloads"], duplicate_keys=dup, persistence_plan=plan, lineage_plan=lineage, rollback_plan=rollback)
    assert lineage["lineage_refs_retained"] is True
    assert rollback["rollback_ready"] is True
    assert halt["halt_triggered"] is False

    exec_ok = execute_lr6_live3_non_dry_wave(entities=_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    summary = build_lr6_live3_execution_summary(exec_ok)
    post = build_lr6_live3_post_wave_review(exec_ok)
    boundary = certify_lr6_live3_execution_boundary()
    review = build_lr6_live3_supervisor_review(_entities(), approval_phrase=REQUIRED_APPROVAL_PHRASE, execution_token=REQUIRED_EXECUTION_TOKEN)
    md = build_lr6_live3_markdown_report(review)

    assert isinstance(summary, dict) and "payloads_inserted" in summary
    assert isinstance(post, dict) and "recommendation" in post
    assert boundary == {
        "governed_non_dry_execution": True,
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
        "rollback_metadata_required": True,
        "lineage_retention_required": True,
    }
    required_sections = [
        "## objective",
        "## inspected LIVE2/LIVE1/LIVE0/EVID paths",
        "## governance verification",
        "## tiny-wave execution scope",
        "## payload preparation review",
        "## append-only persistence review",
        "## duplicate prevention review",
        "## lineage retention review",
        "## rollback metadata review",
        "## halt-condition review",
        "## execution summary",
        "## post-wave review",
        "## realism warning",
        "## boundary certification",
        "## recommendation for next step",
    ]
    for sec in required_sections:
        assert sec in md
