from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from transmission_layers.history_read_model.observation_query import (
    build_observation_intelligence_report,
    get_fragility_leaderboard,
    get_latest_metric_snapshot,
    get_metric_series,
    get_morphology_recurrence,
    get_observation_fact_summary,
    get_stability_transition_summary,
    get_top_deteriorating_metrics,
    get_top_persistent_structures,
)


class _Result:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class _ReadOnlyQuery:
    def __init__(self, rows: list[dict[str, Any]], calls: list[tuple[str, Any]]):
        self.rows = rows
        self.calls = calls
        self.filters: list[tuple[str, Any]] = []
        self._limit: int | None = None

    def select(self, columns: str):
        self.calls.append(("select", columns))
        return self

    def eq(self, key: str, value: Any):
        self.calls.append(("eq", (key, value)))
        self.filters.append((key, value))
        return self

    def order(self, key: str, desc: bool = False):
        self.calls.append(("order", (key, desc)))
        self.rows = sorted(self.rows, key=lambda row: str(row.get(key) or ""), reverse=desc)
        return self

    def limit(self, value: int):
        self.calls.append(("limit", value))
        self._limit = value
        return self

    def execute(self):
        self.calls.append(("execute", None))
        rows = [row for row in self.rows if all(row.get(key) == value for key, value in self.filters)]
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows)

    def insert(self, *_args: Any, **_kwargs: Any):  # pragma: no cover - fail if called
        raise AssertionError("OBS-QUERY-1 must not write")

    upsert = update = delete = insert


class _ReadOnlyClient:
    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows
        self.calls: list[tuple[str, Any]] = []

    def table(self, name: str):
        self.calls.append(("table", name))
        assert name == "sefi_observation_facts"
        return _ReadOnlyQuery(copy.deepcopy(self.rows), self.calls)


def _fact(
    *,
    phase_id: str = "HIST-LONG-8",
    loaded_at: str = "2026-05-01T00:00:00Z",
    run_id: str = "run-1",
    entity_id: str = "HIST-LONG-8:replay_density",
    metric_name: str = "persistence_score",
    metric_value: float | None = 0.9,
    payload: dict[str, Any] | None = None,
    window_days: int | None = None,
) -> dict[str, Any]:
    return {
        "phase_id": phase_id,
        "phase_name": phase_id.lower(),
        "window_days": window_days,
        "entity_type": "phase",
        "entity_id": entity_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "artifact_id": f"artifact-{run_id}",
        "run_id": run_id,
        "loaded_at": loaded_at,
        "payload_jsonb": payload or {},
    }


def _rows() -> list[dict[str, Any]]:
    return [
        _fact(loaded_at="2026-05-01T00:00:00Z", run_id="run-1", entity_id="HIST-LONG-8:replay_density", metric_value=0.92, payload={"dimension": "replay_density", "stability_class": "STABLE"}),
        _fact(loaded_at="2026-05-02T00:00:00Z", run_id="run-2", entity_id="HIST-LONG-8:sector_morphology_persistence", metric_value=0.97, payload={"dimension": "sector_morphology_persistence", "stability_class": "STABLE", "recurring_structures": ["technology", "communication_services"]}),
        _fact(phase_id="HIST-LONG-9", loaded_at="2026-05-03T00:00:00Z", run_id="run-3", entity_id="HIST-LONG-9:replay_stability_drift", metric_name="replay_stability_drift", metric_value=-0.07, payload={"drift_class": "DETERIORATING", "stability_class_transition": "STABLE->PARTIALLY_STABLE"}),
        _fact(phase_id="HIST-LONG-9", loaded_at="2026-05-04T00:00:00Z", run_id="run-4", entity_id="HIST-LONG-9:concentration_stability_drift", metric_name="concentration_stability_drift", metric_value=-0.02, payload={"drift_class": "MIXED", "stability_class_transition": "PARTIALLY_STABLE->VOLATILE"}),
        _fact(phase_id="HIST-LONG-9", loaded_at="2026-05-05T00:00:00Z", run_id="run-5", entity_id="HIST-LONG-9:emerging_fragility", metric_name="emerging_fragility_score", metric_value=0.75, payload={"emerging_fragility_class": "DETERIORATING"}),
        _fact(phase_id="HIST-LONG-9", loaded_at="2026-05-06T00:00:00Z", run_id="run-6", entity_id="HIST-LONG-9:insufficient", metric_name="persistence_drift_class", metric_value=None, payload={"drift_class": "INSUFFICIENT_DATA", "stability_class": "INSUFFICIENT_DATA"}),
    ]


def test_deterministic_local_fact_summary_and_no_mutation():
    rows = _rows()
    original = copy.deepcopy(rows)
    first = build_observation_intelligence_report(fact_rows=rows)
    second = build_observation_intelligence_report(fact_rows=copy.deepcopy(rows))
    assert first == second
    assert rows == original
    assert first["source_table"] == "sefi_observation_facts"
    assert first["source_behavior"] == "bounded_local_fact_rows"
    assert first["summary"]["row_count"] == 6


def test_fact_native_input_usage_and_no_report_parsing(tmp_path: Path):
    rows = _rows()
    fake_report = tmp_path / "old_report.md"
    fake_report.write_text("this must not be parsed: FOXA 999", encoding="utf-8")
    out = tmp_path / "obs_query1.md"
    result = build_observation_intelligence_report(fact_rows=rows, report_path=out)
    assert out.exists()
    assert "FOXA 999" not in result["report"]
    assert "OBS-QUERY-1" in out.read_text(encoding="utf-8")


def test_read_only_client_query_behavior():
    client = _ReadOnlyClient(_rows())
    series = get_metric_series(client=client, phase_id="HIST-LONG-9", metric_name="replay_stability_drift")
    assert len(series) == 1
    methods = [name for name, _ in client.calls]
    assert methods == ["table", "select", "eq", "eq", "order", "limit", "execute"]
    assert not ({"insert", "upsert", "update", "delete"} & set(methods))


def test_top_persistent_structure_ranking():
    ranked = get_top_persistent_structures(fact_rows=_rows())
    assert ranked[0]["structure"] == "sector_morphology_persistence"
    assert ranked[0]["persistence_score"] == 0.97


def test_deteriorating_metric_ranking():
    ranked = get_top_deteriorating_metrics(fact_rows=_rows())
    assert ranked[0]["metric_name"] == "replay_stability_drift"
    assert ranked[0]["drift_class"] == "DETERIORATING"


def test_fragility_leaderboard():
    ranked = get_fragility_leaderboard(fact_rows=_rows())
    assert ranked == [{"entity_id": "HIST-LONG-9:emerging_fragility", "emerging_fragility_score": 0.75, "emerging_fragility_class": "DETERIORATING", "phase_id": "HIST-LONG-9"}]


def test_morphology_recurrence():
    recurrence = get_morphology_recurrence(fact_rows=_rows())
    assert recurrence[0]["morphology"] == "communication_services"
    assert recurrence[0]["recurrence_count"] == 1


def test_stability_transition_summary_and_insufficient_data():
    summary = get_stability_transition_summary(fact_rows=_rows())
    assert summary["transition_counts"]["STABLE->PARTIALLY_STABLE"] == 1
    assert summary["transition_counts"]["PARTIALLY_STABLE->VOLATILE"] == 1
    assert summary["insufficient_data_count"] >= 1


def test_metric_series_and_latest_snapshot():
    rows = _rows()
    series = get_metric_series(fact_rows=rows, metric_name="persistence_score")
    assert [item["metric_value"] for item in series] == [0.92, 0.97]
    latest = get_latest_metric_snapshot(fact_rows=rows, metric_name="persistence_score")
    assert latest["available"] is True
    assert latest["latest"]["metric_value"] == 0.97


def test_summary_local_bounded_fallback():
    rows = _rows() * 300
    summary = get_observation_fact_summary(fact_rows=rows, limit=1000)
    assert summary["source"] == "bounded_local_observation_facts"
    assert summary["row_count"] == 1000


def test_report_contains_required_intelligence_sections_and_governance_flags():
    result = build_observation_intelligence_report(fact_rows=_rows())
    assert result["top_persistent_structures"]
    assert result["top_deteriorating_metrics"]
    assert result["fragility_leaderboard"]
    assert result["morphology_recurrence"]
    assert result["replay_stability_trend_summary"]["trend"] == "DETERIORATING"
    assert result["governance_review"]["provider_api_calls_enabled"] is False
    assert result["governance_review"]["fact_emission_enabled"] is False
