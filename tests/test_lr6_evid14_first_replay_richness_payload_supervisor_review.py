from transmission_layers.expectation_failure.replay_ecology import (
    build_lr6_evid14_review_context,
    build_lr6_evid14_payload_meaningfulness_criteria,
    review_lr6_evid14_replay_richness_payload,
    build_lr6_evid14_signal_sufficiency_review,
    build_lr6_evid14_payload_shallowness_review,
    build_lr6_evid14_persistence_readiness_review,
    build_lr6_evid14_live_ingestion_readiness_review,
    build_lr6_evid14_governed_emission_recommendation,
    build_lr6_evid14_supervisor_review,
    build_lr6_evid14_markdown_report,
    certify_lr6_evid14_review_boundary,
)


def test_public_apis_exist_and_deterministic():
    a = build_lr6_evid14_supervisor_review()
    b = build_lr6_evid14_supervisor_review()
    assert a == b
    assert isinstance(build_lr6_evid14_review_context(), dict)
    assert isinstance(build_lr6_evid14_markdown_report(), str)


def test_meaningfulness_criteria_exist():
    criteria = build_lr6_evid14_payload_meaningfulness_criteria()
    expected = {
        "has_valid_measured_status",
        "has_structured_lineage",
        "has_nonzero_entity_count",
        "has_role_diversity",
        "has_cluster_diversity",
        "has_nontrivial_diversity_ratio",
        "concentration_warning_absent_or_explained",
        "comparison_ready_supported",
        "dry_run_caveat_present",
        "no_scaffold_or_narrative_promotion",
        "sufficient_for_persistence_consideration",
        "sufficient_for_live_ingestion_consideration",
    }
    assert expected.issubset(criteria.keys())


def test_shallow_and_rejected_behaviors():
    sup = build_lr6_evid14_supervisor_review()
    res = sup["reviewed_sample_results"]
    assert res["shallow_measured_payload"]["classification"] == "mechanically_valid_but_shallow"
    assert res["scaffold_rejected_payload"]["classification"] == "unsafe_or_not_measured"
    assert res["missing_lineage_payload"]["classification"] == "insufficient_lineage"
    assert res["comparison_not_ready_payload"]["classification"] == "comparison_not_ready"
    assert res["comparison_not_ready_payload"]["criteria_checks"]["comparison_ready_supported"] is False


def test_readiness_and_recommendation_safety():
    sup = build_lr6_evid14_supervisor_review()
    persistence = sup["persistence_readiness_review"]
    live = sup["live_ingestion_readiness_review"]
    gov = sup["governed_emission_recommendation"]

    assert persistence["persistence_authorized"] is False
    assert live["live_ingestion_readiness"] == "not_ready"
    assert gov["authorizes_writes"] is False
    assert gov["persistence_authorized"] is False


def test_boundary_flags_exact_and_no_execution_paths():
    boundary = certify_lr6_evid14_review_boundary()
    expected = {
        "review_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": "replay_richness",
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "no_interpretation_claims": True,
        "architecture_expansion_frozen": True,
    }
    assert boundary == expected


def test_report_includes_required_sections():
    md = build_lr6_evid14_markdown_report().lower()
    for section in [
        "objective",
        "inspected evid11/evid12/evid13 path",
        "supervisor meaningfulness criteria",
        "reviewed sample payloads",
        "signal sufficiency review",
        "payload shallowness review",
        "persistence readiness review",
        "live ingestion readiness review",
        "governed emission recommendation",
        "boundary certification",
        "recommendation for next step",
    ]:
        assert section in md


def test_standalone_review_helpers():
    payload = {
        "evidence_status": "MEASURED",
        "replay_entity_count": 5,
        "distinct_candidate_count": 2,
        "distinct_role_count": 2,
        "distinct_cluster_count": 2,
        "source_artifact_refs": ["artifact://x"],
        "measurement_basis": "structured_observation",
        "comparison_ready": False,
        "dry_run_caveat": "yes",
    }
    out = review_lr6_evid14_replay_richness_payload(payload)
    suff = build_lr6_evid14_signal_sufficiency_review({"x": out})
    shallow = build_lr6_evid14_payload_shallowness_review({"x": out})
    pres = build_lr6_evid14_persistence_readiness_review({"x": out})
    live = build_lr6_evid14_live_ingestion_readiness_review({"x": out})
    gov = build_lr6_evid14_governed_emission_recommendation()
    assert suff["total_reviewed"] == 1
    assert shallow["shallow_count"] == 1
    assert pres["persistence_authorized"] is False
    assert live["live_ingestion_authorized"] is False
    assert gov["governed_activation_authorized"] is False
