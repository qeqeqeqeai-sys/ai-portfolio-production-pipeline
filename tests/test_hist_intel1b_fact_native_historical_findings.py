from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_intel1b_fact_native_historical_findings import (
    CONFIDENCE_LABELS,
    build_fact_native_historical_findings,
    run_hist_intel1b,
)


def _facts(extra: int = 0) -> list[dict]:
    rows = [
        {
            "phase_id": "HIST-LONG-8",
            "entity_type": "sector",
            "entity_id": "cloud infrastructure",
            "metric_name": "persistence_score",
            "metric_value": 0.92,
            "window_days": 20,
            "payload_jsonb": {"stability_class": "STABLE", "dimension": "cloud infrastructure"},
        },
        {
            "phase_id": "HIST-LONG-8",
            "entity_type": "sector",
            "entity_id": "cloud infrastructure",
            "metric_name": "persistence_score",
            "metric_value": 0.94,
            "window_days": 60,
            "payload_jsonb": {"stability_class": "STABLE", "dimension": "cloud infrastructure"},
        },
        {
            "phase_id": "HIST-LONG-9",
            "entity_type": "subsector",
            "entity_id": "edge ai",
            "metric_name": "replay_density",
            "metric_value": 0.81,
            "window_days": 60,
            "payload_jsonb": {"recurring_structures": ["edge ai"], "stability_class": "STABLE"},
        },
        {
            "phase_id": "HIST-LONG-9",
            "entity_type": "symbol",
            "entity_id": "thin-breadth cohort",
            "metric_name": "emerging_fragility_score",
            "metric_value": 0.73,
            "window_days": 120,
            "payload_jsonb": {"fragility_class": "ELEVATED", "evidence_count": 3},
        },
        {
            "phase_id": "HIST-LONG-9",
            "entity_type": "sector",
            "entity_id": "legacy media",
            "metric_name": "morphology_drift_score",
            "metric_value": -0.43,
            "window_days": 120,
            "payload_jsonb": {"drift_class": "DETERIORATING"},
        },
        {
            "phase_id": "HIST-INTEL-1",
            "entity_type": "pipeline",
            "entity_id": "normalizer",
            "metric_name": "normalized_rows",
            "metric_value": 1000,
            "window_days": 20,
            "payload_jsonb": {"diagnostic": "pipeline"},
        },
        {
            "phase_id": "HIST-INTEL-1",
            "entity_type": "diagnostic",
            "entity_id": "calendar",
            "metric_name": "reconciled_date_ratio",
            "metric_value": 1.0,
            "window_days": 20,
        },
    ]
    for index in range(extra):
        rows.append({
            "phase_id": "HIST-LONG-8",
            "entity_type": "subsector",
            "entity_id": f"subsector-{index:02d}",
            "metric_name": "persistence_score",
            "metric_value": 0.5 + (index / 100),
            "window_days": 20,
            "payload_jsonb": {"stability_class": "STABLE"},
        })
    return rows


def test_deterministic_output_for_same_inputs():
    first = build_fact_native_historical_findings(observation_facts=_facts(), top_n=5)
    second = build_fact_native_historical_findings(observation_facts=copy.deepcopy(_facts()), top_n=5)
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


def test_fact_native_findings_rank_above_pipeline_diagnostics():
    report = build_fact_native_historical_findings(observation_facts=_facts(), top_n=5)
    assert report["findings"]["fact_native_persistent_hubs"][0]["name"] == "cloud infrastructure"
    assert report["findings"]["suppressed_pipeline_diagnostics"]
    assert report["pipeline_diagnostic_rows_suppressed"] == 2


def test_pipeline_metrics_suppressed_from_executive_summary_when_ecosystem_facts_exist():
    report = build_fact_native_historical_findings(observation_facts=_facts(), top_n=5)
    summary = " ".join(report["findings"]["executive_summary"]).lower()
    assert "normalized_rows" not in summary
    assert "reconciled_date_ratio" not in summary
    assert "cloud infrastructure" in summary


def test_missing_fact_native_inputs_fail_gracefully():
    report = build_fact_native_historical_findings(observation_facts=[_facts()[5]], top_n=5)
    assert report["status"] == "limited"
    assert report["fact_native_ecosystem_rows"] == 0
    assert "No fact-native ecosystem" in " ".join(report["limitations"])
    assert report["findings"]["executive_summary"]


def test_governance_flags_present_and_true():
    report = build_fact_native_historical_findings(observation_facts=_facts(), top_n=5)
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
    source = Path("transmission_layers/history_long/hist_intel1b_fact_native_historical_findings.py").read_text(encoding="utf-8")
    runner = Path("scripts/run_hist_intel1b_fact_native_historical_findings.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "httpx.", ".upsert(", ".update(", ".delete(", "create_client(", "supabase.table("]
    combined = source + runner
    assert ".insert(" not in source
    assert not any(token in combined for token in forbidden)


def test_no_prediction_trading_or_portfolio_wording_appears_in_findings():
    report = build_fact_native_historical_findings(observation_facts=_facts(), top_n=5)
    findings_text = json.dumps(report["findings"], sort_keys=True).lower()
    banned = ["buy", "sell", "hold", "price target", "outperform", "underperform", "forecast"]
    assert not any(term in findings_text for term in banned)


def test_bounded_top_n_behavior():
    report = build_fact_native_historical_findings(observation_facts=_facts(extra=20), top_n=50)
    assert report["top_n"] == 10
    for key, rows in report["findings"].items():
        if key != "executive_summary":
            assert len(rows) <= 10


def test_conservative_confidence_labels():
    sparse = [
        {
            "phase_id": "HIST-LONG-8",
            "entity_type": "sector",
            "entity_id": "single window hub",
            "metric_name": "persistence_score",
            "metric_value": 0.9,
            "window_days": 20,
        }
    ]
    report = build_fact_native_historical_findings(observation_facts=sparse, top_n=5)
    labels = []
    for rows in report["findings"].values():
        if isinstance(rows, list):
            labels.extend(item.get("confidence_label") for item in rows if isinstance(item, dict) and item.get("confidence_label"))
    assert labels
    assert set(labels) <= CONFIDENCE_LABELS
    assert "HIGH" not in labels
    assert report["findings"]["fact_native_persistent_hubs"][0]["confidence_label"] == "LOW"


def test_json_and_markdown_reports_are_created(tmp_path: Path):
    json_path = tmp_path / "hist_intel1b.json"
    md_path = tmp_path / "hist_intel1b.md"
    report = run_hist_intel1b(observation_facts=_facts(), top_n=3, json_report_path=json_path, markdown_report_path=md_path)
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["phase_id"] == "HIST-INTEL-1B"
    assert "# HIST-INTEL-1B" in md_path.read_text(encoding="utf-8")
    assert report["output_paths"]["json_report_path"] == json_path.as_posix()
