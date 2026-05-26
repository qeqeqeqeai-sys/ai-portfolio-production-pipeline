from transmission_layers.expectation_failure.replay_ecology.lr6_live4_first_non_dry_execution_result_verification import (
    build_lr6_live4_append_only_verification,
    build_lr6_live4_duplicate_prevention_review,
    build_lr6_live4_halt_condition_review,
    build_lr6_live4_inserted_row_review,
    build_lr6_live4_lineage_retention_review,
    build_lr6_live4_markdown_report,
    build_lr6_live4_payload_rejection_review,
    build_lr6_live4_persistence_event_review,
    build_lr6_live4_persistence_target_review,
    build_lr6_live4_rollback_metadata_review,
    build_lr6_live4_scaling_recommendation,
    build_lr6_live4_scope_compliance_review,
    build_lr6_live4_supervisor_verification,
    build_lr6_live4_verification_context,
    certify_lr6_live4_verification_boundary,
    inspect_lr6_live4_live3_execution_surface,
)


def _summary(**kw):
    base = {
        "persistence_executed": False,
        "append_only_plan_defined": True,
        "payloads_inserted": None,
        "approved_persistence_adapter_called": False,
        "persistence_target": "replay_richness_wave0_shadow",
        "duplicate_prevented": True,
        "append_only": True,
        "lineage_refs_retained": True,
        "rollback_ready": True,
        "halt_triggered": False,
        "metric_target": "replay_richness",
        "entity_count": 5,
    }
    base.update(kw)
    return base


def test_public_apis_exist_and_deterministic():
    ctx = build_lr6_live4_verification_context(live3_summary=_summary())
    assert ctx == build_lr6_live4_verification_context(live3_summary=_summary())


def test_absent_evidence_no_insert_claim_and_guarded_classification():
    ctx = build_lr6_live4_verification_context(live3_summary=_summary())
    surface = inspect_lr6_live4_live3_execution_surface(ctx)
    rows = build_lr6_live4_inserted_row_review(ctx)
    assert surface["classification"] == "guarded_execution_path_defined_only"
    assert rows["inserted_rows"] == 0
    assert rows["evidence_present"] is False


def test_simulated_vs_verified_classification():
    sim = build_lr6_live4_verification_context(live3_summary=_summary(persistence_executed=True, payloads_inserted=2, approved_persistence_adapter_called=False))
    ver = build_lr6_live4_verification_context(live3_summary=_summary(persistence_executed=True, payloads_inserted=2, approved_persistence_adapter_called=True))
    assert inspect_lr6_live4_live3_execution_surface(sim)["classification"] == "persistence_event_simulated_only"
    assert inspect_lr6_live4_live3_execution_surface(ver)["classification"] == "tiny_non_dry_persistence_verified"


def test_inserted_row_review_zero_nonzero():
    zero = build_lr6_live4_inserted_row_review(build_lr6_live4_verification_context(live3_summary=_summary(payloads_inserted=0, persisted_rows=0)))
    nonzero = build_lr6_live4_inserted_row_review(build_lr6_live4_verification_context(live3_summary=_summary(payloads_inserted=3, persisted_rows=3)))
    assert zero["inserted_rows"] == 0
    assert nonzero["inserted_rows"] == 3


def test_target_scope_and_controls_reviews():
    ctx = build_lr6_live4_verification_context(live3_summary=_summary())
    assert build_lr6_live4_persistence_target_review(ctx)["target_approved"] is True
    assert isinstance(build_lr6_live4_duplicate_prevention_review(ctx), dict)
    assert isinstance(build_lr6_live4_append_only_verification(ctx), dict)
    assert isinstance(build_lr6_live4_lineage_retention_review(ctx), dict)
    assert isinstance(build_lr6_live4_rollback_metadata_review(ctx), dict)
    assert isinstance(build_lr6_live4_halt_condition_review(ctx), dict)
    assert isinstance(build_lr6_live4_payload_rejection_review(ctx), dict)


def test_scope_and_scaling_and_boundary_flags():
    ctx = build_lr6_live4_verification_context(live3_summary=_summary(entity_count=6))
    scope = build_lr6_live4_scope_compliance_review(ctx)
    assert scope["replay_richness_only"] is True
    assert scope["entity_cap_respected"] is False
    scaling = build_lr6_live4_scaling_recommendation(all_checks_passed=True, classification="tiny_non_dry_persistence_verified")
    assert scaling["scaling_authorized"] is False
    boundary = certify_lr6_live4_verification_boundary()
    expected = {
        "verification_only": True,
        "new_execution_authorized": False,
        "new_persistence_authorized": False,
        "live_ingestion_expansion_authorized": False,
        "scaling_authorized": False,
        "metric_target": "replay_richness",
        "max_verified_entities": 5,
        "all_seven_metrics_implemented": False,
        "direct_sql_used": False,
        "topology_metrics_enabled": False,
        "contradiction_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
    }
    assert boundary == expected


def test_report_sections_complete_and_supervisor_verification_conservative():
    review = build_lr6_live4_supervisor_verification(live3_summary=_summary())
    md = build_lr6_live4_markdown_report(review)
    for heading in [
        "## objective",
        "## inspected LIVE3/LIVE2/LIVE1/LIVE0/EVID paths",
        "## LIVE3 execution surface review",
        "## persistence event review",
        "## inserted row review",
        "## persistence target review",
        "## duplicate prevention review",
        "## append-only verification",
        "## lineage retention review",
        "## rollback metadata review",
        "## halt-condition review",
        "## payload rejection/quarantine review",
        "## scope compliance review",
        "## scaling recommendation",
        "## realism warning",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert heading in md
    assert "prediction" in str(review["boundary_certification"]) and review["boundary_certification"]["prediction_enabled"] is False


def test_persistence_event_review_api():
    ctx = build_lr6_live4_verification_context(live3_summary=_summary())
    surface = inspect_lr6_live4_live3_execution_surface(ctx)
    out = build_lr6_live4_persistence_event_review(ctx, surface)
    assert isinstance(out, dict)
