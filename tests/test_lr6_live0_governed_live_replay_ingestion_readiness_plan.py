from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_live0_blocked_metric_review,
    build_lr6_live0_conditional_metric_review,
    build_lr6_live0_failure_halt_conditions,
    build_lr6_live0_first_wave_scope_recommendation,
    build_lr6_live0_governance_requirement_review,
    build_lr6_live0_ingestion_wave_constraints,
    build_lr6_live0_markdown_report,
    build_lr6_live0_metric_ingestion_eligibility_review,
    build_lr6_live0_persistence_isolation_plan,
    build_lr6_live0_rate_limit_plan,
    build_lr6_live0_readiness_context,
    build_lr6_live0_supervisor_readiness_review,
    certify_lr6_live0_readiness_boundary,
)


def test_public_apis_exist_and_deterministic():
    first = build_lr6_live0_readiness_context()
    second = build_lr6_live0_readiness_context()
    assert first == second


def test_metric_eligibility_and_blocking_posture():
    review = build_lr6_live0_metric_ingestion_eligibility_review()["metric_posture"]
    assert review["replay_richness"]["eligibility"] == "conditionally_eligible_for_future_limited_ingestion_review"
    assert review["topology_drift"]["eligibility"] == "blocked_pending_longitudinal_comparison"
    assert review["contradiction_persistence_migration"]["eligibility"] == "blocked_pending_longitudinal_history"


def test_first_wave_is_bounded_and_conservative():
    constraints = build_lr6_live0_ingestion_wave_constraints()
    first_wave = build_lr6_live0_first_wave_scope_recommendation()
    assert constraints["entities_max"] <= 10
    assert first_wave["max_entities"] <= 10
    assert constraints["metric_whitelist"] == ["replay_richness"]


def test_governance_halt_persistence_rate_limits_exist():
    assert build_lr6_live0_governance_requirement_review()["required_approvals"]
    assert build_lr6_live0_failure_halt_conditions()["automatic_halt_conditions"]
    assert "isolated_target_table_strategy" in build_lr6_live0_persistence_isolation_plan()
    assert "entities_per_wave" in build_lr6_live0_rate_limit_plan()


def test_no_authorization_and_exact_boundary_flags():
    supervisor = build_lr6_live0_supervisor_readiness_review()
    assert supervisor["live_ingestion_authorized"] is False
    assert supervisor["persistence_authorized"] is False

    boundary = certify_lr6_live0_readiness_boundary()
    assert boundary == {
        "planning_only": True,
        "governance_review_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def test_report_sections_complete_and_planning_only_language():
    report = build_lr6_live0_markdown_report()
    required_sections = [
        "## objective",
        "## inspected prior EVID layers",
        "## metric eligibility review",
        "## blocked metrics review",
        "## conditional metrics review",
        "## governance requirements",
        "## first ingestion wave recommendation",
        "## ingestion constraints",
        "## rate limits",
        "## persistence isolation plan",
        "## halt/failure conditions",
        "## supervisor readiness review",
        "## realism warning",
        "## boundary certification",
        "## recommendation for next step",
    ]
    for section in required_sections:
        assert section in report

    forbidden_terms = [
        "execute replay",
        "INSERT INTO",
        "prediction logic",
        "trading signal",
        "live ingestion authorized",
    ]
    lowered = report.lower()
    for term in forbidden_terms:
        assert term.lower() not in lowered

    blocked = build_lr6_live0_blocked_metric_review()["blocked_or_not_ready_metrics"]
    conditional = build_lr6_live0_conditional_metric_review()["conditional_or_partial_metrics"]
    assert "topology_drift" in blocked
    assert "contradiction_persistence_migration" in blocked
    assert "replay_richness" in conditional
