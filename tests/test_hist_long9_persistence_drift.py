from __future__ import annotations

import copy
import json
from pathlib import Path

from transmission_layers.history_long.hist_long8_cross_window_persistence import build_hist_long8_analysis, build_hist_long8_fact_rows
from transmission_layers.history_long.hist_long9_persistence_drift import (
    PHASE_ID,
    build_hist_long9_analysis,
    build_hist_long9_fact_rows,
    build_hist_long9_observations,
    build_hist_long9_report,
    run_hist_long9,
)
from transmission_layers.history_read_model.fact_emitter import MAX_PAYLOAD_BYTES


def _window(days: int, *, replay_density=0.50, contradiction_burden=0.10, sector_hhi=0.06, weak_symbols=None):
    sectors = [{"sector": "technology", "rank": 1, "share": 0.20}, {"sector": "energy", "rank": 2, "share": 0.12}]
    subsectors = [{"subsector": "software", "rank": 1, "share": 0.18}, {"subsector": "oil", "rank": 2, "share": 0.10}]
    return {
        "window_days": days,
        "replay_density": replay_density,
        "replay_saturation": 0.40,
        "contradiction_burden": contradiction_burden,
        "sector_hhi": {"universe_hhi": sector_hhi, "strongest_sectors": sectors},
        "subsector_hhi": {"universe_hhi": 0.05, "strongest_subsectors": subsectors},
        "effective_symbol_count": 200,
        "weak_symbols": weak_symbols or [],
    }


def _hist8_rows(run_id: str, windows) -> list[dict]:
    analysis = build_hist_long8_analysis(window_metrics=windows)
    return [dict(row) for row in build_hist_long8_fact_rows(analysis, enabled=True, artifact_id=f"artifact-{run_id}", run_id=run_id)]


def _stable_windows():
    return [
        _window(20, weak_symbols=["AAA", "BBB"]),
        _window(60, replay_density=0.51, weak_symbols=["AAA", "CCC"]),
        _window(120, replay_density=0.50, weak_symbols=["AAA", "DDD"]),
    ]


def _deteriorating_windows():
    return [
        _window(20, replay_density=0.10, contradiction_burden=0.80, sector_hhi=0.02, weak_symbols=["AAA"]),
        _window(60, replay_density=0.90, contradiction_burden=0.15, sector_hhi=0.70, weak_symbols=["BBB"]),
        _window(120, replay_density=0.20, contradiction_burden=0.70, sector_hhi=0.10, weak_symbols=["CCC"]),
    ]


def _facts_two_runs():
    return _hist8_rows("run-a", _stable_windows()) + _hist8_rows("run-b", _deteriorating_windows())


def test_deterministic_analysis_output_and_fact_native_input_usage():
    facts = _facts_two_runs()
    a = build_hist_long9_analysis(observation_facts=facts)
    b = build_hist_long9_analysis(observation_facts=copy.deepcopy(facts))

    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)
    assert a["snapshot_count"] == 2
    assert a["inspected_fact_sources"] == ["sefi_observation_facts:HIST-LONG-8"]


def test_no_report_parsing_and_insufficient_data_fail_closed(tmp_path: Path):
    fake_hist8_report = tmp_path / "hist_long8_cross_window_persistence.md"
    fake_hist8_report.write_text("replay_density: score=0.1 class=VOLATILE", encoding="utf-8")

    analysis = build_hist_long9_analysis(observation_facts=[])

    assert analysis["status"] == "blocked"
    assert analysis["overall_drift_class"] == "INSUFFICIENT_DATA"
    assert analysis["metric_level_drift_analysis"]["replay_stability_drift"]["drift_class"] == "INSUFFICIENT_DATA"


def test_drift_classification_transition_and_emerging_fragility_detection():
    analysis = build_hist_long9_analysis(observation_facts=_facts_two_runs())
    replay = analysis["metric_level_drift_analysis"]["replay_stability_drift"]

    assert replay["drift_class"] == "DETERIORATING"
    assert replay["stability_class_transition"] == "STABLE->VOLATILE"
    assert analysis["emerging_fragility_assessment"]["emerging_fragility_class"] in {"MIXED", "DETERIORATING"}
    assert analysis["stability_class_transitions"]["replay_stability_drift"] == "STABLE->VOLATILE"


def test_mixed_and_stable_drift_classification_logic():
    stable = build_hist_long9_analysis(observation_facts=_hist8_rows("run-a", _stable_windows()) + _hist8_rows("run-b", _stable_windows()))
    assert stable["metric_level_drift_analysis"]["replay_stability_drift"]["drift_class"] == "STABLE"

    mixed_facts = _facts_two_runs()
    for row in mixed_facts:
        if row["run_id"] == "run-b" and row["metric_name"] == "replay_density":
            row["metric_value"] = 1.1
            row["payload_jsonb"]["persistence_score"] = 1.1
            row["payload_jsonb"]["stability_class"] = "VOLATILE"
    mixed = build_hist_long9_analysis(observation_facts=mixed_facts)
    assert mixed["metric_level_drift_analysis"]["replay_stability_drift"]["drift_class"] == "MIXED"


def test_deterministic_observation_and_fact_row_generation_with_bounded_payloads():
    analysis = build_hist_long9_analysis(observation_facts=_facts_two_runs())
    observations = build_hist_long9_observations(analysis)
    again = build_hist_long9_observations(copy.deepcopy(analysis))

    assert json.dumps(observations, sort_keys=True, default=str) == json.dumps(again, sort_keys=True, default=str)
    metric_names = {row["metric_name"] for row in observations}
    for metric in (
        "persistence_drift_score",
        "persistence_drift_class",
        "replay_stability_drift",
        "contradiction_stability_drift",
        "concentration_stability_drift",
        "morphology_persistence_drift",
        "weak_symbol_persistence_drift",
        "foxa_persistence_drift",
        "stability_class_transition",
        "emerging_fragility_score",
        "emerging_fragility_class",
    ):
        assert metric in metric_names

    assert build_hist_long9_fact_rows(analysis) == []
    rows = build_hist_long9_fact_rows(analysis, enabled=True)
    assert rows
    assert {row["phase_id"] for row in rows} == {PHASE_ID}
    assert len({row["duplicate_prevention_key"] for row in rows}) == len(rows)
    for row in rows:
        assert len(json.dumps(row["payload_jsonb"], sort_keys=True, default=str).encode("utf-8")) <= MAX_PAYLOAD_BYTES


class _ReadOnlyQuery:
    def __init__(self, rows):
        self.rows = rows
        self.inserted = False

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self.rows = [row for row in self.rows if row.get(key) == value]
        return self

    def order(self, *_args, **_kwargs):
        return self

    def insert(self, _rows):
        self.inserted = True
        return self

    def execute(self):
        return type("Result", (), {"data": self.rows})()


class _Client:
    def __init__(self, rows):
        self.query = _ReadOnlyQuery(rows)

    def table(self, name):
        self.table_name = name
        return self.query


def test_db2_dry_run_defaults_and_no_db_write_unless_explicitly_enabled(tmp_path: Path):
    client = _Client(_facts_two_runs())
    result = run_hist_long9(client=client, report_path=str(tmp_path / "report.md"), enabled=False)

    assert result["analysis"]["snapshot_count"] == 2
    assert result["fact_rows"] == []
    assert result["fact_emission"]["dry_run"] is True
    assert result["fact_emission"]["inserted_rows"] == 0
    assert client.query.inserted is False

    dry_run_result = run_hist_long9(client=_Client(_facts_two_runs()), report_path=None, enabled=True, dry_run=True)
    assert dry_run_result["fact_rows"]
    assert dry_run_result["fact_emission"]["attempted_rows"] == len(dry_run_result["fact_rows"])
    assert dry_run_result["fact_emission"]["inserted_rows"] == 0


def test_no_provider_api_fmp_prediction_trading_live_ingestion_or_replay_paths():
    governance = build_hist_long9_analysis(observation_facts=_facts_two_runs())["governance_review"]

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
    report_path = tmp_path / "hist_long9.md"
    result = run_hist_long9(observation_facts=_facts_two_runs(), report_path=str(report_path))
    report_text = report_path.read_text(encoding="utf-8")

    assert result["analysis"]["status"] == "ok"
    assert "Objective" in report_text
    assert "Inspected Fact Sources" in report_text
    assert "Metric-Level Drift Analysis" in report_text
    assert "Governance Review" in report_text
    assert build_hist_long9_report(result["analysis"]) == result["report"]
