from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_intel1_historical_structural_findings import (
    CONFIDENCE_LABELS,
    build_historical_structural_findings,
    run_hist_intel1,
)


def _write_sources(tmp_path: Path) -> tuple[str, ...]:
    hist4 = {
        "schema_version": "hist_long4_v1",
        "status": "ok",
        "bounded_diagnostics": {
            "strongest_recurring_sectors": [
                {"sector": "alpha", "window_count": 3},
                {"sector": "beta", "window_count": 3},
                {"sector": "gamma", "window_count": 2},
            ],
            "strongest_recurring_subsectors": [{"subsector": "alpha_sub", "window_count": 3}],
            "recurring_weak_symbols": ["WEAK1"],
        },
        "window_level_results": [
            {
                "window_trading_days": 20,
                "replay_density": 0.9,
                "weak_symbols": ["WEAK1"],
                "sector_hhi": {"strongest_sectors": [{"sector": "alpha", "share": 0.4}, {"sector": "beta", "share": 0.3}, {"sector": "gamma", "share": 0.2}]},
                "subsector_hhi": {"strongest_subsectors": [{"subsector": "alpha_sub", "share": 0.4}, {"subsector": "beta_sub", "share": 0.3}, {"subsector": "gamma_sub", "share": 0.2}]},
            },
            {
                "window_trading_days": 60,
                "replay_density": 0.8,
                "weak_symbols": ["WEAK1"],
                "sector_hhi": {"strongest_sectors": [{"sector": "alpha", "share": 0.4}, {"sector": "beta", "share": 0.3}, {"sector": "gamma", "share": 0.2}]},
                "subsector_hhi": {"strongest_subsectors": [{"subsector": "alpha_sub", "share": 0.4}, {"subsector": "beta_sub", "share": 0.3}, {"subsector": "gamma_sub", "share": 0.2}]},
            },
        ],
    }
    hist5b = {
        "schema_version": "hist_long5b_v1",
        "status": "ok",
        "fragility_emergence_detection": {"classification": ["limited_fragility"], "reasons_by_window": {"20": ["provider weakness"], "60": []}},
        "sensitivity_ranking": [
            {"metric": "normalized_rows", "classification": "highly_sensitive", "stability_score": 0.0, "volatility_score": 0.9},
            {"metric": "steady_metric", "classification": "stable", "stability_score": 0.95, "volatility_score": 0.01},
        ],
    }
    hist6 = {
        "schema_version": "hist_long6_v1",
        "status": "ok",
        "findings": {
            "strongest_differentiated_sectors": [
                {"sector": "alpha", "differentiation_score": 0.2, "representation_label": "overrepresented"},
                {"sector": "beta", "differentiation_score": 0.2, "representation_label": "overrepresented"},
            ],
            "strongest_differentiated_subsectors": [{"subsector": "alpha_sub", "differentiation_score": 0.2, "representation_label": "overrepresented"}],
        },
    }
    hist7 = {
        "schema_version": "hist_long7_v1",
        "status": "ok",
        "group_morphology_decomposition": [
            {
                "group": "alpha",
                "metrics": {"morphology_persistence_score": 1.0},
                "persistence_indicators": {"stable_leaders_across_20_60_120": True, "low_rank_churn": True},
                "fragility_indicators": {"high_leader_tail_gap": False, "weak_breadth": False},
                "structural_read": {"persistent_vs_episodic": "persistent", "coherent_vs_stratified": "coherent"},
                "window_observations": [{"window": 20}, {"window": 60}, {"window": 120}],
            }
        ],
    }
    paths = []
    for name, payload in (("hist4.json", hist4), ("hist5b.json", hist5b), ("hist6.json", hist6), ("hist7.json", hist7)):
        path = tmp_path / name
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        paths.append(path.as_posix())
    return tuple(paths)


def _facts() -> list[dict]:
    return [
        {
            "phase_id": "HIST-LONG-8",
            "entity_type": "group",
            "entity_id": "alpha",
            "metric_name": "persistence_score",
            "metric_value": 0.99,
            "window_days": 120,
            "run_id": "r1",
            "payload_jsonb": {"persistence_score": 0.99, "stability_class": "STABLE", "recurring_structures": ["alpha"]},
        },
        {
            "phase_id": "HIST-LONG-9",
            "entity_type": "metric",
            "entity_id": "drift_metric",
            "metric_name": "replay_stability_drift",
            "metric_value": -0.2,
            "window_days": 120,
            "run_id": "r2",
            "payload_jsonb": {"drift_class": "DETERIORATING"},
        },
        {
            "phase_id": "HIST-LONG-9",
            "entity_type": "metric",
            "entity_id": "fragility_metric",
            "metric_name": "emerging_fragility_score",
            "metric_value": 0.7,
            "window_days": 120,
            "run_id": "r3",
            "payload_jsonb": {"emerging_fragility_class": "DETERIORATING"},
        },
    ]


def test_deterministic_output_for_same_inputs(tmp_path: Path):
    sources = _write_sources(tmp_path)
    first = build_historical_structural_findings(source_paths=sources, observation_facts=_facts(), top_n=5)
    second = build_historical_structural_findings(source_paths=sources, observation_facts=copy.deepcopy(_facts()), top_n=5)
    assert json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    assert first["status"] == "ok"


def test_stable_ranking_tie_breaking_and_bounded_top_n(tmp_path: Path):
    report = build_historical_structural_findings(source_paths=_write_sources(tmp_path), observation_facts=_facts(), top_n=1)
    hubs = report["findings"]["persistent_structural_hubs"]
    assert len(hubs) == 1
    assert hubs[0]["name"] == "alpha"
    for section, rows in report["findings"].items():
        if section != "executive_summary":
            assert len(rows) <= 1


def test_missing_source_artifacts_fail_closed(tmp_path: Path):
    report = build_historical_structural_findings(source_paths=(tmp_path / "missing.json",), observation_facts=[], top_n=5)
    assert report["status"] == "blocked"
    assert report["missing_sources"]
    assert report["findings"]["persistent_structural_hubs"] == []
    assert "fail closed" in " ".join(report["limitations"])


def test_governance_flags_present_and_true(tmp_path: Path):
    report = build_historical_structural_findings(source_paths=_write_sources(tmp_path), observation_facts=_facts())
    expected = {
        "analysis_only",
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
    source = Path("transmission_layers/history_long/hist_intel1_historical_structural_findings.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "httpx.", ".insert(", ".upsert(", ".update(", ".delete(", "create_client(", "supabase.table("]
    assert not any(token in source for token in forbidden)


def test_no_prediction_trading_or_portfolio_recommendation_wording_in_findings(tmp_path: Path):
    report = build_historical_structural_findings(source_paths=_write_sources(tmp_path), observation_facts=_facts())
    findings_text = json.dumps(report["findings"], sort_keys=True).lower()
    banned = ["buy", "sell", "hold", "price target", "outperform", "underperform", "portfolio recommendation", "forecast"]
    assert not any(term in findings_text for term in banned)


def test_output_json_and_markdown_are_created(tmp_path: Path):
    json_path = tmp_path / "hist_intel1.json"
    md_path = tmp_path / "hist_intel1.md"
    report = run_hist_intel1(source_paths=_write_sources(tmp_path), observation_facts=_facts(), top_n=3, json_report_path=json_path, markdown_report_path=md_path)
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["phase_id"] == "HIST-INTEL-1"
    assert "# HIST-INTEL-1" in md_path.read_text(encoding="utf-8")
    assert report["output_paths"]["json_report_path"] == json_path.as_posix()


def test_confidence_labels_are_conservative(tmp_path: Path):
    sparse_source = tmp_path / "hist4.json"
    sparse_source.write_text(json.dumps({"schema_version": "hist_long4_v1", "status": "ok", "window_level_results": []}), encoding="utf-8")
    report = build_historical_structural_findings(source_paths=(sparse_source,), observation_facts=[_facts()[0]], top_n=5)
    labels = []
    for rows in report["findings"].values():
        if isinstance(rows, list):
            labels.extend(item.get("confidence_label") for item in rows if isinstance(item, dict) and "confidence_label" in item)
    assert labels
    assert set(labels) <= CONFIDENCE_LABELS
    assert "HIGH" not in labels
