from transmission_layers.expectation_failure.replay_ecology.lr6_exp6_replay_ecology_snapshot_export import (
    build_replay_ecology_snapshot_export,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_exp6a_longitudinal_snapshot_comparison import (
    MAX_CAVEATS,
    MAX_DOMAIN_ITEMS,
    MAX_TOP_LEVEL_SIGNALS,
    build_lr6_exp6a_comparison_summary,
    build_replay_ecology_snapshot_comparison,
    build_replay_ecology_snapshot_sequence_comparison,
    certify_lr6_exp6a_experimental_boundaries,
)

BANNED_TERMS = {"buy", "sell", "outperform", "underperform", "alpha", "expected return", "price target", "trade signal"}


def _walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    elif isinstance(value, str):
        yield value


def test_exp6a_two_snapshot_comparison_is_deterministic_and_complete():
    prior = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    current = build_replay_ecology_snapshot_export(max_entities=300, slice_count=5)
    first = build_replay_ecology_snapshot_comparison(prior, current)
    second = build_replay_ecology_snapshot_comparison(prior, current)
    assert first == second
    required = {
        "comparison_metadata", "ecology_state_change", "replay_drift_change", "propagation_change", "contradiction_change",
        "saturation_monoculture_change", "ecosystem_interaction_change", "entity_cluster_attribution_change",
        "persistent_ecological_signals", "emerged_ecological_signals", "disappeared_ecological_signals",
        "intensified_ecological_signals", "weakened_ecological_signals", "comparison_confidence_band",
        "comparison_caveats", "next_observation_priorities",
    }
    assert required.issubset(first.keys())


def test_exp6a_metadata_boundedness_and_domain_detection():
    prior = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    current = build_replay_ecology_snapshot_export(max_entities=300, slice_count=5)
    comp = build_replay_ecology_snapshot_comparison(prior, current)
    meta = comp["comparison_metadata"]
    for field in {
        "comparison_id", "prior_snapshot_id", "current_snapshot_id", "prior_comparison_key", "current_comparison_key",
        "source_phase", "source_modules", "deterministic_comparison_mode", "experimental_mode_only", "no_prediction",
        "no_trading", "no_governed_activation",
    }:
        assert field in meta

    assert len(comp["persistent_ecological_signals"]) <= MAX_TOP_LEVEL_SIGNALS
    assert len(comp["emerged_ecological_signals"]) <= MAX_TOP_LEVEL_SIGNALS
    assert len(comp["disappeared_ecological_signals"]) <= MAX_TOP_LEVEL_SIGNALS
    assert len(comp["comparison_caveats"]) <= MAX_CAVEATS
    assert len(comp["entity_cluster_attribution_change"]["persistent_entities"]) <= MAX_DOMAIN_ITEMS


def test_exp6a_sequence_summary_and_missing_optional_sections_handled():
    prior = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    current = build_replay_ecology_snapshot_export(max_entities=300, slice_count=5)
    sparse = {"payload": {"overview": current["payload"]["overview"]}, "metadata": {"snapshot_id": "sparse"}}
    seq = build_replay_ecology_snapshot_sequence_comparison([prior, current, sparse])
    assert seq["sequence_size"] == 3
    assert len(seq["pairwise_comparisons"]) == 2
    summary = build_lr6_exp6a_comparison_summary(seq["pairwise_comparisons"][0])
    assert "Ecology" in summary["summary"]


def test_exp6a_boundary_and_vocabulary_constraints():
    prior = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    current = build_replay_ecology_snapshot_export(max_entities=300, slice_count=5)
    comp = build_replay_ecology_snapshot_comparison(prior, current)
    cert = certify_lr6_exp6a_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True

    text = " ".join(s.lower() for s in _walk(comp))
    for banned in BANNED_TERMS:
        assert banned not in text
    assert "select " not in text
    assert "insert " not in text
