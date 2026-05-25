from transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model import (
    _ALLOWED_STATE_ORDER,
    build_replay_ecology_dashboard_summary,
    build_replay_ecology_dashboard_view_model,
    certify_lr6_exp5_experimental_boundaries,
)


BANNED_TERMS = {
    "buy",
    "sell",
    "outperform",
    "underperform",
    "expected return",
    "alpha",
    "portfolio optimization",
}


def _walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    elif isinstance(value, str):
        yield value


def test_exp5_dashboard_is_deterministic_and_complete():
    first = build_replay_ecology_dashboard_view_model(max_entities=120, slice_count=4)
    second = build_replay_ecology_dashboard_view_model(max_entities=120, slice_count=4)
    assert first == second

    required = {
        "overview_panel",
        "replay_drift_panel",
        "propagation_evolution_panel",
        "contradiction_ecology_panel",
        "saturation_monoculture_panel",
        "ecosystem_interaction_panel",
        "entity_cluster_attribution_panel",
        "ecological_caveats",
        "next_observation_priorities",
    }
    assert required.issubset(first.keys())


def test_exp5_dashboard_bounded_and_evidence_linked():
    vm = build_replay_ecology_dashboard_view_model(max_entities=120, slice_count=4)
    assert vm["overview_panel"]["dominant_replay_ecology_state"] in _ALLOWED_STATE_ORDER
    assert vm["overview_panel"]["replay_ecology_maturity_band"] in {"low", "moderate", "high"}
    assert vm["overview_panel"]["observation_confidence_band"] in {"low", "moderate", "high"}

    for key in [
        "replay_drift_panel",
        "propagation_evolution_panel",
        "contradiction_ecology_panel",
        "saturation_monoculture_panel",
        "ecosystem_interaction_panel",
    ]:
        assert "evidence_refs" in vm[key]
        assert len(vm[key]["observations"]) <= 6

    assert len(vm["entity_cluster_attribution_panel"]["most_referenced_entities"]) <= 6
    assert len(vm["ecological_caveats"]) <= 6
    assert len(vm["next_observation_priorities"]) <= 6


def test_exp5_dashboard_summary_and_boundary_certification():
    summary = build_replay_ecology_dashboard_summary(max_entities=120, slice_count=4)
    assert summary["dominant_replay_ecology_state"] in _ALLOWED_STATE_ORDER
    cert = certify_lr6_exp5_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["no_prediction_or_trading"] is True


def test_exp5_dashboard_uses_no_trading_or_prediction_vocabulary():
    vm = build_replay_ecology_dashboard_view_model(max_entities=120, slice_count=4)
    payload_text = " ".join(s.lower() for s in _walk(vm))
    for banned in BANNED_TERMS:
        assert banned not in payload_text
