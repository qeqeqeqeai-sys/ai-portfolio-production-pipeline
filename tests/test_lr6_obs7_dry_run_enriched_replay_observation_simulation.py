from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_obs7_contradiction_stress_review,
    build_lr6_obs7_dry_run_context,
    build_lr6_obs7_dry_run_readiness_decision,
    build_lr6_obs7_expected_review_artifacts,
    build_lr6_obs7_markdown_report,
    build_lr6_obs7_propagation_stress_review,
    build_lr6_obs7_simulated_observation_routes,
    build_lr6_obs7_simulated_wave_manifest,
    build_lr6_obs7_stop_condition_simulation,
    build_lr6_obs7_supervisor_review,
    build_lr6_obs7_weak_signal_stress_review,
    certify_lr6_obs7_dry_run_boundary,
)


def test_public_apis_and_determinism():
    review_a = build_lr6_obs7_supervisor_review()
    review_b = build_lr6_obs7_supervisor_review()
    assert review_a == review_b
    assert isinstance(build_lr6_obs7_dry_run_context(), dict)
    assert isinstance(build_lr6_obs7_simulated_wave_manifest(), dict)
    assert isinstance(build_lr6_obs7_simulated_observation_routes(), list)


def test_fallback_behavior_when_obs6_flag_missing():
    review = build_lr6_obs7_supervisor_review({"lr6_obs6_first_enriched_replay_wave_design": False})
    assert review["context"]["inspected_obs6_outputs"] is False
    assert "inspected_obs6_inputs" in review


def test_manifest_routes_and_reviews_exist_and_guardrails_hold():
    manifest = build_lr6_obs7_simulated_wave_manifest()
    assert manifest["dry_run"] is True
    assert manifest["execution_authorized"] is False
    assert manifest["no_persistence"] is True

    assert build_lr6_obs7_simulated_observation_routes()
    assert build_lr6_obs7_contradiction_stress_review()
    assert build_lr6_obs7_propagation_stress_review()
    assert build_lr6_obs7_weak_signal_stress_review()
    assert build_lr6_obs7_stop_condition_simulation()
    assert build_lr6_obs7_expected_review_artifacts()


def test_decision_boundary_and_markdown_sections_and_language_guards():
    decision = build_lr6_obs7_dry_run_readiness_decision()["decision"]
    assert decision in {
        "DRY_RUN_READY_FOR_GOVERNED_OBSERVATION_PROPOSAL",
        "DRY_RUN_CONDITIONALLY_READY_NEEDS_REBALANCE",
        "DRY_RUN_NOT_READY_REQUIRES_REDESIGN",
    }

    boundary = certify_lr6_obs7_dry_run_boundary()
    assert boundary == {
        "observation_only": True,
        "dry_run_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }

    markdown = build_lr6_obs7_markdown_report(build_lr6_obs7_supervisor_review()).lower()
    required_sections = [
        "objective",
        "inspected obs6 inputs",
        "dry-run boundary",
        "simulated wave manifest",
        "simulated observation routes",
        "contradiction stress review",
        "propagation stress review",
        "weak-signal stress review",
        "stop-condition simulation",
        "expected review artifacts",
        "dry-run readiness decision",
        "explicit non-authorization for execution",
        "architectural overengineering warning",
        "recommendation for next phase",
    ]
    for section in required_sections:
        assert section in markdown

    forbidden = [
        "select ", "insert ", "update ", "delete from", "persist to", "write to db", "execute trade", "buy ", "sell ", "run prediction", "forecast"
    ]
    for token in forbidden:
        assert token not in markdown
    assert "architecture_expansion_frozen" in str(boundary)
