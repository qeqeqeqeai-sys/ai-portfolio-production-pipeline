from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_obs8_approval_gate_requirements,
    build_lr6_obs8_execution_non_authorization_notice,
    build_lr6_obs8_expected_execution_artifacts,
    build_lr6_obs8_fail_closed_conditions,
    build_lr6_obs8_first_wave_governed_manifest,
    build_lr6_obs8_governance_requirements,
    build_lr6_obs8_markdown_report,
    build_lr6_obs8_proposal_context,
    build_lr6_obs8_stop_after_first_wave_policy,
    build_lr6_obs8_supervisor_review,
    build_lr6_obs8_verification_requirements,
    certify_lr6_obs8_governed_proposal_boundary,
)


def test_public_apis_and_determinism():
    review_a = build_lr6_obs8_supervisor_review()
    review_b = build_lr6_obs8_supervisor_review()
    assert review_a == review_b
    assert isinstance(build_lr6_obs8_proposal_context(), dict)
    assert isinstance(build_lr6_obs8_governance_requirements(), list)
    assert isinstance(build_lr6_obs8_approval_gate_requirements(), dict)


def test_fallback_behavior_when_obs6_obs7_flags_missing():
    review = build_lr6_obs8_supervisor_review(
        {
            "lr6_obs6_first_enriched_replay_wave_design": False,
            "lr6_obs7_dry_run_enriched_replay_observation_simulation": False,
        }
    )
    assert review["context"]["inspected_obs6_outputs"] is False
    assert review["context"]["inspected_obs7_outputs"] is False
    assert "inspected_obs6_inputs" in review
    assert "inspected_obs7_inputs" in review


def test_manifest_and_governance_structures_exist():
    manifest = build_lr6_obs8_first_wave_governed_manifest()
    assert manifest["selected_count"] == 16
    assert manifest["execution_authorized"] is False
    assert manifest["governed_execution_proposed_only"] is True
    assert manifest["dry_run_prevalidated"] is True
    assert manifest["roles_represented"]

    assert build_lr6_obs8_expected_execution_artifacts()
    assert build_lr6_obs8_stop_after_first_wave_policy()
    assert build_lr6_obs8_verification_requirements()
    assert build_lr6_obs8_fail_closed_conditions()
    assert build_lr6_obs8_execution_non_authorization_notice()["execution_authorized"] is False


def test_boundary_and_report_sections_and_language_guards():
    boundary = certify_lr6_obs8_governed_proposal_boundary()
    assert boundary == {
        "observation_only": True,
        "proposal_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }

    markdown = build_lr6_obs8_markdown_report(build_lr6_obs8_supervisor_review()).lower()
    required_sections = [
        "objective",
        "inspected obs6/obs7 inputs",
        "governance rationale",
        "approval gate requirements",
        "first-wave governed manifest",
        "expected execution artifacts",
        "stop-after-first-wave policy",
        "verification requirements",
        "fail-closed conditions",
        "explicit non-authorization notice",
        "architectural overengineering warning",
        "recommendation for next phase",
    ]
    for section in required_sections:
        assert section in markdown

    forbidden = [
        "select ", "insert ", "update ", "delete from", "persist to", "write to db",
        "execute trade", "buy ", "sell ", "run prediction", "forecast"
    ]
    for token in forbidden:
        assert token not in markdown
    assert "architecture_expansion_frozen" in str(boundary)
