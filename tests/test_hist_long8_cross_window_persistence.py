from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from transmission_layers.history_long.hist_long8_cross_window_persistence import (
    PHASE_ID,
    build_hist_long8_analysis,
    build_hist_long8_fact_rows,
    build_hist_long8_observations,
    build_hist_long8_report,
    run_hist_long8,
)
from transmission_layers.history_read_model.fact_emitter import MAX_PAYLOAD_BYTES


def _window(days: int, *, replay_density=0.5, sector_hhi=0.06, weak_symbols=None):
    sectors = [
        {"sector": "semiconductors", "rank": 1, "share": 0.20},
        {"sector": "energy", "rank": 2, "share": 0.12},
        {"sector": "healthcare", "rank": 3, "share": 0.10},
    ]
    subsectors = [
        {"subsector": "chips", "rank": 1, "share": 0.18},
        {"subsector": "oil", "rank": 2, "share": 0.11},
    ]
    return {
        "window_days": days,
        "replay_density": replay_density,
        "replay_saturation": 0.40,
        "contradiction_burden": 0.10,
        "sector_hhi": {"universe_hhi": sector_hhi, "strongest_sectors": sectors},
        "subsector_hhi": {"universe_hhi": 0.05, "strongest_subsectors": subsectors},
        "effective_symbol_count": 240,
        "weak_symbols": weak_symbols or [],
    }


def _windows():
    return [
        _window(20, weak_symbols=["AAA", "BBB"]),
        _window(60, replay_density=0.52, sector_hhi=0.061, weak_symbols=["AAA", "CCC"]),
        _window(120, replay_density=0.51, sector_hhi=0.059, weak_symbols=["AAA", "DDD"]),
    ]


def _foxa_facts():
    return [
        {"entity_type": "symbol", "entity_id": "FOXA", "window_days": 20, "metric_name": "foxa_signal", "metric_value": 0.7},
        {"entity_type": "symbol", "entity_id": "FOXA", "window_days": 60, "metric_name": "foxa_signal", "metric_value": 0.69},
        {"entity_type": "symbol", "entity_id": "FOXA", "window_days": 120, "metric_name": "foxa_signal", "metric_value": 0.71},
    ]


def test_deterministic_analysis_output():
    a = build_hist_long8_analysis(window_metrics=_windows(), observation_facts=_foxa_facts())
    b = build_hist_long8_analysis(window_metrics=copy.deepcopy(_windows()), observation_facts=copy.deepcopy(_foxa_facts()))

    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_correct_20_60_120_window_handling():
    analysis = build_hist_long8_analysis(window_metrics=[_window(5), *_windows(), _window(252)])

    assert analysis["completed_windows"] == [20, 60, 120]
    assert analysis["status"] == "ok"


def test_persistence_score_calculation_and_stability_classification():
    analysis = build_hist_long8_analysis(window_metrics=_windows())
    replay = analysis["cross_window_comparison"]["replay_density"]

    assert replay["persistence_score"] == pytest.approx(0.98)
    assert replay["stability_class"] == "STABLE"

    volatile = build_hist_long8_analysis(window_metrics=[_window(20, replay_density=0.1), _window(60, replay_density=0.9), _window(120, replay_density=0.2)])
    assert volatile["cross_window_comparison"]["replay_density"]["stability_class"] == "VOLATILE"


def test_insufficient_data_fail_closed_behavior():
    analysis = build_hist_long8_analysis(window_metrics=[_window(20)])

    assert analysis["status"] == "blocked"
    assert analysis["cross_window_comparison"]["replay_density"]["stability_class"] == "INSUFFICIENT_DATA"
    assert analysis["confidence_assessment"] == "low_insufficient_required_windows"


def test_observation_generation_is_deterministic_and_contains_required_metrics():
    analysis = build_hist_long8_analysis(window_metrics=_windows(), observation_facts=_foxa_facts())
    first = build_hist_long8_observations(analysis)
    second = build_hist_long8_observations(copy.deepcopy(analysis))
    metrics = {row["metric_name"] for row in first}

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    for metric in (
        "persistence_score",
        "stability_class",
        "replay_density",
        "replay_saturation",
        "contradiction_burden",
        "sector_hhi",
        "subsector_hhi",
        "effective_symbol_count",
        "weak_symbol_persistence",
        "sector_morphology_persistence",
        "subsector_morphology_persistence",
        "foxa_persistence",
    ):
        assert metric in metrics


def test_fact_row_generation_deterministic_dry_run_default_and_bounded_payloads():
    analysis = build_hist_long8_analysis(window_metrics=_windows(), observation_facts=_foxa_facts())

    assert build_hist_long8_fact_rows(analysis) == []
    rows = build_hist_long8_fact_rows(analysis, enabled=True)
    again = build_hist_long8_fact_rows(copy.deepcopy(analysis), enabled=True)

    assert json.dumps(rows, sort_keys=True, default=str) == json.dumps(again, sort_keys=True, default=str)
    assert rows
    assert len({row["duplicate_prevention_key"] for row in rows}) == len(rows)
    assert {row["phase_id"] for row in rows} == {PHASE_ID}
    for row in rows:
        assert len(json.dumps(row["payload_jsonb"], sort_keys=True).encode("utf-8")) <= MAX_PAYLOAD_BYTES


class _WriteClient:
    def __init__(self):
        self.inserted = False

    def table(self, name):
        self.name = name
        return self

    def insert(self, rows):
        self.inserted = True
        self.rows = rows
        return self

    def execute(self):
        return {"data": []}


def test_no_db_write_unless_explicitly_enabled(tmp_path: Path):
    source = tmp_path / "hist4.json"
    source.write_text(json.dumps({"window_level_results": _windows()}), encoding="utf-8")
    client = _WriteClient()

    result = run_hist_long8(hist_long4_source_path=str(source), report_path=str(tmp_path / "report.md"), enabled=False)

    assert result["fact_rows"] == []
    assert result["fact_emission"]["inserted_rows"] == 0
    assert client.inserted is False


def test_no_provider_fmp_prediction_trading_live_ingestion_or_replay_paths():
    analysis = build_hist_long8_analysis(window_metrics=_windows())
    governance = analysis["governance_review"]

    for key in (
        "fmp_calls_enabled",
        "provider_api_calls_enabled",
        "live_ingestion_enabled",
        "replay_execution_enabled",
        "prediction_enabled",
        "trading_execution_enabled",
        "topology_persistence_enabled",
    ):
        assert governance[key] is False


def test_report_generation(tmp_path: Path):
    source = tmp_path / "hist4.json"
    report = tmp_path / "hist_long8.md"
    source.write_text(json.dumps({"window_level_results": _windows()}), encoding="utf-8")

    result = run_hist_long8(hist_long4_source_path=str(source), report_path=str(report))
    report_text = report.read_text(encoding="utf-8")

    assert result["analysis"]["status"] == "ok"
    assert "Objective" in report_text
    assert "Governance Review" in report_text
    assert "FOXA Persistence" in report_text
