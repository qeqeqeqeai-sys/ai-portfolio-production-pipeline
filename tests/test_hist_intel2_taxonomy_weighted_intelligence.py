from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_intel2_taxonomy_weighted_intelligence import (
    CONFIDENCE_LABELS,
    TIER_A_WEIGHT,
    TIER_C_WEIGHT,
    build_taxonomy_weighted_intelligence,
    run_hist_intel2,
    taxonomy_for_fact,
)


def _facts() -> list[dict]:
    return [
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "structural_hub_fact",
            "entity_type": "subsector",
            "entity_id": "cloud infrastructure",
            "metric_name": "centrality_score",
            "metric_value": 0.86,
            "window_days": 20,
            "evidence_count": 3,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-8",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "structural_hub_fact",
            "entity_type": "subsector",
            "entity_id": "cloud infrastructure",
            "metric_name": "centrality_score",
            "metric_value": 0.84,
            "window_days": 60,
            "evidence_count": 2,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-9",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "structural_anchor_fact",
            "entity_type": "sector",
            "entity_id": "semiconductors",
            "metric_name": "stability_score",
            "metric_value": 0.9,
            "window_days": 60,
            "evidence_count": 3,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-7",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "replay_density_fact",
            "entity_type": "theme",
            "entity_id": "accelerated compute",
            "metric_name": "replay_density",
            "metric_value": 0.78,
            "window_days": 120,
            "evidence_count": 2,
            "confidence_label": "MEDIUM",
            "source_phase": "HIST-LONG-6",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "persistence_fact",
            "entity_type": "sector",
            "entity_id": "semiconductors",
            "metric_name": "persistence_score",
            "metric_value": 0.83,
            "window_days": 20,
            "evidence_count": 2,
            "confidence_label": "HIGH",
            "source_phase": "HIST-LONG-8",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "breadth_fragility_fact",
            "entity_type": "subsector",
            "entity_id": "consumer devices",
            "metric_name": "fragility_score",
            "metric_value": 0.73,
            "window_days": 60,
            "evidence_count": 2,
            "confidence_label": "MEDIUM",
            "source_phase": "HIST-LONG-7",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "morphology_drift_fact",
            "entity_type": "sector",
            "entity_id": "legacy media",
            "metric_name": "morphology_drift_score",
            "metric_value": -0.52,
            "window_days": 120,
            "evidence_count": 2,
            "confidence_label": "MEDIUM",
            "source_phase": "HIST-LONG-9",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "topology_fragmentation_fact",
            "entity_type": "group",
            "entity_id": "thinly represented software",
            "metric_name": "fragmentation_score",
            "metric_value": 0.67,
            "window_days": 120,
            "evidence_count": 2,
            "confidence_label": "MEDIUM",
            "source_phase": "HIST-LONG-7",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "pipeline_diagnostic_fact",
            "entity_type": "pipeline",
            "entity_id": "normalizer",
            "metric_name": "normalized_rows",
            "metric_value": 1000000,
            "window_days": 20,
            "evidence_count": 99,
            "confidence_label": "HIGH",
            "source_phase": "HIST-INTEL-1",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "reconciliation_diagnostic_fact",
            "entity_type": "diagnostic",
            "entity_id": "calendar",
            "metric_name": "reconciled_date_ratio",
            "metric_value": 1.0,
            "window_days": 20,
            "evidence_count": 99,
            "confidence_label": "HIGH",
            "source_phase": "HIST-INTEL-1",
        },
    ]


def test_deterministic_output_for_same_inputs():
    first = build_taxonomy_weighted_intelligence(observation_facts=_facts(), local_facts_path=None, top_n=5)
    second = build_taxonomy_weighted_intelligence(observation_facts=copy.deepcopy(_facts()), local_facts_path=None, top_n=5)
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


def test_taxonomy_weighting_applied():
    tier_a = taxonomy_for_fact(_facts()[0])
    tier_c = taxonomy_for_fact(_facts()[-1])
    assert tier_a["tier"] == "A"
    assert tier_a["weight"] == TIER_A_WEIGHT
    assert tier_c["tier"] == "C"
    assert tier_c["weight"] == TIER_C_WEIGHT


def test_tier_a_outranks_tier_c_even_when_tier_c_metric_is_large():
    report = build_taxonomy_weighted_intelligence(observation_facts=_facts(), local_facts_path=None, top_n=5)
    assert report["findings"]["highest_ranked_ecosystem_hubs"][0]["name"] == "cloud_infrastructure"
    summary = " ".join(report["findings"]["executive_summary"]).lower()
    assert "cloud_infrastructure" in summary
    assert "normalized_rows" not in summary
    assert "reconciled_date_ratio" not in summary


def test_tier_c_findings_suppressed_when_tier_a_exists():
    report = build_taxonomy_weighted_intelligence(observation_facts=_facts(), local_facts_path=None, top_n=5)
    suppressed = report["findings"]["suppressed_operational_diagnostics"]
    assert report["operational_diagnostic_rows_suppressed"] == 2
    assert {row["taxonomy_tier"] for row in suppressed} == {"C"}
    assert {row["metric_name"] for row in suppressed} == {"normalized_rows", "reconciled_date_ratio"}


def test_stable_ranking_tie_breakers():
    facts = [
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "structural_hub_fact",
            "entity_type": "sector",
            "entity_id": "beta",
            "metric_name": "centrality_score",
            "metric_value": 0.5,
            "window_days": 20,
            "evidence_count": 1,
            "confidence_label": "MEDIUM",
        },
        {
            "phase_id": "HIST-FACT-1",
            "fact_type": "structural_hub_fact",
            "entity_type": "sector",
            "entity_id": "alpha",
            "metric_name": "centrality_score",
            "metric_value": 0.5,
            "window_days": 20,
            "evidence_count": 1,
            "confidence_label": "MEDIUM",
        },
    ]
    report = build_taxonomy_weighted_intelligence(observation_facts=facts, local_facts_path=None, top_n=5)
    assert [row["name"] for row in report["findings"]["highest_ranked_ecosystem_hubs"]] == ["alpha", "beta"]


def test_governance_flags_present_and_true():
    report = build_taxonomy_weighted_intelligence(observation_facts=_facts(), local_facts_path=None, top_n=5)
    expected = {
        "analysis_only",
        "local_only",
        "no_provider_calls",
        "no_supabase_writes",
        "no_prediction",
        "no_trading",
        "no_portfolio_recommendation",
        "no_governed_activation",
    }
    assert set(report["governance_certification"]) == expected
    assert all(report["governance_certification"].values())


def test_no_provider_api_or_supabase_write_path_is_introduced():
    source = Path("transmission_layers/history_long/hist_intel2_taxonomy_weighted_intelligence.py").read_text(encoding="utf-8")
    runner = Path("scripts/run_hist_intel2_taxonomy_weighted_intelligence.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "httpx.", ".upsert(", ".update(", ".delete(", "create_client(", "supabase.table("]
    combined = source + runner
    assert ".insert(" not in source
    assert not any(token in combined for token in forbidden)


def test_no_prediction_trading_or_portfolio_wording_appears_in_findings():
    report = build_taxonomy_weighted_intelligence(observation_facts=_facts(), local_facts_path=None, top_n=5)
    findings_text = json.dumps(report["findings"], sort_keys=True).lower()
    banned = ["buy", "sell", "hold", "price target", "outperform", "underperform", "forecast"]
    assert not any(term in findings_text for term in banned)


def test_confidence_labels_are_bounded():
    report = build_taxonomy_weighted_intelligence(observation_facts=_facts(), local_facts_path=None, top_n=5)
    labels = []
    for rows in report["findings"].values():
        if isinstance(rows, list):
            labels.extend(item.get("confidence_label") for item in rows if isinstance(item, dict) and item.get("confidence_label"))
    assert labels
    assert set(labels) <= set(CONFIDENCE_LABELS)


def test_json_and_markdown_reports_are_created(tmp_path: Path):
    json_path = tmp_path / "hist_intel2.json"
    md_path = tmp_path / "hist_intel2.md"
    report = run_hist_intel2(observation_facts=_facts(), local_facts_path=None, top_n=3, json_report_path=json_path, markdown_report_path=md_path)
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["phase_id"] == "HIST-INTEL-2"
    assert "# HIST-INTEL-2" in md_path.read_text(encoding="utf-8")
    assert report["output_paths"]["json_report_path"] == json_path.as_posix()


def _operational_fact(fact_type: str, metric_name: str, *, entity_type: str = "metric", entity_id: str | None = None) -> dict:
    return {
        "phase_id": "HIST-FACT-1",
        "fact_type": fact_type,
        "entity_type": entity_type,
        "entity_id": entity_id or metric_name,
        "metric_name": metric_name,
        "metric_value": 1.0,
        "window_days": 20,
        "evidence_count": 5,
        "confidence_label": "HIGH",
        "source_phase": "HIST-LONG-5B",
    }


def test_operational_metric_with_persistence_fact_becomes_tier_c():
    taxonomy = taxonomy_for_fact(_operational_fact("persistence_fact", "classification_code"))
    assert taxonomy["tier"] == "C"
    assert taxonomy["weight"] == TIER_C_WEIGHT


def test_operational_metric_with_replay_recurrence_fact_becomes_tier_c():
    taxonomy = taxonomy_for_fact(_operational_fact("replay_recurrence_fact", "absolute_delta"))
    assert taxonomy["tier"] == "C"
    assert taxonomy["weight"] == TIER_C_WEIGHT


def test_operational_metric_with_structural_instability_fact_becomes_tier_c():
    taxonomy = taxonomy_for_fact(_operational_fact("structural_instability_fact", "endpoint_failure_count"))
    assert taxonomy["tier"] == "C"
    assert taxonomy["weight"] == TIER_C_WEIGHT


def test_metric_entity_type_suppressed_unless_allowlisted():
    suppressed = taxonomy_for_fact(_operational_fact("topology_persistence_fact", "source_score", entity_id="generic_internal_metric"))
    allowed = taxonomy_for_fact(_operational_fact("replay_density_fact", "source_score", entity_id="replay_density"))
    operational_allowed = taxonomy_for_fact(_operational_fact("replay_density_fact", "exact_date_match_ratio", entity_id="replay_density"))
    assert suppressed["tier"] == "C"
    assert allowed["tier"] == "A"
    assert operational_allowed["tier"] == "C"


def test_tier_c_never_appears_in_executive_summary_when_tier_a_exists():
    facts = _facts() + [
        _operational_fact("persistence_fact", "classification_code"),
        _operational_fact("replay_recurrence_fact", "absolute_delta"),
        _operational_fact("structural_instability_fact", "exact_date_match_ratio"),
    ]
    report = build_taxonomy_weighted_intelligence(observation_facts=facts, local_facts_path=None, top_n=10)
    summary = " ".join(report["findings"]["executive_summary"]).lower()
    suppressed_metrics = {row["metric_name"] for row in report["findings"]["suppressed_operational_diagnostics"]}
    assert {"classification_code", "absolute_delta", "exact_date_match_ratio"} <= suppressed_metrics
    assert "classification_code" not in summary
    assert "absolute_delta" not in summary
    assert "exact_date_match_ratio" not in summary
