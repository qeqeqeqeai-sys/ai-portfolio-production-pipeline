from pathlib import Path

from transmission_layers.daily_briefing.adapter import (
    build_daily_briefing,
    infer_lifecycle_state,
    infer_narrative_archetype,
    load_daily_briefing,
    rank_investigations,
)


def _sample_payload():
    return {
        "schema_version": "obs_query4_analyst_consumption_view_v1",
        "query_parameters": {"snapshot_date": "2026-05-29"},
        "sections": [
            {
                "section_name": "Significant Deviations",
                "items": [
                    {
                        "identifier": "AI infrastructure demand",
                        "classification": "live_deviates_from_historical",
                        "source_comparison_type": "baseline_deviation",
                        "ranking_metric": {"name": "absolute_numeric_delta", "value": 31},
                        "delta": 31,
                        "supporting_fact_ids": ["fact-2", "fact-1"],
                        "supporting_evidence_ids": ["ev-2", "ev-1"],
                        "source_phases": ["HIST-INTEL", "OPS-LIVE"],
                    }
                ],
            },
            {
                "section_name": "Investigation Candidates",
                "items": [
                    {
                        "identifier": "Supply chain divergence",
                        "classification": "live_only",
                        "queue_source": "live_only_anomaly",
                        "ranking_metric": {"name": "live_fact_count", "value": 4},
                        "supporting_fact_ids": ["fact-3"],
                        "supporting_evidence_ids": ["ev-3"],
                    },
                    {
                        "identifier": "Recurring margin pressure",
                        "classification": "live_weaker_than_historical",
                        "queue_source": "persistent_weakening_live",
                        "ranking_metric": {"name": "absolute_numeric_delta", "value": 11},
                        "supporting_fact_ids": ["fact-4"],
                        "supporting_evidence_ids": ["ev-4"],
                    },
                ],
            },
            {
                "section_name": "Persistent Structures",
                "items": [
                    {
                        "identifier": "Capex concentration",
                        "source_query_type": "persisted",
                        "ranking_metric": {"name": "fact_count", "value": 2},
                        "supporting_fact_ids": ["fact-5"],
                    }
                ],
            },
        ],
    }


def test_adapter_handles_missing_files(tmp_path: Path):
    result = load_daily_briefing(
        selected_date="2026-05-29",
        artifact_paths=["missing_briefing.json"],
        project_root=tmp_path,
    )

    assert result.briefing["empty"] is True
    assert result.inspected_paths == ["missing_briefing.json"]
    assert result.loaded_paths == []
    assert result.missing_paths == ["missing_briefing.json"]


def test_adapter_normalizes_sample_intelligence_payload():
    briefing = build_daily_briefing([_sample_payload()], selected_date="2026-05-29", source_paths=["artifact.json"])

    assert briefing["briefing_date"] == "2026-05-29"
    assert briefing["attention_level"] == "critical"
    assert 3 <= len(briefing["major_developments"]) <= 5
    assert briefing["investigation_candidates"][0]["title"] == "Supply chain divergence"
    assert briefing["historical_live_deviation_highlights"][0]["title"] == "AI infrastructure demand"
    assert briefing["persistence_watchlist"][0]["title"] == "Capex concentration"
    assert briefing["briefing_quality_status"] == "strong"
    assert briefing["suppression_summary"]["final_items_shown"] == 7


def test_investigation_ranking_order_is_deterministic():
    source_items = [
        {
            "identifier": "B item",
            "queue_source": "persistent_weakening_live",
            "classification": "live_weaker_than_historical",
            "ranking_metric": {"value": 12},
        },
        {
            "identifier": "A item",
            "queue_source": "historical_live_deviation",
            "classification": "live_deviates_from_historical",
            "ranking_metric": {"value": 30},
        },
        {
            "identifier": "C item",
            "queue_source": "historical_live_deviation",
            "classification": "live_deviates_from_historical",
            "ranking_metric": {"value": 30},
        },
    ]

    first = rank_investigations(source_items)
    second = rank_investigations(reversed(source_items))

    assert [item["title"] for item in first] == ["A item", "C item", "B item"]
    assert [item["title"] for item in first] == [item["title"] for item in second]


def test_raw_evidence_is_suppressed_from_top_level_briefing_fields():
    briefing = build_daily_briefing([_sample_payload()], selected_date="2026-05-29")

    top_level_item = briefing["major_developments"][0]
    assert "supporting_fact_ids" not in top_level_item
    assert "supporting_evidence_ids" not in top_level_item
    assert "evidence" not in top_level_item

    story = briefing["stories"][0]
    assert "evidence" in story
    assert story["evidence"]["supporting_evidence_ids"] == ["ev-3"]


def test_lifecycle_and_archetype_mapping_is_deterministic():
    item = {
        "identifier": "AI infrastructure demand",
        "classification": "live_deviates_from_historical",
        "source_comparison_type": "baseline_deviation",
        "ranking_metric": {"value": 31},
        "delta": 31,
    }

    assert infer_lifecycle_state(item) == infer_lifecycle_state(dict(item)) == "developing"
    assert infer_narrative_archetype(item) == infer_narrative_archetype(dict(item)) == "transition"


def test_live_only_anomaly_maps_to_new_emergence():
    item = {"classification": "live_only", "queue_source": "live_only_anomaly", "ranking_metric": {"value": 4}}

    assert infer_lifecycle_state(item) == "new"
    assert infer_narrative_archetype(item) == "emergence"


def test_persistent_weakening_maps_to_weakening_breakdown():
    item = {
        "classification": "live_weaker_than_historical",
        "queue_source": "persistent_weakening_live",
        "ranking_metric": {"value": 11},
    }

    assert infer_lifecycle_state(item) == "weakening"
    assert infer_narrative_archetype(item) == "breakdown"


def test_historical_live_deviation_maps_to_developing_transition():
    item = {
        "classification": "live_deviates_from_historical",
        "source_comparison_type": "historical_live_deviation",
        "ranking_metric": {"value": 30},
        "delta": 30,
    }

    assert infer_lifecycle_state(item) == "developing"
    assert infer_narrative_archetype(item) == "transition"


def test_lifecycle_archetype_and_continuity_appear_in_normalized_stories():
    briefing = build_daily_briefing([_sample_payload()], selected_date="2026-05-29")

    story = briefing["stories"][0]
    assert story["lifecycle_state"] == "new"
    assert story["narrative_archetype"] == "emergence"
    assert "continuity_explanation" in story
    assert "existing live_only_anomaly" in story["continuity_explanation"]


def test_lifecycle_fields_do_not_expose_evidence_on_top_level_cards():
    briefing = build_daily_briefing([_sample_payload()], selected_date="2026-05-29")

    summary_item = briefing["major_developments"][0]
    assert summary_item["lifecycle_state"] in {"new", "developing", "stable", "weakening", "resolved"}
    assert summary_item["narrative_archetype"] in {"continuation", "acceleration", "emergence", "breakdown", "transition"}
    assert "supporting_fact_ids" not in summary_item
    assert "supporting_evidence_ids" not in summary_item
    assert "evidence" not in summary_item


def _item(identifier, *, metric=1, facts=(), evidence=(), classification="live_deviates_from_historical", source="baseline_deviation"):
    return {
        "identifier": identifier,
        "classification": classification,
        "source_comparison_type": source,
        "queue_source": source,
        "ranking_metric": {"name": "score", "value": metric},
        "supporting_fact_ids": list(facts),
        "supporting_evidence_ids": list(evidence),
    }


def _payload(section_name, items):
    return {"sections": [{"section_name": section_name, "items": items}]}


def test_quality_gate_section_caps_are_enforced():
    items = [
        _item(f"Major {index}", metric=100 - index, facts=[f"fact-{index}", f"fact-x-{index}"])
        for index in range(8)
    ]

    briefing = build_daily_briefing([_payload("Significant Deviations", items)], selected_date="2026-05-29")

    assert len(briefing["major_developments"]) == 5
    assert len(briefing["historical_live_deviation_highlights"]) == 5
    assert briefing["suppression_summary"]["total_items_suppressed"] == 7


def test_quality_gate_duplicate_items_are_collapsed_deterministically_to_stronger_item():
    weak = _item("Duplicate Story", metric=5, facts=["fact-1"])
    strong = _item("Duplicate Story", metric=10, facts=["fact-1", "fact-2", "fact-3", "fact-4"])

    first = build_daily_briefing([_payload("Significant Deviations", [weak, strong])], selected_date="2026-05-29")
    second = build_daily_briefing([_payload("Significant Deviations", [strong, weak])], selected_date="2026-05-29")

    assert [item["title"] for item in first["major_developments"]] == ["Duplicate Story"]
    assert first["major_developments"] == second["major_developments"]
    assert first["major_developments"][0]["why_it_matters"].endswith("score=10.")
    assert first["suppression_summary"]["duplicates_suppressed"] == second["suppression_summary"]["duplicates_suppressed"] == 3


def test_quality_gate_suppresses_low_confidence_when_stronger_alternatives_exist():
    low = _item("Unsupported deviation", metric=100)
    medium = _item("Supported deviation", metric=10, facts=["fact-1", "fact-2"])

    briefing = build_daily_briefing([_payload("Significant Deviations", [low, medium])], selected_date="2026-05-29")

    assert [item["title"] for item in briefing["major_developments"]] == ["Supported deviation"]
    assert briefing["suppression_summary"]["low_confidence_suppressed"] == 3


def test_quality_gate_suppresses_low_priority_investigations_when_higher_priority_exists():
    low = _item("Manual review candidate", metric=0, facts=["fact-1", "fact-2"], classification="needs review", source="manual_review")
    high = _item("Live anomaly", metric=4, facts=["fact-3", "fact-4"], classification="live_only", source="live_only_anomaly")

    briefing = build_daily_briefing([_payload("Investigation Candidates", [low, high])], selected_date="2026-05-29")

    assert [item["title"] for item in briefing["investigation_candidates"]] == ["Live anomaly"]
    assert briefing["suppression_summary"]["low_priority_suppressed"] == 1


def test_quality_gate_suppresses_internal_artifact_like_items():
    internal = _item("Pipeline validation artifact", metric=20, facts=["fact-1", "fact-2"], classification="pipeline validation-only")
    analyst = _item("Analyst relevant deviation", metric=10, facts=["fact-3", "fact-4"])

    briefing = build_daily_briefing([_payload("Significant Deviations", [internal, analyst])], selected_date="2026-05-29")

    assert [item["title"] for item in briefing["major_developments"]] == ["Analyst relevant deviation"]
    assert briefing["suppression_summary"]["internal_artifacts_suppressed"] == 3


def test_quality_status_empty_thin_strong_and_noisy_are_computed():
    empty = build_daily_briefing([], selected_date="2026-05-29")
    thin = build_daily_briefing([_payload("Significant Deviations", [_item("Single supported", facts=["f1", "f2"])])])
    strong = build_daily_briefing(
        [_payload("Significant Deviations", [_item(f"Supported {idx}", facts=[f"f{idx}", f"fx{idx}"]) for idx in range(3)])]
    )
    noisy = build_daily_briefing(
        [
            _payload(
                "Significant Deviations",
                [
                    _item("Supported core", facts=["f1", "f2"]),
                    _item("Pipeline validation artifact A", facts=["f3", "f4"], classification="pipeline validation-only"),
                    _item("Pipeline validation artifact B", facts=["f5", "f6"], classification="governance validation-only"),
                    _item("Pipeline validation artifact C", facts=["f7", "f8"], classification="artifact validation-only"),
                ],
            )
        ]
    )

    assert empty["briefing_quality_status"] == "empty"
    assert thin["briefing_quality_status"] == "thin"
    assert strong["briefing_quality_status"] == "strong"
    assert noisy["briefing_quality_status"] == "noisy"


def _dated_payload(snapshot_date, section_name, items):
    payload = _payload(section_name, items)
    payload["query_parameters"] = {"snapshot_date": snapshot_date}
    return payload


def test_story_key_is_stable_across_lifecycle_and_archetype_changes():
    from transmission_layers.daily_briefing.adapter import story_key

    first = _item(
        "Continuity Story",
        metric=4,
        facts=["fact-1", "fact-2"],
        classification="live_only",
        source="live_only_anomaly",
    )
    second = _item(
        "Continuity Story",
        metric=22,
        facts=["fact-3", "fact-4"],
        classification="live_weaker_than_historical",
        source="persistent_weakening_live",
    )

    assert story_key(first) == story_key(second) == "story:continuity story"


def test_story_history_construction_is_deterministic_across_dates():
    from transmission_layers.daily_briefing.adapter import build_story_histories, story_key

    older = _dated_payload("2026-05-27", "Investigation Candidates", [_item("History Story", metric=4, facts=["fact-1", "fact-2"])])
    newer = _dated_payload("2026-05-28", "Investigation Candidates", [_item("History Story", metric=8, facts=["fact-3", "fact-4"])])

    histories = build_story_histories([newer, older], selected_date="2026-05-28")
    history = histories[story_key(_item("History Story"))]

    assert history["first_seen"] == "2026-05-27"
    assert history["last_seen"] == "2026-05-28"
    assert history["appearance_count"] == 2
    assert history["consecutive_appearances"] == 2
    assert history["highest_priority_seen"] == "high"
    assert history["confidence_trend"] == ["medium", "medium"]


def test_evolution_direction_rising_classification():
    old = _dated_payload("2026-05-28", "Investigation Candidates", [_item("Rising Story", metric=2, facts=["fact-1", "fact-2"], source="manual_review")])
    current = _dated_payload("2026-05-29", "Investigation Candidates", [_item("Rising Story", metric=4, facts=["fact-3", "fact-4"], classification="live_only", source="live_only_anomaly")])

    briefing = build_daily_briefing([old, current], selected_date="2026-05-29")

    assert briefing["stories"][0]["evolution_direction"] == "rising"
    assert briefing["stories"][0]["why_now"] == "priority increased versus previous appearance"


def test_evolution_direction_stable_classification():
    old = _dated_payload("2026-05-28", "Investigation Candidates", [_item("Stable Story", metric=4, facts=["fact-1", "fact-2"], classification="live_only", source="live_only_anomaly")])
    current = _dated_payload("2026-05-29", "Investigation Candidates", [_item("Stable Story", metric=4, facts=["fact-3", "fact-4"], classification="live_only", source="live_only_anomaly")])

    briefing = build_daily_briefing([old, current], selected_date="2026-05-29")

    assert briefing["stories"][0]["evolution_direction"] == "stable"
    assert briefing["stories"][0]["why_now"] == "no material change detected"


def test_evolution_direction_falling_classification():
    old = _dated_payload("2026-05-28", "Investigation Candidates", [_item("Falling Story", metric=4, facts=["fact-1", "fact-2"], classification="live_only", source="live_only_anomaly")])
    current = _dated_payload("2026-05-29", "Investigation Candidates", [_item("Falling Story", metric=11, facts=["fact-3", "fact-4"], classification="live_weaker_than_historical", source="persistent_weakening_live")])

    briefing = build_daily_briefing([old, current], selected_date="2026-05-29")

    assert briefing["stories"][0]["evolution_direction"] == "falling"
    assert briefing["stories"][0]["why_now"] == "priority or lifecycle weakened versus previous appearance"


def test_evolution_direction_reappearing_classification():
    old = _dated_payload("2026-05-27", "Investigation Candidates", [_item("Reappearing Story", metric=4, facts=["fact-1", "fact-2"], classification="live_only", source="live_only_anomaly")])
    current = _dated_payload("2026-05-29", "Investigation Candidates", [_item("Reappearing Story", metric=4, facts=["fact-3", "fact-4"], classification="live_only", source="live_only_anomaly")])

    briefing = build_daily_briefing([old, current], selected_date="2026-05-29")

    assert briefing["stories"][0]["evolution_direction"] == "reappearing"
    assert briefing["stories"][0]["why_now"] == "first appearance after absence"


def test_evolution_highlight_sections_are_capped_at_five_items_per_group():
    old_items = [_item(f"Rising {index}", metric=2, facts=[f"old-{index}", f"old-x-{index}"], source="manual_review") for index in range(7)]
    current_items = [
        _item(f"Rising {index}", metric=4, facts=[f"new-{index}", f"new-x-{index}"], classification="live_only", source="live_only_anomaly")
        for index in range(7)
    ]

    briefing = build_daily_briefing(
        [
            _dated_payload("2026-05-28", "Investigation Candidates", old_items),
            _dated_payload("2026-05-29", "Investigation Candidates", current_items),
        ],
        selected_date="2026-05-29",
    )

    assert len(briefing["evolution_highlights"]["rising_stories"]) == 5


def test_evolution_highlights_respect_suppression_and_do_not_include_internal_items():
    internal = _item("Pipeline validation smoke test", metric=100, facts=["fact-1", "fact-2"], classification="live_only", source="live_only_anomaly")
    visible = _item("Visible Story", metric=4, facts=["fact-3", "fact-4"], classification="live_only", source="live_only_anomaly")

    briefing = build_daily_briefing([_dated_payload("2026-05-29", "Investigation Candidates", [internal, visible])], selected_date="2026-05-29")

    highlighted_titles = [item["title"] for group in briefing["evolution_highlights"].values() for item in group]
    assert "Pipeline validation smoke test" not in highlighted_titles
    assert briefing["suppression_summary"]["internal_artifacts_suppressed"] >= 1


def test_evolution_fields_do_not_move_evidence_out_of_drill_down():
    briefing = build_daily_briefing([_sample_payload()], selected_date="2026-05-29")

    highlight = briefing["evolution_highlights"]["rising_stories"] + briefing["evolution_highlights"]["stable_stories"]
    if highlight:
        assert "evidence" not in highlight[0]
        assert "supporting_evidence_ids" not in highlight[0]
    assert "evidence" in briefing["stories"][0]
