from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_obs6_candidate_scores,
    build_lr6_obs6_execution_non_authorization_notice,
    build_lr6_obs6_first_wave_candidates,
    build_lr6_obs6_markdown_report,
    build_lr6_obs6_observation_questions,
    build_lr6_obs6_role_balance_review,
    build_lr6_obs6_selection_criteria,
    build_lr6_obs6_stop_conditions,
    build_lr6_obs6_supervisor_review,
    build_lr6_obs6_wave_design_context,
    certify_lr6_obs6_wave_design_boundary,
)


def test_public_apis_and_determinism():
    review_a = build_lr6_obs6_supervisor_review()
    review_b = build_lr6_obs6_supervisor_review()
    assert review_a == review_b
    assert isinstance(build_lr6_obs6_wave_design_context(), dict)
    assert isinstance(build_lr6_obs6_selection_criteria(), list)
    assert isinstance(build_lr6_obs6_candidate_scores(), list)


def test_fallback_when_obs4_obs5_missing_artifact_flags():
    review = build_lr6_obs6_supervisor_review(
        {
            "lr6_obs4_enriched_replay_candidate_universe": False,
            "lr6_obs5_enriched_universe_readiness_review": False,
        }
    )
    assert "inspected_obs4_inputs" in review
    assert "inspected_obs5_inputs" in review
    assert "selected_first_wave_candidates" in review


def test_wave_size_roles_and_deterministic_membership():
    wave_1 = build_lr6_obs6_first_wave_candidates()
    wave_2 = build_lr6_obs6_first_wave_candidates()
    assert wave_1 == wave_2
    assert 12 <= len(wave_1) <= 20
    roles = {r for c in wave_1 for r in c["roles"]}
    assert "weak_signal_secondary_bridges" in roles
    assert "cross_regime_contradiction_carriers" in roles
    assert any(r in roles for r in ("grid_utilities_power_demand", "telecom_infrastructure", "data_center_infrastructure", "logistics_supply_chain"))


def test_reviews_questions_stops_and_non_authorization():
    role_balance = build_lr6_obs6_role_balance_review()
    assert role_balance["selected_candidate_count"] >= 12
    assert isinstance(build_lr6_obs6_observation_questions(), list)
    assert isinstance(build_lr6_obs6_stop_conditions(), list)
    notice = build_lr6_obs6_execution_non_authorization_notice()
    assert notice["execution_authorized"] is False


def test_boundary_flags_and_report_sections_and_language_guards():
    boundary = certify_lr6_obs6_wave_design_boundary()
    assert boundary == {
        "observation_only": True,
        "design_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }

    markdown = build_lr6_obs6_markdown_report(build_lr6_obs6_supervisor_review()).lower()
    required_sections = [
        "objective",
        "inspected obs4/obs5 inputs",
        "readiness basis",
        "selection criteria",
        "selected first-wave candidates",
        "role balance review",
        "observation questions",
        "stop conditions",
        "explicit non-authorization for execution",
        "architectural overengineering warning",
        "recommendation for next phase",
    ]
    for section in required_sections:
        assert section in markdown

    forbidden = [
        "select ", "insert ", "update ", "delete from", "persist to", "write to db", "execute trade", "buy ", "sell ", "prediction", "forecast"
    ]
    for token in forbidden:
        assert token not in markdown
    assert "architecture_expansion_frozen" in str(boundary)
