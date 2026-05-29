from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from transmission_layers.history_read_model.analyst_consumption_views import (
    HARD_LIMIT,
    build_anomaly_monitor_view,
    build_change_monitor_view,
    build_consumption_view,
    build_ecosystem_briefing_view,
    build_investigation_queue_view,
    build_persistence_monitor_view,
    write_consumption_view_outputs,
)


class _Result:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class _ReadOnlyQuery:
    def __init__(self, rows: list[dict[str, Any]], calls: list[tuple[str, Any]]):
        self.rows = rows
        self.calls = calls
        self.filters: list[tuple[str, Any]] = []
        self.orders: list[tuple[str, bool]] = []
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
        self.orders.append((key, desc))
        return self

    def limit(self, value: int):
        self.calls.append(("limit", value))
        self._limit = value
        return self

    def execute(self):
        self.calls.append(("execute", None))
        rows = [row for row in self.rows if all(row.get(key) == value for key, value in self.filters)]
        for key, desc in reversed(self.orders):
            rows = sorted(rows, key=lambda row: str(row.get(key) or ""), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows)

    def insert(self, *_args: Any, **_kwargs: Any):  # pragma: no cover
        raise AssertionError("OBS-QUERY-4 consumption views must not write")

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
    fact_id: int,
    identifier: str,
    metric_value: float | str | None,
    phase_id: str,
    metric_name: str = "persistence_score",
    loaded_at: str = "2026-05-01T00:00:00Z",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "phase_id": phase_id,
        "phase_name": phase_id.lower(),
        "window_days": 30,
        "entity_type": "phase",
        "entity_id": f"{phase_id}:{identifier}",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "artifact_id": f"artifact-{fact_id}",
        "run_id": f"run-{fact_id}",
        "created_at": loaded_at,
        "loaded_at": loaded_at,
        "payload_jsonb": {"evidence_id": f"ev-{fact_id}", "identifier": identifier, "dimension": identifier, **(payload or {})},
        "duplicate_prevention_key": f"dup-{fact_id}",
    }


def _rows() -> list[dict[str, Any]]:
    return [
        _fact(fact_id=1, identifier="overlap", metric_value=0.70, phase_id="HIST-INTEL-1"),
        _fact(fact_id=2, identifier="overlap", metric_value=0.80, phase_id="OPS-LIVE2"),
        _fact(fact_id=3, identifier="live_only", metric_value=0.40, phase_id="OPS-LIVE2"),
        _fact(fact_id=4, identifier="historical_only", metric_value=0.90, phase_id="HIST-INTEL-1"),
        _fact(fact_id=5, identifier="weaker", metric_value=0.95, phase_id="HIST-INTEL-1"),
        _fact(fact_id=6, identifier="weaker", metric_value=0.55, phase_id="OPS-LIVE2"),
        _fact(fact_id=7, identifier="stronger", metric_value=0.15, phase_id="HIST-INTEL-1"),
        _fact(fact_id=8, identifier="stronger", metric_value=0.65, phase_id="OPS-LIVE2"),
        _fact(fact_id=9, identifier="recurring", metric_value=0.20, phase_id="HIST-INTEL-1", loaded_at="2026-05-02T00:00:00Z"),
        _fact(fact_id=10, identifier="recurring", metric_value=0.22, phase_id="HIST-INTEL-2", loaded_at="2026-05-03T00:00:00Z"),
        _fact(fact_id=11, identifier="recurring", metric_value=0.21, phase_id="OPS-LIVE2", loaded_at="2026-05-04T00:00:00Z"),
        _fact(fact_id=12, identifier="drift", metric_value=-0.50, phase_id="HIST-LONG-9", metric_name="replay_stability_drift", payload={"drift_class": "DETERIORATING", "stability_class_transition": "STABLE->PARTIALLY_STABLE"}),
        _fact(fact_id=13, identifier="dominant", metric_value=0.73, phase_id="HIST-INTEL-2", metric_name="sector_hhi", payload={"dominance_score": 0.73}),
        _fact(fact_id=14, identifier="morphology", metric_value=2, phase_id="HIST-INTEL-3", metric_name="morphology_recurrence", payload={"recurring_structures": ["morphology", "overlap"]}),
    ]


def _section(view: dict[str, Any], name: str) -> dict[str, Any]:
    return next(section for section in view["sections"] if section["section_name"] == name)


def test_ecosystem_briefing_generation():
    view = build_ecosystem_briefing_view(fact_rows=_rows(), limit=3)
    assert view["view_type"] == "ecosystem_briefing"
    assert {"persisted", "dominant", "recurred"} <= set(view["source_query_types"])
    assert {"baseline_overlap", "baseline_deviation", "live_anomalies"} <= set(view["source_comparison_types"])
    assert _section(view, "Persistent Structures")["item_count"] == 3
    assert _section(view, "Investigation Candidates")["items"][0]["queue_source"] == "live_only_anomaly"


def test_change_monitor_generation():
    view = build_change_monitor_view(fact_rows=_rows(), limit=5)
    assert view["view_type"] == "change_monitor"
    assert _section(view, "Changed Structures")["items"][0]["identifier"] == "drift"
    assert "persistent_weakening_live" in view["source_comparison_types"]
    assert "weak_strengthening_live" in view["source_comparison_types"]


def test_persistence_monitor_generation():
    view = build_persistence_monitor_view(fact_rows=_rows(), limit=4)
    assert view["view_type"] == "persistence_monitor"
    assert _section(view, "Historical-Live Recurrence")["item_count"] >= 1
    assert "historical_recurrence" in view["source_comparison_types"]


def test_anomaly_monitor_generation():
    view = build_anomaly_monitor_view(fact_rows=_rows(), limit=4)
    assert view["view_type"] == "anomaly_monitor"
    live_only = _section(view, "Live-Only Anomalies")
    assert live_only["items"][0]["identifier"] == "live_only"
    assert live_only["items"][0]["classification"] == "live_only"


def test_investigation_queue_generation_and_methodology():
    view = build_investigation_queue_view(fact_rows=_rows(), limit=10)
    queue = _section(view, "Investigation Queue")["items"]
    assert [item["queue_source"] for item in queue[:4]] == [
        "live_only_anomaly",
        "historical_live_deviation",
        "historical_live_deviation",
        "historical_live_deviation",
    ]
    assert all("supporting_fact_ids" in item for item in queue)
    assert "changed" in view["source_query_types"]


def test_deterministic_ordering():
    first = build_ecosystem_briefing_view(fact_rows=_rows(), limit=10)
    second = build_ecosystem_briefing_view(fact_rows=list(reversed(_rows())), limit=10)
    assert first == second


def test_bounded_limits():
    rows = []
    for i in range(700):
        rows.append(_fact(fact_id=i, identifier=f"id-{i:04d}", metric_value=0.1, phase_id="HIST-INTEL-1"))
        rows.append(_fact(fact_id=1000 + i, identifier=f"id-{i:04d}", metric_value=0.2, phase_id="OPS-LIVE2"))
    view = build_anomaly_monitor_view(fact_rows=rows, limit=9999)
    assert view["effective_limit"] == HARD_LIMIT
    assert _section(view, "Historical-Live Deviations")["item_count"] == HARD_LIMIT


def test_evidence_traceability():
    view = build_anomaly_monitor_view(fact_rows=_rows(), limit=4)
    live_only = _section(view, "Live-Only Anomalies")
    assert live_only["supporting_facts"] == ["3"]
    assert live_only["supporting_evidence"] == ["ev-3"]
    assert "3" in view["supporting_fact_ids"]
    assert "ev-3" in view["supporting_evidence_ids"]


def test_empty_results():
    view = build_ecosystem_briefing_view(fact_rows=[])
    assert all(section["item_count"] == 0 for section in view["sections"])
    assert view["supporting_fact_ids"] == []
    assert view["supporting_evidence_ids"] == []


def test_output_generation(tmp_path: Path):
    view = build_ecosystem_briefing_view(fact_rows=_rows(), limit=2)
    output_json = tmp_path / "obs_query4.json"
    output_md = tmp_path / "obs_query4.md"
    paths = write_consumption_view_outputs(view, output_json=output_json, output_md=output_md)
    assert paths == {"output_json": str(output_json), "output_md": str(output_md)}
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert payload["schema_version"] == "obs_query4_analyst_consumption_view_v1"
    assert "# View Summary" in markdown
    assert "## Supporting Facts" in markdown
    assert "## Supporting Evidence" in markdown
    assert "## Governance Certification" in markdown


def test_cli_execution(tmp_path: Path):
    local_rows = tmp_path / "facts.json"
    output_json = tmp_path / "cli.json"
    output_md = tmp_path / "cli.md"
    local_rows.write_text(json.dumps(_rows()), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_obs_query4_consumption_view.py",
            "--view-type",
            "ecosystem_briefing",
            "--local-facts-json",
            str(local_rows),
            "--limit",
            "2",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(completed.stdout)
    assert summary["status"] == "ok"
    assert summary["view_type"] == "ecosystem_briefing"
    assert json.loads(output_json.read_text(encoding="utf-8"))["effective_limit"] == 2
    assert "OBS-QUERY-4" in output_md.read_text(encoding="utf-8")


def test_no_db_writes_with_client():
    client = _ReadOnlyClient(_rows())
    view = build_ecosystem_briefing_view(client=client, limit=2)
    methods = [name for name, _ in client.calls]
    assert view["sections"]
    assert "execute" in methods
    assert not ({"insert", "upsert", "update", "delete"} & set(methods))
    assert view["governance_certification"]["db_writes_enabled"] is False


def test_no_provider_calls_governance():
    view = build_consumption_view(view_type="anomaly_monitor", fact_rows=_rows())
    assert view["governance_certification"]["provider_api_calls_enabled"] is False
    assert view["governance_certification"]["no_new_intelligence_generation"] is True
    assert view["governance_certification"]["source_of_truth"] == "sefi_observation_facts"
