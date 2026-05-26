from transmission_layers.expectation_failure import replay_ecology as mod


def _ctx(b=None, e=None):
    return mod.build_lr6_evid1_evidence_context(
        baseline_evidence=b,
        enriched_evidence=e,
        inspected_sources=["LR6-RUN1", "LR6-RUN2", "LR6-EXEC2", "LR6-OBS9"],
    )


def test_public_apis_exist():
    names = [
        "build_lr6_evid1_evidence_context",
        "build_lr6_evid1_baseline_evidence_profile",
        "build_lr6_evid1_enriched_evidence_profile",
        "build_lr6_evid1_pre_post_delta_table",
        "build_lr6_evid1_weak_signal_delta",
        "build_lr6_evid1_contradiction_delta",
        "build_lr6_evid1_propagation_delta",
        "build_lr6_evid1_topology_drift_delta",
        "build_lr6_evid1_saturation_delta",
        "build_lr6_evid1_megacap_gravity_delta",
        "build_lr6_evid1_replay_richness_delta",
        "build_lr6_evid1_evidence_sufficiency_assessment",
        "build_lr6_evid1_supervisor_review",
        "build_lr6_evid1_markdown_report",
        "certify_lr6_evid1_evidence_boundary",
    ]
    for n in names:
        assert hasattr(mod, n)


def test_deterministic_outputs():
    c = _ctx({"weak_signal_attribution_count": 1}, {"weak_signal_attribution_count": 2})
    assert mod.build_lr6_evid1_supervisor_review(c) == mod.build_lr6_evid1_supervisor_review(c)


def test_missing_baseline_status_conservative():
    c = _ctx(None, {"weak_signal_attribution_count": 2})
    t = mod.build_lr6_evid1_pre_post_delta_table(
        mod.build_lr6_evid1_baseline_evidence_profile(c),
        mod.build_lr6_evid1_enriched_evidence_profile(c),
    )
    assert any(r["evidence_status"] == "MISSING_BASELINE" for r in t)


def test_missing_enriched_status_conservative():
    c = _ctx({"weak_signal_attribution_count": 2}, None)
    t = mod.build_lr6_evid1_pre_post_delta_table(
        mod.build_lr6_evid1_baseline_evidence_profile(c),
        mod.build_lr6_evid1_enriched_evidence_profile(c),
    )
    assert any(r["evidence_status"] == "MISSING_ENRICHED" for r in t)


def test_scaffold_only_does_not_claim_improvement():
    c = _ctx({"scaffold_complete": True}, {"scaffold_complete": True})
    review = mod.build_lr6_evid1_supervisor_review(c)
    assert review["evidence_sufficiency_assessment"]["decision"] != "SUFFICIENT_FOR_STRUCTURAL_IMPROVEMENT_CLAIM"


def test_delta_table_includes_all_dimensions_and_valid_enums():
    c = _ctx(
        {
            "weak_signal_attribution_count": 1,
            "contradiction_persistence_count": 1,
            "propagation_bridge_diversity": 1,
            "topology_drift_indicator": 1,
            "saturation_concentration": 0.6,
            "megacap_concentration": 0.7,
            "replay_richness_score": 0.4,
        },
        {
            "weak_signal_attribution_count": 2,
            "contradiction_persistence_count": 2,
            "propagation_bridge_diversity": 2,
            "topology_drift_indicator": 2,
            "saturation_concentration": 0.4,
            "megacap_concentration": 0.5,
            "replay_richness_score": 0.7,
        },
    )
    t = mod.build_lr6_evid1_pre_post_delta_table(
        mod.build_lr6_evid1_baseline_evidence_profile(c),
        mod.build_lr6_evid1_enriched_evidence_profile(c),
    )
    assert len(t) == 7
    assert {r["evidence_status"] for r in t}.issubset(mod.EVIDENCE_STATUS_VALUES)
    decision = mod.build_lr6_evid1_evidence_sufficiency_assessment(t)["decision"]
    assert decision in mod.SUFFICIENCY_VALUES


def test_boundary_flags_and_no_execution_auth():
    b = mod.certify_lr6_evid1_evidence_boundary()
    assert b["execution_authorized"] is False
    assert b["no_direct_sql"] is True
    assert b["no_persistence_write"] is True
    assert b["no_prediction"] is True
    assert b["no_trading"] is True
    assert b["no_live_ingestion"] is True
    assert b["no_governed_activation"] is True


def test_report_sections_required():
    c = _ctx()
    md = mod.build_lr6_evid1_markdown_report(c)
    for section in [
        "## objective",
        "## inspected evidence sources",
        "## baseline evidence profile",
        "## enriched evidence profile",
        "## pre/post delta table",
        "## weak-signal delta",
        "## contradiction delta",
        "## propagation delta",
        "## topology drift delta",
        "## saturation / monoculture delta",
        "## megacap gravity delta",
        "## replay richness delta",
        "## evidence sufficiency assessment",
        "## anti-hype interpretation guardrails",
        "## final recommendation",
    ]:
        assert section in md
