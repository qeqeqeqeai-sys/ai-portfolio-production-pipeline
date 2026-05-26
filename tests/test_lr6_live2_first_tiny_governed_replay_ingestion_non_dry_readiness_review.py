from transmission_layers.expectation_failure.replay_ecology.lr6_live2_first_tiny_governed_replay_ingestion_non_dry_readiness_review import (
    build_lr6_live2_append_only_readiness_review,
    build_lr6_live2_duplicate_key_review,
    build_lr6_live2_governance_pass_review,
    build_lr6_live2_halt_trigger_review,
    build_lr6_live2_lineage_readiness_review,
    build_lr6_live2_live1_dry_run_result_review,
    build_lr6_live2_markdown_report,
    build_lr6_live2_non_dry_gate_requirements,
    build_lr6_live2_non_dry_readiness_recommendation,
    build_lr6_live2_payload_validity_review,
    build_lr6_live2_readiness_context,
    build_lr6_live2_rollback_readiness_review,
    build_lr6_live2_shadow_persistence_readiness_review,
    build_lr6_live2_supervisor_review,
    certify_lr6_live2_readiness_boundary,
)


def test_public_apis_exist_and_deterministic_output():
    context1 = build_lr6_live2_readiness_context()
    context2 = build_lr6_live2_readiness_context()
    assert context1 == context2
    assert build_lr6_live2_live1_dry_run_result_review(context1)["passed"] is True
    assert build_lr6_live2_governance_pass_review(context1)["governance_passed"] is True
    assert build_lr6_live2_halt_trigger_review(context1)["passed"] is True
    assert build_lr6_live2_payload_validity_review(context1)["passed"] is True
    assert build_lr6_live2_duplicate_key_review(context1)["passed"] is True
    assert build_lr6_live2_append_only_readiness_review(context1)["passed"] is True
    assert build_lr6_live2_shadow_persistence_readiness_review(context1)["passed"] is True
    assert build_lr6_live2_rollback_readiness_review(context1)["passed"] is True
    assert build_lr6_live2_lineage_readiness_review(context1)["passed"] is True


def test_recommendation_non_authorizing_even_when_conditionally_ready():
    review = build_lr6_live2_supervisor_review()
    rec = review["non_dry_readiness_recommendation"]
    assert rec["readiness_classification"] in {
        "conditionally_ready_for_tiny_non_dry_execution",
        "ready_but_requires_explicit_operator_approval",
        "not_ready",
        "blocked",
    }
    assert rec["execution_authorized"] is False
    assert rec["persistence_authorized"] is False
    assert rec["live_ingestion_authorized"] is False


def test_failure_case_blocked_or_not_ready():
    failing = {
        "governance_passed": False,
        "halt_triggered": True,
        "critical_halt_count": 1,
        "payloads_prepared": 0,
        "payloads_rejected": 1,
        "rejected_payloads_safely_quarantined": False,
        "unsafe_promotion_count": 1,
        "duplicate_prevention_keys_deterministic": False,
        "append_only_simulation_passed": False,
        "shadow_persistence_simulation_passed": False,
        "rollback_ready": False,
        "lineage_complete": False,
        "isolated_persistence_target_adequate": False,
        "metric_dimensions": ["replay_richness", "other_metric"],
        "entity_count": 8,
        "persisted": False,
        "dry_run_only": True,
        "explicit_non_dry_operator_approval_required": True,
    }
    context = build_lr6_live2_readiness_context(failing)
    rec = build_lr6_live2_non_dry_readiness_recommendation(context)
    assert rec["readiness_classification"] in {"blocked", "not_ready"}
    assert rec["execution_authorized"] is False


def test_boundary_and_scope_flags_and_report_sections():
    boundary = certify_lr6_live2_readiness_boundary()
    assert boundary == {
        "non_dry_readiness_review_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": "replay_richness",
        "max_entities": 5,
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }

    gates = build_lr6_live2_non_dry_gate_requirements()
    assert gates["metric_whitelist_confirmation"] == ["replay_richness"]
    assert gates["entity_limit_confirmation_max"] <= 5

    report = build_lr6_live2_markdown_report()
    required_sections = [
        "## objective",
        "## inspected LIVE1/LIVE0/EVID paths",
        "## LIVE1 dry-run result review",
        "## governance pass review",
        "## halt trigger review",
        "## payload validity review",
        "## duplicate key review",
        "## append-only readiness review",
        "## shadow persistence readiness review",
        "## rollback readiness review",
        "## lineage readiness review",
        "## non-dry gate requirements",
        "## non-dry readiness recommendation",
        "## supervisor decision",
        "## realism warning",
        "## boundary certification",
        "## recommendation for next step",
    ]
    for section in required_sections:
        assert section in report
    review = build_lr6_live2_supervisor_review()
    rec = review["non_dry_readiness_recommendation"]
    assert rec["execution_authorized"] is False
    assert rec["persistence_authorized"] is False
    assert rec["live_ingestion_authorized"] is False
