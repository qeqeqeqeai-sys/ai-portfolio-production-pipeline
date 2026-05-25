import json

from transmission_layers.expectation_failure.replay_ecology.lr6_exp6_replay_ecology_snapshot_export import (
    MAX_SECTION_ITEMS,
    SECTION_ORDER,
    build_replay_ecology_snapshot_comparison_key,
    build_replay_ecology_snapshot_export,
    build_replay_ecology_snapshot_json_payload,
    build_replay_ecology_snapshot_markdown,
    build_replay_ecology_snapshot_metadata,
    certify_lr6_exp6_experimental_boundaries,
    validate_replay_ecology_snapshot_export,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model import (
    build_replay_ecology_dashboard_view_model,
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


def test_exp6_snapshot_export_is_deterministic_and_validates():
    first = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    second = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    assert first == second
    validation = validate_replay_ecology_snapshot_export(first)
    assert validation["passed"] is True


def test_exp6_snapshot_metadata_and_sections_present():
    snapshot = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    metadata = snapshot["metadata"]
    for field in {
        "snapshot_id", "generated_at_marker", "source_phase", "source_modules", "ecosystem_universe_size",
        "dashboard_sections_included", "deterministic_comparison_key", "experimental_mode_only", "no_prediction",
        "no_trading", "no_governed_activation",
    }:
        assert field in metadata

    assert metadata["dashboard_sections_included"] == SECTION_ORDER
    for section in SECTION_ORDER:
        assert section in snapshot["payload"]


def test_exp6_json_and_markdown_are_deterministic_and_readable():
    vm = build_replay_ecology_dashboard_view_model(max_entities=120, slice_count=4)
    metadata = build_replay_ecology_snapshot_metadata(vm)
    payload = build_replay_ecology_snapshot_json_payload(vm)

    json.dumps(payload, sort_keys=True)
    markdown_1 = build_replay_ecology_snapshot_markdown(metadata, payload)
    markdown_2 = build_replay_ecology_snapshot_markdown(metadata, payload)
    assert markdown_1 == markdown_2
    assert "# LR6-EXP6 Replay Ecology Snapshot" in markdown_1
    assert "## Overview" in markdown_1


def test_exp6_comparison_key_is_deterministic_and_bounded_sections_hold():
    vm = build_replay_ecology_dashboard_view_model(max_entities=120, slice_count=4)
    key_1 = build_replay_ecology_snapshot_comparison_key(vm)
    key_2 = build_replay_ecology_snapshot_comparison_key(vm)
    assert key_1 == key_2

    snapshot = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    payload = snapshot["payload"]
    for section in ["replay_drift", "propagation_evolution", "contradiction_ecology", "saturation_monoculture", "ecosystem_interaction"]:
        assert len(payload[section]["observations"]) <= MAX_SECTION_ITEMS

    assert len(payload["caveats"]) <= MAX_SECTION_ITEMS
    assert len(payload["next_observation_priorities"]) <= MAX_SECTION_ITEMS


def test_exp6_boundaries_and_vocabulary_constraints():
    snapshot = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    cert = certify_lr6_exp6_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["no_prediction_or_trading"] is True

    payload_text = " ".join(s.lower() for s in _walk(snapshot))
    for banned in BANNED_TERMS:
        assert banned not in payload_text
    assert "select " not in payload_text
    assert "insert " not in payload_text
