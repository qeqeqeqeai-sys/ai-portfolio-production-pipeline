from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    BLOCKED_CANDIDATE_DIVERSITY_STRENGTHENING,
    CERTIFIED_CANDIDATE_DIVERSITY_STRENGTHENING,
    build_cd1_candidate_diversity_inventory,
    build_cd1_candidate_diversity_taxonomy,
    build_cd1_dashboard_payload,
    build_cd1_diversification_recommendations,
    build_cd1_diversity_gap_analysis,
    build_cd1_semantic_richness_assessment,
    certify_cd1_candidate_diversity_strengthening,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import D7_RENDER_SECTION_ORDER, build_d7_dashboard_view_model


def _sample():
    return [
        {"run_id": "r1", "regime": "stress", "contradiction_state": "high", "continuity_state": "stable", "confidence_state": "converging", "semantic_themes": ["liquidity", "margin"], "recurring_findings": ["f1"], "pattern_family": "a"},
        {"run_id": "r2", "regime": "calm", "contradiction_state": "low", "continuity_state": "fragmented", "confidence_state": "oscillatory", "semantic_themes": ["credit"], "recurring_findings": ["f2", "f3"], "pattern_family": "b"},
    ]


def test_cd1_deterministic_and_immutable_and_certified():
    rows = _sample()
    frozen = deepcopy(rows)
    inv = build_cd1_candidate_diversity_inventory(replay_candidates=rows)
    gap = build_cd1_diversity_gap_analysis(candidate_diversity_inventory=inv)
    tax = build_cd1_candidate_diversity_taxonomy(candidate_diversity_inventory=inv)
    sem = build_cd1_semantic_richness_assessment(candidate_diversity_inventory=inv)
    rec = build_cd1_diversification_recommendations(diversity_gap_analysis=gap, taxonomy=tax)
    dash = build_cd1_dashboard_payload(candidate_diversity_inventory=inv, diversity_taxonomy=tax, diversity_gap_analysis=gap, semantic_richness_assessment=sem, diversification_recommendations=rec)
    cert1 = certify_cd1_candidate_diversity_strengthening(candidate_diversity_inventory=inv, dashboard_payload=dash)
    cert2 = certify_cd1_candidate_diversity_strengthening(candidate_diversity_inventory=inv, dashboard_payload=dash)
    assert rows == frozen
    assert cert1["status"] == CERTIFIED_CANDIDATE_DIVERSITY_STRENGTHENING
    assert cert1["checksum"] == cert2["checksum"]
    assert tax["assigned_categories"] == sorted(tax["assigned_categories"])
    assert all("execute" not in str(r).lower() for r in rec)


def test_cd1_blocked_and_d7_ordering():
    inv = build_cd1_candidate_diversity_inventory(replay_candidates=[])
    dash = build_cd1_dashboard_payload(candidate_diversity_inventory=inv, diversity_taxonomy={}, diversity_gap_analysis={}, semantic_richness_assessment={}, diversification_recommendations=[])
    cert = certify_cd1_candidate_diversity_strengthening(candidate_diversity_inventory=inv, dashboard_payload=dash)
    assert cert["status"] == BLOCKED_CANDIDATE_DIVERSITY_STRENGTHENING
    assert D7_RENDER_SECTION_ORDER[8] == "cd1_candidate_diversity_strengthening"


def test_cd1_integrated_into_d7_view_model():
    vm = build_d7_dashboard_view_model(
        findings_payload={"rows": [], "status": "empty"},
        narratives_payload={"rows": [], "status": "empty"},
        evidence_payload={"rows": [], "status": "empty"},
        integrity_payload={"replay": {"rows": []}, "manifests": {"rows": []}, "audits": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}},
    )
    assert "cd1_candidate_diversity_strengthening" in vm
    assert vm["cd1_candidate_diversity_strengthening"]["Governance/Lineage Controls"]["no_writes"] is True
