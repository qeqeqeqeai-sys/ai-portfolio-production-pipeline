from transmission_layers.expectation_failure.replay_ecology.lr6_exp6_replay_ecology_snapshot_export import build_replay_ecology_snapshot_export
from transmission_layers.expectation_failure.replay_ecology.lr6_exp6a_longitudinal_snapshot_comparison import build_replay_ecology_snapshot_comparison
from transmission_layers.expectation_failure.replay_ecology.lr6_exp7_replay_ecology_interestingness_scoring import build_interestingness_summary, build_replay_ecology_interestingness_scores
from transmission_layers.expectation_failure.replay_ecology.lr6_exp8_replay_ecology_findings_report import (
    MAX_CAVEATS,
    MAX_CLUSTERS,
    MAX_CONTRADICTIONS,
    MAX_DOMAIN_FINDINGS,
    MAX_ENTITIES,
    MAX_PATHWAYS,
    MAX_REFS,
    MAX_TOP_INTERESTING_FINDINGS,
    build_lr6_exp8_dashboard_payload,
    build_replay_ecology_findings_markdown,
    build_replay_ecology_findings_report,
    certify_lr6_exp8_experimental_boundaries,
)

BANNED_TERMS = {"buy", "sell", "outperform", "underperform", "alpha", "expected return", "trade signal", "portfolio allocation", "investment opportunity"}


def _walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    elif isinstance(value, str):
        yield value


def _interestingness():
    prior = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    current = build_replay_ecology_snapshot_export(max_entities=300, slice_count=5)
    comparison = build_replay_ecology_snapshot_comparison(prior, current)
    return build_interestingness_summary(build_replay_ecology_interestingness_scores(comparison))


def test_exp8_deterministic_and_required_sections_present():
    i = _interestingness()
    first = build_replay_ecology_findings_report(i)
    second = build_replay_ecology_findings_report(i)
    assert first == second
    required = {
        "report_metadata", "executive_summary", "top_interesting_findings", "contradiction_ecology_findings",
        "propagation_evolution_findings", "saturation_monoculture_findings", "ecosystem_interaction_findings",
        "entity_cluster_attribution_findings", "ecological_caveats", "next_observation_priorities",
    }
    assert required.issubset(first.keys())


def test_exp8_boundedness_and_finding_structure_completeness():
    report = build_replay_ecology_findings_report(_interestingness())
    assert len(report["top_interesting_findings"]) <= MAX_TOP_INTERESTING_FINDINGS
    assert len(report["ecological_caveats"]) <= MAX_CAVEATS

    for section_name in [
        "top_interesting_findings", "contradiction_ecology_findings", "propagation_evolution_findings",
        "saturation_monoculture_findings", "ecosystem_interaction_findings", "entity_cluster_attribution_findings",
    ]:
        section = report[section_name]
        assert len(section) <= max(MAX_TOP_INTERESTING_FINDINGS, MAX_DOMAIN_FINDINGS)
        for finding in section:
            for key in [
                "finding_id", "finding_title", "finding_summary", "interestingness_band", "supporting_entities",
                "supporting_clusters", "supporting_pathways", "supporting_contradiction_surfaces",
                "supporting_evidence_refs", "structural_significance", "caveats",
            ]:
                assert key in finding
            assert len(finding["supporting_entities"]) <= MAX_ENTITIES
            assert len(finding["supporting_clusters"]) <= MAX_CLUSTERS
            assert len(finding["supporting_pathways"]) <= MAX_PATHWAYS
            assert len(finding["supporting_contradiction_surfaces"]) <= MAX_CONTRADICTIONS
            assert len(finding["supporting_evidence_refs"]) <= MAX_REFS


def test_exp8_markdown_dashboard_payload_and_boundary_certification():
    report = build_replay_ecology_findings_report(_interestingness())
    md1 = build_replay_ecology_findings_markdown(report)
    md2 = build_replay_ecology_findings_markdown(report)
    assert md1 == md2
    assert "## Top Interesting Findings" in md1

    payload = build_lr6_exp8_dashboard_payload(_interestingness())
    assert "lr6_exp8_replay_ecology_findings_dashboard" in payload
    assert "lr6_exp8_replay_ecology_findings_summary" in payload

    cert = certify_lr6_exp8_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True


def test_exp8_non_prediction_non_trading_vocabulary_and_no_sql_strings():
    text = " ".join(s.lower() for s in _walk(build_lr6_exp8_dashboard_payload(_interestingness())))
    for banned in BANNED_TERMS:
        assert banned not in text
    assert "select " not in text and "insert " not in text and "update " not in text
