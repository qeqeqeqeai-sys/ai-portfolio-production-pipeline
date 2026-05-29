from pathlib import Path

from transmission_layers.daily_briefing.adapter import build_daily_briefing, load_daily_briefing, rank_investigations


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
    assert 3 <= len(briefing["major_developments"]) <= 7
    assert briefing["investigation_candidates"][0]["title"] == "Supply chain divergence"
    assert briefing["historical_live_deviation_highlights"][0]["title"] == "AI infrastructure demand"
    assert briefing["persistence_watchlist"][0]["title"] == "Capex concentration"


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
