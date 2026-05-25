from transmission_layers.expectation_failure.replay_ecology.lr6_exp4_replay_ecology_evidence_trace import (
    build_lr6_exp4_dashboard_payload,
    build_replay_ecology_evidence_trace,
    certify_lr6_exp4_experimental_boundaries,
)


def test_exp4_deterministic_output():
    assert build_replay_ecology_evidence_trace() == build_replay_ecology_evidence_trace()


def test_exp4_domain_presence_and_boundedness():
    payload = build_replay_ecology_evidence_trace(max_entities=90, slice_count=4)
    domains = payload["attribution_domains"]
    expected = {
        "top_replay_drift_entities",
        "replay_drift_cluster_contributors",
        "replay_drift_ecosystem_roles",
        "replay_drift_pathway_refs",
        "propagation_dense_entities",
        "replay_bridge_entities",
        "pathway_concentration_refs",
        "cross_cluster_pathway_links",
        "contradiction_persistent_entities",
        "contradiction_surface_density",
        "contradiction_cluster_refs",
        "contradiction_migration_refs",
        "replay_recurrence_entities",
        "saturation_pressure_entities",
        "novelty_decay_clusters",
        "replay_density_refs",
        "semantic_gravity_entities",
        "cluster_concentration_refs",
        "diversity_decay_refs",
        "replay_monoculture_entities",
        "replay_interaction_entities",
        "replay_cascade_refs",
        "cross_cluster_interaction_refs",
        "ecosystem_coupling_entities",
    }
    assert expected <= set(domains)
    for key, value in domains.items():
        assert isinstance(value, list)
        assert len(value) <= 12


def test_exp4_composite_bands_and_traceability():
    payload = build_replay_ecology_evidence_trace()
    summary = payload["composite_attribution_summary"]
    assert summary["replay_ecology_density_band"] in {"low", "moderate", "high"}
    assert summary["replay_ecology_maturity_band"] in {"low", "moderate", "high"}
    assert summary["observation_confidence_band"] in {"low", "moderate", "high"}
    assert summary["most_referenced_entities"]
    assert summary["most_referenced_clusters"]
    assert summary["strongest_propagation_pathways"]
    assert summary["strongest_contradiction_surfaces"]


def test_exp4_boundary_and_language_guards():
    cert = certify_lr6_exp4_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["no_prediction_or_trading"] is True

    serialized = str(build_replay_ecology_evidence_trace()).lower()
    for banned in ["buy", "sell", "alpha", "forecast", "expected return", "target price", "insert into", "select * from"]:
        assert banned not in serialized


def test_exp4_dashboard_payload_sections():
    payload = build_lr6_exp4_dashboard_payload(max_entities=80, slice_count=3)
    assert payload["phase"] == "LR6-EXP4"
    sections = payload["dashboard_sections"]
    assert {
        "replay_drift_attribution",
        "propagation_pathway_attribution",
        "contradiction_ecology_attribution",
        "saturation_novelty_attribution",
        "monoculture_diversity_attribution",
        "ecosystem_interaction_attribution",
        "composite_summary",
    } <= set(sections)
